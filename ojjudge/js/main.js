// OJJudge 官网 · 公共脚本
(function () {
  "use strict";

  // 移动端导航展开/收起
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", nav.classList.contains("open") ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") nav.classList.remove("open");
    });
  }

  // 当前页高亮：按文件名匹配
  var page = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  if (page === "") page = "index.html";
  document.querySelectorAll(".site-nav a").forEach(function (a) {
    var href = (a.getAttribute("href") || "").split("#")[0];
    if (href === page || (page === "index.html" && href === "index.html")) {
      a.classList.add("active");
    }
  });

  // 复制 SHA256
  document.querySelectorAll("[data-copy]").forEach(function (el) {
    el.addEventListener("click", function () {
      var text = el.getAttribute("data-copy") || "";
      function done() {
        var old = el.textContent;
        el.textContent = "已复制";
        setTimeout(function () { el.textContent = old; }, 1600);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(); });
      } else {
        fallback();
      }
      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) { /* ignore */ }
        document.body.removeChild(ta);
      }
    });
  });

  // 页脚年份
  var yr = document.getElementById("year");
  if (yr) yr.textContent = new Date().getFullYear();
})();
