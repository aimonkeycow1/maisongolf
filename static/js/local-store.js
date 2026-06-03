/* =========================================================================
   Maison Golf — 本地儲存資料層（零登入 / localStorage-first）
   唯一資料來源是瀏覽器 localStorage。各頁共用此模組讀寫場次與草稿，
   並負責逐洞統計計算與單色樣式 helper。
   ========================================================================= */
(function (global) {
  "use strict";

  var KEY_ROUNDS = "mg_rounds";
  var KEY_DRAFT = "mg_draft";
  var KEY_NAME = "mg_pname";
  var HOLES = 18;

  function read(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }
  function write(key, val) {
    try {
      localStorage.setItem(key, JSON.stringify(val));
      return true;
    } catch (e) {
      return false;
    }
  }

  function genId() {
    var d = new Date();
    var p = (n) => String(n).padStart(2, "0");
    var stamp = "" + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) +
      "_" + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
    return "r_" + stamp + "_" + Math.random().toString(36).slice(2, 7);
  }

  function todayParts() {
    var d = new Date();
    var p = (n) => String(n).padStart(2, "0");
    return {
      date: d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()),
      time: p(d.getHours()) + ":" + p(d.getMinutes()),
    };
  }

  /* ───────── 名稱記憶（取代登入帳號） ───────── */
  function getName() { return read(KEY_NAME, "") || ""; }
  function setName(name) { if (name && name.trim()) write(KEY_NAME, name.trim()); }

  /* ───────── 草稿 ───────── */
  function getDraft() { return read(KEY_DRAFT, null); }
  function saveDraft(draft) {
    if (!draft) return clearDraft();
    draft.updated_at = new Date().toISOString();
    return write(KEY_DRAFT, draft);
  }
  function clearDraft() {
    try { localStorage.removeItem(KEY_DRAFT); } catch (e) {}
  }

  /* ───────── 場次 CRUD ───────── */
  function allRounds() {
    var list = read(KEY_ROUNDS, []);
    return Array.isArray(list) ? list : [];
  }
  function getRound(id) {
    return allRounds().filter((r) => r && r.id === id)[0] || null;
  }
  function addRound(input) {
    var parts = todayParts();
    var pars = (input.pars || []).slice(0, HOLES);
    var round = {
      id: genId(),
      course: input.course_name || input.course || "自訂球場",
      date: input.date || parts.date,
      time: input.time || parts.time,
      note: input.note || "",
      par_total: pars.reduce((a, b) => a + (parseInt(b, 10) || 0), 0),
      pars: pars,
      players: (input.players || []).map((p) => ({
        name: (p.name || "").trim() || "球友",
        scores: (p.scores || []).slice(0, HOLES).map((s) => parseInt(s, 10) || 0),
        putts: (p.putts || []).slice(0, HOLES).map((s) => parseInt(s, 10) || 0),
      })),
      created_at: new Date().toISOString(),
    };
    var list = allRounds();
    list.push(round);
    write(KEY_ROUNDS, list);
    return round;
  }
  function deleteRound(id) {
    write(KEY_ROUNDS, allRounds().filter((r) => r && r.id !== id));
  }
  function clearAll() {
    try {
      localStorage.removeItem(KEY_ROUNDS);
      localStorage.removeItem(KEY_DRAFT);
    } catch (e) {}
  }

  /* ───────── 統計計算 ───────── */
  // 回傳依總桿排序、含完整統計的球員列；以及 par_total。
  function rankedPlayers(round) {
    var pars = round.pars || [];
    var parTotal = round.par_total || pars.reduce((a, b) => a + (b || 0), 0);
    var rows = (round.players || []).map(function (p) {
      var scores = p.scores || [];
      var front9 = 0, back9 = 0, total = 0;
      var birdies = 0, parsCount = 0, bogeys = 0, doublePlus = 0;
      var holeResults = [];
      for (var i = 0; i < HOLES; i++) {
        var sc = parseInt(scores[i], 10) || 0;
        var par = parseInt(pars[i], 10) || 0;
        var diff = sc - par;
        total += sc;
        if (i < 9) front9 += sc; else back9 += sc;
        if (sc > 0) {
          if (diff <= -1) birdies++;
          else if (diff === 0) parsCount++;
          else if (diff === 1) bogeys++;
          else doublePlus++;
        }
        holeResults.push({ hole: i + 1, par: par, score: sc, diff: diff });
      }
      return {
        name: p.name, scores: scores, putts: p.putts || [],
        front9: front9, back9: back9, total: total, to_par: total - parTotal,
        birdies: birdies, pars: parsCount, bogeys: bogeys, double_plus: doublePlus,
        hole_results: holeResults,
      };
    });
    rows.sort((a, b) => a.total - b.total);
    return rows;
  }

  /* ───────── 顯示 helper（與 _macros 單色規則一致） ───────── */
  function scoreCellClass(diff) {
    if (diff <= -1) return "bg-zinc-900 text-white";
    if (diff === 0) return "bg-zinc-100 text-zinc-900";
    return "bg-white text-zinc-400 ring-1 ring-zinc-200";
  }
  function toParText(n) { return n > 0 ? "+" + n : (n === 0 ? "E" : String(n)); }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  global.MG = {
    HOLES: HOLES,
    getName: getName, setName: setName,
    getDraft: getDraft, saveDraft: saveDraft, clearDraft: clearDraft,
    allRounds: allRounds, getRound: getRound, addRound: addRound,
    deleteRound: deleteRound, clearAll: clearAll,
    rankedPlayers: rankedPlayers,
    scoreCellClass: scoreCellClass, toParText: toParText, esc: esc,
  };
})(window);
