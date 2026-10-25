/* ============================================================
 * OJJudge 对拍实验室 · 战绩分享卡
 * 对拍完成后，把结果画成一张可下载 / 可复制的图片，
 * 专门用于小红书等社媒传播（带 #WorkBuddy #1024程序员节 话题可加分）。
 * 由 lab.js 在对拍结束时调用 window.OJJudgeShareCard.onBattleDone。
 * ============================================================ */
(function () {
  "use strict";

  var SITE = "https://huake-counter.app.workbuddy.host/";
  var W = 1080, H = 1350;

  /* ---------- 界面语言工具 ---------- */
  function uiLang() {
    return (window.OJJudgeI18n && window.OJJudgeI18n.get()) === "en" ? "en" : "zh";
  }
  function T(zh) {
    if (!zh) return zh;
    if (uiLang() === "zh") return zh;
    if (window.OJJudgeI18n && window.OJJudgeI18n.translate) {
      return window.OJJudgeI18n.translate(zh);
    }
    return zh;
  }

  /* ---- 出品方签名（透明背景 PNG）----
     canvas 画图片必须等图片 load 完，否则画出来是空的。
     所以：页面加载时就预热，onload 里置 ready 并触发一次重绘。 */
  var SIG_SRC = "media/sig-brand-bar.png";
  var sigImg = null, sigReady = false;
  var lastBattle = null, lastPreset = null;

  function preloadSig() {
    if (sigImg) return;
    try {
      var im = new Image();
      im.onload = function () {
        sigReady = true;
        sigImg = im;
        /* 图片可能晚于首次 drawCard 就绪，此时补画一次 */
        if (lastBattle) drawCard(lastBattle, lastPreset);
      };
      im.onerror = function () { sigReady = false; };
      im.src = SIG_SRC;
      sigImg = im;
    } catch (e) { sigImg = null; }
  }

  function el(id) { return document.getElementById(id); }
  function resetCanvas(cv) { cv.width = W; cv.height = H; }

  function roundRect(ctx, x, y, w, h, r) {
    if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); return; }
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function onBattleDone(battle, preset) {
    var host = el("lab-share");
    if (!host) return;
    host.hidden = false;
    host._battle = battle;
    host._preset = preset;
    if (!host.dataset.built) {
      host.dataset.built = "1";
      host.innerHTML =
        '<div class="lab-share-cta">' +
        '  <p class="lab-share-tip">' + T("对拍结果不错？生成一张") + '<strong>' + T("战绩卡") + '</strong>' + T("。") + '</p>' +
        '  <button class="btn btn-primary" id="lab-share-btn">' + T("生成战绩卡") + '</button>' +
        '</div>' +
        '<div class="lab-share-modal" id="lab-share-modal" hidden>' +
        '  <div class="lab-share-modal-in">' +
        '    <div class="lab-share-modal-bar"><b>' + T("对拍战绩卡") + '</b><button class="lab-share-x" id="lab-share-x" aria-label="' + T("关闭") + '">×</button></div>' +
        '    <div class="lab-share-canvas-wrap"><canvas id="lab-share-canvas" width="' + W + '" height="' + H + '"></canvas></div>' +
        '    <div class="lab-share-actions">' +
        '      <button class="btn btn-outline btn-sm" id="lab-share-dl">' + T("下载图片") + '</button>' +
        '      <button class="btn btn-primary btn-sm" id="lab-share-cp">' + T("复制图片") + '</button>' +
        '    </div>' +
        '    <p class="lab-share-note" id="lab-share-note"></p>' +
        '  </div>' +
        '</div>';
      el("lab-share-btn").addEventListener("click", function () { openModal(host); });
      el("lab-share-x").addEventListener("click", closeModal);
      el("lab-share-modal").addEventListener("click", function (e) {
        if (e.target === el("lab-share-modal")) closeModal();
      });
      el("lab-share-dl").addEventListener("click", downloadCard);
      el("lab-share-cp").addEventListener("click", copyCard);
    }
  }

  function openModal(host) {
    drawCard(host._battle, host._preset);
    var m = el("lab-share-modal");
    if (m) m.hidden = false;
    var note = el("lab-share-note");
    if (note) note.textContent = "";
  }
  function closeModal() { var m = el("lab-share-modal"); if (m) m.hidden = true; }

  function drawCard(battle, preset) {
    var cv = el("lab-share-canvas");
    if (!cv) return;
    resetCanvas(cv);
    var ctx = cv.getContext("2d");
    lastBattle = battle; lastPreset = preset;
    preloadSig();

    var N = battle.problems.length;
    var rounds = battle.rounds, consistent = battle.consistent;
    var pass = N === 0;
    var firstRound = N ? battle.problems[0].r : null;
    var bugType = (preset && preset.bug) ? T(preset.bug) : (N ? T("输出不一致") : "—");
    var chName = (preset && preset.name) ? T(preset.name) : T("自定义对拍");
    var accent = pass ? "#34d399" : "#fb7185";

    // 背景
    var bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, "#1b1f3b");
    bg.addColorStop(1, "#241a46");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // 顶部品牌条
    var hg = ctx.createLinearGradient(0, 0, W, 0);
    hg.addColorStop(0, "#6a5df4");
    hg.addColorStop(1, "#4f7df9");
    ctx.fillStyle = hg;
    ctx.fillRect(0, 0, W, 150);
    ctx.fillStyle = "rgba(255,255,255,.92)";
    roundRect(ctx, 40, 45, 60, 60, 12); ctx.fill();
    ctx.fillStyle = "#5b5bd6";
    ctx.font = "700 30px sans-serif";
    ctx.textBaseline = "middle"; ctx.textAlign = "left";
    ctx.fillText("OJ", 51, 76);
    ctx.fillStyle = "#fff";
    ctx.font = "600 34px 'PingFang SC','Microsoft YaHei',sans-serif";
    ctx.fillText(T("OJJudge · 对拍实验室"), 122, 77);

    /* 出品方签名：画在标题右侧，占掉原来 STRESS TEST CARD 的位置
       （签名图本身就是品牌标识，再挂一行英文会挤在一起） */
    var drewSig = false;
    if (sigReady && sigImg && sigImg.width) {
      var sigH = 92, sigW = Math.round(sigImg.width * sigH / sigImg.height);
      try {
        ctx.drawImage(sigImg, W - 40 - sigW, 29, sigW, sigH);
        drewSig = true;
      } catch (e) { /* 图片没准备好就跳过，不影响卡片其余部分 */ }
    }
    if (!drewSig) {
      /* 签名图没加载出来时的兜底：至少别留空白 */
      ctx.fillStyle = "rgba(255,255,255,.7)";
      ctx.font = "600 18px monospace";
      ctx.textAlign = "right";
      ctx.fillText("STRESS TEST CARD", W - 40, 77);
      ctx.textAlign = "left";
    }

    // 结论大字
    ctx.textBaseline = "alphabetic";
    ctx.textAlign = "center";
    if (!pass) {
      ctx.fillStyle = accent;
      ctx.font = "800 230px 'PingFang SC',sans-serif";
      ctx.fillText(String(N), W / 2, 430);
      ctx.fillStyle = "#fff";
      ctx.font = "700 62px 'PingFang SC','Microsoft YaHei',sans-serif";
      ctx.fillText(T("处 BUG 被我揪出"), W / 2, 520);
    } else {
      ctx.fillStyle = accent;
      ctx.font = "800 150px 'PingFang SC',sans-serif";
      ctx.fillText("0 BUG", W / 2, 400);
      ctx.fillStyle = "#fff";
      ctx.font = "700 60px 'PingFang SC','Microsoft YaHei',sans-serif";
      ctx.fillText(T("完美通过 · 全程一致"), W / 2, 500);
    }
    ctx.textAlign = "left";

    // 信息面板
    var panelY = 600, panelH = 380;
    ctx.fillStyle = "rgba(255,255,255,.05)";
    roundRect(ctx, 40, panelY, W - 80, panelH, 18); ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,.08)";
    ctx.lineWidth = 1; ctx.stroke();

    var rows = [
      [T("挑战"), chName],
      [T("第几轮现形"), pass ? T("全程一致") : (T("第 ") + firstRound + T(" 轮"))],
      [T("bug 类型"), bugType],
      [T("一致轮数"), consistent + " / " + rounds + T(" 轮")]
    ];
    var rowH = panelH / rows.length;
    ctx.textBaseline = "middle";
    for (var i = 0; i < rows.length; i++) {
      var y = panelY + rowH * i + rowH / 2;
      ctx.fillStyle = "rgba(255,255,255,.55)";
      ctx.font = "400 30px 'PingFang SC','Microsoft YaHei',sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(rows[i][0], 80, y);
      ctx.fillStyle = "#fff";
      ctx.font = "700 38px 'PingFang SC','Microsoft YaHei',sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(rows[i][1], W - 80, y);
    }
    ctx.textAlign = "left";

    // 现场还原（仅在有问题时）
    if (!pass && battle.problems[0]) {
      var p0 = battle.problems[0];
      /* 输入常是多行（如「n」单独一行 + 数组行），折成一行才看得出是什么数据 */
      var inp = String(p0.input).replace(/\s+/g, " ").trim().slice(0, 46);
      var mo = String(p0.m.ok ? p0.m.out : T("运行异常")).trim().replace(/\s+/g, " ").slice(0, 34);
      var bo = String(p0.b.ok ? p0.b.out : T("运行异常")).trim().replace(/\s+/g, " ").slice(0, 34);
      var ry = 1010, rh = 170;
      ctx.fillStyle = "rgba(255,255,255,.05)";
      roundRect(ctx, 40, ry, W - 80, rh, 14); ctx.fill();
      ctx.fillStyle = accent;
      ctx.font = "600 26px 'PingFang SC','Microsoft YaHei',sans-serif";
      ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";
      ctx.fillText(T("第 ") + firstRound + T(" 轮 · 现场还原"), 70, ry + 42);
      ctx.font = "400 22px monospace";
      ctx.fillStyle = "rgba(255,255,255,.7)";
      ctx.fillText(T("输入  ") + inp, 70, ry + 82);
      ctx.fillStyle = "#fca5a5";
      ctx.fillText(T("主程序  ") + mo, 70, ry + 118);
      ctx.fillStyle = "#86efac";
      ctx.fillText(T("暴力    ") + bo, 70, ry + 150);
      ctx.textAlign = "left";
    }

    // 底部信息条
    var fy = 1210;
    ctx.fillStyle = "rgba(255,255,255,.06)";
    roundRect(ctx, 40, fy, W - 80, 110, 16); ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "600 30px 'PingFang SC','Microsoft YaHei',sans-serif";
    ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";
    ctx.fillText(T("打开网页就能对拍 · 不用装环境"), 80, fy + 46);
    ctx.fillStyle = "#a9b0d6";
    ctx.font = "500 24px monospace";
    ctx.fillText(SITE, 80, fy + 86);
    ctx.textAlign = "left";
  }

  function downloadCard() {
    var cv = el("lab-share-canvas");
    if (!cv) return;
    cv.toBlob(function (blob) {
      if (!blob) return;
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "OJJudge对拍战绩.png";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1500);
      var note = el("lab-share-note");
      if (note) note.textContent = T("已下载图片，去小红书发笔记时配上即可～");
    }, "image/png");
  }

  function copyCard() {
    var cv = el("lab-share-canvas");
    if (!cv) return;
    if (!navigator.clipboard || !window.ClipboardItem) {
      downloadCard();
      var n1 = el("lab-share-note");
      if (n1) n1.textContent = T("当前浏览器不支持复制图片，已改为下载。");
      return;
    }
    cv.toBlob(function (blob) {
      if (!blob) { downloadCard(); return; }
      try {
        navigator.clipboard.write([new window.ClipboardItem({ "image/png": blob })])
          .then(function () {
            var note = el("lab-share-note");
            if (note) note.textContent = T("已复制到剪贴板，直接去小红书粘贴～");
          })
          .catch(function () { downloadCard(); });
      } catch (e) { downloadCard(); }
    }, "image/png");
  }

  if (typeof window !== "undefined") {
    window.OJJudgeShareCard = { onBattleDone: onBattleDone };
  }
})();
