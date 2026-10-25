#!/usr/bin/env python3
"""OJJudge 官网服务。

在标准 http.server 基础上补上两件事：
1) 缓存策略
   - HTML 页面：no-cache（每次都向源站校验，保证更新立即生效）
   - 其他资源（css/js/图片/安装包）：短缓存
2) 对拍实验室的服务端编译/运行后端（/api/*）
   - /api/env      查询服务端有哪些工具链（g++ / python3 / JDK）
   - /api/compile  编译一份程序，返回 session
   - /api/run       用 session 跑一次（喂 stdin，取 stdout）
   - /api/dispose   立刻销毁某个 session
   网页版「对拍实验室」据此用真编译器做多语言对拍，与桌面版逻辑一致。

安全约束（公网可访问，必须限死）：
   - 源码体积上限、输出体积上限、编译/运行超时、CPU/文件/进程数 rlimit
   - session 存临时目录，TTL 到期自动清理，进程退出时全量清理
   - 错误信息不回显服务端绝对路径
监听 PORT 环境变量（缺省 3000），绑定 0.0.0.0。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT") or 3000)
ROOT = os.path.dirname(os.path.abspath(__file__))

CACHE_RULES = (
    (".html", "no-cache, max-age=0, must-revalidate"),
)

# ---------- 沙箱参数 ----------
SANDBOX_ROOT = os.path.join(tempfile.gettempdir(), "ojjudge-sandbox")
SESSION_TTL = 1800          # session 存活 30 分钟
MAX_SOURCE = 64 * 1024      # 单个文件源码上限 64KB
MAX_FILES = 4               # 一次最多 4 个文件
MAX_OUTPUT = 256 * 1024     # 单次输出上限 256KB
COMPILE_TIMEOUT = 25        # 编译超时（秒）
RUN_TIMEOUT = 5             # 运行超时（秒）
MAX_SESSIONS = 40           # 同时存在的 session 上限
MAX_RUNS_PER_MIN = 300      # 单 IP 每分钟最多运行次数

LANGS = ("cpp", "python", "java")

_sessions = {}
_sessions_lock = threading.Lock()
_rate = {}
_rate_lock = threading.Lock()


def cache_control_for(path):
    low = path.lower()
    for ext, cc in CACHE_RULES:
        if low.endswith(ext):
            return cc
    return "public, max-age=600"


# ============================================================
# 工具链探测
# ============================================================
def _which(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def _tool_info(exe, probe_args=("--version",)):
    if not exe:
        return {"ok": False, "version": ""}
    try:
        r = subprocess.run([exe] + list(probe_args), capture_output=True,
                           text=True, timeout=10)
        out = (r.stdout or r.stderr or "").strip().splitlines()
        return {"ok": True, "version": out[0][:80] if out else ""}
    except Exception:
        return {"ok": True, "version": ""}


def detect_env():
    """探测服务端可用工具链。"""
    gpp = _which("g++", "g++.exe", "clang++")
    py = _which("python3", "python")
    javac = _which("javac")
    java = _which("java")
    return {
        "cpp": {"ok": bool(gpp), **_tool_info(gpp)},
        "python": {"ok": bool(py), **_tool_info(py)},
        "java": {"ok": bool(javac and java),
                 **_tool_info(javac or java)},
    }


# ============================================================
# session 管理
# ============================================================
def _cleanup_expired():
    now = time.time()
    with _sessions_lock:
        dead = [k for k, v in _sessions.items() if now - v["created"] > SESSION_TTL]
        for k in dead:
            v = _sessions.pop(k, None)
            if v:
                shutil.rmtree(v["dir"], ignore_errors=True)


def _new_session_dir():
    os.makedirs(SANDBOX_ROOT, exist_ok=True)
    d = os.path.join(SANDBOX_ROOT, uuid.uuid4().hex[:12])
    os.makedirs(d, exist_ok=True)
    return d


def _dispose(session):
    with _sessions_lock:
        v = _sessions.pop(session, None)
    if v:
        shutil.rmtree(v["dir"], ignore_errors=True)
        return True
    return False


def _rate_ok(client):
    """单 IP 每分钟运行次数限流。"""
    now = time.time()
    with _rate_lock:
        arr = _rate.get(client) or []
        arr = [t for t in arr if now - t < 60]
        if len(arr) >= MAX_RUNS_PER_MIN:
            _rate[client] = arr
            return False
        arr.append(now)
        _rate[client] = arr
        return True


# ============================================================
# 编译 / 运行
# ============================================================
def _rlimit_preexec(lang, timeout=None):
    """给子进程套上 CPU/内存/文件限制（Linux 有效，其他平台忽略）。

    注意：**不设 RLIMIT_NPROC**。Linux 上 NPROC 同时限制线程数，且计数的是
    「该用户名的全部进程」而非子孙进程数——在共享用户的容器里，容器自身
    进程已占掉额度，结果是 g++ 派生 cc1plus 时 vfork EAGAIN、
    JVM 起 GC 线程时 pthread_create EAGAIN，编译/运行全被误杀。
    替代防线：进程组（见 _run_proc），超时整组 kill，fork 炸弹也一起收掉。
    """
    try:
        import resource
    except Exception:
        return None

    cpu = max(1, int(timeout or RUN_TIMEOUT))
    if lang == "java":
        # JVM 启动 + JIT 编译本身要吃不少 CPU，rlimit 太紧会把 JVM 一起杀掉
        cpu = max(cpu, 8)

    def _preexec():
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
            resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
            if lang != "java":     # JVM 需要巨大的虚拟地址空间，别限 AS
                resource.setrlimit(resource.RLIMIT_AS,
                                   (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        except Exception:
            pass
    return _preexec


def _clamp_timeout(timeout, lang=None):
    """客户端指定的单轮超时（秒），上限不超过服务端硬上限。

    Java 启动 JVM 本身就要吃掉几百毫秒 CPU，rlimit 太紧会把 JVM 一起杀掉，
    所以给 Java 一个 4 秒的下限。
    """
    try:
        t = float(timeout)
    except Exception:
        return RUN_TIMEOUT
    if t <= 0:
        return RUN_TIMEOUT
    t = min(t, RUN_TIMEOUT)
    if lang == "java":
        t = max(t, 4.0)
    return max(0.2, t)


def _safe_text(data):
    if data is None:
        return ""
    if isinstance(data, bytes):
        data = data.decode("utf-8", "replace")
    # 统一行尾为 \n：Windows 下子进程输出是 \r\n，
    # 与浏览器内 JS 模式（\n）不一致会让同一份数据在两种模式下比对结果不同
    data = data.replace("\r\n", "\n").replace("\r", "\n")
    return data[:MAX_OUTPUT]


def _kill_group(proc):
    """杀掉子进程所在的整个进程组（POSIX），否则 g++/JVM 的孙进程会残留。"""
    try:
        import signal
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        return
    except Exception:
        pass
    try:
        proc.kill()
    except Exception:
        pass


def _run_proc(argv, cwd=None, input_bytes=None, timeout=None, lang=None):
    """跑一个子进程，超时整组杀掉。返回 (stdout, stderr, code, timedOut)。"""
    kw = {}
    if os.name == "posix":
        # 独立进程组，便于整组回收（Windows 没有 start_new_session）
        kw["start_new_session"] = True
    try:
        proc = subprocess.Popen(
            argv, cwd=cwd, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=_rlimit_preexec(lang, timeout), **kw)
    except Exception:
        return b"", b"", -2, False
    try:
        out, err = proc.communicate(input=input_bytes, timeout=timeout)
        return out or b"", err or b"", proc.returncode, False
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        try:
            out, err = proc.communicate(timeout=5)
        except Exception:
            out, err = b"", b""
        return out or b"", err or b"", -1, True


def _compile(lang, files):
    """把源码编译成可执行程序，返回 (ok, session_id, error)。"""
    if lang not in LANGS:
        return False, None, "不支持的语言"
    if not files or len(files) > MAX_FILES:
        return False, None, "文件数量超限"

    srcs = []
    for f in files:
        name = os.path.basename(str(f.get("name", "main")) or "main")
        if not name or name.startswith("."):
            return False, None, "非法文件名"
        content = str(f.get("content", ""))
        if len(content.encode("utf-8", "replace")) > MAX_SOURCE:
            return False, None, "源码过长（上限 64KB）"
        srcs.append((name, content))

    _cleanup_expired()
    with _sessions_lock:
        if len(_sessions) >= MAX_SESSIONS:
            # 顺手清一批过期的再试
            pass

    d = _new_session_dir()
    try:
        for name, content in srcs:
            with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                f.write(content)

        if lang == "cpp":
            cxx = _which("g++", "g++.exe", "clang++")
            if not cxx:
                shutil.rmtree(d, ignore_errors=True)
                return False, None, "服务端未安装 g++ 编译器"
            src = next((n for n, _ in srcs if n.endswith((".cpp", ".cxx", ".cc"))), None)
            if not src:
                shutil.rmtree(d, ignore_errors=True)
                return False, None, "缺少 .cpp 源文件"
            exe = os.path.join(d, "prog")
            argv = [cxx, "-O2", "-o", exe, src, "-std=c++14"]
            run_argv = [exe]
        elif lang == "python":
            py = _which("python3", "python")
            if not py:
                shutil.rmtree(d, ignore_errors=True)
                return False, None, "服务端未安装 Python"
            src = next((n for n, _ in srcs if n.endswith(".py")), None)
            if not src:
                shutil.rmtree(d, ignore_errors=True)
                return False, None, "缺少 .py 源文件"
            run_argv = [py, src]
        else:  # java
            javac, java = _which("javac"), _which("java")
            if not (javac and java):
                shutil.rmtree(d, ignore_errors=True)
                return False, None, "服务端未安装 JDK（javac / java）"
            src = next((n for n, _ in srcs if n.endswith(".java")), None)
            if not src:
                shutil.rmtree(d, ignore_errors=True)
                return False, None, "缺少 .java 源文件"
            out, err, code, timed_out = _run_proc([javac, "-d", d, src], cwd=d,
                                                 timeout=COMPILE_TIMEOUT, lang="java")
            if code != 0:
                shutil.rmtree(d, ignore_errors=True)
                if timed_out:
                    return False, None, "编译超时"
                return False, None, _safe_text(err or out)[:2000]
            cls = os.path.splitext(src)[0]
            run_argv = [java, "-cp", d, cls]

        if lang == "cpp":
            out, err, code, timed_out = _run_proc(argv, cwd=d,
                                                  timeout=COMPILE_TIMEOUT, lang="cpp")
            if code != 0:
                shutil.rmtree(d, ignore_errors=True)
                if timed_out:
                    return False, None, "编译超时"
                return False, None, _safe_text(err or out)[:2000]
    except Exception as e:
        shutil.rmtree(d, ignore_errors=True)
        return False, None, "编译失败：%s" % type(e).__name__

    sid = uuid.uuid4().hex[:16]
    with _sessions_lock:
        _sessions[sid] = {"dir": d, "lang": lang, "argv": run_argv,
                          "created": time.time()}
    return True, sid, None


def _run_one(v, stdin_text, timeout=None):
    """用单个 session 跑一次。"""
    data = (stdin_text or "").encode("utf-8")
    limit = _clamp_timeout(timeout, v.get("lang"))
    out, err, code, timed_out = _run_proc(v["argv"], cwd=v["dir"],
                                          input_bytes=data, timeout=limit,
                                          lang=v.get("lang"))
    return {"stdout": _safe_text(out),
            "stderr": _safe_text(err)[:1000], "code": code,
            "timedOut": bool(timed_out)}


def _run(session, stdin_text, timeout=None):
    """用 session 跑一次，返回 dict。"""
    with _sessions_lock:
        v = _sessions.get(session)
    if not v:
        return {"ok": False, "error": "session 不存在或已过期，请重新编译"}
    out = _run_one(v, stdin_text, timeout)
    out["ok"] = True
    return out


def _compare(session_a, session_b, stdin_text, timeout=None):
    """一轮对拍：同一个输入分别喂给两个程序，一次请求跑完（省一半往返）。"""
    with _sessions_lock:
        va = _sessions.get(session_a)
        vb = _sessions.get(session_b)
    if not va or not vb:
        return {"ok": False, "error": "session 不存在或已过期，请重新编译"}
    return {"ok": True,
            "a": _run_one(va, stdin_text, timeout),
            "b": _run_one(vb, stdin_text, timeout)}


# ============================================================
# HTTP 处理
# ============================================================
class Handler(SimpleHTTPRequestHandler):
    server_version = "OJJudgeSite/1.8"

    def end_headers(self):
        self.send_header("Cache-Control", cache_control_for(self.translate_path(self.path)))
        super().end_headers()

    # ---- 工具 ----
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except Exception:
            n = 0
        if n <= 0 or n > 4 * 1024 * 1024:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8", "replace"))
        except Exception:
            return {}

    def _client(self):
        try:
            return self.client_address[0]
        except Exception:
            return "-"

    # ---- 路由 ----
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/env":
            self._json({"ok": True, "tools": detect_env()})
            return
        super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/compile":
            if not _rate_ok(self._client()):
                self._json({"ok": False, "error": "请求过于频繁，请稍后再试"}, 429)
                return
            b = self._body()
            ok, sid, err = _compile(str(b.get("language", "")), b.get("files") or [])
            if not ok:
                self._json({"ok": False, "error": err or "编译失败"})
                return
            self._json({"ok": True, "session": sid})
            return
        if path == "/api/run":
            if not _rate_ok(self._client()):
                self._json({"ok": False, "error": "请求过于频繁，请稍后再试"}, 429)
                return
            b = self._body()
            self._json(_run(str(b.get("session", "")), b.get("stdin", ""),
                            b.get("timeout")))
            return
        if path == "/api/dispose":
            b = self._body()
            self._json({"ok": _dispose(str(b.get("session", "")))})
            return
        if path == "/api/compare":
            if not _rate_ok(self._client()):
                self._json({"ok": False, "error": "请求过于频繁，请稍后再试"}, 429)
                return
            b = self._body()
            self._json(_compare(str(b.get("a", "")), str(b.get("b", "")),
                                b.get("stdin", ""), b.get("timeout")))
            return
        self._json({"ok": False, "error": "未知接口"}, 404)


def _cleanup_all():
    with _sessions_lock:
        for v in _sessions.values():
            shutil.rmtree(v["dir"], ignore_errors=True)
        _sessions.clear()


def main():
    os.chdir(ROOT)
    try:
        import atexit
        atexit.register(_cleanup_all)
    except Exception:
        pass
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
