/* Course2000 · 检查更新
   浏览器：拉 GitHub raw 的 version.json，版本更高则弹 HTML 模态框
   exe 内：自动改走原生 WinForms 弹窗（宿主对象桥），避免出现两套提示 */
(function () {
  "use strict";

  var CURRENT_VERSION = "1.1.0";
  var VERSION_URLS = [
    "https://raw.githubusercontent.com/zhangjiahang666/cpp-studio-zhangjh/main/course2000/version.json",
    "https://zhangjiahang666.github.io/cpp-studio-zhangjh/course2000/version.json",
    "https://cdn.jsdelivr.net/gh/zhangjiahang666/cpp-studio-zhangjh@main/course2000/version.json"
  ];
  var TIMEOUT_MS = 5000;
  var AUTO_DELAY_MS = 3000;

  /* ---------- 自带样式：保证本脚本可独立放进任意页面 ---------- */
  var STYLE_ID = "course2000-update-style";
  if (!document.getElementById(STYLE_ID)) {
    var css = document.createElement("style");
    css.id = STYLE_ID;
    css.textContent =
      ".upd-mask{position:fixed;inset:0;z-index:9999;background:rgba(20,26,48,.45);display:flex;align-items:center;justify-content:center;padding:24px;animation:upd-fade .18s ease-out}" +
      "@keyframes upd-fade{from{opacity:0}to{opacity:1}}" +
      ".upd-card{width:100%;max-width:460px;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 18px 48px rgba(20,26,48,.28);animation:upd-pop .2s ease-out}" +
      "@keyframes upd-pop{from{transform:translateY(10px) scale(.98);opacity:0}to{transform:none;opacity:1}}" +
      ".upd-head{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#eaf1ff;color:#2f6bd6;font-size:15px;font-weight:500}" +
      ".upd-close{border:0;background:transparent;cursor:pointer;color:#7a7e93;font-size:13px;line-height:1;padding:4px 6px;border-radius:6px}" +
      ".upd-close:hover{background:rgba(74,125,255,.12);color:#2f6bd6}" +
      ".upd-body{display:flex;gap:14px;padding:20px 18px 14px}" +
      ".upd-ic{flex:none;width:38px;height:38px;border-radius:50%;background:#4A7DFF;color:#fff;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:500;font-family:Georgia,serif}" +
      ".upd-txt{min-width:0}" +
      ".upd-title{color:#4A7DFF;font-size:17px;font-weight:500;margin-bottom:6px}" +
      ".upd-line{color:#4b4f63;font-size:14px;line-height:1.7}" +
      ".upd-foot{display:flex;flex-wrap:wrap;gap:8px;padding:6px 18px 20px}" +
      ".upd-btn{display:inline-flex;align-items:center;justify-content:center;padding:9px 18px;border-radius:9px;border:1px solid #e4e5ee;background:#fff;color:#4b4f63;font-size:14px;cursor:pointer;text-decoration:none;font-family:inherit}" +
      ".upd-btn:hover{background:#f5f6fb;text-decoration:none}" +
      ".upd-btn.primary{background:#4A7DFF;border-color:#4A7DFF;color:#fff;box-shadow:0 4px 14px rgba(74,125,255,.3)}" +
      ".upd-btn.primary:hover{background:#2f6bd6}" +
      ".upd-toast{position:fixed;left:50%;bottom:34px;transform:translate(-50%,12px);z-index:10000;padding:11px 20px;border-radius:10px;background:#1f2233;color:#fff;font-size:14px;opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}" +
      ".upd-toast.show{opacity:1;transform:translate(-50%,0)}";
    document.head.appendChild(css);
  }

  /* ---------- 版本号：逐段比较，容忍 v 前缀与多余后缀 ---------- */
  function parse(v) {
    var m = String(v == null ? "" : v).trim().replace(/^v/i, "").match(/(\d+)(?:\.(\d+))?(?:\.(\d+))?/);
    if (!m) return null;
    return [parseInt(m[1] || 0, 10), parseInt(m[2] || 0, 10), parseInt(m[3] || 0, 10)];
  }

  function isNewer(latest, current) {
    var a = parse(latest), b = parse(current);
    if (!a || !b) return false;
    for (var i = 0; i < 3; i++) {
      if (a[i] > b[i]) return true;
      if (a[i] < b[i]) return false;
    }
    return false;
  }

  /* ---------- 拉取版本信息（多源依次兜底，全程超时可控） ---------- */
  function fetchWithTimeout(url, timeoutMs) {
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = null;
    var opts = { cache: "no-store" };
    if (ctrl) {
      opts.signal = ctrl.signal;
      timer = setTimeout(function () { ctrl.abort(); }, timeoutMs);
    }
    return fetch(url, opts).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (j) {
      if (timer) clearTimeout(timer);
      return j;
    }, function (e) {
      if (timer) clearTimeout(timer);
      throw e;
    });
  }

  function loadVersion(timeoutMs) {
    var i = 0;
    function next() {
      if (i >= VERSION_URLS.length) return Promise.reject(new Error("no version source reachable"));
      var url = VERSION_URLS[i++];
      return fetchWithTimeout(url, timeoutMs).catch(next);
    }
    return next();
  }

  /* ---------- exe 内宿主对象桥 ---------- */
  function nativeHost() {
    try {
      var cv = window.chrome && window.chrome.webview;
      if (cv && cv.hostObjects && cv.hostObjects.courseHost) return cv.hostObjects.courseHost;
    } catch (e) { /* 非 exe 环境，忽略 */ }
    return null;
  }

  /* ---------- 轻提示 ---------- */
  var toastTimer = null;
  function toast(msg) {
    var el = document.getElementById("upd-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "upd-toast";
      el.className = "upd-toast";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add("show");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove("show"); }, 2600);
  }

  /* ---------- 更新提示模态框（复刻桌面端弹窗布局） ---------- */
  function showModal(info) {
    if (document.getElementById("upd-mask")) return;
    var dl = (info.downloads && info.downloads.length) ? info.downloads : [{ label: "进入官网", url: info.homepage }];
    var btns = dl.map(function (d, i) {
      return '<a class="upd-btn primary" href="' + String(d.url).replace(/"/g, "&quot;") + '"' +
        (i === 0 ? "" : ' style="margin-left:8px"') + '>' + escapeHtml(d.label || "进入官网") + "</a>";
    }).join("");

    var mask = document.createElement("div");
    mask.id = "upd-mask";
    mask.className = "upd-mask";
    mask.innerHTML =
      '<div class="upd-card" role="dialog" aria-modal="true" aria-label="发现新版本">' +
        '<div class="upd-head">发现新版本<button class="upd-close" type="button" aria-label="关闭">&#10005;</button></div>' +
        '<div class="upd-body">' +
          '<div class="upd-ic">i</div>' +
          '<div class="upd-txt">' +
            '<div class="upd-title">Course2000 v' + escapeHtml(info.version) + " 已发布！</div>" +
            '<div class="upd-line">当前版本：v' + CURRENT_VERSION + "</div>" +
            (info.notes ? '<div class="upd-line">更新内容：' + escapeHtml(info.notes) + "</div>" : "") +
            '<div class="upd-line">点击下方按钮前往官网获取更新：</div>' +
          "</div>" +
        "</div>" +
        '<div class="upd-foot">' + btns +
          '<button class="upd-btn" type="button" data-upd-dismiss>稍后再说</button>' +
        "</div>" +
      "</div>";
    document.body.appendChild(mask);

    function close() {
      if (mask.parentNode) mask.parentNode.removeChild(mask);
    }
    mask.querySelector(".upd-close").addEventListener("click", close);
    mask.querySelector("[data-upd-dismiss]").addEventListener("click", close);
    mask.addEventListener("click", function (e) { if (e.target === mask) close(); });
    document.addEventListener("keydown", function onKey(e) {
      if (e.key === "Escape") { close(); document.removeEventListener("keydown", onKey); }
    });
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  /* ---------- 对外入口 ---------- */
  function check(manual) {
    var host = nativeHost();
    if (host) {
      // exe 内：交给原生弹窗处理（原生侧自带版本号、超时与失败提示）
      try {
        var r = host.CheckForUpdates();
        if (r && typeof r.then === "function") r.then(function () {}, function () {});
        return;
      } catch (e) { /* 桥不可用则退回网页实现 */ }
    }
    loadVersion(TIMEOUT_MS).then(function (info) {
      if (isNewer(info.version, CURRENT_VERSION)) showModal(info);
      else if (manual) toast("当前已是最新版本 v" + CURRENT_VERSION);
    }).catch(function () {
      if (manual) toast("检查失败：无法连接网络");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    // 手动入口
    document.querySelectorAll("[data-update-check]").forEach(function (el) {
      el.addEventListener("click", function (e) {
        e.preventDefault();
        check(true);
      });
    });
    // 启动自动检查（exe 内由原生侧负责，避免重复弹窗）
    if (!nativeHost()) {
      setTimeout(function () { check(false); }, AUTO_DELAY_MS);
    }
  });

  window.Course2000Update = { check: check, currentVersion: function () { return CURRENT_VERSION; } };
})();
