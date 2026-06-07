/* Maison Golf — 語音優先記分流程 */
(function () {
  "use strict";

  const HOLES = 18;
  const DEFAULT_PARS = [4,4,3,5,4,4,3,4,5, 4,3,4,5,4,4,3,4,5];
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const COURSE_CATALOG = window.MG_COURSE_CATALOG || {};

  const el = (id) => document.getElementById(id);
  const esc = (s) => MG.esc(s);
  const FORCE_NEW_ROUND = new URLSearchParams(window.location.search).get("new") === "1";

  if (FORCE_NEW_ROUND) MG.clearVoiceDraft();

  let round = FORCE_NEW_ROUND ? null : (MG.getVoiceDraft() || null);
  let pending = null;
  let recognition = null;
  let recognizing = false;

  function todayParts() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, "0");
    return {
      date: d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()),
      time: p(d.getHours()) + ":" + p(d.getMinutes()),
    };
  }

  function cleanPlayers(raw) {
    return String(raw || "")
      .split(/[、,\n，\s]+/)
      .map((x) => x.trim())
      .filter(Boolean)
      .slice(0, 8);
  }

  function normalizeKey(s) {
    return String(s || "")
      .toLowerCase()
      .replace(/\s+/g, "")
      .replace(/[·・\-.()（）]/g, "");
  }

  function teeAliases(teeId, tee) {
    const raw = [
      teeId,
      tee && tee.name,
      tee && tee.name_en,
    ].filter(Boolean);
    const colorMap = {
      white: ["白", "白梯", "白tee", "white"],
      blue: ["藍", "蓝", "藍梯", "蓝梯", "藍tee", "blue"],
      yellow: ["黃", "黄", "黃梯", "黄梯", "yellow"],
      red: ["紅", "红", "紅梯", "red"],
      black: ["黑", "黑梯", "black"],
      championship: ["錦標", "锦标", "championship"],
      club: ["會員", "会员", "club"],
      forward: ["前梯", "forward"],
      gold: ["金", "金梯", "gold"],
    };
    return raw.concat(colorMap[teeId] || []).map(normalizeKey);
  }

  function courseAliases(courseId, course) {
    const raw = [courseId, course.name, course.name_en, course.location].filter(Boolean);
    if (courseId === "ksc-east") raw.push("滘西洲東場", "滘西洲东场", "東場", "东场", "kau sai chau east", "ksc east");
    if (courseId === "ksc-south") raw.push("滘西洲南場", "滘西洲南场", "南場", "南场", "kau sai chau south", "ksc south");
    if (courseId === "ksc-north") raw.push("滘西洲北場", "滘西洲北场", "北場", "北场", "kau sai chau north", "ksc north");
    if (courseId === "hk-cwbgc") raw.push("清水灣", "清水湾", "clear water bay");
    if (courseId === "hk-fanling-eden") raw.push("粉嶺eden", "粉岭eden", "eden");
    return raw.map(normalizeKey);
  }

  function detectCourseAndTee(text, explicitCourse) {
    const haystack = normalizeKey([text, explicitCourse].filter(Boolean).join(" "));
    let best = null;
    Object.keys(COURSE_CATALOG || {}).forEach((cid) => {
      const course = COURSE_CATALOG[cid];
      courseAliases(cid, course).forEach((alias) => {
        if (!alias || !haystack.includes(alias)) return;
        const score = alias.length;
        if (!best || score > best.score) best = { course_id: cid, course, score };
      });
    });
    if (!best) return null;

    const tees = best.course.tees || {};
    let teeId = null;
    Object.keys(tees).forEach((tid) => {
      const matched = teeAliases(tid, tees[tid]).some((alias) => alias && haystack.includes(alias));
      if (matched) teeId = tid;
    });
    if (!teeId) teeId = tees.white ? "white" : Object.keys(tees)[0];
    const tee = tees[teeId];
    if (!tee || !Array.isArray(tee.pars) || tee.pars.length !== HOLES) return null;
    return {
      course_id: best.course_id,
      course_name: best.course.name,
      tee_id: teeId,
      tee_name: tee.name || tee.name_en || teeId,
      pars: tee.pars.slice(),
      par_total: tee.par_total || tee.pars.reduce((a, b) => a + b, 0),
    };
  }

  function renderCourseMatch(match) {
    const node = el("course-match");
    if (!node) return;
    if (!match) {
      node.textContent = "未匹配到內建球場，會先用 Par 72 預設；你仍可先測語音流程。";
      node.classList.remove("hidden");
      return;
    }
    node.textContent = "已匹配：" + match.course_name + " · " + match.tee_name + " · Par " + match.par_total;
    node.classList.remove("hidden");
  }

  function newRound(course, players, courseMatch) {
    const parts = todayParts();
    const pars = courseMatch ? courseMatch.pars.slice() : DEFAULT_PARS.slice();
    return {
      id: "v_" + parts.date.replace(/-/g, "") + "_" + parts.time.replace(":", "") + "_" + Math.random().toString(36).slice(2, 7),
      input_mode: "voice",
      course_id: courseMatch ? courseMatch.course_id : null,
      tee_id: courseMatch ? courseMatch.tee_id : null,
      tee: courseMatch ? courseMatch.tee_name : "自訂",
      course: (courseMatch && courseMatch.course_name) || course || "自訂球場",
      date: parts.date,
      time: parts.time,
      pars,
      par_total: pars.reduce((a, b) => a + b, 0),
      players: players.map((name) => ({ name, scores: Array(HOLES).fill(0), putts: Array(HOLES).fill(0) })),
      current_hole: 1,
      status: "in_progress",
      voice_holes: [],
      voice_transcripts: [],
      created_at: new Date().toISOString(),
    };
  }

  function saveDraft() {
    MG.saveVoiceDraft(round);
  }

  function showSetup() {
    el("setup-panel").classList.remove("hidden");
    el("round-panel").classList.add("hidden");
    el("finish-panel").classList.add("hidden");
  }

  function showRound() {
    el("setup-panel").classList.add("hidden");
    el("round-panel").classList.remove("hidden");
    el("finish-panel").classList.add("hidden");
    renderRound();
  }

  function playerScoreThrough(player, throughHole) {
    return player.scores.slice(0, throughHole).reduce((a, b) => a + (parseInt(b, 10) || 0), 0);
  }

  function renderRound() {
    if (!round) return showSetup();
    const h = Math.max(1, Math.min(HOLES, round.current_hole || 1));
    el("voice-course").textContent = round.course || "自訂球場";
    el("voice-tee").textContent = (round.tee || "自訂") + " · 本洞 Par " + (round.pars[h - 1] || 4);
    el("voice-hole").textContent = "第 " + h + " 洞";
    el("voice-progress").style.width = ((h / HOLES) * 100) + "%";
    el("voice-player-count").textContent = (round.players || []).length + " 人";
    el("voice-transcript").value = "";
    el("parse-error").classList.add("hidden");
    pending = null;
    renderStandings();
    renderPending();
  }

  function renderStandings() {
    const through = Math.max(0, (round.current_hole || 1) - 1);
    const parThrough = round.pars.slice(0, through).reduce((a, b) => a + b, 0);
    const rows = (round.players || []).map((p) => {
      const total = playerScoreThrough(p, through);
      return { name: p.name, total, toPar: total ? total - parThrough : 0 };
    }).sort((a, b) => {
      if (!a.total && !b.total) return 0;
      if (!a.total) return 1;
      if (!b.total) return -1;
      return a.total - b.total;
    });
    el("voice-standings").innerHTML = rows.map((r, i) => {
      const score = r.total ? r.total : "-";
      const tp = r.total ? MG.toParText(r.toPar) : "";
      return '<div class="flex items-center gap-3 py-2">' +
        '<span class="w-5 text-center text-sm text-zinc-400">' + (i + 1) + '</span>' +
        '<span class="min-w-0 flex-1 truncate text-sm font-medium text-zinc-900">' + esc(r.name) + '</span>' +
        '<span class="w-12 text-right text-lg font-semibold tabular-nums text-zinc-900">' + score + '</span>' +
        '<span class="w-10 text-right text-xs font-medium tabular-nums text-zinc-400">' + tp + '</span>' +
      '</div>';
    }).join("");
  }

  function renderPending() {
    const wrap = el("pending-panel");
    if (!pending || !pending.entries.length) {
      wrap.classList.add("hidden");
      wrap.innerHTML = "";
      return;
    }
    const missing = pending.missing && pending.missing.length
      ? '<p class="mt-2 text-xs text-zinc-500">未讀到：' + pending.missing.map(esc).join("、") + '</p>'
      : "";
    wrap.innerHTML =
      '<div class="rounded-2xl border border-zinc-900 p-4">' +
        '<div class="flex items-center justify-between gap-3">' +
          '<p class="text-sm font-semibold text-zinc-900">解析結果 · 第 ' + pending.hole + ' 洞</p>' +
          '<span class="text-xs text-zinc-400">' + Math.round((pending.confidence || 0) * 100) + "%</span>" +
        '</div>' +
        '<div class="mt-3 divide-y divide-zinc-100">' +
          pending.entries.map((x) => {
            const detail = x.green_shots != null && x.putts != null
              ? x.green_shots + " 上 " + x.putts + " 推"
              : x.score_label ? labelText(x.score_label) : "總桿";
            return '<div class="flex items-center gap-3 py-2">' +
              '<span class="min-w-0 flex-1 truncate text-sm font-medium text-zinc-900">' + esc(x.player) + '</span>' +
              '<span class="text-sm text-zinc-500">' + detail + '</span>' +
              '<span class="w-10 text-right text-xl font-semibold tabular-nums text-zinc-900">' + (x.score || "-") + '</span>' +
            '</div>';
          }).join("") +
        '</div>' +
        missing +
        '<div class="mt-4 grid grid-cols-2 gap-3">' +
          '<button type="button" id="confirm-hole" class="rounded-xl bg-zinc-900 py-3 text-sm font-medium text-white">確認，下一洞</button>' +
          '<button type="button" id="retry-hole" class="rounded-xl border border-zinc-300 py-3 text-sm font-medium text-zinc-700">重說</button>' +
        '</div>' +
      '</div>';
    wrap.classList.remove("hidden");
    el("confirm-hole").addEventListener("click", confirmHole);
    el("retry-hole").addEventListener("click", () => {
      pending = null;
      el("voice-transcript").value = "";
      renderPending();
    });
  }

  function labelText(label) {
    const labels = {
      "hole in one": "一桿進洞",
      "albatross": "信天翁",
      "eagle": "Eagle",
      "birdie": "Birdie",
      "par": "Par",
      "bogey": "Bogey",
      "double bogey": "Double",
    };
    return labels[label] || label || "總桿";
  }

  function resolveSemanticScores(result) {
    if (!round || !result || !Array.isArray(result.entries)) return result;
    const hole = Math.max(1, Math.min(HOLES, result.hole || round.current_hole || 1));
    const par = round.pars[hole - 1] || 4;
    result.entries = result.entries.map((entry) => {
      if (entry.score || entry.score_diff == null) return entry;
      return {
        ...entry,
        score: Math.max(1, par + entry.score_diff),
        par,
      };
    });
    return result;
  }

  function parseCurrentTranscript() {
    if (!round) return;
    const text = el("voice-transcript").value.trim();
    if (!text) {
      showError("先說一句或輸入本洞成績");
      return;
    }
    pending = resolveSemanticScores(MaisonGolfSpeech.parseHoleTranscript(
      text,
      round.players.map((p) => p.name),
      { hole: round.current_hole }
    ));
    if (!pending.ok) {
      showError("暫時讀不到成績。例：小明三上二推，小王二上一推");
      renderPending();
      return;
    }
    el("parse-error").classList.add("hidden");
    renderPending();
  }

  function showError(msg) {
    const node = el("parse-error");
    node.textContent = msg;
    node.classList.remove("hidden");
  }

  function confirmHole() {
    if (!round || !pending || !pending.entries.length) return;
    const hole = Math.max(1, Math.min(HOLES, pending.hole || round.current_hole || 1));
    const idx = hole - 1;
    pending.entries.forEach((entry) => {
      const p = round.players.find((x) => x.name === entry.player);
      if (!p || !entry.score) return;
      p.scores[idx] = entry.score;
      p.putts[idx] = entry.putts || 0;
    });
    const record = {
      hole,
      raw_transcript: pending.raw_transcript,
      entries: pending.entries,
      confirmed: true,
      created_at: new Date().toISOString(),
    };
    round.voice_holes = (round.voice_holes || []).filter((x) => x.hole !== hole);
    round.voice_holes.push(record);
    round.voice_holes.sort((a, b) => a.hole - b.hole);
    round.voice_transcripts = round.voice_holes.map((x) => x.raw_transcript);
    round.current_hole = Math.min(HOLES, hole + 1);
    saveDraft();
    if (hole >= HOLES) {
      showFinish();
    } else {
      showRound();
    }
  }

  function showFinish() {
    el("setup-panel").classList.add("hidden");
    el("round-panel").classList.add("hidden");
    el("finish-panel").classList.remove("hidden");
    const ranked = buildRankedPreview();
    el("finish-list").innerHTML = ranked.map((p, i) => (
      '<div class="flex items-center gap-4 py-3">' +
        '<span class="w-5 text-center text-sm text-zinc-400">' + (i + 1) + '</span>' +
        '<span class="min-w-0 flex-1 truncate font-medium text-zinc-900">' + esc(p.name) + '</span>' +
        '<span class="text-sm text-zinc-400">推 ' + p.putts + '</span>' +
        '<span class="w-12 text-right text-2xl font-semibold tabular-nums text-zinc-900">' + p.total + '</span>' +
      '</div>'
    )).join("");
  }

  function buildRankedPreview() {
    return (round.players || []).map((p) => ({
      name: p.name,
      total: p.scores.reduce((a, b) => a + (parseInt(b, 10) || 0), 0),
      putts: p.putts.reduce((a, b) => a + (parseInt(b, 10) || 0), 0),
    })).sort((a, b) => a.total - b.total);
  }

  function completeRound() {
    if (!round) return;
    const saved = MG.addRound({
      input_mode: "voice",
      voice_recorded_holes: (round.voice_holes || []).length,
      course_id: round.course_id,
      tee_id: round.tee_id,
      tee: round.tee,
      course_name: round.course,
      note: "語音記分",
      date: round.date,
      time: round.time,
      pars: round.pars,
      players: round.players.map((p) => ({ name: p.name, scores: p.scores, putts: p.putts })),
      voice_holes: round.voice_holes || [],
      voice_transcripts: round.voice_transcripts || [],
    });
    MG.clearVoiceDraft();
    window.location.href = "/round/" + encodeURIComponent(saved.id);
  }

  function setupRecognition() {
    if (!SpeechRecognition) {
      el("voice-support").textContent = "此瀏覽器不支援直接語音輸入，可先用文字輸入測試同一套流程。";
      return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = "zh-HK";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onstart = () => {
      recognizing = true;
      el("mic-label").textContent = "聽緊...";
      el("mic-btn").classList.add("ring-4", "ring-zinc-200");
    };
    recognition.onend = () => {
      recognizing = false;
      el("mic-label").textContent = "按一下，說本洞成績";
      el("mic-btn").classList.remove("ring-4", "ring-zinc-200");
    };
    recognition.onerror = () => showError("語音沒有收清楚，可以重說或直接打字");
    recognition.onresult = (event) => {
      const text = Array.from(event.results).map((r) => r[0].transcript).join(" ");
      el("voice-transcript").value = text;
      parseCurrentTranscript();
    };
  }

  function bind() {
    el("start-voice-round").addEventListener("click", () => {
      const setupText = el("setup-speech").value.trim();
      const parsed = MaisonGolfSpeech.parseSetup(setupText);
      const course = (el("course-name").value.trim() || parsed.course || "自訂球場");
      const players = cleanPlayers(el("player-names").value || parsed.players.join("、"));
      const courseMatch = detectCourseAndTee(setupText, course);
      renderCourseMatch(courseMatch);
      if (!players.length) {
        el("setup-error").textContent = "至少輸入一位球友";
        el("setup-error").classList.remove("hidden");
        return;
      }
      round = newRound(course, players, courseMatch);
      saveDraft();
      showRound();
    });

    el("parse-text").addEventListener("click", parseCurrentTranscript);
    el("finish-round").addEventListener("click", showFinish);
    el("save-final-round").addEventListener("click", completeRound);
    el("back-to-round").addEventListener("click", showRound);
    el("abandon-voice").addEventListener("click", () => {
      MG.clearVoiceDraft();
      round = null;
      showSetup();
    });
    el("mic-btn").addEventListener("click", () => {
      if (!recognition) {
        showError("這個瀏覽器不能直接收音，請在下方輸入一句測試");
        return;
      }
      if (recognizing) recognition.stop();
      else recognition.start();
    });
  }

  setupRecognition();
  bind();
  if (round && round.status === "in_progress") showRound();
  else showSetup();
})();
