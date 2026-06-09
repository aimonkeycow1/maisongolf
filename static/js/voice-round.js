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
  let setupRecognizer = null;
  let recognizing = false;
  let mediaRecorder = null;
  let audioChunks = [];
  let recording = false;
  let recordingPurpose = "";
  let recordingTimer = null;
  let fallbackNoticeShown = false;
  let aiTranscribeAvailable = false;

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

  function newRound(course, players, courseMatch, setupInfo) {
    const parts = todayParts();
    const info = setupInfo || {};
    const pars = courseMatch ? courseMatch.pars.slice() : DEFAULT_PARS.slice();
    return {
      id: "v_" + (info.date || parts.date).replace(/-/g, "") + "_" + (info.time || parts.time).replace(":", "") + "_" + Math.random().toString(36).slice(2, 7),
      input_mode: "voice",
      course_id: courseMatch ? courseMatch.course_id : null,
      tee_id: courseMatch ? courseMatch.tee_id : null,
      tee: courseMatch ? courseMatch.tee_name : "自訂",
      course: (courseMatch && courseMatch.course_name) || course || "自訂球場",
      date: info.date || parts.date,
      time: info.time || parts.time,
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
    const parts = todayParts();
    if (!el("round-date").value) el("round-date").value = parts.date;
    if (!el("round-time").value) el("round-time").value = parts.time;
  }

  function selectedSpeechLang() {
    const picker = el("speech-lang");
    return picker && picker.value ? picker.value : "zh-HK";
  }

  function openAiLanguage() {
    return selectedSpeechLang().toLowerCase().startsWith("en") ? "en" : "zh";
  }

  function setupPromptText() {
    if (selectedSpeechLang().toLowerCase().startsWith("en")) {
      return "Say: today 2 pm play Kau Sai Chau East, white tee, with John and Peter";
    }
    return "請說：今天下午兩點打滘西洲東場，白梯，球友有小舒、小王、小陳";
  }

  function renderEngineStatus() {
    const node = el("voice-engine-status");
    if (!node) return;
    const langLabel = {
      "zh-HK": "廣東話 / 香港中文",
      "zh-CN": "普通話 / 簡體中文",
      "zh-TW": "台灣中文",
      "en-US": "English",
    }[selectedSpeechLang()] || selectedSpeechLang();
    const engine = (aiTranscribeAvailable ? "AI 語音" : "瀏覽器語音") + " · " + langLabel;
    node.textContent = aiTranscribeAvailable ? engine : engine + " · " + localAiHint();
    setSetupVoiceStatus(setupPromptText());
  }

  function browserSpeechSupported() {
    return !!SpeechRecognition;
  }

  function localAiHint() {
    if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
      return "本機未設定 OpenAI key；完整 AI 語音請用線上版測試。";
    }
    return "AI 語音未啟用；目前使用瀏覽器語音。";
  }

  async function initTranscribeStatus() {
    try {
      const res = await fetch("/voice/transcribe/status", { cache: "no-store" });
      const data = await res.json().catch(() => ({}));
      aiTranscribeAvailable = !!(res.ok && data.openai_enabled);
    } catch (err) {
      aiTranscribeAvailable = false;
    }
    renderEngineStatus();
    if (aiTranscribeAvailable) {
      setVoiceStatus("AI 語音已啟用；按一下後說本洞成績，系統會自動解析");
    } else if (browserSpeechSupported()) {
      setVoiceStatus(localAiHint() + " 請選對語言後再說。");
    } else {
      setVoiceStatus(localAiHint() + " 此瀏覽器不支援原生語音，請改用文字輸入或線上版。");
    }
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

  function showSetupError(msg) {
    const node = el("setup-error");
    node.textContent = msg;
    node.classList.remove("hidden");
  }

  function applySetupSpeech() {
    const setupText = el("setup-speech").value.trim();
    const parsed = MaisonGolfSpeech.parseSetup(setupText);
    if (parsed.date) el("round-date").value = parsed.date;
    if (parsed.time) el("round-time").value = parsed.time;
    if (parsed.course && !el("course-name").value.trim()) el("course-name").value = parsed.course;
    if (parsed.players && parsed.players.length && !el("player-names").value.trim()) {
      el("player-names").value = parsed.players.join("、");
    }
    const course = el("course-name").value.trim() || parsed.course;
    renderCourseMatch(detectCourseAndTee(setupText, course));
    el("setup-error").classList.add("hidden");
    return parsed;
  }

  function showError(msg) {
    const node = el("parse-error");
    node.textContent = msg;
    node.classList.remove("hidden");
  }

  function setVoiceStatus(msg) {
    el("voice-support").textContent = msg || "";
  }

  function setSetupVoiceStatus(msg) {
    el("setup-voice-support").textContent = msg || "";
  }

  function clearRecordingTimer() {
    if (recordingTimer) {
      clearTimeout(recordingTimer);
      recordingTimer = null;
    }
  }

  function speechErrorMessage(event) {
    const code = event && event.error;
    if (code === "not-allowed" || code === "service-not-allowed") return "麥克風權限未開啟，請允許瀏覽器使用麥克風";
    if (code === "no-speech") return "沒有聽到聲音，請靠近手機再說一次";
    if (code === "audio-capture") return "沒有偵測到麥克風，請檢查裝置權限";
    if (code === "network") return "語音服務連線不穩，請稍後再試或改用文字";
    if (code === "language-not-supported") return "目前瀏覽器不支援這個語言，請換一個語言選項";
    return "語音沒有收清楚，可以重說或直接打字";
  }

  function preferredAudioType() {
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return "";
    const types = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/mpeg",
    ];
    return types.find((type) => MediaRecorder.isTypeSupported(type)) || "";
  }

  function voiceContextForm(blob, purpose) {
    const form = new FormData();
    const type = blob.type || "audio/webm";
    const ext = type.includes("mp4") ? "m4a" : type.includes("mpeg") ? "mp3" : "webm";
    const isSetup = purpose === "setup";
    form.append("audio", blob, (isSetup ? "setup" : "hole-" + (round.current_hole || 1)) + "." + ext);
    form.append("purpose", isSetup ? "setup" : "hole");
    form.append("course", isSetup ? el("course-name").value.trim() : (round.course || ""));
    form.append("tee", isSetup ? "" : (round.tee || ""));
    form.append("hole", isSetup ? "" : String(round.current_hole || 1));
    form.append("players", isSetup ? el("player-names").value.trim() : (round.players || []).map((p) => p.name).join("、"));
    form.append("language", openAiLanguage());
    return form;
  }

  async function transcribeRecordedAudio(blob, purpose) {
    const isSetup = purpose === "setup";
    if (isSetup) setSetupVoiceStatus("正在識別開局資訊...");
    else setVoiceStatus("正在整理語音...");
    el(isSetup ? "setup-mic-btn" : "mic-btn").disabled = true;
    try {
      const res = await fetch("/voice/transcribe", {
        method: "POST",
        body: voiceContextForm(blob, purpose),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        if (data.fallback === "browser") {
          if (isSetup && setupRecognizer) {
            setSetupVoiceStatus("AI 語音尚未設定，暫時使用瀏覽器收音。");
            startSetupBrowserRecognition();
            return;
          }
          if (!isSetup && recognition) {
            setVoiceStatus("AI 語音尚未設定，暫時使用瀏覽器收音。");
            startBrowserRecognition();
            return;
          }
          if (!fallbackNoticeShown) {
            fallbackNoticeShown = true;
            (isSetup ? showSetupError : showError)("AI 語音尚未設定；可先用文字輸入測試");
          }
          return;
        }
        (isSetup ? showSetupError : showError)(data.error || "語音辨識暫時失敗，可以重說或直接打字");
        if (isSetup) setSetupVoiceStatus("");
        else setVoiceStatus("");
        return;
      }
      if (isSetup) {
        el("setup-speech").value = data.text || "";
        applySetupSpeech();
        setSetupVoiceStatus("已識別，請確認下方基本信息");
      } else {
        el("voice-transcript").value = data.text || "";
        setVoiceStatus("AI 已聽寫完成，請確認解析結果");
        parseCurrentTranscript();
      }
    } catch (err) {
      (isSetup ? showSetupError : showError)("網路或語音服務暫時不穩，可以重說或直接打字");
      if (isSetup) setSetupVoiceStatus("");
      else setVoiceStatus("");
    } finally {
      el(isSetup ? "setup-mic-btn" : "mic-btn").disabled = false;
      el(isSetup ? "setup-mic-label" : "mic-label").textContent = isSetup ? "按一下說開局資訊" : "按一下開始錄音";
      el(isSetup ? "setup-mic-btn" : "mic-btn").classList.remove("ring-4", "ring-zinc-200");
    }
  }

  async function startRecording(purpose) {
    const isSetup = purpose === "setup";
    if (!aiTranscribeAvailable) {
      if (isSetup) startSetupBrowserRecognition();
      else startBrowserRecognition();
      return;
    }
    const nav = window.navigator || {};
    if (!nav.mediaDevices || !nav.mediaDevices.getUserMedia || !window.MediaRecorder) {
      if (isSetup) startSetupBrowserRecognition();
      else startBrowserRecognition();
      return;
    }
    try {
      const stream = await nav.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      const mimeType = preferredAudioType();
      mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size) audioChunks.push(event.data);
      };
      mediaRecorder.onstop = () => {
        clearRecordingTimer();
        stream.getTracks().forEach((track) => track.stop());
        recording = false;
        recordingPurpose = "";
        el(isSetup ? "setup-mic-label" : "mic-label").textContent = "正在辨識...";
        const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
        if (!blob.size) {
          (isSetup ? showSetupError : showError)("沒有收到聲音，可以再按一次重說");
          if (isSetup) setSetupVoiceStatus("");
          else setVoiceStatus("");
          return;
        }
        transcribeRecordedAudio(blob, purpose);
      };
      mediaRecorder.start();
      recording = true;
      recordingPurpose = purpose;
      const seconds = isSetup ? 8 : 6;
      el(isSetup ? "setup-mic-label" : "mic-label").textContent = "錄音中，" + seconds + " 秒後自動識別";
      el(isSetup ? "setup-mic-btn" : "mic-btn").classList.add("ring-4", "ring-zinc-200");
      if (isSetup) setSetupVoiceStatus("請說：時間、球場、Tee、球友；說完可再按一下提前識別。");
      else setVoiceStatus("請說本洞每位球友的成績；說完可再按一下提前識別。");
      recordingTimer = setTimeout(stopRecording, seconds * 1000);
    } catch (err) {
      (isSetup ? showSetupError : showError)("麥克風權限未開啟，可以改用文字輸入");
      if (isSetup) setSetupVoiceStatus("");
      else setVoiceStatus("");
    }
  }

  function stopRecording() {
    clearRecordingTimer();
    if (mediaRecorder && recording) mediaRecorder.stop();
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
      setVoiceStatus("可錄一小段語音由 AI 轉文字；若瀏覽器不支援錄音，可先用文字輸入測試。");
      return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = selectedSpeechLang();
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.maxAlternatives = 3;
    recognition.onstart = () => {
      recognizing = true;
      el("mic-label").textContent = "聽緊...";
      el("mic-btn").classList.add("ring-4", "ring-zinc-200");
    };
    recognition.onend = () => {
      recognizing = false;
      el("mic-label").textContent = "按一下開始錄音";
      el("mic-btn").classList.remove("ring-4", "ring-zinc-200");
    };
    recognition.onerror = (event) => showError(speechErrorMessage(event));
    recognition.onresult = (event) => {
      const text = Array.from(event.results).map((r) => r[0].transcript).join(" ");
      el("voice-transcript").value = text;
      parseCurrentTranscript();
    };
    setVoiceStatus("按一下錄音，說完再按一下；AI 未設定時會降級用瀏覽器收音。");
  }

  function setupOpeningRecognition() {
    if (!SpeechRecognition) return;
    setupRecognizer = new SpeechRecognition();
    setupRecognizer.lang = selectedSpeechLang();
    setupRecognizer.interimResults = false;
    setupRecognizer.continuous = false;
    setupRecognizer.maxAlternatives = 3;
    setupRecognizer.onstart = () => {
      recognizing = true;
      el("setup-mic-label").textContent = "聽緊...";
      el("setup-mic-btn").classList.add("ring-4", "ring-zinc-200");
    };
    setupRecognizer.onend = () => {
      recognizing = false;
      el("setup-mic-label").textContent = "按一下說開局資訊";
      el("setup-mic-btn").classList.remove("ring-4", "ring-zinc-200");
    };
    setupRecognizer.onerror = (event) => showSetupError(speechErrorMessage(event));
    setupRecognizer.onresult = (event) => {
      const text = Array.from(event.results).map((r) => r[0].transcript).join(" ");
      el("setup-speech").value = text;
      applySetupSpeech();
    };
  }

  function startBrowserRecognition() {
    if (!recognition) {
      showError("這個瀏覽器不能直接收音，請在下方輸入一句測試");
      return;
    }
    recognition.lang = selectedSpeechLang();
    if (recognizing) recognition.stop();
    else recognition.start();
  }

  function startSetupBrowserRecognition() {
    if (!setupRecognizer) {
      showSetupError("這個瀏覽器不能直接收音，請先輸入一句開局資訊");
      return;
    }
    setupRecognizer.lang = selectedSpeechLang();
    if (recognizing) setupRecognizer.stop();
    else setupRecognizer.start();
  }

  function bind() {
    el("start-voice-round").addEventListener("click", () => {
      const setupText = el("setup-speech").value.trim();
      const parsed = applySetupSpeech();
      const course = (el("course-name").value.trim() || parsed.course || "自訂球場");
      const players = cleanPlayers(el("player-names").value || parsed.players.join("、"));
      const courseMatch = detectCourseAndTee(setupText, course);
      renderCourseMatch(courseMatch);
      if (!players.length) {
        el("setup-error").textContent = "至少輸入一位球友";
        el("setup-error").classList.remove("hidden");
        return;
      }
      round = newRound(course, players, courseMatch, {
        date: el("round-date").value,
        time: el("round-time").value,
      });
      saveDraft();
      showRound();
    });

    el("setup-mic-btn").addEventListener("click", () => {
      if (recording && recordingPurpose === "setup") stopRecording();
      else startRecording("setup");
    });
    el("parse-setup").addEventListener("click", applySetupSpeech);
    el("setup-speech").addEventListener("input", applySetupSpeech);
    el("speech-lang").addEventListener("change", renderEngineStatus);
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
      if (recording) stopRecording();
      else if (fallbackNoticeShown) startBrowserRecognition();
      else startRecording("hole");
    });
  }

  setupRecognition();
  setupOpeningRecognition();
  bind();
  initTranscribeStatus();
  if (round && round.status === "in_progress") showRound();
  else showSetup();
})();
