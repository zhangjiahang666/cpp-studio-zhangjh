# -*- coding: utf-8 -*-
"""
OJJudge —— 本地 OI 评测软件
功能：
  1) 单题模式：选一个源码 + 一个数据目录，一键评测。
  2) 多题模式：添加任意多道题（题名/源码/数据目录），一键全部评测，结果按题分组汇总。
  3) 对拍：主程序 vs 暴力/标程，随机数据揪 bug。
  4) 造数据：自动生成随机 .in 与 .out。
  表格显示每组 AC/WA、得分、用时、期望/实际输出。
  用 tkinter 实现：Windows 打包为独立 .exe（无需 Python 环境）；macOS / Linux 可直接以 Python 3 运行本源码。
"""
import os, re, sys, subprocess, threading, time, glob, random, json, queue, locale
import shutil, webbrowser, tempfile

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    # 当前 Python 未编译 tkinter（精简版 / 部分自制发行版 Python 常见）。
    # 这里给出可操作的提示，而不是甩一句 ModuleNotFoundError。
    sys.stderr.write(
        "\n"
        "============================================================\n"
        " 启动失败：当前 Python 环境缺少 tkinter 模块。\n"
        " Failed to start: this Python has no tkinter module.\n"
        "============================================================\n"
        "\n"
        " Windows：请安装 python.org 官方版 Python（自带 tkinter），\n"
        "   地址 https://www.python.org/downloads/ ，安装后重跑\n"
        "   python ojjudge.py ；或直接下载 OJJudge评测.exe 免安装使用。\n"
        "\n"
        " macOS：用 python.org 官方版（自带 tkinter）；\n"
        "   Homebrew 的 python 需先执行 brew install python-tk 。\n"
        "\n"
        " Linux（Debian/Ubuntu）：sudo apt install python3-tk\n"
        "\n"
        " 注意：部分精简版 / 自编译 Python 不带 tkinter，且无法用 pip 安装，\n"
        "   只能换一个带 tkinter 的 Python 发行版。\n"
        "\n"
    )
    sys.exit(1)

DEFAULT_GXX = r"C:\mingw64\bin\g++.exe"
VERSION = "1.8"

# ---------- 界面语言（中文 / English） ----------
UI_LANG = "zh"          # 当前界面语言：zh / en
UI_LANGS = (("zh", "中文"), ("en", "English"))

# 中文原文 -> 英文译文（用于界面整体切换；日志与提示语仍用中文）
ZH2EN = {
    # 标签页
    "  单题  ": "  Single  ", "  多题  ": "  Multi  ", "  对拍  ": "  Battle  ",
    "  造数据  ": "  Data Gen  ", "  随机数据  ": "  Random  ", "  记录  ": "  Records  ",
    # 标题栏
    "OJJudge 评测软件": "OJJudge Desktop Judge",
    "单题 · 多题 · 对拍 · 造数据": "Single · Multi · Battle · Data Gen",
    "CPP Studio zhangjh 出品 · 本地 OI 评测": "CPP Studio zhangjh · Local OI Judge",
    # 底栏
    "编译器:": "Compiler:", "浏览": "Browse", "下载编译器": "Get Compiler",
    "标准:": "Std:", "O2 优化": "O2 Optimize", "每组分:": "Score/case:",
    "超时(ms):": "Timeout(ms):", "界面:": "UI:",
    # 单题
    "源码与数据": "Source & Data", "源码(.cpp):": "Source(.cpp):", "语言:": "Language:",
    "数据目录:": "Data dir:", "开始评测": "Evaluate", "载入示例": "Load Example",
    "评测结果": "Results", "组": "Case", "状态": "Status", "得分": "Score",
    "用时(ms)": "Time(ms)", "期望": "Expected", "实际": "Actual",
    "总分: - / -": "Total: - / -", "总分: 评测中...": "Total: evaluating...",
    # 多题
    "添加题目": "Add Problem", "导入题目": "Import", "删除选中": "Delete",
    "清空列表": "Clear", "开始评测全部": "Evaluate All", "题名": "Name",
    "源码": "Source", "数据目录": "Data dir", "题": "Problem",
    "汇总: - / -": "Summary: - / -", "汇总: 评测中...": "Summary: evaluating...",
    # 对拍
    "参数设置": "Settings", "主程序(.cpp):": "Main program(.cpp):",
    "暴力/标程(.cpp):": "Brute / reference(.cpp):", "数据生成器(.cpp):": "Generator(.cpp):",
    "对拍轮数:": "Rounds:", "开始对拍": "Start Battle", "载入挑战": "Load Challenge",
    "对拍日志": "Battle Log", "对拍中...": "Battling...", "对拍中": "Battling",
    # 造数据
    "题名前缀:": "Task prefix:", "输出目录:": "Output dir:",
    "答案程序(.cpp):": "Answer program(.cpp):", "组数:": "Cases:",
    "答案后缀:": "Answer suffix:", "开始生成": "Generate", "生成日志": "Log",
    "生成中...": "Generating...", "生成中": "Generating",
    # 随机数据
    "输入格式": "Input format", "输入格式：": "Input format: ",
    "输入范围：": "Ranges: ", "AC 代码(.cpp)（可留空）:": "AC code(.cpp) (optional):",
    "生成位置:": "Output location:", "数量:": "Count:", "前缀:": "Prefix:",
    "后缀:": "Suffix:",
    # 记录
    "评测记录": "Evaluations", "改动日志": "Changelog", "清空记录": "Clear Records",
    "记录列表": "History", "时间": "Time", "模式": "Mode", "结果": "Result",
    "详情 / 日志": "Detail / Log",
    # 通用
    "就绪": "Ready", "完成": "Done", "提示": "Notice", "错误": "Error",
    "关闭": "Close", "确定": "OK", "取消": "Cancel", "通过": "Passed",
    "发现问题": "Problem found", "出错": "Error", "评测异常": "Eval error",
    "单题": "Single", "多题": "Multi", "对拍": "Battle", "造数据": "Data Gen",
    "随机数据": "Random Data", "请先添加题目": "Add a problem first",
    "战绩报告": "Battle report", "载入示例题": "Load Example Problem",
    "载入对拍挑战": "Load Battle Challenge", "导入失败": "Import failed",
    "导入完成": "Import done", "选择文件": "Select file", "选择目录": "Select folder",
    "所有文件": "All files", "C++ 源码": "C++ source", "可执行文件": "Executable",
    "JSON 导入文件": "JSON import file", "选择题目导入文件": "Select import file",
    "对拍全部一致": "All rounds consistent", "对拍发现问题": "Mismatches found",
    "对拍异常": "Battle error", "对拍发现不一致": "Battle mismatch",
    "题名/源码/数据目录都要填": "Name / source / data dir are required",
    "请填好源码/数据目录": "Please fill in source and data dir",
    "源码文件不存在: ": "Source file not found: ",
    "数据目录不存在: ": "Data dir not found: ",
    "编译器不存在: ": "Compiler not found: ",
    "AC 代码文件不存在: ": "AC code file not found: ",
    "主程序/暴力/生成器": "Main / brute / generator", "/编译器": "/compiler",
    "都要填": " are required",
    "输出目录/生成器/答案程序/编译器都要填":
        "Output dir / generator / answer program / compiler are required",
    "输入格式 / 生成位置 / 编译器 都要填":
        "Input format / output location / compiler are required",
    "确定清空全部评测记录？": "Clear all evaluation records?",
    "战绩卡已生成，已用浏览器打开（也可在「对拍报告」文件夹查看）":
        "Battle card generated and opened in browser (also in the Battle Reports folder)",
}

# 动态文本（带数字/变量）用正则翻译
_ZH2EN_RE = [
    (r"^就绪（(\d+) 题）$", r"Ready (\1 problems)"),
    (r"^就绪（可点「载入示例」零配置试跑）$", r"Ready (click Load Example for a zero-config run)"),
    (r"^就绪（可点「载入挑战」一键备齐生成器\+主程序\+暴力）$",
     r"Ready (click Load Challenge to prepare gen+main+brute)"),
    (r"^已载入示例：(.+)，点「开始评测」试跑$", r"Loaded example: \1 - click Evaluate to run"),
    (r"^已载入挑战：(.+)，点「开始对拍」揪虫$", r"Loaded challenge: \1 - click Start Battle"),
    (r"^总分: (.+)$", r"Total: \1"),
    (r"^汇总: (.+)$", r"Summary: \1"),
    (r"^评测中: (.+)$", r"Evaluating: \1"),
    (r"^评测记录 (\d+) 条$", r"\1 evaluation records"),
    (r"^已导入 (\d+) 道题。$", r"Imported \1 problems."),
    (r"^对拍战绩卡$", r"Battle card"),
    (r"^第(\d+)轮: (.+)$", r"Round \1: \2"),
    (r"^第(\d+)组: (.+)$", r"Case \1: \2"),
]


def _t(text):
    """按当前界面语言翻译一段界面文案。"""
    if UI_LANG == "en":
        if text in ZH2EN:
            return ZH2EN[text]
        for pat, rep in _ZH2EN_RE:
            m = re.match(pat, text)
            if m:
                return re.sub(pat, rep, text)
    return text


# ---------- 主题配色（现代简洁 · 靛青渐变） ----------
BG       = "#eef1f7"   # 窗口背景（浅灰蓝）
CARD     = "#ffffff"   # 卡片/输入框背景
BORDER   = "#dfe4ee"   # 卡片/控件描边
HEADER_A = "#4f46e5"   # 标题栏渐变起（靛蓝）
HEADER_B = "#7c3aed"   # 标题栏渐变止（紫）
HEADER_T = "#c7d2fe"   # 标题栏副文字
PRIMARY  = "#6366f1"   # 主靛蓝
PRIMARY_D= "#4f46e5"
ACCENT   = "#22d3ee"   # 青蓝点缀
GREEN    = "#10b981"
RED      = "#ef4444"
AMBER    = "#f59e0b"
GRAY     = "#9aa3b2"
ROW_ALT  = "#f7f9fc"
SEL_BG   = "#eef0ff"   # 表格选中行背景


def _blend(c1, c2, t):
    """两个十六进制颜色按比例混合（t: 0~1）。"""
    r = int(int(c1[1:3], 16) * (1 - t) + int(c2[1:3], 16) * t)
    g = int(int(c1[3:5], 16) * (1 - t) + int(c2[3:5], 16) * t)
    b = int(int(c1[5:7], 16) * (1 - t) + int(c2[5:7], 16) * t)
    return "#%02x%02x%02x" % (r, g, b)


def _default_import_path():
    """返回「题目导入.json」的默认位置：程序所在目录（exe 或脚本同目录）。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "题目导入.json")


def _records_path():
    """评测记录文件位置：程序所在目录。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "评测记录.json")


def _settings_path():
    """设置文件位置：程序所在目录（与 exe / 脚本同目录）。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "ojjudge_settings.json")


def load_settings():
    """读取上次保存的界面设置（编译器/标准/O2/每组分/超时/对拍轮数）。"""
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save_settings(data):
    """写入界面设置（失败静默，不影响主流程）。"""
    try:
        with open(_settings_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_records(path=None):
    """读取评测记录列表（list of dict）。"""
    path = path or _records_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return d.get("evaluations", [])
        except Exception:
            pass
    return []


def save_records(records, path=None):
    """把评测记录列表写回文件。"""
    path = path or _records_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"evaluations": records}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# 改动日志：记录每次迭代做了什么，可在软件「记录」页查看
CHANGELOG = """OJJudge 评测软件 · 改动记录
────────────────────────────
v1.0  （基础版）
  · 单题评测：一个源码 + 一个数据目录，一键出分（AC/WA/TLE、得分、用时、期望/实际）。
  · 多题评测：添加多道题，一键全部评测，结果按题分组汇总。
  · 对拍：主程序 vs 暴力/标程，用随机数据揪 bug。
  · 造数据：自动生成随机 .in 与 .out。

v1.1  （增强）
  · 新增「随机数据」：填输入格式/范围/数量 + AC 代码，自动生成可测数据（无需 freopen 手写生成器）。
  · 界面美化：靛紫渐变标题栏、胶囊标签页、分区色条、卡片、斑马纹表格，整体对齐网页版风格。

v1.2  （对拍不中断）
  · 对拍遇到错误不再中途停止：跑完全部轮，统计并一次性列出所有不一致/异常。
  · 结果表状态徽章：AC 浅绿 / WA 浅红 / 其他浅黄，一眼看清。

v1.3  （导入与稳定）
  · 多题支持启动自动导入：exe 同目录的「题目导入.json」自动填进多题列表，也可手动「导入题目」。
  · 修复多题评测"只测一个就跳过"：改为线程安全队列模式，工作线程不碰界面控件，单题异常不中断后续。

v1.4  （记录）
  · 新增「记录」页：评测记录（单题/多题/对拍每次运行自动保存，可回看历史）+ 改动日志。
  · 评测记录持久化到 exe 同目录的「评测记录.json」。

v1.5  （兼容增强）
  · 单题 / 多题评测新增 cin/cout 标准输入输出支持：自动把该组 .in 经 stdin 喂给程序并捕获
    stdout，与 freopen 写法并存（同时存在时优先取 <题名>.out），兼容洛谷等 OJ 常规写法。
  · 「随机数据」的 AC 代码改为可选：提供则编译跑出 .out，留空则只生成 .in。
  · README 与说明书同步更新两种写法的约定。
  · 新增 macOS / Linux 源码版（Python 3 + tkinter，无第三方依赖）；修复编译器诊断输出
    编码在非 Windows 平台不可用的问题（mbcs → 按平台取编码，errors=replace 保证不崩）。

v1.6  （体验与健壮性）
  · 输出比对归一化：行尾空白与末尾空行不再判错（OI 常规做法），单题评测与对拍同时生效，
    消除「答案明明对却 WA」的误报。
  · 设置持久化：编译器路径 / C++ 标准 / 优化开关 / 每题分值 / 超时 / 对拍轮数记到 exe 同目录
    「ojjudge_settings.json」，重启不丢；文件损坏时静默回退默认值，不影响启动。
  · 超时可调：底部栏新增「超时(ms)」调节（1–60 秒），单题 / 多题 / 对拍共用，适配慢机器与
    深度搜索题。
  · 对拍崩溃检测：主程序或暴力程序非零退出（段错误 / 断言失败等）记为「运行异常」并展示
    退出码，不再误报成「输出不一致」。
  · 问题数据留存：对拍发现输出不一致或运行异常的轮次，输入自动存到工作目录「问题数据」，
    拿到数据即可离线复现调试。

