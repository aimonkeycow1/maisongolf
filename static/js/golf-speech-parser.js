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
      .replace(/左鳥|左鸟|抓烏|抓乌|小烏|小乌/g, "抓鳥")
      .replace(/老英|老應|抓英|抓應/g, "抓鷹")
      .replace(/保趴|保怕|補帕/g, "保帕")
      .replace(/柏技|柏忌忌|bogie/gi, "柏忌")
      .replace(/兩腿|二腿|兩退|二退/g, "兩推")
      .replace(/一腿|一退/g, "一推")
      .replace(/三腿|三退/g, "三推")
      .replace(/四腿|四退/g, "四推")
      .replace(/五腿|五退/g, "五推")
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

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function dateString(date) {
    return date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate());
  }

  function parseSetupDate(text, now) {
    const base = now || new Date();
    const d = new Date(base.getFullYear(), base.getMonth(), base.getDate());
    if (/明天|聽日/.test(text)) d.setDate(d.getDate() + 1);
    else if (/昨天|尋日|琴日/.test(text)) d.setDate(d.getDate() - 1);

    const monthDay = text.match(new RegExp(numberPattern() + "\\s*月\\s*" + numberPattern() + "\\s*(?:日|號|号)?"));
    if (monthDay) {
      const month = toNumber(monthDay[1]);
      const day = toNumber(monthDay[2]);
      if (month && day) return dateString(new Date(base.getFullYear(), month - 1, day));
    }
    return dateString(d);
  }

  function parseSetupTime(text) {
    const n = numberPattern();
    const m = text.match(new RegExp("(上午|早上|朝早|中午|下午|下晝|晚上|夜晚)?\\s*" + n + "\\s*(?:點|点|時|时)(?:\\s*" + n + "\\s*分?)?"));
    if (!m) return "";
    let hour = toNumber(m[2]);
    const minute = m[3] ? toNumber(m[3]) : 0;
    if (hour == null || minute == null) return "";
    const period = m[1] || "";
    if (/下午|下晝|晚上|夜晚/.test(period) && hour < 12) hour += 12;
    if (/中午/.test(period) && hour < 11) hour += 12;
    if (hour > 23 || minute > 59) return "";
    return pad(hour) + ":" + pad(minute);
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
    const courseMatch = normalized.match(/(?:打|在|去)(.+?)(?:球場|高爾夫|白梯|藍梯|蓝梯|紅梯|红梯|黃梯|黄梯|黑梯|，|,| 有| 球友| 同組| 和| 跟| 與|$)/);
    if (courseMatch) {
      course = courseMatch[1]
        .replace(/^(今天|今日|聽日|明天|昨天|尋日|琴日|上午|早上|朝早|中午|下午|下晝|晚上|夜晚|\d+點|\d+点|\d+時|\d+时|\S+月\S+日)\s*/, "")
        .trim();
      if (course && /球場|高爾夫/.test(normalized) && !/球場|高爾夫/.test(course)) course += "球場";
    }

    let peopleText = "";
    const peopleMatch = normalized.match(/(?:球友|同組|同组|朋友|有)(.+)$/);
    if (peopleMatch) peopleText = peopleMatch[1];
    else {
      const afterCourse = normalized.match(/(?:和|跟|與|同)(.+?)(?:一起|一齊|去|打|$)/);
      if (afterCourse) peopleText = afterCourse[1];
    }
    peopleText = peopleText
      .replace(/^[有是為:：\s]+/, "")
      .replace(/(?:一起|一齊|開球|打球|打高爾夫|打高尔夫).*$/, "");
    const players = peopleText
      ? peopleText.split(/[、,\s和跟與]+/).map((x) => x.trim()).filter(Boolean).slice(0, 8)
      : [];
    return {
      course,
      players,
      date: parseSetupDate(normalized),
      time: parseSetupTime(normalized),
      normalized,
    };
  }

  global.MaisonGolfSpeech = {
    normalizeText,
    toNumber,
    parseSetup,
    parseHoleTranscript,
  };
})(window);
