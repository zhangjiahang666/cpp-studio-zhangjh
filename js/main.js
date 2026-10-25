/* =========================================================
 * cpp-studio-zhangjh · 全站共享交互
 * 新增页面时，把各页面独有的逻辑放进 initPageXxx()，
 * 并在末尾按页面特征调用即可。
 * ========================================================= */
(function () {
  "use strict";

  /* ---------- 1. 主题切换（浅 / 深，localStorage 记忆） ---------- */
  function initTheme() {
    var root = document.documentElement;
    var saved = null;
    try { saved = localStorage.getItem("theme"); } catch (e) { /* 隐私模式忽略 */ }
    var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.setAttribute("data-theme", saved || (prefersDark ? "dark" : "light"));

    var toggle = document.getElementById("theme-toggle");
    if (!toggle) return;
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) { /* 忽略 */ }
    });
  }

  /* ---------- 2. 移动端汉堡菜单 ---------- */
  function initNavToggle() {
    var toggle = document.getElementById("nav-toggle");
    var menu = document.getElementById("nav-menu");
    if (!toggle || !menu) return;

    function closeMenu() {
      menu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "打开菜单");
    }

    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "关闭菜单" : "打开菜单");
    });

    // 点击菜单项后自动收起
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) closeMenu();
    });

    // 点击页面其他区域收起
    document.addEventListener("click", function (e) {
      if (!e.target.closest("nav") && !e.target.closest("#nav-toggle")) closeMenu();
    });
  }

  /* ---------- 3. 导航滚动态 + 当前栏目高亮 ---------- */
  function initHeaderScroll() {
    var header = document.getElementById("site-header");
    if (!header) return;
    var onScroll = function () {
      header.classList.toggle("scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  function initScrollSpy() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".nav-link[href^='#']"));
    if (!links.length) return;
    var map = {};
    var sections = [];
    links.forEach(function (link) {
      var id = link.getAttribute("href").slice(1);
      var el = document.getElementById(id);
      if (el) { map[id] = link; sections.push(el); }
    });
    if (!sections.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          links.forEach(function (l) { l.classList.remove("active"); });
          var link = map[entry.target.id];
          if (link) link.classList.add("active");
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px", threshold: 0 });

    sections.forEach(function (el) { observer.observe(el); });
  }

  /* ---------- 4. Hero 打字机 ---------- */
  function initTypewriter() {
    var el = document.getElementById("typewriter");
    if (!el) return;
    var phrases = [
      "从语言基础到现代 C++",
      "用代码理解，用项目练手",
      "把学过的东西沉淀下来"
    ];
    var pi = 0, ci = 0, deleting = false;

    function tick() {
      var text = phrases[pi];
      ci += deleting ? -1 : 1;
      el.textContent = text.slice(0, ci);

      var delay = deleting ? 45 : 110;
      if (!deleting && ci === text.length) { delay = 1800; deleting = true; }
      else if (deleting && ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; delay = 350; }
      setTimeout(tick, delay);
    }
    tick();
  }

  /* ---------- 5. 滚动显现动画 ---------- */
  function initReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) { observer.observe(el); });
  }

  /* ---------- 6. 统计数字滚动 ---------- */
  function initCountUp() {
    var nums = document.querySelectorAll(".stat-num[data-count]");
    if (!nums.length) return;

    function format(n) {
      return n >= 1000 ? n.toLocaleString("en-US") : String(n);
    }

    function animate(el) {
      var target = parseInt(el.getAttribute("data-count"), 10) || 0;
      var duration = 1200;
      var start = null;
      function step(ts) {
        if (!start) start = ts;
        var p = Math.min((ts - start) / duration, 1);
        // easeOutCubic
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = format(Math.round(target * eased));
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animate(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    nums.forEach(function (el) { observer.observe(el); });
  }

  /* ---------- 7. 返回顶部 ---------- */
  function initBackToTop() {
    var btn = document.getElementById("back-to-top");
    if (!btn) return;
    var onScroll = function () {
      btn.classList.toggle("show", window.scrollY > 600);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- 8. 页脚年份 ---------- */
  function initYear() {
    var el = document.getElementById("year");
    if (el) el.textContent = String(new Date().getFullYear());
  }

  /* ---------- 启动 ---------- */
  function init() {
    initTheme();
    initNavToggle();
    initHeaderScroll();
    initScrollSpy();
    initTypewriter();
    initReveal();
    initCountUp();
    initBackToTop();
    initYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