v1.7  （更好上手 · 更好看）
  · 单题「载入示例」：内置 3 道示例题（A+B / 最大子段和 / 数组排序），一键落盘源码与样例，
    零配置先跑通，验证环境是否 OK。
  · 对拍「载入挑战」：内置 4 个埋了真 bug 的对拍挑战（初值之坑 / 溢出之坑 / 负数取模 / 整数溢出），
    生成器 + 主程序 + 暴力一键备齐，落地即对拍揪虫，体验和官网「对拍实验室」一致。
  · 编译器自动探测：启动扫描 PATH，找到 g++/clang++ 自动填好；找不到时给出 WinLibs 下载引导，
    底部栏新增「下载编译器」一键打开，新手不再卡在「找不到编译器」。
  · 对拍战绩卡：对拍完成自动生成样式化 HTML 战绩报告（同官网视觉）+ 纯文本备份，浏览器一键查看，
    方便截图分享到朋友圈 / 小红书参赛。
  · 界面打磨：标题栏加版本号，状态色更直观（AC 绿 / 问题红 / 警告琥珀），暗色对拍日志更聚焦。

v1.8  （多语言 · 双语界面）
  · **评测支持多种编程语言**：C++ / Python / Java 三选一。单题、多题、对拍、造数据、随机数据
    全流程按所选语言走对应运行时——C++ 用 g++ 编译，Python 用解释器直跑，Java 用 javac 编译、
    java 运行（类名取源文件名）。语言下拉放在单题/多题/对拍页，选「浏览」时按扩展名自动切换
    （.py → Python、.java → Java），切换后其余页面同步。
  · **运行环境自动探测**：Python 解释器与 JDK（javac + java）自动在 PATH 上探测；缺环境时给出
    明确引导文案（装哪个、勾哪个选项），不再抛英文异常。
  · **界面语言切换**：底栏新增「界面: 中文 / English」，一键把标签页、按钮、表头、分区标题、
    底栏与状态提示整体切成英文，切回中文完全还原（动态状态栏也不会被覆盖回初始值）。
  · 兼容性：Python / Java 模式下不再强制要求填写编译器路径；非 C++ 语言的造数据与随机数据
    也支持用对应语言的 AC 程序跑出标准答案。
"""


# ============================================================
# 内置示例题（单题页「载入示例」）：含正确源码 + 硬编码样例
# ============================================================
EXAMPLES = [
    {
        "name": "示例1 · A+B",
        "desc": "最基础的输入输出题：读两个整数，输出它们的和。适合第一次上手验证环境。",
        "cpp": (
            "#include <iostream>\n"
            "using namespace std;\n"
            "int main() {\n"
            "    int a, b;\n"
            "    cin >> a >> b;\n"
            "    cout << a + b << \"\\n\";\n"
            "    return 0;\n"
            "}\n"
        ),
        "cases": [
            ("2 3\n", "5\n"),
            ("-10 4\n", "-6\n"),
            ("100 200\n", "300\n"),
        ],
    },
    {
        "name": "示例2 · 最大子段和",
        "desc": "读 n 与 n 个整数，求连续子段的最大和（可含负数，全为负时取最大的那个负数）。",
        "cpp": (
            "#include <iostream>\n"
            "#include <vector>\n"
            "#include <algorithm>\n"
            "#include <climits>\n"
            "using namespace std;\n"
            "int main() {\n"
            "    ios::sync_with_stdio(false);\n"
            "    cin.tie(0);\n"
            "    int n; cin >> n;\n"
            "    vector<long long> a(n);\n"
            "    for (int i = 0; i < n; i++) cin >> a[i];\n"
            "    long long best = LLONG_MIN, cur = 0;\n"
            "    for (int i = 0; i < n; i++) {\n"
            "        cur = max(a[i], cur + a[i]);\n"
            "        best = max(best, cur);\n"
            "    }\n"
            "    cout << best << \"\\n\";\n"
            "    return 0;\n"
            "}\n"
        ),
        "cases": [
            ("5\n1 -2 3 4 -1\n", "7\n"),
            ("3\n-5 -2 -3\n", "-2\n"),
            ("4\n2 1 -3 4\n", "4\n"),
        ],
    },
    {
        "name": "示例3 · 数组排序",
        "desc": "读 n 与 n 个整数，按从小到大升序输出。",
        "cpp": (
            "#include <iostream>\n"
            "#include <vector>\n"
            "#include <algorithm>\n"
            "using namespace std;\n"
            "int main() {\n"
            "    ios::sync_with_stdio(false);\n"
            "    cin.tie(0);\n"
            "    int n; cin >> n;\n"
            "    vector<int> a(n);\n"
            "    for (int i = 0; i < n; i++) cin >> a[i];\n"
            "    sort(a.begin(), a.end());\n"
            "    for (int i = 0; i < n; i++) cout << a[i] << (i + 1 < n ? \" \" : \"\\n\");\n"
            "    return 0;\n"
            "}\n"
        ),
        "cases": [
            ("5\n5 3 8 1 2\n", "1 2 3 5 8\n"),
            ("3\n10 9 8\n", "8 9 10\n"),
            ("1\n42\n", "42\n"),
        ],
    },
]

# ============================================================
# 内置对拍挑战（对拍页「载入挑战」）：每个都埋了一个真 bug。
# 生成器造随机数据，主程序（带 bug）vs 暴力/标程（正确）对拍揪虫。
# ============================================================
BATTLE_CHALLENGES = [
    {
        "id": "kadane",
        "name": "挑战1 · 最大子段和",
        "bug": "初值之坑",
        "desc": "主程序用 Kadane 求最大子段和，但初值设成了 0——全负数时返回 0，而真正的最大子段和是负数。暴力 O(n²) 枚举显然正确。",
        "rounds": 100,
        "gen_cpp": (
            "#include <iostream>\n#include <cstdlib>\n#include <ctime>\nusing namespace std;\n"
            "int main() {\n"
            "    srand((unsigned)time(0) + rand());\n"
            "    int n = 1 + rand() % 8;\n"
            "    cout << n << \"\\n\";\n"
            "    for (int i = 0; i < n; i++) cout << (rand() % 21 - 10) << (i + 1 < n ? \" \" : \"\\n\");\n"
            "    return 0;\n"
            "}\n"
        ),
        "main_cpp": (
            "#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\n"
            "int main() {\n"
            "    ios::sync_with_stdio(false); cin.tie(0);\n"
            "    int n; cin >> n; vector<long long> a(n);\n"
            "    for (int i = 0; i < n; i++) cin >> a[i];\n"
            "    long long best = 0, cur = 0;   // 坑：初值设 0，全负数时会返回 0\n"
            "    for (int i = 0; i < n; i++) { cur = max(0LL, cur + a[i]); best = max(best, cur); }\n"
            "    cout << best << \"\\n\"; return 0;\n"
            "}\n"
        ),
        "brute_cpp": (
            "#include <iostream>\n#include <vector>\n#include <climits>\nusing namespace std;\n"
            "int main() {\n"
            "    ios::sync_with_stdio(false); cin.tie(0);\n"
            "    int n; cin >> n; vector<long long> a(n);\n"
            "    for (int i = 0; i < n; i++) cin >> a[i];\n"
            "    long long best = LLONG_MIN;\n"
            "    for (int i = 0; i < n; i++) { long long s = 0; for (int j = i; j < n; j++) { s += a[j]; if (s > best) best = s; } }\n"
            "    cout << best << \"\\n\"; return 0;\n"
            "}\n"
        ),
    },
    {
        "id": "bigmod",
        "name": "挑战2 · 大数取模",
        "bug": "溢出之坑",
        "desc": "主程序直接 (a*b)%p 且用 int 存放——a、b 到 1e9 量级时乘积溢出 32 位整数，结果悄悄算错。暴力用 long long 精确计算。",
        "rounds": 100,
        "gen_cpp": (
            "#include <iostream>\n#include <cstdlib>\n#include <ctime>\nusing namespace std;\n"
            "long long rnd(long long lo, long long hi) { long long r = (long long)rand() * RAND_MAX + rand(); return lo + r % (hi - lo + 1); }\n"
            "int main() {\n"
            "    srand((unsigned)time(0) + rand());\n"
            "    long long a = rnd(100000000LL, 1000000000LL);\n"
            "    long long b = rnd(100000000LL, 1000000000LL);\n"
            "    long long p = rnd(2LL, 1000000000LL);\n"
            "    cout << a << \" \" << b << \" \" << p << \"\\n\";\n"
            "    return 0;\n"
            "}\n"
        ),
        "main_cpp": (
            "#include <iostream>\nusing namespace std;\n"
            "int main() {\n"
            "    int a, b, p; cin >> a >> b >> p;\n"
            "    cout << (a * b) % p << \"\\n\";   // 坑：int 乘积溢出，结果错误\n"
            "    return 0;\n"
            "}\n"
        ),
        "brute_cpp": (
            "#include <iostream>\nusing namespace std;\n"
            "int main() {\n"
            "    long long a, b, p; cin >> a >> b >> p;\n"
            "    cout << (a * b) % p << \"\\n\";   // long long 精确\n"
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "id": "mod-neg",
        "name": "挑战3 · 负数取模",
        "bug": "语义之坑",
        "desc": "C++ 的 % 余数符号跟着被除数走：-7 % 3 = -1，而数学上余数应是 2。主程序直接 a%b，暴力用 ((a%b)+b)%b 归一化成非负余数。只要 a 是负数几乎必现。",
        "rounds": 100,
        "gen_cpp": (
            "#include <iostream>\n#include <cstdlib>\n#include <ctime>\nusing namespace std;\n"
            "int main() {\n"
            "    srand((unsigned)time(0) + rand());\n"
            "    int a = rand() % 21 - 10;\n"
            "    int b = 2 + rand() % 4;\n"
            "    cout << a << \" \" << b << \"\\n\";\n"
            "    return 0;\n"
            "}\n"
        ),
        "main_cpp": (
            "#include <iostream>\nusing namespace std;\n"
            "int main() {\n"
            "    int a, b; cin >> a >> b;\n"
            "    cout << a % b << \"\\n\";   // 坑：-7 % 3 = -1，余数带负号\n"
            "    return 0;\n"
            "}\n"
        ),
        "brute_cpp": (
            "#include <iostream>\nusing namespace std;\n"
            "int main() {\n"
            "    int a, b; cin >> a >> b;\n"
            "    cout << ((a % b) + b) % b << \"\\n\";   // 数学上的非负余数\n"
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "id": "int-overflow",
        "name": "挑战4 · 整数溢出",
        "bug": "溢出之坑",
        "desc": "把乘积塞进 32 位整数（(int)(a*b)），乘积超过约 21 亿（2^31）就绕回一圈变成另一个数。暴力用 long long 直接算，数据在 10~1e5 时约一半轮次现形。",
        "rounds": 100,
        "gen_cpp": (
            "#include <iostream>\n#include <cstdlib>\n#include <ctime>\nusing namespace std;\n"
            "long long rnd(long long lo, long long hi) { long long r = (long long)rand() * RAND_MAX + rand(); return lo + r % (hi - lo + 1); }\n"
            "int main() {\n"
            "    srand((unsigned)time(0) + rand());\n"
            "    long long a = rnd(10, 100000), b = rnd(10, 100000);\n"
            "    cout << a << \" \" << b << \"\\n\";\n"
            "    return 0;\n"
            "}\n"
        ),
        "main_cpp": (
            "#include <iostream>\nusing namespace std;\n"
            "int main() {\n"
            "    long long a, b; cin >> a >> b;\n"
            "    int r = (int)(a * b);   // 坑：按 32 位截断，超 2^31 绕回\n"
            "    cout << r << \"\\n\";\n"
            "    return 0;\n"
            "}\n"
        ),
        "brute_cpp": (
            "#include <iostream>\nusing namespace std;\n"
            "int main() {\n"
            "    long long a, b; cin >> a >> b;\n"
            "    cout << a * b << \"\\n\";   // long long 精确\n"
            "    return 0;\n"
            "}\n"
        ),
    },
]


def _app_base():
    """内置示例/挑战文件落地目录（exe 或脚本同目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _detect_compiler():
    """在 PATH 上探测 g++ / g++.exe / clang++，找到则返回路径，否则 None。"""
    for name in ("g++.exe", "g++", "clang++.exe", "clang++"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _detect_python():
    """探测 Python 解释器（python3 优先，其次 python）。"""
    for name in ("python3", "python.exe", "python"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _detect_java():
    """探测 JDK：需要 javac（编译）与 java（运行），返回 (javac, java) 或 (None, None)。"""
    javac = shutil.which("javac.exe") or shutil.which("javac")
    java = shutil.which("java.exe") or shutil.which("java")
    return (javac, java) if (javac and java) else (None, None)


# ============================================================
# 支持的编程语言
#   cpp    : g++ 编译后运行
#   python : 解释器直跑（无需编译）
#   java   : javac 编译成 .class 后 java 运行（类名取源文件名）
# ============================================================
LANG_DEFS = {
    "cpp": {
        "label": "C++",
        "exts": (".cpp", ".cxx", ".cc", ".c++"),
        "need_compile": True,
        "tool": "g++",
        "hint": "需要 g++ 编译器：可用 MinGW-w64（WinLibs）装到 C:\\mingw64，或在底部栏指定 g++.exe 路径。",
    },
    "python": {
        "label": "Python",
        "exts": (".py", ".pyw"),
        "need_compile": False,
        "tool": "python",
        "hint": "需要 Python 解释器：安装 Python 3 并勾选 Add to PATH，或在系统 PATH 中提供 python3。",
    },
    "java": {
        "label": "Java",
        "exts": (".java",),
        "need_compile": True,
        "tool": "JDK",
        "hint": "需要 JDK（同时提供 javac 与 java）：安装 JDK 17 并勾选 Add to PATH。",
    },
}

LANG_ORDER = ("cpp", "python", "java")


def _lang_label(lang):
    return LANG_DEFS.get(lang, LANG_DEFS["cpp"])["label"]


def _guess_lang(src):
    """按扩展名猜语言，猜不到默认 C++。"""
    ext = os.path.splitext(src)[1].lower()
    for key, meta in LANG_DEFS.items():
        if ext in meta["exts"]:
            return key
    return "cpp"


def _prepare_prog(lang, gxx, src, workdir, std, opt):
    """
    按语言准备程序：需要则编译。
    返回 (exe_path_or_None, run_argv, compile_cmd_or_None, error_msg_or_None)
      · cpp    : 编译成 <workdir>/<名>.exe，run_argv = [exe]
      · python : 不编译，run_argv = [解释器, 源文件]
      · java   : 编译到 <workdir>/_java_<名>/，run_argv = [java, -cp, 目录, 类名]
    """
    base = os.path.splitext(os.path.basename(src))[0]
    if lang == "cpp":
        exe = os.path.join(workdir, base + ".exe")
        cmd = [gxx, "-o", exe, src, "-std=" + std]
        if opt:
            cmd.append("-O2")
        return exe, [exe], cmd, None
    if lang == "python":
        interp = _detect_python()
        if not interp:
            return None, None, None, LANG_DEFS["python"]["hint"]
        return None, [interp, src], None, None
    if lang == "java":
        javac, java = _detect_java()
        if not javac or not java:
            return None, None, None, LANG_DEFS["java"]["hint"]
        cp = os.path.join(workdir, "_java_" + base)
        try:
            os.makedirs(cp, exist_ok=True)
        except Exception as e:
            return None, None, None, "无法创建 Java 类输出目录：%s" % e
        return None, [java, "-cp", cp, base], [javac, "-d", cp, src], None
    return None, None, None, "不支持的语言：%s" % lang


def _run_compile(cmd, timeout=120):
    """执行编译命令，返回 subprocess 结果（沿用平台编码策略）。"""
    if sys.platform == "win32":
        enc = "mbcs"
    else:
        try:
            enc = locale.getpreferredencoding(False)
        except Exception:
            enc = "utf-8"
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              encoding=enc, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        class _R:
            returncode = 1
            stdout = ""
            stderr = "编译超时（%d 秒）" % timeout
        return _R()
    except Exception as e:
        class _R:
            returncode = 1
            stdout = ""
            stderr = "无法启动编译器：%s" % e
        return _R()


def setup_style(root):
    """配置 ttk 全局主题（现代简洁风，仿主流桌面应用）。"""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # 基础容器 / 文本
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground="#2b3344", font=("微软雅黑", 10))
    style.configure("Card.TFrame", background=CARD)
    style.configure("Card.TLabel", background=CARD, foreground="#2b3344", font=("微软雅黑", 10))
    style.configure("Section.TLabel", background=BG, foreground="#3a4256",
                    font=("微软雅黑", 11, "bold"))
    style.configure("TLabelframe", background=BG, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG, foreground="#4b5563",
                    font=("微软雅黑", 10, "bold"))

    # 按钮：主按钮（靛蓝）、次按钮（白底描边）、危险按钮（浅红）
    style.configure("Accent.TButton", font=("微软雅黑", 10, "bold"), padding=(16, 8),
                    background=PRIMARY, foreground="#ffffff", bordercolor=PRIMARY,
                    focuscolor="#ffffff", relief="flat")
    style.map("Accent.TButton",
              background=[("active", PRIMARY_D), ("pressed", PRIMARY_D), ("disabled", "#c7d2fe")],
              foreground=[("disabled", "#ffffff")])
    style.configure("TButton", font=("微软雅黑", 10), padding=(12, 6),
                    background="#ffffff", foreground="#3a4256", bordercolor=BORDER,
                    focuscolor="#ffffff", relief="flat")
    style.map("TButton",
              background=[("active", "#f2f4f9"), ("pressed", "#e9ecf4"), ("disabled", "#f3f5f9")],
              foreground=[("disabled", "#b6bdc9")])
    style.configure("Danger.TButton", font=("微软雅黑", 10), padding=(12, 6),
                    background="#fee2e2", foreground="#dc2626", bordercolor="#fecaca",
                    focuscolor="#ffffff", relief="flat")
    style.map("Danger.TButton", background=[("active", "#fecaca"), ("disabled", "#fde8e8")])

    # 输入框
    style.configure("TEntry", font=("微软雅黑", 10), fieldbackground=CARD,
                    foreground="#2b3344", bordercolor=BORDER, insertcolor=PRIMARY, padding=5)
    style.map("TEntry", bordercolor=[("focus", PRIMARY)], lightcolor=[("focus", PRIMARY)])
    style.configure("TCombobox", font=("微软雅黑", 10), fieldbackground=CARD,
                    background="#ffffff", foreground="#2b3344", arrowcolor="#7b8494",
                    bordercolor=BORDER, padding=4)
    style.map("TCombobox", bordercolor=[("focus", PRIMARY)])
    style.configure("TSpinbox", font=("微软雅黑", 10), fieldbackground=CARD,
                    background="#ffffff", foreground="#2b3344", bordercolor=BORDER, padding=4)
    style.map("TSpinbox", bordercolor=[("focus", PRIMARY)])
    style.configure("TCheckbutton", background=BG, foreground="#3a4256", font=("微软雅黑", 10))
    style.map("TCheckbutton", background=[("active", BG)])
    style.configure("TRadiobutton", background=BG, foreground="#3a4256", font=("微软雅黑", 10))

    # Tab：胶囊式
    style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(12, 8, 12, 0))
    style.configure("TNotebook.Tab", font=("微软雅黑", 11, "bold"),
                    padding=(22, 9), background="#e2e8f2", foreground="#5b6b82")
    style.map("TNotebook.Tab",
              background=[("selected", PRIMARY), ("active", "#cdd6e8")],
              foreground=[("selected", "#ffffff"), ("active", "#334155")],
              bordercolor=[("selected", PRIMARY), ("active", "#cdd6e8")])

    # 表格
    style.configure("Treeview", font=("微软雅黑", 10), rowheight=28,
                    background=CARD, fieldbackground=CARD, foreground="#2b3344",
                    bordercolor=BORDER, relief="flat")
    style.map("Treeview",
              background=[("selected", SEL_BG), ("active", ROW_ALT)],
              foreground=[("selected", "#3730a3")])
    style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"),
                    background="#eef1f7", foreground="#5b6b82", padding=(8, 7), relief="flat")
    style.map("Treeview.Heading", background=[("active", "#e2e8f2")])

    # 滚动条
    style.configure("Vertical.TScrollbar", background="#cfd6e4", troughcolor=BG,
                    borderwidth=0, arrowcolor="#8a93a5")
    style.configure("Horizontal.TScrollbar", background="#cfd6e4", troughcolor=BG,
                    borderwidth=0, arrowcolor="#8a93a5")

    # 状态 / 提示
    style.configure("Status.TLabel", font=("微软雅黑", 10, "bold"), foreground=PRIMARY, background=BG)
    style.configure("Hint.TLabel", font=("微软雅黑", 9), foreground="#8a93a5", background=BG)
    return style


