/* Maison Golf — 高爾夫口述解析器（本機規則版） */
(function (global) {
  "use strict";

  const CN_NUM = {
    "零": 0, "〇": 0, "一": 1, "壹": 1, "兩": 2, "二": 2, "貳": 2,
    "三": 3, "參": 3, "四": 4, "肆": 4, "五": 5, "伍": 5,
    "六": 6, "陸": 6, "七": 7, "柒": 7, "八": 8, "捌": 8,
    "九": 9, "玖": 9, "十": 10, "拾": 10,
  };

  function escReg(s) {
    return String(s || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function normalizeText(text) {
    return String(text || "")
      .replace(/[，。；;、]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function toNumber(raw) {
    const s = String(raw || "").trim();
    if (!s) return null;
    if (/^\d+$/.test(s)) return parseInt(s, 10);
    if (s.length === 1 && CN_NUM[s] != null) return CN_NUM[s];
    if (s === "十一") return 11;
    if (s === "十二") return 12;
    if (s.startsWith("十")) {
      const rest = s.slice(1);
      return 10 + (CN_NUM[rest] || 0);
    }
    if (s.endsWith("十")) {
      return (CN_NUM[s[0]] || 1) * 10;
    }
    if (s.includes("十")) {
      const parts = s.split("十");
      return (CN_NUM[parts[0]] || 1) * 10 + (CN_NUM[parts[1]] || 0);
    }
    return null;
  }

  function numberPattern() {
    return "(\\d+|[零〇一壹兩二貳三參四肆五伍六陸七柒八捌九玖十拾]{1,3})";
  }

  function findHole(text) {
    const n = numberPattern();
    const m = text.match(new RegExp(n + "\\s*(?:號)?\\s*洞"));
    return m ? toNumber(m[1]) : null;
  }

  function parsePlayerEntry(segment, playerName) {
    const n = numberPattern();
    const clean = normalizeText(segment);
    let m = clean.match(new RegExp(n + "\\s*上\\s*" + n + "\\s*推"));
    if (m) {
      const greenShots = toNumber(m[1]);
      const putts = toNumber(m[2]);
      if (greenShots != null && putts != null) {
        return {
          player: playerName,
          green_shots: greenShots,
          putts: putts,
          penalties: /(?:罰|罚|ob|OB)/.test(clean) ? 1 : 0,
          score: greenShots + putts + (/(?:罰|罚|ob|OB)/.test(clean) ? 1 : 0),
          confidence: 0.94,
          source: clean,
        };
      }
    }

    m = clean.match(new RegExp("(?:總共|一共|是|打)\\s*" + n + "\\s*(?:桿|杆)?"));
    if (!m) m = clean.match(new RegExp(n + "\\s*(?:桿|杆)"));
    if (m) {
      const score = toNumber(m[1]);
      if (score != null) {
        return {
          player: playerName,
          green_shots: null,
          putts: null,
          penalties: /(?:罰|罚|ob|OB)/.test(clean) ? 1 : 0,
          score: score,
          confidence: 0.72,
          source: clean,
        };
      }
    }

    const lower = clean.toLowerCase();
    if (/一桿進洞|一杆进洞|hole\s*in\s*one|ace/i.test(lower)) {
      return {
        player: playerName,
        green_shots: null,
        putts: null,
        penalties: 0,
        score_label: "hole in one",
        score: 1,
        confidence: 0.9,
        source: clean,
      };
    }

    const semanticScores = [
      { label: "albatross", diff: -3, re: /信天翁|albatross|double\s+eagle/i },
      { label: "eagle", diff: -2, re: /老鷹|老鹰|抓鷹|抓鹰|eagle/i },
      { label: "birdie", diff: -1, re: /抓鳥|抓鸟|小鳥|小鸟|博蒂|birdie/i },
      { label: "par", diff: 0, re: /保帕|平標準桿|平标准杆|標準桿|标准杆|\bpar\b/i },
      { label: "double bogey", diff: 2, re: /雙柏忌|双柏忌|double\s+bogey/i },
      { label: "bogey", diff: 1, re: /柏忌|bogey/i },
    ];
    for (const item of semanticScores) {
      if (item.re.test(lower)) {
        return {
          player: playerName,
          green_shots: null,
          putts: null,
          penalties: 0,
          score_label: item.label,
          score_diff: item.diff,
          confidence: 0.82,
          source: clean,
        };
      }
    }
    return null;
  }

  function splitByPlayers(text, players) {
    const found = [];
    players.forEach((name) => {
      const re = new RegExp(escReg(name), "g");
      let m;
      while ((m = re.exec(text))) {
        found.push({ name, index: m.index });
      }
    });
    found.sort((a, b) => a.index - b.index);
    return found.map((item, i) => {
      const start = item.index + item.name.length;
      const end = found[i + 1] ? found[i + 1].index : text.length;
      return { name: item.name, segment: text.slice(start, end) };
    });
  }

  function parseHoleTranscript(text, players, options) {
    const normalized = normalizeText(text);
    const hole = findHole(normalized) || (options && options.hole) || 1;
    const parts = splitByPlayers(normalized, players || []);
    const entries = [];
    const missing = [];

    parts.forEach((part) => {
      const parsed = parsePlayerEntry(part.segment, part.name);
      if (parsed) entries.push(parsed);
      else missing.push(part.name);
    });

    const named = new Set(entries.map((e) => e.player));
    (players || []).forEach((name) => {
      if (!named.has(name) && !missing.includes(name)) missing.push(name);
    });

    return {
      ok: entries.length > 0,
      hole,
      entries,
      missing,
      raw_transcript: text,
      normalized,
      confidence: entries.length && !missing.length ? 0.9 : entries.length ? 0.66 : 0.2,
    };
  }

  function parseSetup(text) {
    const normalized = normalizeText(text);
    let course = "";
    const courseMatch = normalized.match(/(?:打|在|去)(.+?)(?:球場|高爾夫|，|,| 有| 球友|$)/);
    if (courseMatch) course = courseMatch[1].trim() + (normalized.includes("球場") ? "球場" : "");
    const peopleMatch = normalized.match(/(?:球友|同組|有)(.+)$/);
    const peopleText = peopleMatch ? peopleMatch[1].replace(/^[有是為:：\s]+/, "") : "";
    const players = peopleMatch
      ? peopleText.split(/[、,\s和跟與]+/).map((x) => x.trim()).filter(Boolean)
      : [];
    return { course, players };
  }

  global.MaisonGolfSpeech = {
    normalizeText,
    toNumber,
    parseSetup,
    parseHoleTranscript,
  };
})(window);
