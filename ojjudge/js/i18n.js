/* ============================================================
 * OJJudge 官网 · 界面语言切换（中文 / English）
 *
 * 做法：短语级词典 + DOM 文本节点替换。
 *   · 词典 key 是中文原文，value 是英文译文（js/i18n-dict.js）
 *   · 遍历所有文本节点：
 *       1) 整节点精确匹配（优先，最稳）
 *       2) 匹配不到时，按词典 key 长度降序做子串替换
 *          （HTML 里 <b>/<code>/<a> 常把一句话切碎，子串替换能逐段命中）
 *       3) 短词（< 4 字符）只在整节点精确匹配时生效，避免长句里误伤
 *   · 每个节点的原始中文用 WeakMap 记住，切回中文时精确还原
 *
 * 切换后状态存 localStorage，刷新保持；也支持 ?lang=en / ?lang=zh。
 * 快捷键：Alt+L
 * ============================================================ */
(function () {
  "use strict";

  var DICT = Object.assign({}, window.OJJudgeI18N_DICT || {},
                           window.OJJudgeI18N_DICT_EXTRA || {});
  var STORAGE_KEY = "ojjudge_ui_lang";
  var cur = "zh";
  var hasCJK = /[\u3400-\u9fff]/;

  /* ---------- 词典查询 ---------- */

  function exact(s) {
    var t = DICT[s];
    return (typeof t === "string" && t) ? t : null;
  }

  // 子串替换用的有序词表（按长度降序，长词优先）
  var subsCache = null;
  function substrPairs() {
    if (subsCache) return subsCache;
    var keys = Object.keys(DICT);
    var pairs = [];
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (k.length < 4) continue;                 // 短词不参与子串替换
      var v = DICT[k];
      if (typeof v !== "string" || !v) continue;
      pairs.push([k, v]);
    }
    pairs.sort(function (a, b) { return b[0].length - a[0].length; });
    subsCache = pairs;
    return pairs;
  }

  // 对一段文本做翻译（整段精确 -> 子串兜底）
  function translateString(s) {
    if (!s) return s;
    var t = exact(String(s).trim());
    if (t) return t;
    var pairs = substrPairs();
    var out = String(s);
    for (var i = 0; i < pairs.length; i++) {
      if (out.indexOf(pairs[i][0]) >= 0) {
        out = out.split(pairs[i][0]).join(pairs[i][1]);
      }
    }
    return out;
  }

  /* ---------- 文本节点翻译 ---------- */

  // 记录每个文本节点/属性的原始中文，切回中文时精确还原
  var ORIG = new WeakMap();
  var attrOrig = new WeakMap();

  // 把中文原文翻成英文；原文已是英文时原样返回
  function toEn(orig) {
    // 1) 整段精确匹配（保留首尾空白）
    var t = exact(orig.trim());
    if (t) {
      var lead = orig.match(/^\s*/)[0];
      var tail = orig.match(/\s*$/)[0];
      return lead + t + tail;
    }
    // 2) 子串替换（始终基于原始中文，重复切换不累积误差）
    var pairs = substrPairs();
    var out = orig;
    for (var i = 0; i < pairs.length; i++) {
      if (out.indexOf(pairs[i][0]) >= 0) {
        out = out.split(pairs[i][0]).join(pairs[i][1]);
      }
    }
    return out;
  }

  function translateTextNode(node, dir) {
    var raw = node.nodeValue;
    var orig = ORIG.get(node);
    if (orig === undefined) {
      // 从未登记：非中文节点直接跳过；中文节点登记原文
      if (!raw || !hasCJK.test(raw)) return;
      orig = raw;
      ORIG.set(node, orig);
    }
    // 已登记（可能当前是英文）：按方向写回
    var next = (dir === "en") ? toEn(orig) : orig;
    if (next !== node.nodeValue) node.nodeValue = next;
  }

  /* ---------- 属性翻译 ---------- */

  var ATTR_LIST = ["title", "aria-label", "placeholder", "alt", "content"];

  function translateAttrs(el, dir) {
    var store = attrOrig.get(el);
    if (!store) { store = {}; attrOrig.set(el, store); }
    for (var i = 0; i < ATTR_LIST.length; i++) {
      var name = ATTR_LIST[i];
      var orig = store[name];
      if (orig === undefined) {
        var val0 = el.getAttribute(name);
        if (!val0 || !hasCJK.test(val0)) continue;   // 非中文属性不登记
        orig = val0;
        store[name] = orig;
      }
      var val = el.getAttribute(name);
      var next = (dir === "en") ? toEn(orig) : orig;
      if (next !== val) el.setAttribute(name, next);
    }
  }

  /* ---------- 全站遍历 ---------- */

  function walk(root, dir) {
    if (!root) return;
    var all = root.querySelectorAll("*");
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      var tag = el.tagName;
      if (tag === "SCRIPT" || tag === "STYLE" || tag === "TEXTAREA") continue;
      if (tag === "CODE" && el.closest("pre")) continue;   // 代码块内容不翻
      translateAttrs(el, dir);
      var kids = el.childNodes;
      for (var j = 0; j < kids.length; j++) {
        var n = kids[j];
        if (n.nodeType === 3) translateTextNode(n, dir);
      }
    }
  }

  /* ---------- 切换按钮 ---------- */

  function setToggleText() {
    var btn = document.getElementById("oj-lang-toggle");
    if (!btn) return;
    var en = cur === "zh";
    btn.textContent = en ? "EN" : "中文";
    var tip = en ? "Switch to English" : "切换到中文";
    btn.setAttribute("title", tip);
    btn.setAttribute("aria-label", tip);
    btn.setAttribute("data-lang", cur);
  }

  function persist() {
    try { localStorage.setItem(STORAGE_KEY, cur); } catch (e) { /* ignore */ }
  }

  function readStored() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      return (v === "en" || v === "zh") ? v : null;
    } catch (e) { return null; }
  }

  /* ---------- 对外 API ---------- */

  function apply(lang) {
    cur = (lang === "en") ? "en" : "zh";
    document.documentElement.setAttribute("lang", cur === "en" ? "en" : "zh-CN");
    document.documentElement.classList.toggle("lang-en", cur === "en");
    walk(document.head, cur);     // <title> 与 meta 描述（标签页标题随之切换）
    walk(document.body, cur);
    setToggleText();
    // 通知其它脚本（lab.js 的动态文案）
    document.dispatchEvent(new CustomEvent("oj:langchange", { detail: { lang: cur } }));
  }

  function toggle() {
    apply(cur === "zh" ? "en" : "zh");
    persist();
  }

  function init() {
    // URL 参数优先（分享链接可带语言），其次 localStorage
    var m = /[?&]lang=(zh|en)/.exec(location.search || "");
    var lang = m ? m[1] : readStored();
    apply(lang || "zh");

    var btn = document.getElementById("oj-lang-toggle");
    if (btn) btn.addEventListener("click", toggle);

    // 快捷键 Alt+L
    document.addEventListener("keydown", function (e) {
      if (e.altKey && (e.key === "l" || e.key === "L")) {
        e.preventDefault();
        toggle();
      }
    });
  }

  if (typeof window !== "undefined") {
    window.OJJudgeI18n = {
      apply: apply,
      toggle: toggle,
      get: function () { return cur; },
      translate: translateString,
      // 供动态内容使用：翻译一段 HTML 片段里的所有中文
      translateHtml: function (html) {
        if (!html || !hasCJK.test(html)) return html;
        var pairs = substrPairs();
        var out = String(html);
        for (var i = 0; i < pairs.length; i++) {
          if (out.indexOf(pairs[i][0]) >= 0) {
            out = out.split(pairs[i][0]).join(pairs[i][1]);
          }
        }
        return out;
      }
    };
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})();