def build_header(root):
    """顶部渐变标题栏 + 徽标 + 副标语 + 底部渐变细条。"""
    h = tk.Canvas(root, height=76, highlightthickness=0, bd=0)
    h.pack(fill="x")

    def draw():
        h.delete("all")
        w = max(h.winfo_width(), 400)
        steps = 84
        for i in range(steps):
            t = i / (steps - 1)
            h.create_rectangle(0, i, w, i + 1, fill=_blend(HEADER_A, HEADER_B, t), outline="")
        # 徽标
        h.create_oval(20, 15, 54, 49, fill="#ffffff", outline="")
        h.create_text(37, 32, text="OJ", fill=PRIMARY, font=("Segoe UI", 13, "bold"))
        # 标题与副标题
        h.create_text(68, 22, text=_t("OJJudge 评测软件") + "  v" + VERSION, anchor="w", fill="#ffffff",
                      font=("微软雅黑", 15, "bold"))
        h.create_text(68, 47, text=_t("单题 · 多题 · 对拍 · 造数据"), anchor="w", fill=HEADER_T,
                      font=("微软雅黑", 9))
        # 右侧标语
        h.create_text(w - 20, 38, text=_t("CPP Studio zhangjh 出品 · 本地 OI 评测"), anchor="e", fill=HEADER_T,
                      font=("微软雅黑", 9))
    h.bind("<Configure>", lambda e: draw())
    draw()
    # 供界面语言切换时重绘标题栏
    try:
        root._oj_header_redraw = draw
    except Exception:
        pass

    # 底部渐变细条（靛 → 青）
    strip = tk.Frame(root, height=4)
    strip.pack(fill="x")
    strip.pack_propagate(False)
    n = 6
    for i in range(n):
        seg = tk.Frame(strip, bg=_blend(PRIMARY, ACCENT, i / (n - 1)))
        seg.pack(side="left", fill="x", expand=True)
    # 标题栏下方的柔和投影线（网页风层次感）
    shadow = tk.Frame(root, height=2, bg="#d7dced")
    shadow.pack(fill="x")
    return h


def natural_key(name):
    m = re.search(r"(\d+)", os.path.basename(name))
    return int(m.group(1)) if m else 0


def run_battle(main_src, brute_src, gen_src, gxx, std, opt, rounds,
               workdir, report=None, timeout_ms=5000, lang="cpp"):
    """
    对拍：数据生成器造随机数据 -> 主程序与暴力/标程同跑 -> 比对输出。
    report 回调: report(kind, message)，kind in {info, warn, fail, ok, error}
    发现不一致/异常不会中途停止，会跑完全部轮并累计，最后汇总报告。
    lang: cpp / python / java —— 三个程序使用同一种语言。
    返回 True=全部一致，False=至少一处问题。数据保存在 workdir。
    """
    def rep(kind, msg):
        if report:
            report(kind, msg)

    # 准备三个程序（按语言决定编译 / 运行方式）
    run_argvs = {}
    for tag, s in (("生成器", gen_src), ("主程序", main_src), ("暴力", brute_src)):
        exe, argv, cmd, err = _prepare_prog(lang, gxx, s, workdir, std, opt)
        if err:
            rep("error", "%s：%s" % (tag, err))
            return False
        if cmd:
            p = _run_compile(cmd)
            if p.returncode != 0:
                rep("error", f"{tag}编译失败:\n{(p.stderr or p.stdout or '')[:500]}")
                return False
        run_argvs[tag] = argv

    data_in = os.path.join(workdir, "data.in")
    main_out = os.path.join(workdir, "main.out")
    brute_out = os.path.join(workdir, "brute.out")

    def save_case(r):
        """留存问题轮（输出不一致 / 运行异常）的输入数据，便于复现调试。失败静默。"""
        try:
            dd = os.path.join(workdir, "问题数据")
            os.makedirs(dd, exist_ok=True)
            with open(data_in, "rb") as fi, open(os.path.join(dd, f"第{r}轮.in"), "wb") as fo:
                fo.write(fi.read())
        except Exception:
            pass

    issues = []          # 累计所有不一致 / 异常轮
    consistent = 0       # 一致轮数

    for r in range(1, rounds + 1):
        # 1) 生成数据：生成器 stdout -> data.in
        try:
            with open(data_in, "wb") as fo:
                subprocess.run(run_argvs["生成器"], cwd=workdir, stdout=fo,
                               timeout=timeout_ms / 1000.0)
        except subprocess.TimeoutExpired:
            rep("warn", f"第{r}轮: 数据生成器超时（继续）")
            issues.append(f"第{r}轮: 数据生成器超时")
            continue
        except Exception as e:
            rep("warn", f"第{r}轮: 生成器出错 {e}（继续）")
            issues.append(f"第{r}轮: 生成器出错 {e}")
            continue

        # 2) 主程序 与 暴力程序 各跑一遍
        def run_one(argv, out_file):
            with open(data_in, "rb") as fi, open(out_file, "wb") as fo:
                try:
                    rp = subprocess.run(argv, cwd=workdir, stdin=fi, stdout=fo,
                                   timeout=timeout_ms / 1000.0)
                except subprocess.TimeoutExpired:
                    return "TLE"
                except Exception as e:
                    return f"ERR:{e}"
            if rp.returncode != 0:
                return f"RE:{rp.returncode}"   # 非零退出：崩溃/断言失败，判运行异常
            return "OK"

        s_main = run_one(run_argvs["主程序"], main_out)
        s_brute = run_one(run_argvs["暴力"], brute_out)

        # 3) 比对
        m = _read_text(main_out).strip() if os.path.isfile(main_out) else ""
        b = _read_text(brute_out).strip() if os.path.isfile(brute_out) else ""
        d = _read_text(data_in).strip() if os.path.isfile(data_in) else ""
        if s_main != "OK" or s_brute != "OK":
            rep("warn", f"第{r}轮: 运行异常 主[{s_main}] 暴力[{s_brute}]（继续）")
            issues.append(f"第{r}轮: 运行异常 主[{s_main}] 暴力[{s_brute}]\n输入:\n{d}")
            save_case(r)   # 崩溃/超时的输入同样留存，便于复现
            continue
        if _normalize_out(m) != _normalize_out(b):
            rep("warn", f"第{r}轮: 输出不一致（继续）")
            issues.append(f"第{r}轮: 输出不一致\n--- 输入 ---\n{d}\n--- 主程序输出 ---\n{m}\n--- 暴力/标程输出 ---\n{b}")
            save_case(r)   # 留存分歧数据，便于复现调试
            continue
        consistent += 1
        rep("info", f"第{r}轮: 一致 ({m[:30]})")

    if issues:
        summary = (f"对拍完成：共 {rounds} 轮，一致 {consistent} 轮，发现 {len(issues)} 处问题：\n"
                   + "\n".join(issues))
        rep("fail", summary)
        return False
    rep("ok", f"对拍完成：共 {rounds} 轮全部一致，没有发现问题。")
    return True


