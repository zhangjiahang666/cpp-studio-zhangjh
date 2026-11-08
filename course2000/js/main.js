/* Course2000 简介站 · 共享脚本（模仿 OJJudge 站点交互） */
(function () {
  "use strict";

  /* ---------- 导航当前页高亮 ---------- */
  var path = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".site-nav a").forEach(function (a) {
    if (a.getAttribute("href") === path) a.classList.add("active");
  });

  /* ---------- 移动端菜单 ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".site-nav");
  if (toggle && links) {
    toggle.addEventListener("click", function () { links.classList.toggle("open"); });
  }

  /* ---------- 复制工具 ---------- */
  function copyText(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(); });
    } else fallback();
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.cssText = "position:fixed;opacity:0;top:0;left:0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(ta);
    }
  }

  /* ---------- 完整哈希复制（hero-meta / 下载区 copy-hint） ---------- */
  document.querySelectorAll(".copy-hint[data-copy]").forEach(function (el) {
    el.addEventListener("click", function () {
      var t = el.getAttribute("data-copy");
      var old = el.textContent;
      copyText(t, function () {
        el.textContent = "已复制 ✓";
        setTimeout(function () { el.textContent = old; }, 1800);
      });
    });
  });

  /* ---------- 哈希块一键复制 ---------- */
  document.querySelectorAll("[data-copy-text]").forEach(function (el) {
    el.style.cursor = "pointer";
    el.title = "点击复制";
    el.addEventListener("click", function () {
      copyText(el.getAttribute("data-copy-text"), function () {
        var b = el.querySelector("b");
        var old = b ? b.textContent : el.textContent;
        if (b) b.textContent = "已复制 ✓";
        setTimeout(function () { if (b) b.textContent = old; }, 1800);
      });
    });
  });

  /* ---------- 代码复制按钮 ---------- */
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    if (btn.classList.contains("copy-hint")) return; // 上面已处理
    btn.addEventListener("click", function () {
      var target = document.querySelector(btn.getAttribute("data-copy"));
      if (!target) return;
      var old = btn.textContent;
      copyText(target.textContent, function () {
        btn.textContent = "已复制 ✓";
        btn.classList.add("copied");
        setTimeout(function () { btn.textContent = old; btn.classList.remove("copied"); }, 1800);
      });
    });
  });

  /* ---------- 年份注入 ---------- */
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();

  /* ---------- Python 语法高亮（零依赖 token 化） ---------- */
  var KEYWORDS = ("False None True and as assert async await break class continue def del elif " +
    "else except finally for from global if import in is lambda nonlocal not or pass raise " +
    "return try while with yield match case");
  var KW = {};
  KEYWORDS.split(" ").forEach(function (k) { KW[k] = 1; });

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function highlightPy(code) {
    var re = /("""[\s\S]*?"""|'''[\s\S]*?''')|(#[^\n]*)|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')|(\b\d+(?:\.\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)/g;
    var out = "", last = 0, m;
    while ((m = re.exec(code)) !== null) {
      out += esc(code.slice(last, m.index));
      last = re.lastIndex;
      if (m[1]) out += '<span class="tok-str">' + esc(m[1]) + "</span>";
      else if (m[2]) out += '<span class="tok-com">' + esc(m[2]) + "</span>";
      else if (m[3]) out += '<span class="tok-str">' + esc(m[3]) + "</span>";
      else if (m[4]) out += '<span class="tok-num">' + esc(m[4]) + "</span>";
      else {
        var w = m[5];
        if (KW[w]) out += '<span class="tok-kw">' + w + "</span>";
        else if (w === "self") out += '<span class="tok-self">' + w + "</span>";
        else {
          var before = code.slice(0, m.index);
          if (/(^|[^A-Za-z0-9_])(def|class)\s+$/.test(before)) out += '<span class="tok-def">' + w + "</span>";
          else out += w;
        }
      }
    }
    out += esc(code.slice(last));
    return out;
  }

  document.querySelectorAll('pre[data-lang="python"]').forEach(function (pre) {
    var raw = pre.textContent;
    var lines = raw.replace(/\n$/, "").split("\n");
    pre.innerHTML = lines.map(function (ln, i) {
      return '<span class="ln">' + String(i + 1).padStart(4, " ") + "  </span>" + highlightPy(ln);
    }).join("\n");
  });
})();