def generate_data(gen_src, ans_src, task, rounds, outdir, gxx, std, opt,
                  ext=".out", report=None, timeout_ms=5000, lang="cpp"):
    """
    造数据：数据生成器每轮造一组随机输入 -> 存为 <task><n>.in；
            答案程序读该输入 -> 存为 <task><n>.out（或 .ans）。
    report(kind, msg)。返回 (成功组数, 总组数)。
    要求生成器、答案程序都用标准输入输出（stdout 出、stdin 进）。
    lang: cpp / python / java —— 生成器与答案程序使用同一种语言。
    """
    def rep(kind, msg):
        if report:
            report(kind, msg)

    if not os.path.isdir(outdir):
        os.makedirs(outdir, exist_ok=True)

    run_argvs = {}
    for tag, s in (("生成器", gen_src), ("答案程序", ans_src)):
        exe, argv, cmd, err = _prepare_prog(lang, gxx, s, outdir, std, opt)
        if err:
            rep("error", "%s：%s" % (tag, err))
            return 0, rounds
        if cmd:
            p = _run_compile(cmd)
            if p.returncode != 0:
                rep("error", f"{tag}编译失败:\n{(p.stderr or p.stdout or '')[:500]}")
                return 0, rounds
        run_argvs[tag] = argv

    ok_count = 0
    for r in range(1, rounds + 1):
        in_path = os.path.join(outdir, f"{task}{r}{'.in'}")
        out_path = os.path.join(outdir, f"{task}{r}{ext}")
        # 1) 生成输入
        try:
            with open(in_path, "wb") as fo:
                subprocess.run(run_argvs["生成器"], cwd=outdir, stdout=fo,
                               timeout=timeout_ms / 1000.0)
        except subprocess.TimeoutExpired:
            rep("error", f"第{r}组: 生成器超时"); continue
        except Exception as e:
            rep("error", f"第{r}组: 生成器出错 {e}"); continue
        # 2) 答案程序跑出输出
        try:
            with open(in_path, "rb") as fi, open(out_path, "wb") as fo:
                subprocess.run(run_argvs["答案程序"], cwd=outdir, stdin=fi, stdout=fo,
                               timeout=timeout_ms / 1000.0)
        except subprocess.TimeoutExpired:
            rep("error", f"第{r}组: 答案程序超时"); continue
        except Exception as e:
            rep("error", f"第{r}组: 答案程序出错 {e}"); continue
        ok_count += 1
        rep("info", f"第{r}组: 已生成 {task}{r}.in 和 {task}{r}{ext}")

    rep("ok", f"造数据完成：成功 {ok_count}/{rounds} 组 → {outdir}")
    return ok_count, rounds


# ---------- 随机数据生成（按格式+范围，无需手写生成器） ----------
def _range_int(s):
    """把范围端点转成整数，支持 1e9 / -1e9 这类写法；失败返回 None。"""
    s = s.strip().replace("e", "E")
    try:
        return int(float(s))
    except Exception:
        return None


def parse_ranges(ranges_str):
    """解析「输入范围」为 {字母: (最小, 最大)}。支持 a=1~100 或 a 1 100 写法。"""
    res = {}
    if not ranges_str:
        return res
    for part in re.split(r"[;,，\s]+", ranges_str):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"([A-Za-z])\s*=\s*(.+?)\s*[~～\-]\s*(.+)", part)
        if not m:
            m = re.match(r"([A-Za-z])\s+(.+?)\s+([^\s]+)\s*$", part)
        if m:
            v, a, b = m.group(1), m.group(2), m.group(3)
            lo, hi = _range_int(a), _range_int(b)
            if lo is not None and hi is not None:
                if lo > hi:
                    lo, hi = hi, lo
                res[v] = (lo, hi)
    return res


def parse_format(format_str):
    """解析「输入格式」为行列表。
    每行元素: ('single', [占位变量]) 或 ('repeat', ('var'|'num', 计数), [占位变量]).
    例： `{n}`            → 输出一行一个随机数 n
         `{n} 行: {a} {b}` → 按 n 的值重复输出多行，每行一个 a、一个 b
    """
    rows = []
    for raw in format_str.splitlines():
        line = raw.strip()
        if not line:
            continue
        colon = [loc for loc in (line.find(":"), line.find("：")) if loc != -1]
        if colon:
            idx = min(colon)
            left, right = line[:idx], line[idx + 1:]
            cm = re.search(r"\{([A-Za-z])\}", left)
            if cm:
                count = ("var", cm.group(1))
            else:
                dm = re.match(r"\s*(\d+)\s*", left)
                if dm:
                    count = ("num", int(dm.group(1)))
                else:
                    vm = re.search(r"([A-Za-z])", left)
                    count = ("var", vm.group(1)) if vm else ("num", 1)
            pattern = re.findall(r"\{([A-Za-z])\}", right)
            rows.append(("repeat", count, pattern))
        else:
            rows.append(("single", None, re.findall(r"\{([A-Za-z])\}", line)))
    return rows


def _rand_in(ranges, var, default=(1, 1000)):
    lo, hi = ranges.get(var, default)
    return random.randint(lo, hi)


def gen_one_input(rows, ranges):
    """按格式与范围生成一组随机输入文本。
    规则：出现在首行或作为重复次数的变量，同一组内只取一个值并全局复用；
    只出现在重复行数据里的变量（如每行的 a、b），每一行都重新随机。
    """
    global_vars = set()
    for kind, count, pattern in rows:
        if kind == "single":
            global_vars.update(pattern)
        else:
            if count[0] == "var":
                global_vars.add(count[1])
    gvals = {v: _rand_in(ranges, v) for v in global_vars}

    out = []
    for kind, count, pattern in rows:
        if kind == "single":
            out.append(" ".join(str(gvals[v]) for v in pattern))
        else:
            if count[0] == "var":
                c = gvals[count[1]]
            else:
                c = count[1]
            c = max(0, c)
            for _ in range(c):
                vals = []
                for v in pattern:
                    if v in gvals:
                        vals.append(str(gvals[v]))
                    else:
                        vals.append(str(_rand_in(ranges, v)))
                out.append(" ".join(vals))
    return "\n".join(out) + "\n"


def generate_random_data(format_str, ranges_str, count, ac_src, outdir, gxx, std, opt,
                         task="test", ext=".out", report=None, timeout_ms=10000, lang="cpp"):
    """
    随机造数据：按「输入格式/输入范围」生成随机 .in。
    AC 代码可选：提供了则编译并跑出 .out（可直接用于评测）；留空则只生成 .in。
    全程用标准输入输出（不用 freopen）。
    返回 (成功组数, 总组数)。
    """
    def rep(kind, msg):
        if report:
            report(kind, msg)

    rows = parse_format(format_str)
    ranges = parse_ranges(ranges_str)
    if not rows:
        rep("error", "输入格式无法解析（请用 {字母} 占位，如 {n} 或 {n} 行: {a} {b}）")
        return 0, 0
    if not os.path.isdir(outdir):
        os.makedirs(outdir, exist_ok=True)

    # AC 代码可选：留空则只出 .in，不出 .out
    ac_argv = None
    if ac_src.strip():
        ac_exe, ac_argv, cmd, err = _prepare_prog(lang, gxx, ac_src, outdir, std, opt)
        if err:
            rep("error", "AC 代码：" + err)
            return 0, 0
        if cmd:
            p = _run_compile(cmd)
            if p.returncode != 0:
                rep("error", "AC 代码编译失败:\n" + (p.stderr or p.stdout or "")[:500])
                return 0, 0

    ok = 0
    for i in range(1, count + 1):
        in_path = os.path.join(outdir, f"{task}{i}.in")
        out_path = os.path.join(outdir, f"{task}{i}{ext}")
        try:
            with open(in_path, "w", encoding="utf-8") as f:
                f.write(gen_one_input(rows, ranges))
        except Exception as e:
            rep("error", f"第{i}组: 写输入失败 {e}")
            continue
        if ac_argv is None:
            ok += 1
            rep("info", f"第{i}组: 已生成 {task}{i}.in（未提供 AC 代码，无 .out）")
            continue
        try:
            with open(in_path, "rb") as fi, open(out_path, "wb") as fo:
                subprocess.run(ac_argv, cwd=outdir, stdin=fi, stdout=fo,
                               timeout=timeout_ms / 1000.0)
        except subprocess.TimeoutExpired:
            rep("error", f"第{i}组: AC 运行超时")
            continue
        except Exception as e:
            rep("error", f"第{i}组: AC 运行出错 {e}")
            continue
        ok += 1
        rep("info", f"第{i}组: 已生成 {task}{i}.in 和 {task}{i}{ext}")

    rep("ok", f"随机数据完成：成功 {ok}/{count} 组 → {outdir}")
    return ok, count


def _read_text(path):
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    return ""


def _normalize_out(text):
    """比对前归一化：去掉每行行尾空白与末尾空行（OI 常规做法，行尾空格不判错）。"""
    if not text:
        return ""
    lines = [ln.rstrip() for ln in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _copy_file(src, dst):
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        fo.write(fi.read())


def compile_one(gxx, src, exe, std, opt):
    """编译，返回 subprocess.run 结果。"""
    cmd = [gxx, "-o", exe, src, "-std=" + std]
    if opt:
        cmd.append("-O2")
    # 编译器诊断输出按平台取编码：Windows 用 mbcs（cp936，中文报错正常显示）；
    # macOS/Linux 没有 mbcs 编码，用系统区域编码（通常 UTF-8），errors=replace 保证不崩。
    if sys.platform == "win32":
        enc = "mbcs"
    else:
        try:
            enc = locale.getpreferredencoding(False)
        except Exception:
            enc = "utf-8"
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding=enc, errors="replace", timeout=120)


def evaluate_one(src, data, gxx, std, opt, score_per, report=None, timeout_ms=10000,
                 lang="cpp"):
    """
    评测单题。report 为可选回调 report(label, status, score, ms, expect, actual)。
    lang: cpp / python / java —— 决定如何编译与运行。
    返回 (ac_count, total_score, group_count)。
    """
    task = os.path.splitext(os.path.basename(src))[0]

    def rep(label, status, score, ms, expect, actual):
        if report:
            report(label, status, score, ms, expect, actual)

    # 准备程序（按语言决定编译 / 运行方式）
    exe, run_argv, compile_cmd, err = _prepare_prog(lang, gxx, src, data, std, opt)
    if err:
        rep("环境", "缺环境", 0, 0, "", err)
        return 0, 0, 0

    # 编译（Python 不需要）
    if compile_cmd:
        p = _run_compile(compile_cmd)
        if p.returncode != 0:
            rep("编译", "CE", 0, 0, "", (p.stderr or p.stdout or "编译失败"))
            return 0, 0, 0

    # 收集样例
    ins = sorted(glob.glob(os.path.join(data, "*.in")), key=natural_key)
    if not ins:
        rep("数据", "无样例", 0, 0, "", "目录里没有 .in 文件")
        return 0, 0, 0

    total = 0
    ac = 0
    for in_f in ins:
        base = os.path.splitext(in_f)[0]
        ref = None
        for ext in (".out", ".ans"):
            cand = base + ext
            if os.path.isfile(cand):
                ref = cand
                break
        if not ref:
            rep(os.path.basename(base), "缺答案", 0, 0, "", "")
            continue

        tmp_in = os.path.join(data, task + ".in")
        tmp_out = os.path.join(data, task + ".out")
        _copy_file(in_f, tmp_in)
        if os.path.exists(tmp_out):
            os.remove(tmp_out)
        t0 = time.time()
        try:
            # 把输入经 stdin 喂给程序（兼容 cin/cout 写法；freopen 写法会忽略 stdin 读文件）
            with open(in_f, "rb") as fi:
                rp = subprocess.run(run_argv, cwd=data, stdin=fi,
                                    capture_output=True, timeout=timeout_ms / 1000.0)
        except subprocess.TimeoutExpired:
            rep(os.path.basename(base), "TLE", 0, int(timeout_ms), "", "超时")
            continue
        except Exception as e:
            rep(os.path.basename(base), "运行异常", 0, 0, "", str(e))
            continue
        ms = int((time.time() - t0) * 1000)

        # 优先用 freopen 写出的 <task>.out；否则用标准输出（cin/cout 程序）
        mine = None
        if os.path.isfile(tmp_out):
            mine = _read_text(tmp_out).strip()
        elif rp.stdout:
            mine = rp.stdout.decode("utf-8", "replace").strip()
        if mine is None:
            rep(os.path.basename(base), "无输出", 0, ms, "", "")
            continue
        ans = _read_text(ref).strip()
        if _normalize_out(mine) == _normalize_out(ans):
            ac += 1
            total += score_per
            rep(os.path.basename(base), "AC", score_per, ms, ans, mine)
        else:
            rep(os.path.basename(base), "WA", 0, ms, ans, mine)

    # 清理
    for tmp in (exe, tmp_in, tmp_out):
        try:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
    # Java 的 .class 输出目录
    if lang == "java":
        try:
            import shutil as _sh
            _sh.rmtree(os.path.join(data, "_java_" + task), ignore_errors=True)
        except Exception:
            pass
    return ac, total, len(ins)


class JudgeApp:
    def __init__(self, root):
        self.root = root
        self.style = setup_style(root)
        root.title("OJJudge 评测软件")
        root.geometry("960x660")
        root.minsize(780, 540)
        root.configure(bg=BG)

        _s = load_settings()
        self.var_gxx = tk.StringVar(value=_s.get("gxx") or DEFAULT_GXX)
        self.var_std = tk.StringVar(value=_s.get("std") or "c++14")
        self.var_opt = tk.BooleanVar(value=bool(_s.get("opt", True)))
        self.var_score = tk.IntVar(value=int(_s.get("score", 20)))
        self.var_timeout = tk.IntVar(value=int(_s.get("timeout_ms", 10000)))
        self.var_lang = tk.StringVar(value=_s.get("lang") or "cpp")   # 评测语言

        self._running = False
        self._current_challenge = None   # 当前载入的对拍挑战名（用于战绩报告）
        self._last_battle = None         # 最近一次对拍统计（rounds/consistent/problems）
        # 界面国际化：控件原文/上次译文 备份、标签页、表格列头
        self._i18n_state = {}
        self._i18n_tabs = []
        self._i18n_trees = []
        build_header(root)
        # 编译器自动探测：PATH 上找到就自动填上，找不到则留默认并提示引导
        self._auto_detect_compiler()
        # 线程安全：工作线程只把 UI 更新动作丢进队列，主线程轮询执行
        self._ui_queue = queue.Queue()
        self.root.after(80, self._poll_ui)
        self._nb = ttk.Notebook(root)
        self._nb.pack(fill="both", expand=True, padx=10, pady=(6, 0))
        self._build_single_tab()
        self._build_multi_tab()
        self._build_battle_tab()
        self._build_gen_tab()
        self._build_random_tab()
        # 评测记录（软件内持久化）
        self._records = load_records()
        self._battle_ok = None
        self._build_record_tab()
        # 启动时自动导入「题目导入.json」里预置的题目（如未配置则跳过）
        self._loaded_import_count = self._load_problem_import()

        # 底部通用选项：网页风卡片（白底 + 细描边 + 底部柔和投影线）
        #
        # 布局分两行：编译器路径独占第一行（它最长，46 字符输入框），
        # 评测参数 + 界面语言放第二行。
        # 之前所有控件挤在一行，请求宽度 1239px > 窗口 960px，
        # 最右侧的「界面:」下拉会被挤出可视区看不见——语言切换等于没有。
        bar = tk.Frame(root, bg=CARD, bd=0, highlightthickness=1, highlightbackground=BORDER)
        bar.pack(fill="x", padx=10, pady=(6, 2))
        bar_shadow = tk.Frame(root, bg="#e3e7f0", height=2)
        bar_shadow.pack(fill="x", padx=14, pady=(0, 8))

        # ---- 第 1 行：编译器路径 ----
        row1 = tk.Frame(bar, bg=CARD)
        row1.pack(fill="x", padx=2, pady=(4, 0))
        ttk.Label(row1, text="编译器:", style="Card.TLabel").pack(side="left", padx=(8, 4))
        ttk.Entry(row1, textvariable=self.var_gxx).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(row1, text="浏览", command=self._pick_gxx).pack(side="left", padx=4)
        ttk.Button(row1, text="下载编译器", command=self._open_compiler_guide).pack(side="left", padx=(2, 8))

        # ---- 第 2 行：评测参数 + 界面语言 ----
        row2 = tk.Frame(bar, bg=CARD)
        row2.pack(fill="x", padx=2, pady=(2, 4))
        ttk.Label(row2, text="标准:", style="Card.TLabel").pack(side="left", padx=(8, 4))
        ttk.Combobox(row2, textvariable=self.var_std, width=7,
                     values=["c++11", "c++14", "c++17", "c++20"]).pack(side="left")
        ttk.Checkbutton(row2, text="O2 优化", variable=self.var_opt, style="TCheckbutton").pack(side="left", padx=8)
        ttk.Label(row2, text="每组分:", style="Card.TLabel").pack(side="left", padx=(8, 4))
        ttk.Spinbox(row2, from_=1, to=100, textvariable=self.var_score, width=5).pack(side="left")
        ttk.Label(row2, text="超时(ms):", style="Card.TLabel").pack(side="left", padx=(8, 4))
        ttk.Spinbox(row2, from_=1000, to=60000, increment=1000,
                    textvariable=self.var_timeout, width=6).pack(side="left")
        # 界面语言靠右固定：无论窗口多窄都在可视区内
        ttk.Label(row2, text="界面:", style="Card.TLabel").pack(side="right", padx=(10, 4))
        self.cb_ui_lang = ttk.Combobox(row2, width=8, state="readonly",
                                       values=[name for _, name in UI_LANGS])
        self.cb_ui_lang.set(dict(UI_LANGS).get(UI_LANG, "中文"))
        self.cb_ui_lang.bind("<<ComboboxSelected>>", self._on_ui_lang)
        self.cb_ui_lang.pack(side="right", padx=(0, 8))

        # 设置持久化：选项一改就写盘，重启后保持上次选择
        for _v in (self.var_gxx, self.var_std, self.var_opt, self.var_score, self.var_timeout):
            _v.trace_add("write", lambda *a: self._persist_settings())
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _persist_settings(self):
        try:
            save_settings({
                "gxx": self.var_gxx.get().strip(),
                "std": self.var_std.get().strip(),
                "opt": bool(self.var_opt.get()),
                "score": int(self.var_score.get()),
                "timeout_ms": int(self.var_timeout.get()),
                "battle_rounds": int(self.var_b_rounds.get()),
                "lang": self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp",
            })
        except Exception:
            pass

    def _on_close(self):
        self._persist_settings()
        self.root.destroy()

    # ---------- 分区标题 ----------
    def _section_label(self, parent, text):
        """带左侧色条的分区标题，让界面分区更清晰。"""
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=12, pady=(10, 4))
        tk.Frame(row, bg=ACCENT, width=4, height=16).pack(side="left", pady=2)
        tk.Label(row, text=text, bg=BG, fg="#3a4256",
                 font=("微软雅黑", 11, "bold")).pack(side="left", padx=7)
        return row

    # ---------- 单题模式 ----------
    def _build_single_tab(self):
        tab = ttk.Frame(self._nb)
        self._nb.add(tab, text="  单题  ")
        self._reg_tab(tab, "  单题  ")
        pad = {"padx": 10, "pady": 5}
        self._section_label(tab, "源码与数据")

        r1 = ttk.Frame(tab); r1.pack(fill="x", **pad)
        ttk.Label(r1, text="源码(.cpp):").pack(side="left")
        self.var_src = tk.StringVar()
        ttk.Entry(r1, textvariable=self.var_src).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r1, text="浏览", command=lambda: self._pick_file(self.var_src, True)).pack(side="left")
        ttk.Label(r1, text="语言:").pack(side="left", padx=(10, 4))
        self.cb_lang_s = self._mk_lang_combo(r1)

        r2 = ttk.Frame(tab); r2.pack(fill="x", **pad)
        ttk.Label(r2, text="数据目录:").pack(side="left")
        self.var_data = tk.StringVar()
        ttk.Entry(r2, textvariable=self.var_data).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r2, text="浏览", command=lambda: self._pick_dir(self.var_data)).pack(side="left")

        r3 = ttk.Frame(tab); r3.pack(fill="x", **pad)
        self.btn_single = ttk.Button(r3, text="开始评测", style="Accent.TButton", command=self._start_single)
        self.btn_single.pack(side="left")
        ttk.Button(r3, text="载入示例", command=self._load_example_dialog).pack(side="left", padx=8)
        self.status_single = ttk.Label(r3, text="就绪（可点「载入示例」零配置试跑）", style="Status.TLabel")
        self.status_single.pack(side="left", padx=12)

        self._section_label(tab, "评测结果")
        cols = ("组", "状态", "得分", "用时(ms)", "期望", "实际")
        self.tree_s = ttk.Treeview(tab, columns=cols, show="headings", height=14)
        self._reg_tree(self.tree_s, cols)
        for c in cols:
            self.tree_s.heading(c, text=c)
        self.tree_s.column("组", width=70, anchor="center")
        self.tree_s.column("状态", width=70, anchor="center")
        self.tree_s.column("得分", width=55, anchor="center")
        self.tree_s.column("用时(ms)", width=70, anchor="center")
        self.tree_s.column("期望", width=160, anchor="w")
        self.tree_s.column("实际", width=160, anchor="w")
        self.tree_s.tag_configure("AC", background="#e7f9f1", foreground=GREEN, font=("微软雅黑", 10, "bold"))
        self.tree_s.tag_configure("WA", background="#fdeeee", foreground=RED, font=("微软雅黑", 10, "bold"))
        self.tree_s.tag_configure("other", background="#fdf3e3", foreground=AMBER)
        self.tree_s.tag_configure("alt", background=ROW_ALT)
        self.tree_s.pack(fill="both", expand=True, padx=10, pady=2)
        sb = ttk.Scrollbar(tab, command=self.tree_s.yview)
        self.tree_s.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.total_s = tk.Label(tab, text="总分: - / -", font=("微软雅黑", 13, "bold"),
                                bg=BG, fg=PRIMARY, anchor="w")
        self.total_s.pack(fill="x", padx=12, pady=6)

    # ---------- 多题模式 ----------
    def _build_multi_tab(self):
        tab = ttk.Frame(self._nb)
        self._nb.add(tab, text="  多题  ")
        self._reg_tab(tab, "  多题  ")
        pad = {"padx": 10, "pady": 5}

        bar = ttk.Frame(tab); bar.pack(fill="x", **pad)
        ttk.Button(bar, text="添加题目", command=self._add_problem).pack(side="left")
        ttk.Button(bar, text="导入题目", command=self._import_problems_dialog).pack(side="left", padx=6)
        ttk.Button(bar, text="删除选中", style="Danger.TButton",
                   command=self._del_problem).pack(side="left", padx=6)
        ttk.Button(bar, text="清空列表", command=self._clear_problems).pack(side="left", padx=6)
        ttk.Button(bar, text="开始评测全部", style="Accent.TButton",
                   command=self._start_multi).pack(side="left", padx=10)
        ttk.Label(bar, text="语言:").pack(side="left", padx=(4, 4))
        self.cb_lang_m = self._mk_lang_combo(bar)
        self.status_multi = ttk.Label(bar, text="就绪（0 题）", style="Status.TLabel")
        self.status_multi.pack(side="left", padx=12)

        # 题目列表
        self._section_label(tab, "题目列表")
        self.problem_tree = ttk.Treeview(tab, columns=("题名", "源码", "数据目录"),
                                         show="headings", height=5)
        self._reg_tree(self.problem_tree, ("题名", "源码", "数据目录"))
        for c, w in (("题名", 90), ("源码", 300), ("数据目录", 300)):
            self.problem_tree.heading(c, text=c)
            self.problem_tree.column(c, width=w, anchor="w")
        self.problem_tree.pack(fill="x", padx=10, pady=2)


        # 结果表格
        self._section_label(tab, "评测结果")
        cols = ("题", "组", "状态", "得分", "用时(ms)", "期望", "实际")
        self.tree_m = ttk.Treeview(tab, columns=cols, show="headings", height=9)
        self._reg_tree(self.tree_m, cols)
        for c in cols:
            self.tree_m.heading(c, text=c)
        self.tree_m.column("题", width=90, anchor="w")
        self.tree_m.column("组", width=90, anchor="center")
        self.tree_m.column("状态", width=70, anchor="center")
        self.tree_m.column("得分", width=55, anchor="center")
        self.tree_m.column("用时(ms)", width=70, anchor="center")
        self.tree_m.column("期望", width=120, anchor="w")
        self.tree_m.column("实际", width=120, anchor="w")
        self.tree_m.tag_configure("AC", background="#e7f9f1", foreground=GREEN, font=("微软雅黑", 10, "bold"))
        self.tree_m.tag_configure("WA", background="#fdeeee", foreground=RED, font=("微软雅黑", 10, "bold"))
        self.tree_m.tag_configure("other", background="#fdf3e3", foreground=AMBER)
        self.tree_m.pack(fill="both", expand=True, padx=10, pady=2)
        self.total_m = tk.Label(tab, text="汇总: - / -", font=("微软雅黑", 13, "bold"),
                                bg=BG, fg=PRIMARY, anchor="w")
        self.total_m.pack(fill="x", padx=12, pady=6)

    # ---------- 工具 ----------
    def _pick_gxx(self):
        f = filedialog.askopenfilename(title="选择编译器 g++.exe", filetypes=[("可执行文件", "*.exe")])
        if f:
            self.var_gxx.set(f)

    def _mk_lang_combo(self, parent):
        """语言下拉：显示 C++/Python/Java，内部保存语言 id。"""
        cb = ttk.Combobox(parent, width=9, state="readonly",
                          values=[_lang_label(x) for x in LANG_ORDER])
        cb.set(_lang_label(self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp"))
        cb.bind("<<ComboboxSelected>>", self._on_lang_pick)
        cb.pack(side="left")
        return cb

    def _on_lang_pick(self, event=None):
        """下拉选中后把显示名写回内部语言 id。"""
        cb = getattr(event, "widget", None) or self.root.focus_get()
        try:
            label = cb.get()
        except Exception:
            return
        for k in LANG_ORDER:
            if _lang_label(k) == label:
                self.var_lang.set(k)
                self._sync_lang_combos()
                return

    def _sync_lang_combos(self):
        """语言 id 变化后，把所有下拉显示同步成对应名字。"""
        label = _lang_label(self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp")
        for name in ("cb_lang_s", "cb_lang_m", "cb_lang_b"):
            cb = getattr(self, name, None)
            if cb is not None:
                try:
                    cb.set(label)
                except Exception:
                    pass

    def _auto_pick_lang(self, path):
        """按源码扩展名自动切换语言（.py → Python，.java → Java，其余 C++）。"""
        if not path:
            return
        lang = _guess_lang(path)
        if lang != self.var_lang.get():
            self.var_lang.set(lang)
            self._sync_lang_combos()

    def _pick_file(self, var, guess_lang=False):
        f = filedialog.askopenfilename(title="选择文件", filetypes=[("C++ 源码", "*.cpp"), ("所有文件", "*.*")])
        if f:
            var.set(f)
            if guess_lang:
                self._auto_pick_lang(f)

    def _pick_dir(self, var):
        d = filedialog.askdirectory(title="选择目录")
        if d:
            var.set(d)

    # ---------- 界面语言切换 ----------
    def _reg_tab(self, tab, zh_text):
        """登记一个标签页，便于切换语言时改标题。"""
        self._i18n_tabs.append((tab, zh_text))
        return tab

    def _reg_tree(self, tree, cols):
        """登记一个表格的列头，便于切换语言时改列名。"""
        self._i18n_trees.append((tree, list(cols)))
        return tree

    @staticmethod
    def _collect_widgets(widget, out):
        """递归收集可翻译控件（跳过输入框与下拉，避免破坏用户输入）。"""
        try:
            kids = widget.winfo_children()
        except Exception:
            kids = []
        for w in kids:
            cls = w.winfo_class()
            if cls not in ("TEntry", "Entry", "TCombobox", "Combobox", "Text"):
                out.append(w)
            JudgeApp._collect_widgets(w, out)

    def _apply_lang(self):
        """按当前语言刷新界面文案（控件文本 / 表格列头 / 标签页 / 标题栏）。

        策略：每个控件记住「原文 + 上次应用后的文本」。若当前文本仍等于上次应用值，
        说明程序没改过它 → 用原文重新翻译；若程序改过（如状态栏变成「完成」），
        则以当前文本为新原文重新翻译，避免把动态状态覆盖回初始值。
        """
        widgets = []
        self._collect_widgets(self.root, widgets)
        for w in widgets:
            try:
                cur = w.cget("text")
            except Exception:
                continue
            if not isinstance(cur, str) or not cur.strip():
                continue
            key = id(w)
            orig = self._resolve_i18n(key, cur)
            new = _t(orig)
            self._i18n_state[key] = (orig, new)
            if new != cur:
                try:
                    w.configure(text=new)
                except Exception:
                    pass
        # 表格列头
        for tree, cols in self._i18n_trees:
            for col in cols:
                try:
                    cur = tree.heading(col, "text")
                except Exception:
                    continue
                key = ("h", id(tree), col)
                orig = self._resolve_i18n(key, cur)
                new = _t(orig)
                self._i18n_state[key] = (orig, new)
                if new != cur:
                    try:
                        tree.heading(col, text=new)
                    except Exception:
                        pass
        # 标签页
        for tab, zh in self._i18n_tabs:
            try:
                self._nb.tab(tab, text=_t(zh))
            except Exception:
                pass
        # 标题栏（Canvas 需重绘）
        redraw = getattr(self.root, "_oj_header_redraw", None)
        if callable(redraw):
            try:
                redraw()
            except Exception:
                pass

    def _resolve_i18n(self, key, cur):
        """判断控件当前文本的「原文」是什么（区分程序改过与只是语言切换）。"""
        state = self._i18n_state.get(key)
        if state:
            orig, applied = state
            if cur == applied or cur == orig:
                return orig
        return cur

    def _on_ui_lang(self, event=None):
        """界面语言下拉：切换中文 / English。"""
        cb = getattr(event, "widget", None)
        try:
            label = cb.get() if cb is not None else "中文"
        except Exception:
            return
        global UI_LANG
        for code, name in UI_LANGS:
            if name == label:
                UI_LANG = code
                break
        self._apply_lang()
        self._sync_lang_combos()

    # ---------- 编译器自动探测与引导 ----------
    def _auto_detect_compiler(self):
        """启动探测 PATH 上的编译器：默认路径存在则不动；否则自动探测并填好。"""
        cur = self.var_gxx.get().strip()
        if cur and os.path.isfile(cur):
            return
        found = _detect_compiler()
        if found:
            self.var_gxx.set(found)
            self._persist_settings()

    def _open_compiler_guide(self):
        """打开 WinLibs 下载页（解压即用，对应默认路径 C:\\mingw64）。"""
        url = "https://www.winlibs.com/"
        try:
            webbrowser.open(url)
        except Exception:
            pass
        messagebox.showinfo("下载编译器",
            "已在浏览器打开 WinLibs 下载页。\n\n"
            "推荐下载「UCRT 运行时」版、64-bit 的 ZIP，解压后把 mingw64 文件夹放到 C 盘根目录，\n"
            "即 C:\\mingw64\\bin\\g++.exe，软件已默认指向该路径。\n\n"
            "解压后若编译器仍未自动识别，可点「浏览」手动选择 g++.exe。")

    # ---------- 内置示例题（单题页） ----------
    def _load_example_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("载入示例题")
        dlg.geometry("440x330")
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Label(dlg, text="选一道示例题，一键落盘源码与样例数据：", font=("微软雅黑", 10), pady=8).pack()
        for ex in EXAMPLES:
            f = tk.Frame(dlg); f.pack(fill="x", padx=12, pady=4)
            ttk.Button(f, text=ex["name"], command=lambda e=ex, d=dlg: self._load_example(e, d)).pack(side="left")
            tk.Label(f, text=ex["desc"], font=("微软雅黑", 9), fg="#8a93a5",
                     wraplength=290, justify="left").pack(side="left", padx=8)
        ttk.Button(dlg, text="关闭", command=dlg.destroy).pack(pady=10)

    def _load_example(self, ex, dlg):
        try:
            idx = EXAMPLES.index(ex) + 1
            folder = os.path.join(_app_base(), "内置示例", "example%d" % idx)
            datadir = os.path.join(folder, "data")
            os.makedirs(datadir, exist_ok=True)
            with open(os.path.join(folder, "main.cpp"), "w", encoding="utf-8") as f:
                f.write(ex["cpp"])
            for i, (inp, out) in enumerate(ex["cases"], 1):
                with open(os.path.join(datadir, "%d.in" % i), "w", encoding="utf-8") as f:
                    f.write(inp)
                with open(os.path.join(datadir, "%d.out" % i), "w", encoding="utf-8") as f:
                    f.write(out)
            self.var_src.set(os.path.join(folder, "main.cpp"))
            self.var_data.set(datadir)
            self.status_single.config(text="已载入示例：%s，点「开始评测」试跑" % ex["name"])
            dlg.destroy()
        except Exception as e:
            messagebox.showerror("载入失败", str(e))

    # ---------- 内置对拍挑战（对拍页） ----------
    def _load_challenge_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("载入对拍挑战")
        dlg.geometry("470x370")
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Label(dlg, text="每个挑战都埋了一个真 bug，生成器+主程序+暴力已备齐，对拍即现形：",
                 font=("微软雅黑", 10), pady=8).pack()
        for ch in BATTLE_CHALLENGES:
            f = tk.Frame(dlg); f.pack(fill="x", padx=12, pady=4)
            ttk.Button(f, text=ch["name"], command=lambda c=ch, d=dlg: self._load_challenge(c, d)).pack(side="left")
            tk.Label(f, text="[%s] %s" % (ch["bug"], ch["desc"]), font=("微软雅黑", 9),
                     fg="#8a93a5", wraplength=320, justify="left").pack(side="left", padx=8)
        ttk.Button(dlg, text="关闭", command=dlg.destroy).pack(pady=10)

    def _load_challenge(self, ch, dlg):
        try:
            folder = os.path.join(_app_base(), "内置挑战", ch["id"])
            os.makedirs(folder, exist_ok=True)
            for fn, code in (("gen.cpp", ch["gen_cpp"]), ("main.cpp", ch["main_cpp"]),
                             ("brute.cpp", ch["brute_cpp"])):
                with open(os.path.join(folder, fn), "w", encoding="utf-8") as f:
                    f.write(code)
            self.var_b_main.set(os.path.join(folder, "main.cpp"))
            self.var_b_brute.set(os.path.join(folder, "brute.cpp"))
            self.var_b_gen.set(os.path.join(folder, "gen.cpp"))
            self.var_b_rounds.set(ch.get("rounds", 100))
            self._current_challenge = ch["name"]
            self.status_battle.config(text="已载入挑战：%s，点「开始对拍」揪虫" % ch["name"])
            dlg.destroy()
        except Exception as e:
            messagebox.showerror("载入失败", str(e))

    # ---------- 对拍战绩卡导出 ----------
    def _export_battle_report(self):
        """对拍完成后生成样式化 HTML 战绩卡 + 纯文本备份，并用浏览器打开。"""
        stat = self._last_battle
        if not stat:
            return
        try:
            ts = time.strftime("%Y%m%d_%H%M%S")
            raw = (stat.get("name") or "自由对拍").replace(" ", "_").replace("·", "")
            out_dir = os.path.join(_app_base(), "对拍报告")
            os.makedirs(out_dir, exist_ok=True)
            html_path = os.path.join(out_dir, "对拍战绩_%s_%s.html" % (raw, ts))
            txt_path = os.path.join(out_dir, "对拍战绩_%s_%s.txt" % (raw, ts))

            ok = stat.get("ok")
            problems = stat.get("problems", 0)
            consistent = stat.get("consistent", 0)
            rounds = stat.get("rounds", 0)
            verdict = "全部一致 ✓" if ok else ("发现问题 ✗" if ok is False else "异常")
            vclass = "ok" if ok else ("bad" if ok is False else "warn")
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            title = stat.get("name") or "自由对拍"

            html = (
                "<!doctype html><html lang=\"zh\"><head><meta charset=\"utf-8\">"
                "<title>OJJudge 对拍战绩卡</title><style>"
                "body{margin:0;font-family:\"Microsoft YaHei\",system-ui,sans-serif;background:#0f1226;"
                "display:flex;justify-content:center;padding:32px}"
                ".card{width:680px;background:linear-gradient(160deg,#1b1f3b,#241a46);border-radius:18px;"
                "padding:28px 32px;color:#e7e9f5;box-shadow:0 20px 60px rgba(0,0,0,.45)}"
                ".brand{font-size:13px;letter-spacing:2px;color:#a5b4fc;text-transform:uppercase}"
                "h1{margin:6px 0 2px;font-size:24px}.sub{color:#c4b5fd;font-size:13px}"
                ".verdict{margin:18px 0;font-size:30px;font-weight:800}"
                ".ok{color:#34d399}.bad{color:#fb7185}.warn{color:#fbbf24}"
                ".stats{display:flex;gap:14px;margin:14px 0}"
                ".stat{flex:1;background:rgba(255,255,255,.06);border-radius:12px;padding:14px;text-align:center}"
                ".stat .n{font-size:26px;font-weight:800}.stat .l{font-size:12px;color:#aab;margin-top:4px}"
                ".foot{margin-top:18px;font-size:12px;color:#9aa3b2;border-top:1px solid rgba(255,255,255,.12);"
                "padding-top:12px}</style></head><body><div class=\"card\">"
                "<div class=\"brand\">OJJudge 对拍战绩卡</div>"
                "<h1>%s</h1><div class=\"sub\">v%s</div>"
                "<div class=\"verdict %s\">%s</div>"
                "<div class=\"stats\">"
                "<div class=\"stat\"><div class=\"n\">%d</div><div class=\"l\">总轮数</div></div>"
                "<div class=\"stat\"><div class=\"n\" style=\"color:#34d399\">%d</div><div class=\"l\">一致轮数</div></div>"
                "<div class=\"stat\"><div class=\"n\" style=\"color:#fb7185\">%d</div><div class=\"l\">发现问题</div></div>"
                "</div>"
                "<div class=\"foot\">生成时间：%s · 用 OJJudge 本地评测软件对拍生成 · "
                "参赛话题 #WorkBuddy #1024程序员节</div>"
                "</div></body></html>"
            ) % (title, VERSION, vclass, verdict, rounds, consistent, problems, now)

            txt = ("OJJudge 对拍战绩卡\n挑战：%s\n结果：%s\n总轮数：%d　一致：%d　问题：%d\n生成时间：%s\n"
                   "（用 OJJudge 本地评测软件对拍生成 · #WorkBuddy #1024程序员节）\n") % (
                   title, verdict, rounds, consistent, problems, now)

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(txt)
            try:
                webbrowser.open("file://" + html_path.replace("\\", "/"))
            except Exception:
                pass
            self.status_battle.config(text=_t("战绩卡已生成，已用浏览器打开（也可在「对拍报告」文件夹查看）"))
        except Exception as e:
            try:
                messagebox.showinfo("战绩报告", "生成报告时出错：%s" % e)
            except Exception:
                pass

    # ---------- 对拍模式 ----------
    def _build_battle_tab(self):
        tab = ttk.Frame(self._nb)
        self._nb.add(tab, text="  对拍  ")
        self._reg_tab(tab, "  对拍  ")
        pad = {"padx": 10, "pady": 5}
        self._section_label(tab, "参数设置")

        r1 = ttk.Frame(tab); r1.pack(fill="x", **pad)
        ttk.Label(r1, text="主程序(.cpp):").pack(side="left")
        self.var_b_main = tk.StringVar()
        ttk.Entry(r1, textvariable=self.var_b_main).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r1, text="浏览", command=lambda: self._pick_file(self.var_b_main)).pack(side="left")

        r2 = ttk.Frame(tab); r2.pack(fill="x", **pad)
        ttk.Label(r2, text="暴力/标程(.cpp):").pack(side="left")
        self.var_b_brute = tk.StringVar()
        ttk.Entry(r2, textvariable=self.var_b_brute).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r2, text="浏览", command=lambda: self._pick_file(self.var_b_brute)).pack(side="left")

        r3 = ttk.Frame(tab); r3.pack(fill="x", **pad)
        ttk.Label(r3, text="数据生成器(.cpp):").pack(side="left")
        self.var_b_gen = tk.StringVar()
        ttk.Entry(r3, textvariable=self.var_b_gen).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r3, text="浏览", command=lambda: self._pick_file(self.var_b_gen)).pack(side="left")

        r4 = ttk.Frame(tab); r4.pack(fill="x", **pad)
        ttk.Label(r4, text="对拍轮数:").pack(side="left")
        self.var_b_rounds = tk.IntVar(value=int(load_settings().get("battle_rounds", 100)))
        ttk.Spinbox(r4, from_=1, to=100000, textvariable=self.var_b_rounds, width=8).pack(side="left", padx=6)
        ttk.Label(r4, text="语言:").pack(side="left", padx=(6, 4))
        self.cb_lang_b = self._mk_lang_combo(r4)
        self.btn_battle = ttk.Button(r4, text="开始对拍", style="Accent.TButton", command=self._start_battle)
        self.btn_battle.pack(side="left", padx=12)
        ttk.Button(r4, text="载入挑战", command=self._load_challenge_dialog).pack(side="left")
        self.status_battle = ttk.Label(r4, text="就绪（可点「载入挑战」一键备齐生成器+主程序+暴力）", style="Status.TLabel")
        self.status_battle.pack(side="left", padx=6)

        # 说明
        tip = ("对拍说明：数据生成器每轮生成一组随机输入，主程序与暴力/标程分别运行并比对输出；\n"
               "三者约定通过标准输入输出读写（生成器往 stdout 写数据，主/暴力从 stdin 读并往 stdout 写）。\n"
               "若你的程序用了 freopen 读写固定文件名，请改用标准输入输出，否则无法对拍。")
        ttk.Label(tab, text=tip, style="Hint.TLabel", wraplength=780, justify="left").pack(anchor="w", padx=10)

        # 日志
        self._section_label(tab, "对拍日志")
        self.battle_log = tk.Text(tab, height=12, state="disabled", wrap="word",
                                  bg="#0f172a", fg="#e2e8f0",
                                  insertbackground="#e2e8f0", relief="flat",
                                  font=("Consolas", 10), padx=8, pady=6)
        self.battle_log.pack(fill="both", expand=True, padx=10, pady=4)
        self.battle_log.tag_configure("ok", foreground="#4ade80")
        self.battle_log.tag_configure("fail", foreground="#f87171")
        self.battle_log.tag_configure("err", foreground="#fbbf24")
        sb = ttk.Scrollbar(tab, command=self.battle_log.yview)
        self.battle_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

    def _battle_log_append(self, msg, tag=None):
        self.battle_log.configure(state="normal")
        self.battle_log.insert("end", msg + "\n", tag)
        self.battle_log.see("end")
        self.battle_log.configure(state="disabled")

    def _start_battle(self):
        if self._running:
            return
        main = self.var_b_main.get().strip()
        brute = self.var_b_brute.get().strip()
        gen = self.var_b_gen.get().strip()
        gxx = self.var_gxx.get().strip()
        lang = self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp"
        if not main or not brute or not gen or (lang == "cpp" and not gxx):
            messagebox.showwarning("提示", "主程序/暴力/生成器" + ("/编译器" if lang == "cpp" else "") + "都要填")
            return
        for label, p in (("主程序", main), ("暴力", brute), ("生成器", gen)):
            if not os.path.isfile(p):
                messagebox.showwarning("提示", f"{label}文件不存在: {p}")
                return
        rounds = max(1, self.var_b_rounds.get())

        self._running = True
        self.btn_battle.state(["disabled"])
        self.battle_log.configure(state="normal")
        self.battle_log.delete("1.0", "end")
        self.battle_log.configure(state="disabled")
        self.status_battle.config(text=_t("对拍中..."))
        std = self.var_std.get().strip() or "c++14"
        opt = self.var_opt.get()
        tmo = int(self.var_timeout.get())
        threading.Thread(target=self._run_battle, args=(main, brute, gen, rounds, gxx, std, opt, tmo, lang), daemon=True).start()

    def _run_battle(self, main, brute, gen, rounds, gxx, std, opt, tmo, lang="cpp"):
        workdir = os.path.join(os.path.dirname(main), "_battle_tmp")
        os.makedirs(workdir, exist_ok=True)
        # 对拍统计：供战绩卡使用
        self._battle_stat = {"rounds": rounds, "consistent": 0,
                             "problems": 0, "name": self._current_challenge}

        def rep(kind, msg):
            if kind == "info":
                self._battle_stat["consistent"] += 1
                self._ui(lambda m=msg: (self._battle_log_append(m, "ok"),
                                        self.status_battle.config(text=_t("对拍中"))))
            elif kind == "warn":
                # 每一处不一致/异常：记录到日志，但继续对拍，不弹窗
                self._battle_stat["problems"] += 1
                self._ui(lambda m=msg: self._battle_log_append(m, "fail"))
            elif kind in ("fail", "error"):
                tag = "fail" if kind == "fail" else "err"
                self._ui(lambda m=msg, t=tag: (self._battle_log_append(m, t),
                                               self.status_battle.config(text=_t("发现问题")),
                                               messagebox.showwarning("对拍发现不一致", m)))
            else:
                self._ui(lambda m=msg: (self._battle_log_append(m, "ok"),
                                        self.status_battle.config(text=_t("通过"))))

        try:
            ok = run_battle(main, brute, gen, gxx, std, opt, rounds, workdir, report=rep,
                            timeout_ms=tmo, lang=lang)
            self._battle_ok = ok
        except Exception as e:
            self._battle_ok = None
            self._ui(lambda: messagebox.showerror("错误", str(e)))
        finally:
            self._ui(self._battle_done)
            # 清理临时文件（保留最后一份 data 便于查看）
            for f in ("_gen.exe", "_main.exe", "_brute.exe", "main.out", "brute.out"):
                try:
                    p = os.path.join(workdir, f)
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    def _battle_done(self):
        self._running = False
        self.btn_battle.state(["!disabled"])
        ok = self._battle_ok
        summary = ("对拍全部一致" if ok else ("对拍发现问题" if ok is False else "对拍异常"))
        detail = self.battle_log.get("1.0", "end").strip()
        self._add_eval_record("对拍", summary, detail)
        # 生成战绩卡（快照统计，避免后续被覆盖）
        self._last_battle = dict(self._battle_stat or {})
        self._last_battle["ok"] = ok
        self._export_battle_report()
        self._battle_ok = None

    # ---------- 造数据模式 ----------
    def _build_gen_tab(self):
        tab = ttk.Frame(self._nb)
        self._nb.add(tab, text="  造数据  ")
        self._reg_tab(tab, "  造数据  ")
        pad = {"padx": 10, "pady": 5}
        self._section_label(tab, "参数设置")

        r1 = ttk.Frame(tab); r1.pack(fill="x", **pad)
        ttk.Label(r1, text="题名前缀:").pack(side="left")
        self.var_g_task = tk.StringVar(value="test")
        ttk.Entry(r1, textvariable=self.var_g_task, width=12).pack(side="left", padx=6)
        ttk.Label(r1, text="输出目录:").pack(side="left")
        self.var_g_dir = tk.StringVar()
        ttk.Entry(r1, textvariable=self.var_g_dir).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r1, text="浏览", command=lambda: self._pick_dir(self.var_g_dir)).pack(side="left")

        r2 = ttk.Frame(tab); r2.pack(fill="x", **pad)
        ttk.Label(r2, text="数据生成器(.cpp):").pack(side="left")
        self.var_g_gen = tk.StringVar()
        ttk.Entry(r2, textvariable=self.var_g_gen).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r2, text="浏览", command=lambda: self._pick_file(self.var_g_gen)).pack(side="left")

        r3 = ttk.Frame(tab); r3.pack(fill="x", **pad)
        ttk.Label(r3, text="答案程序(.cpp):").pack(side="left")
        self.var_g_ans = tk.StringVar()
        ttk.Entry(r3, textvariable=self.var_g_ans).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r3, text="浏览", command=lambda: self._pick_file(self.var_g_ans)).pack(side="left")

        r4 = ttk.Frame(tab); r4.pack(fill="x", **pad)
        ttk.Label(r4, text="组数:").pack(side="left")
        self.var_g_rounds = tk.IntVar(value=10)
        ttk.Spinbox(r4, from_=1, to=1000, textvariable=self.var_g_rounds, width=6).pack(side="left", padx=6)
        ttk.Label(r4, text="答案后缀:").pack(side="left")
        self.var_g_ext = tk.StringVar(value=".out")
        ttk.Combobox(r4, textvariable=self.var_g_ext, width=6,
                     values=[".out", ".ans"]).pack(side="left", padx=6)
        self.btn_gen = ttk.Button(r4, text="开始生成", style="Accent.TButton", command=self._start_gen)
        self.btn_gen.pack(side="left", padx=12)
        self.status_gen = ttk.Label(r4, text="就绪", style="Status.TLabel")
        self.status_gen.pack(side="left", padx=6)

        tip = ("造数据说明：数据生成器每轮造一组随机输入（往 stdout 写），存为 <前缀><n>.in；\n"
               "答案程序读取该输入（stdin）、往 stdout 写答案，存为 <前缀><n>.out/.ans。\n"
               "生成的数据即可用于「单题/多题」评测。若已有同名文件会被覆盖。")
        ttk.Label(tab, text=tip, style="Hint.TLabel", wraplength=780, justify="left").pack(anchor="w", padx=10)

        self._section_label(tab, "生成日志")
        self.gen_log = tk.Text(tab, height=12, state="disabled", wrap="word",
                               bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0",
                               relief="flat", font=("Consolas", 10), padx=8, pady=6)
        self.gen_log.pack(fill="both", expand=True, padx=10, pady=4)
        self.gen_log.tag_configure("ok", foreground="#4ade80")
        self.gen_log.tag_configure("err", foreground="#fbbf24")
        sb = ttk.Scrollbar(tab, command=self.gen_log.yview)
        self.gen_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

    def _gen_log_append(self, msg, tag=None):
        self.gen_log.configure(state="normal")
        self.gen_log.insert("end", msg + "\n", tag)
        self.gen_log.see("end")
        self.gen_log.configure(state="disabled")

    def _start_gen(self):
        if self._running:
            return
        task = self.var_g_task.get().strip() or "test"
        outdir = self.var_g_dir.get().strip()
        gen = self.var_g_gen.get().strip()
        ans = self.var_g_ans.get().strip()
        gxx = self.var_gxx.get().strip()
        if not outdir or not gen or not ans or not gxx:
            messagebox.showwarning("提示", "输出目录/生成器/答案程序/编译器都要填")
            return
        for label, p in (("生成器", gen), ("答案程序", ans)):
            if not os.path.isfile(p):
                messagebox.showwarning("提示", f"{label}文件不存在: {p}")
                return
        rounds = max(1, self.var_g_rounds.get())

        self._running = True
        self.btn_gen.state(["disabled"])
        self.gen_log.configure(state="normal")
        self.gen_log.delete("1.0", "end")
        self.gen_log.configure(state="disabled")
        self.status_gen.config(text=_t("生成中..."))
        std = self.var_std.get().strip() or "c++14"
        opt = self.var_opt.get()
        ext = self.var_g_ext.get().strip() or ".out"
        lang = self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp"
        threading.Thread(target=self._run_gen, args=(task, outdir, gen, ans, rounds, gxx, std, opt, ext, lang), daemon=True).start()

    def _run_gen(self, task, outdir, gen, ans, rounds, gxx, std, opt, ext, lang="cpp"):
        def rep(kind, msg):
            if kind == "info":
                self._ui(lambda m=msg: (self._gen_log_append(m, "ok"),
                                        self.status_gen.config(text=_t("生成中"))))
            elif kind in ("fail", "error"):
                self._ui(lambda m=msg: (self._gen_log_append("【错误】" + m, "err"),
                                        self.status_gen.config(text=_t("出错"))))
            else:
                self._ui(lambda m=msg: (self._gen_log_append(m, "ok"),
                                        self.status_gen.config(text=_t("完成"))))

        try:
            generate_data(gen, ans, task, rounds, outdir, gxx, std, opt,
                          ext=ext, report=rep, lang=lang)
        except Exception as e:
            self._ui(lambda: messagebox.showerror("错误", str(e)))
        finally:
            self._ui(self._gen_done)

    def _gen_done(self):
        self._running = False
        self.btn_gen.state(["!disabled"])
        detail = self.gen_log.get("1.0", "end").strip()
        self._add_eval_record("造数据", "造数据完成", detail)

    # ---------- 随机数据模式（按格式+范围，无需手写生成器） ----------
    def _build_random_tab(self):
        tab = ttk.Frame(self._nb)
        self._nb.add(tab, text="  随机数据  ")
        self._reg_tab(tab, "  随机数据  ")
        pad = {"padx": 10, "pady": 4}
        self._section_label(tab, "输入格式")

        r0 = ttk.Frame(tab); r0.pack(fill="x", **pad)
        ttk.Label(r0, text="输入格式：").pack(side="left")
        self.var_r_format = tk.Text(r0, width=60, height=3, wrap="none",
                                    bg="#ffffff", fg="#2b3344",
                                    insertbackground=PRIMARY, relief="flat",
                                    highlightbackground=BORDER, highlightthickness=1,
                                    font=("Consolas", 10), padx=6, pady=4)
        self.var_r_format.pack(side="left", fill="x", expand=True, padx=6)
        self.var_r_format.insert("1.0", "{n}\n{n} 行: {a} {b}")

        r1 = ttk.Frame(tab); r1.pack(fill="x", **pad)
        ttk.Label(r1, text="输入范围：").pack(side="left")
        self.var_r_range = tk.StringVar(value="n=1~100000 a=-1e9~1e9 b=-1e9~1e9")
        ttk.Entry(r1, textvariable=self.var_r_range).pack(side="left", fill="x", expand=True, padx=6)

        r2 = ttk.Frame(tab); r2.pack(fill="x", **pad)
        ttk.Label(r2, text="AC 代码(.cpp)（可留空）:").pack(side="left")
        self.var_r_ac = tk.StringVar()
        ttk.Entry(r2, textvariable=self.var_r_ac).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r2, text="浏览", command=lambda: self._pick_file(self.var_r_ac)).pack(side="left")

        r3 = ttk.Frame(tab); r3.pack(fill="x", **pad)
        ttk.Label(r3, text="生成位置:").pack(side="left")
        self.var_r_dir = tk.StringVar()
        ttk.Entry(r3, textvariable=self.var_r_dir).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(r3, text="浏览", command=lambda: self._pick_dir(self.var_r_dir)).pack(side="left")

        r4 = ttk.Frame(tab); r4.pack(fill="x", **pad)
        ttk.Label(r4, text="数量:").pack(side="left")
        self.var_r_count = tk.IntVar(value=20)
        ttk.Spinbox(r4, from_=1, to=1000, textvariable=self.var_r_count, width=6).pack(side="left", padx=6)
        ttk.Label(r4, text="前缀:").pack(side="left")
        self.var_r_task = tk.StringVar(value="test")
        ttk.Entry(r4, textvariable=self.var_r_task, width=8).pack(side="left", padx=6)
        ttk.Label(r4, text="后缀:").pack(side="left")
        self.var_r_ext = tk.StringVar(value=".out")
        ttk.Combobox(r4, textvariable=self.var_r_ext, width=6,
                     values=[".out", ".ans"]).pack(side="left", padx=6)
        self.btn_random = ttk.Button(r4, text="开始生成", style="Accent.TButton",
                                     command=self._start_random)
        self.btn_random.pack(side="left", padx=12)
        self.status_random = ttk.Label(r4, text="就绪", style="Status.TLabel")
        self.status_random.pack(side="left", padx=6)

        tip = ("格式说明：{字母} 表示随机数，空格分隔；单行 `{n} {m}` 输出一行；"
               "重复用 `{n} 行: {a} {b}` 表示按 n 的值输出多行。\n"
               "范围用 `字母=最小~最大`（支持 1e9），多个用空格分开。"
               "AC 代码编译后对每组输入跑出 .out，走标准输入输出（不用 freopen）。")
        ttk.Label(tab, text=tip, style="Hint.TLabel", wraplength=820,
                  justify="left").pack(anchor="w", padx=10, pady=(2, 2))

        self._section_label(tab, "生成日志")
        self.random_log = tk.Text(tab, height=10, state="disabled", wrap="word",
                                  bg="#0f172a", fg="#e2e8f0", insertbackground="#e2e8f0",
                                  relief="flat", font=("Consolas", 10), padx=8, pady=6)
        self.random_log.pack(fill="both", expand=True, padx=10, pady=4)
        self.random_log.tag_configure("ok", foreground="#4ade80")
        self.random_log.tag_configure("err", foreground="#fbbf24")
        sb = ttk.Scrollbar(tab, command=self.random_log.yview)
        self.random_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

    def _random_log_append(self, msg, tag=None):
        self.random_log.configure(state="normal")
        self.random_log.insert("end", msg + "\n", tag)
        self.random_log.see("end")
        self.random_log.configure(state="disabled")

    def _start_random(self):
        if self._running:
            return
        fmt = self.var_r_format.get("1.0", "end")
        rng = self.var_r_range.get().strip()
        ac = self.var_r_ac.get().strip()
        outdir = self.var_r_dir.get().strip()
        gxx = self.var_gxx.get().strip()
        if not fmt.strip() or not outdir or not gxx:
            messagebox.showwarning("提示", "输入格式 / 生成位置 / 编译器 都要填")
            return
        if ac and not os.path.isfile(ac):
            messagebox.showwarning("提示", "AC 代码文件不存在: " + ac)
            return
        count = max(1, self.var_r_count.get())

        self._running = True
        self.btn_random.state(["disabled"])
        self.random_log.configure(state="normal")
        self.random_log.delete("1.0", "end")
        self.random_log.configure(state="disabled")
        self.status_random.config(text=_t("生成中..."))
        std = self.var_std.get().strip() or "c++14"
        opt = self.var_opt.get()
        task = self.var_r_task.get().strip() or "test"
        ext = self.var_r_ext.get().strip() or ".out"
        lang = self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp"
        threading.Thread(target=self._run_random,
                         args=(fmt, rng, count, ac, outdir, gxx, std, opt, task, ext, lang), daemon=True).start()

    def _run_random(self, fmt, rng, count, ac, outdir, gxx, std, opt, task, ext, lang="cpp"):
        def rep(kind, msg):
            if kind == "info":
                self._ui(lambda m=msg: (self._random_log_append(m, "ok"),
                                        self.status_random.config(text=_t("生成中"))))
            elif kind in ("fail", "error"):
                self._ui(lambda m=msg: (self._random_log_append("【错误】" + m, "err"),
                                        self.status_random.config(text=_t("出错"))))
            else:
                self._ui(lambda m=msg: (self._random_log_append(m, "ok"),
                                        self.status_random.config(text=_t("完成"))))

        try:
            generate_random_data(fmt, rng, count, ac, outdir, gxx, std, opt,
                                 task=task, ext=ext, report=rep, lang=lang)
        except Exception as e:
            self._ui(lambda: messagebox.showerror("错误", str(e)))
        finally:
            self._ui(self._random_done)

    def _random_done(self):
        self._running = False
        self.btn_random.state(["!disabled"])
        detail = self.random_log.get("1.0", "end").strip()
        self._add_eval_record("随机数据", "随机数据完成", detail)

    # ---------- 记录页（评测记录 + 改动日志） ----------
    def _build_record_tab(self):
        tab = ttk.Frame(self._nb)
        self._nb.add(tab, text="  记录  ")
        self._reg_tab(tab, "  记录  ")
        pad = {"padx": 10, "pady": 5}

        bar = ttk.Frame(tab); bar.pack(fill="x", **pad)
        self.btn_rec_evals = ttk.Button(bar, text="评测记录", command=lambda: self._show_record_view("evals"))
        self.btn_rec_log = ttk.Button(bar, text="改动日志", command=lambda: self._show_record_view("log"))
        self.btn_rec_evals.pack(side="left")
        self.btn_rec_log.pack(side="left", padx=6)
        ttk.Button(bar, text="清空记录", style="Danger.TButton",
                   command=self._clear_records).pack(side="left", padx=6)
        self.rec_status = ttk.Label(bar, text=f"评测记录 {len(self._records)} 条", style="Status.TLabel")
        self.rec_status.pack(side="left", padx=12)

        self._section_label(tab, "记录列表")
        self.rec_tree = ttk.Treeview(tab, columns=("时间", "模式", "结果"), show="headings", height=8)
        self._reg_tree(self.rec_tree, ("时间", "模式", "结果"))
        for c, w in (("时间", 150), ("模式", 60), ("结果", 440)):
            self.rec_tree.heading(c, text=c)
            self.rec_tree.column(c, width=w, anchor="w")
        self.rec_tree.pack(fill="x", padx=10, pady=2)
        self.rec_tree.bind("<<TreeviewSelect>>", self._on_rec_select)

        self._section_label(tab, "详情 / 日志")
        self.rec_detail = tk.Text(tab, bg="#0f172a", fg="#e2e8f0", font=("Consolas", 10),
                                  state="disabled", height=12, wrap="none")
        self.rec_detail.pack(fill="both", expand=True, padx=10, pady=2)
        self.rec_detail.tag_configure("ok", foreground="#4ade80")
        self.rec_detail.tag_configure("err", foreground="#fbbf24")

        self._refresh_record_tree()
        self._show_record_view("evals")

    def _refresh_record_tree(self):
        for i in self.rec_tree.get_children():
            self.rec_tree.delete(i)
        # 最新的放最上面
        for rec in reversed(self._records):
            self.rec_tree.insert("", "end", values=(
                rec.get("time", ""), rec.get("mode", ""), rec.get("summary", "")))
        self.rec_status.config(text=_t(f"评测记录 {len(self._records)} 条"))

    def _on_rec_select(self, event=None):
        sel = self.rec_tree.selection()
        if not sel:
            return
        idx = self.rec_tree.index(sel[0])
        rec = list(reversed(self._records))[idx]
        self._set_detail(rec.get("detail", rec.get("summary", "")))

    def _show_record_view(self, view):
        if view == "log":
            self.rec_tree.pack_forget()
            self._set_detail(CHANGELOG)
        else:
            self.rec_tree.pack(fill="x", padx=10, pady=2)
            sel = self.rec_tree.selection()
            if sel:
                self._on_rec_select()

    def _set_detail(self, text):
        self.rec_detail.configure(state="normal")
        self.rec_detail.delete("1.0", "end")
        self.rec_detail.insert("1.0", text)
        self.rec_detail.configure(state="disabled")

    def _add_eval_record(self, mode, summary, detail=""):
        self._records.append({"time": time.strftime("%Y-%m-%d %H:%M:%S"),
                              "mode": mode, "summary": summary, "detail": detail})
        save_records(self._records)
        self._refresh_record_tree()

    def _clear_records(self):
        if not self._records:
            return
        if not messagebox.askyesno("清空记录", "确定清空全部评测记录？"):
            return
        self._records = []
        save_records(self._records)
        self._refresh_record_tree()
        self._set_detail("")

    # ---------- 单题评测 ----------
    def _poll_ui(self):
        """主线程轮询 UI 队列，执行工作线程丢来的界面更新。"""
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                fn()
        except queue.Empty:
            pass
        except Exception:
            pass
        self.root.after(80, self._poll_ui)

    def _ui(self, fn):
        """工作线程安全地把界面更新交给主线程执行。"""
        self._ui_queue.put(fn)

    def _start_single(self):
        if self._running:
            return
        src = self.var_src.get().strip()
        data = self.var_data.get().strip()
        gxx = self.var_gxx.get().strip()
        lang = self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp"
        if not self._validate(src, data, gxx, need_gxx=(lang == "cpp")):
            return
        self._running = True
        self.btn_single.state(["disabled"])
        self.status_single.config(text=_t("评测中..."))
        for i in self.tree_s.get_children():
            self.tree_s.delete(i)
        self.total_s.config(text=_t("总分: 评测中..."))
        std = self.var_std.get().strip() or "c++14"
        opt = self.var_opt.get()
        sp = self.var_score.get()
        tmo = int(self.var_timeout.get())
        lang = self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp"
        threading.Thread(target=self._run_single, args=(src, data, gxx, std, opt, sp, tmo, lang), daemon=True).start()

    def _run_single(self, src, data, gxx, std, opt, sp, tmo, lang="cpp"):
        def rep(label, status, score, ms, expect, actual):
            tag = "AC" if status == "AC" else ("WA" if status == "WA" else "other")
            self._ui(lambda l=label, s=status, sc=score, m=ms, e=expect, a=actual, t=tag:
                     self.tree_s.insert("", "end", values=(l, s, sc, m, e, a), tags=(t,)))

        ac, total, n = evaluate_one(src, data, gxx, std, opt, sp, report=rep,
                                    timeout_ms=tmo, lang=lang)
        self._ui(lambda t=total, a=ac, g=n: self._done_single(t, a, g))

    def _done_single(self, total, ac, n):
        self._running = False
        self.btn_single.state(["!disabled"])
        self.status_single.config(text=_t("完成"))
        sp = self.var_score.get()
        self.total_s.config(text=_t(f"总分: {total} / {n * sp}   （{ac}/{n} 组 AC）"))
        detail = "\n".join("  ".join(str(v) for v in self.tree_s.item(i, "values"))
                           for i in self.tree_s.get_children())
        self._add_eval_record("单题", f"总分 {total}/{n*sp}（{ac}/{n} AC）", detail)

    # ---------- 多题评测 ----------
    def _add_problem(self):
        # 用一个简单对话框收集题名/源码/数据目录
        dlg = tk.Toplevel(self.root)
        dlg.title("添加题目")
        dlg.geometry("520x160")
        dlg.transient(self.root)
        dlg.grab_set()
        name = tk.StringVar(value=f"题{self.problem_tree.get_children().__len__()+1}")
        src = tk.StringVar()
        data = tk.StringVar()
        r = ttk.Frame(dlg); r.pack(fill="x", padx=8, pady=4)
        ttk.Label(r, text="题名:").pack(side="left"); ttk.Entry(r, textvariable=name).pack(side="left", fill="x", expand=True)
        r = ttk.Frame(dlg); r.pack(fill="x", padx=8, pady=4)
        ttk.Label(r, text="源码:").pack(side="left"); ttk.Entry(r, textvariable=src).pack(side="left", fill="x", expand=True)
        ttk.Button(r, text="浏览", command=lambda: self._pick_file(src)).pack(side="left", padx=4)
        r = ttk.Frame(dlg); r.pack(fill="x", padx=8, pady=4)
        ttk.Label(r, text="数据:").pack(side="left"); ttk.Entry(r, textvariable=data).pack(side="left", fill="x", expand=True)
        ttk.Button(r, text="浏览", command=lambda: self._pick_dir(data)).pack(side="left", padx=4)
        btns = ttk.Frame(dlg); btns.pack(fill="x", padx=8, pady=6)
        def ok():
            if name.get().strip() and src.get().strip() and data.get().strip():
                self.problem_tree.insert("", "end",
                    values=(name.get().strip(), src.get().strip(), data.get().strip()))
                self._refresh_status_multi()
                dlg.destroy()
            else:
                messagebox.showwarning("提示", "题名/源码/数据目录都要填")
        ttk.Button(btns, text="确定", command=ok).pack(side="left")
        ttk.Button(btns, text="取消", command=dlg.destroy).pack(side="left", padx=6)

    def _del_problem(self):
        sel = self.problem_tree.selection()
        for i in sel:
            self.problem_tree.delete(i)
        self._refresh_status_multi()

    def _clear_problems(self):
        for i in self.problem_tree.get_children():
            self.problem_tree.delete(i)
        self._refresh_status_multi()

    def _import_problems_dialog(self):
        """手动导入：选择一个「题目导入.json」文件填入列表。"""
        path = filedialog.askopenfilename(
            title="选择题目导入文件", filetypes=[("JSON 导入文件", "*.json"), ("所有文件", "*.*")])
        if not path:
            return
        n = self._load_problem_import(path)
        if n >= 0:
            messagebox.showinfo("导入完成", f"已导入 {n} 道题。")

    def _load_problem_import(self, path=None):
        """从 JSON 导入题目到多题列表，返回导入的题数；文件不存在返回 0，解析失败返回 -1。"""
        path = path or _default_import_path()
        if not os.path.isfile(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception as e:
            messagebox.showwarning("导入失败", f"导入文件读取失败：\n{e}")
            return -1
        count = 0
        for e in entries:
            if not isinstance(e, dict):
                continue
            name = str(e.get("name", "")).strip()
            src = str(e.get("src", "")).strip()
            data = str(e.get("data", "")).strip()
            if name and src and data:
                self.problem_tree.insert("", "end", values=(name, src, data))
                count += 1
        self._refresh_status_multi()
        return count

    def _refresh_status_multi(self):
        n = len(self.problem_tree.get_children())
        self.status_multi.config(text=_t(f"就绪（{n} 题）"))

    def _start_multi(self):
        if self._running:
            return
        probs = []
        for i in self.problem_tree.get_children():
            vals = self.problem_tree.item(i, "values")
            probs.append((vals[0], vals[1], vals[2]))
        if not probs:
            messagebox.showwarning("提示", "请先添加题目")
            return
        for name, src, data in probs:
            if not self._validate(src, data, self.var_gxx.get().strip(), quiet=True,
                                  need_gxx=(self.var_lang.get() == "cpp")):
                return
        self._running = True
        self.status_multi.config(text=_t("评测中..."))
        for i in self.tree_m.get_children():
            self.tree_m.delete(i)
        self.total_m.config(text=_t("汇总: 评测中..."))
        gxx = self.var_gxx.get().strip()
        std = self.var_std.get().strip() or "c++14"
        opt = self.var_opt.get()
        sp = self.var_score.get()
        tmo = int(self.var_timeout.get())
        lang = self.var_lang.get() if self.var_lang.get() in LANG_DEFS else "cpp"
        threading.Thread(target=self._run_multi, args=(probs, gxx, std, opt, sp, tmo, lang), daemon=True).start()

    def _run_multi(self, probs, gxx, std, opt, sp, tmo, lang="cpp"):
        grand_ac = 0
        grand_total = 0
        grand_groups = 0
        lines = []

        def rep(name, label, status, score, ms, expect, actual):
            tag = "AC" if status == "AC" else ("WA" if status == "WA" else "other")
            self._ui(lambda n=name, l=label, s=status, sc=score, m=ms, e=expect, a=actual, t=tag:
                     self.tree_m.insert("", "end", values=(n, l, s, sc, m, e, a), tags=(t,)))

        for name, src, data in probs:
            self._ui(lambda n=name: self.status_multi.config(text=_t(f"评测中: {n}")))
            try:
                ac, total, n = evaluate_one(src, data, gxx, std, opt, sp,
                                            report=lambda l, s, sc, m, e, a, _n=name: rep(_n, l, s, sc, m, e, a),
                                            timeout_ms=tmo, lang=lang)
            except Exception as ex:
                # 单题评测异常不中断后续题目
                self._ui(lambda nm=name, err=ex: self.tree_m.insert(
                    "", "end", values=(nm, "评测异常", 0, 0, "", str(err)), tags=("other",)))
                ac, total, n = 0, 0, 0
            grand_ac += ac
            grand_total += total
            grand_groups += n
            lines.append((name, ac, total, n))

        def finish():
            self._running = False
            self.status_multi.config(text=_t("完成"))
            detail = "  ".join(f"{n}:{a}/{c} AC({t}分)" for n, a, t, c in lines)
            self.total_m.config(text=_t(f"汇总: {grand_total}/{grand_groups*sp}   （{grand_ac}/{grand_groups} 组 AC）"))
            self._summary_multi = detail
            rows = "\n".join("  ".join(str(v) for v in self.tree_m.item(i, "values"))
                             for i in self.tree_m.get_children())
            self._add_eval_record("多题", f"汇总 {grand_total}/{grand_groups*sp}（{grand_ac}/{grand_groups} AC）",
                                  detail + "\n" + rows)
        self._ui(finish)

    # ---------- 校验 ----------
    def _validate(self, src, data, gxx, quiet=False, need_gxx=True):
        if not src or not data or (need_gxx and not gxx):
            if not quiet:
                messagebox.showwarning("提示", "请填好源码/数据目录" + ("/编译器" if need_gxx else ""))
            return False
        if not os.path.isfile(src):
            if not quiet:
                messagebox.showwarning("提示", "源码文件不存在: " + src)
            return False
        if not os.path.isdir(data):
            if not quiet:
                messagebox.showwarning("提示", "数据目录不存在: " + data)
            return False
        if need_gxx and not os.path.isfile(gxx):
            if not quiet:
                messagebox.showwarning("提示", "编译器不存在: " + gxx)
            return False
        return True


def main():
    root = tk.Tk()
    JudgeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
