/**
 * 社交分享內容生成 — 照片 / 短視頻
 */
(function () {
  if (window.MaisonShareContent) return;

  const modal = document.getElementById("share-content-modal");
  if (!modal) return;

  const closeBtn = document.getElementById("share-modal-close");
  const playerSelect = document.getElementById("share-player-select");
  const metaBar = document.getElementById("share-meta-bar");
  const metaCourse = document.getElementById("share-meta-course");
  const metaLine = document.getElementById("share-meta-line");
  const statusEl = document.getElementById("share-status");
  const photoInput = document.getElementById("share-photo-input");
  const photoFilename = document.getElementById("share-photo-filename");
  const photoPreviewWrap = document.getElementById("share-photo-preview-wrap");
  const photoPreview = document.getElementById("share-photo-preview");
  const genPhotoBtn = document.getElementById("share-generate-photo");
  const photoResults = document.getElementById("share-photo-results");
  const photoGrid = document.getElementById("share-photo-grid");
  const videoInput = document.getElementById("share-video-input");
  const videoFilename = document.getElementById("share-video-filename");
  const musicSelect = document.getElementById("share-music-select");
  const musicHint = document.getElementById("share-music-hint");
  const durationRange = document.getElementById("share-duration-range");
  const durationLabel = document.getElementById("share-duration-label");
  const genVideoBtn = document.getElementById("share-generate-video");
  const videoResult = document.getElementById("share-video-result");
  const videoPlayer = document.getElementById("share-video-player");
  const videoDownload = document.getElementById("share-video-download");
  const cardCanvas = document.getElementById("share-card-canvas");
  const cardDownload = document.getElementById("share-card-download");
  const cardSizeGroup = document.getElementById("card-size-group");

  let currentRoundId = null;
  let metaCache = null;
  let photoFile = null;
  let videoFile = null;
  let objectPreviewUrl = null;
  let currentCardSize = "xhs";
  let cardFontsReady = false;

  function showStatus(msg, type) {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.classList.remove("hidden", "bg-red-900/40", "text-red-100", "bg-emerald-900/40", "text-emerald-100", "bg-gold/15", "text-gold-light");
    if (type === "error") statusEl.classList.add("bg-red-900/40", "text-red-100");
    else if (type === "ok") statusEl.classList.add("bg-emerald-900/40", "text-emerald-100");
    else statusEl.classList.add("bg-gold/15", "text-gold-light");
  }

  function hideStatus() {
    statusEl?.classList.add("hidden");
  }

  function setTab(tab) {
    document.querySelectorAll(".share-tab-btn").forEach((btn) => {
      const active = btn.dataset.shareTab === tab;
      btn.classList.toggle("border-gold/50", active);
      btn.classList.toggle("bg-gold/20", active);
      btn.classList.toggle("text-gold-light", active);
      btn.classList.toggle("font-bold", active);
      btn.classList.toggle("border-white/15", !active);
      btn.classList.toggle("bg-white/5", !active);
      btn.classList.toggle("text-green-200/80", !active);
      btn.classList.toggle("font-semibold", !active);
    });
    document.getElementById("share-panel-card")?.classList.toggle("hidden", tab !== "card");
    document.getElementById("share-panel-photo")?.classList.toggle("hidden", tab !== "photo");
    document.getElementById("share-panel-video")?.classList.toggle("hidden", tab !== "video");
    if (tab === "card") renderCard();
  }

  function updateMetaBar(meta) {
    if (!meta || !metaBar) return;
    metaBar.classList.remove("hidden");
    metaCourse.textContent = meta.course || "";
    metaLine.textContent = `${meta.player_name} · ${meta.total} 桿（${meta.to_par_label}）· ${meta.date} · ${meta.player_count} 位球友`;
  }

  async function loadMeta(roundId) {
    const player = playerSelect?.value || "";
    const q = player ? `?player_name=${encodeURIComponent(player)}` : "";
    const res = await fetch(`/share/meta/${roundId}${q}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "載入失敗");
    metaCache = data.meta;

    if (playerSelect && data.players?.length) {
      const prev = playerSelect.value;
      playerSelect.innerHTML = data.players
        .map(
          (p) =>
            `<option value="${escapeAttr(p.name)}">${escapeHtml(p.name)} · ${p.total} 桿</option>`
        )
        .join("");
      if (prev) playerSelect.value = prev;
      else playerSelect.selectedIndex = 0;
    }

    if (musicSelect && data.music_tracks) {
      const cur = musicSelect.value;
      musicSelect.innerHTML =
        '<option value="">無配樂（僅畫面）</option>' +
        data.music_tracks
          .map((t) => {
            const dis = t.available ? "" : "（音檔未配置）";
            return `<option value="${escapeAttr(t.id)}" ${t.available ? "" : "disabled"}>${escapeHtml(t.name)}${dis}</option>`;
          })
          .join("");
      if (cur) musicSelect.value = cur;
      const avail = data.music_tracks.filter((t) => t.available).length;
      if (musicHint) {
        musicHint.textContent =
          avail > 0
            ? `已配置 ${avail} 首背景音樂，合成時將自動混音。`
            : "管理員可將 MP3 放入 static/audio/ 目錄以啟用配樂。";
      }
    }

    updateMetaBar(metaCache);
    return data;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function escapeAttr(s) {
    return String(s).replace(/"/g, "&quot;");
  }

  function openModal(roundId, tab) {
    currentRoundId = roundId;
    photoFile = null;
    videoFile = null;
    photoResults?.classList.add("hidden");
    photoGrid.innerHTML = "";
    videoResult?.classList.add("hidden");
    hideStatus();
    if (objectPreviewUrl) {
      URL.revokeObjectURL(objectPreviewUrl);
      objectPreviewUrl = null;
    }
    photoPreviewWrap?.classList.add("hidden");
    photoFilename?.classList.add("hidden");
    videoFilename?.classList.add("hidden");
    genPhotoBtn.disabled = true;
    genVideoBtn.disabled = true;
    if (photoInput) photoInput.value = "";
    if (videoInput) videoInput.value = "";

    modal.classList.remove("hidden");
    modal.classList.add("flex");
    document.body.style.overflow = "hidden";

    setTab(tab || "card");
    loadMeta(roundId)
      .then(() => renderCard())
      .catch((e) => showStatus(e.message, "error"));
  }

  /* ===== 戰報圖卡（純前端 canvas 生成 · 免上傳） ===== */
  const CARD_SIZES = {
    xhs: [1080, 1440],
    story: [1080, 1920],
    square: [1080, 1080],
  };

  async function ensureCardFonts() {
    if (cardFontsReady) return;
    try {
      if (document.fonts && document.fonts.load) {
        await Promise.all([
          document.fonts.load('700 120px "Playfair Display"'),
          document.fonts.load('700 48px "Noto Serif TC"'),
          document.fonts.load('600 32px "Noto Sans TC"'),
        ]);
        await document.fonts.ready;
      }
    } catch (e) {
      /* 字型載入失敗則使用系統字型 fallback */
    }
    cardFontsReady = true;
  }

  function roundRect(ctx, x, y, w, h, r) {
    const rr = Math.min(r, h / 2, w / 2);
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.arcTo(x + w, y, x + w, y + h, rr);
    ctx.arcTo(x + w, y + h, x, y + h, rr);
    ctx.arcTo(x, y + h, x, y, rr);
    ctx.arcTo(x, y, x + w, y, rr);
    ctx.closePath();
  }

  function wrapText(ctx, text, maxWidth) {
    const chars = String(text).split("");
    const lines = [];
    let line = "";
    for (const ch of chars) {
      const test = line + ch;
      if (ctx.measureText(test).width > maxWidth && line) {
        lines.push(line);
        line = ch;
      } else {
        line = test;
      }
    }
    if (line) lines.push(line);
    return lines.slice(0, 2);
  }

  async function renderCard() {
    if (!cardCanvas || !metaCache) return;
    await ensureCardFonts();

    const m = metaCache;
    const [W, H] = CARD_SIZES[currentCardSize] || CARD_SIZES.xhs;
    cardCanvas.width = W;
    cardCanvas.height = H;
    const ctx = cardCanvas.getContext("2d");
    const cx = W / 2;

    // 背景：深綠漸層 + 香檳光暈
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, "#0c2418");
    bg.addColorStop(0.55, "#0a1c12");
    bg.addColorStop(1, "#06120b");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    const glow = ctx.createRadialGradient(cx, H * 0.22, 40, cx, H * 0.22, W * 0.8);
    glow.addColorStop(0, "rgba(217,183,140,0.20)");
    glow.addColorStop(1, "rgba(217,183,140,0)");
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, W, H);

    // 金色細框
    ctx.strokeStyle = "rgba(217,183,140,0.45)";
    ctx.lineWidth = 3;
    roundRect(ctx, 36, 36, W - 72, H - 72, 36);
    ctx.stroke();

    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";

    // 頁眉
    ctx.fillStyle = "rgba(246,231,197,0.85)";
    ctx.font = '600 30px "Noto Sans TC", sans-serif';
    ctx.save();
    ctx.letterSpacing = "8px";
    ctx.fillText("MAISON GOLF · SCORECARD", cx, 130);
    ctx.restore();

    // 球場名稱（serif，可換行）
    ctx.fillStyle = "#ffffff";
    ctx.font = '700 70px "Noto Serif TC", "Playfair Display", serif';
    const courseLines = wrapText(ctx, m.course || "高爾夫球場", W - 200);
    let cy = 230;
    for (const ln of courseLines) {
      ctx.fillText(ln, cx, cy);
      cy += 84;
    }

    // 日期 · Tee
    ctx.fillStyle = "rgba(200,224,210,0.7)";
    ctx.font = '400 34px "Noto Sans TC", sans-serif';
    const sub = [m.date, m.tee].filter(Boolean).join(" · ");
    ctx.fillText(sub, cx, cy + 14);
    let headerBottom = cy + 40;

    // 差點指數徽章（社交炫耀）
    if (m.index !== null && m.index !== undefined) {
      const label = `差點指數 ${Number(m.index).toFixed(1)}`;
      ctx.font = '700 34px "Noto Sans TC", sans-serif';
      const bw = ctx.measureText(label).width + 70;
      const bh = 66;
      const by = cy + 34;
      ctx.fillStyle = "rgba(217,183,140,0.16)";
      roundRect(ctx, cx - bw / 2, by, bw, bh, bh / 2);
      ctx.fill();
      ctx.strokeStyle = "rgba(217,183,140,0.6)";
      ctx.lineWidth = 2;
      roundRect(ctx, cx - bw / 2, by, bw, bh, bh / 2);
      ctx.stroke();
      ctx.fillStyle = "#f6e7c5";
      ctx.textBaseline = "middle";
      ctx.fillText(label, cx, by + bh / 2 + 1);
      ctx.textBaseline = "alphabetic";
      headerBottom = by + bh + 6;
    }

    const footerTop = H - 190;

    // 中央群組（估算高度後垂直置中）
    const GROUP_H = 760;
    let y = Math.max(headerBottom + 30, (headerBottom + footerTop) / 2 - GROUP_H / 2);

    // 「總桿」標籤
    ctx.fillStyle = "rgba(246,231,197,0.7)";
    ctx.font = '600 32px "Noto Sans TC", sans-serif';
    ctx.fillText("總桿", cx, y + 36);
    y += 70;

    // 巨大總桿數字（香檳金漸層）
    ctx.font = '700 300px "Playfair Display", "Noto Serif TC", serif';
    const numGrad = ctx.createLinearGradient(0, y, 0, y + 300);
    numGrad.addColorStop(0, "#f6e7c5");
    numGrad.addColorStop(1, "#d9b78c");
    ctx.fillStyle = numGrad;
    ctx.textBaseline = "middle";
    ctx.fillText(String(m.total), cx, y + 150);
    ctx.textBaseline = "alphabetic";
    y += 320;

    // 比標準桿膠囊
    const pillText = m.to_par_label || "";
    ctx.font = '700 42px "Noto Sans TC", sans-serif';
    const pw = ctx.measureText(pillText).width + 80;
    const ph = 78;
    const toPar = typeof m.to_par === "number" ? m.to_par : 0;
    const pillColor =
      toPar < 0 ? "rgba(34,197,94,0.22)" : toPar === 0 ? "rgba(217,183,140,0.22)" : "rgba(234,179,8,0.18)";
    const pillStroke =
      toPar < 0 ? "rgba(34,197,94,0.6)" : toPar === 0 ? "rgba(217,183,140,0.6)" : "rgba(234,179,8,0.55)";
    ctx.fillStyle = pillColor;
    roundRect(ctx, cx - pw / 2, y, pw, ph, ph / 2);
    ctx.fill();
    ctx.strokeStyle = pillStroke;
    ctx.lineWidth = 2;
    roundRect(ctx, cx - pw / 2, y, pw, ph, ph / 2);
    ctx.stroke();
    ctx.fillStyle = "#ffffff";
    ctx.textBaseline = "middle";
    ctx.fillText(pillText, cx, y + ph / 2 + 2);
    ctx.textBaseline = "alphabetic";
    y += ph + 64;

    // 三欄數據：前九 / 後九 / 名次
    const cols = [
      { label: "前九", value: m.front9 != null ? String(m.front9) : "—" },
      { label: "後九", value: m.back9 != null ? String(m.back9) : "—" },
      { label: "名次", value: `${m.rank || 1}/${m.player_count || 1}` },
    ];
    const colX = [cx - 320, cx, cx + 320];
    cols.forEach((c, i) => {
      ctx.fillStyle = "#ffffff";
      ctx.font = '700 60px "Noto Sans TC", sans-serif';
      ctx.fillText(c.value, colX[i], y + 20);
      ctx.fillStyle = "rgba(246,231,197,0.6)";
      ctx.font = '600 28px "Noto Sans TC", sans-serif';
      ctx.fillText(c.label, colX[i], y + 70);
    });
    y += 130;

    // 亮點洞（最多 4 個 chip，置中換行）
    const hl = (m.highlights || []).slice(0, 4);
    if (hl.length) {
      ctx.font = '600 28px "Noto Sans TC", sans-serif';
      const gap = 18;
      const chipH = 56;
      const sizes = hl.map((t) => ctx.measureText(t).width + 48);
      // 分行（最多 2 行）
      const rows = [[]];
      let rowW = 0;
      const maxRowW = W - 160;
      hl.forEach((t, i) => {
        const w = sizes[i];
        if (rowW + w + gap > maxRowW && rows[rows.length - 1].length) {
          rows.push([]);
          rowW = 0;
        }
        rows[rows.length - 1].push({ t, w });
        rowW += w + gap;
      });
      rows.forEach((row, ri) => {
        const totalW = row.reduce((a, c) => a + c.w, 0) + gap * (row.length - 1);
        let sx = cx - totalW / 2;
        const ry = y + ri * (chipH + 16);
        row.forEach((c) => {
          ctx.fillStyle = "rgba(255,255,255,0.06)";
          roundRect(ctx, sx, ry, c.w, chipH, chipH / 2);
          ctx.fill();
          ctx.strokeStyle = "rgba(217,183,140,0.35)";
          ctx.lineWidth = 1.5;
          roundRect(ctx, sx, ry, c.w, chipH, chipH / 2);
          ctx.stroke();
          ctx.fillStyle = "rgba(246,231,197,0.95)";
          ctx.textBaseline = "middle";
          ctx.fillText(c.t, sx + c.w / 2, ry + chipH / 2 + 1);
          ctx.textBaseline = "alphabetic";
          sx += c.w + gap;
        });
      });
    }

    // 頁腳品牌
    ctx.fillStyle = "rgba(246,231,197,0.95)";
    ctx.font = '700 46px "Playfair Display", "Noto Serif TC", serif';
    ctx.fillText("Maison Golf", cx, H - 120);
    ctx.fillStyle = "rgba(200,224,210,0.55)";
    ctx.font = '400 28px "Noto Sans TC", sans-serif';
    ctx.fillText(`${m.player_name} · 高爾夫隨身球僮`, cx, H - 76);

    // 下載連結
    try {
      cardCanvas.toBlob((blob) => {
        if (!blob || !cardDownload) return;
        if (cardDownload._url) URL.revokeObjectURL(cardDownload._url);
        const url = URL.createObjectURL(blob);
        cardDownload._url = url;
        cardDownload.href = url;
        cardDownload.download = `maison-golf-${m.player_name || "card"}-${currentCardSize}.png`;
      }, "image/png");
    } catch (e) {
      /* 某些瀏覽器需 https/互動，下載仍可長按圖片 */
    }
  }

  function closeModal() {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    document.body.style.overflow = "";
    currentRoundId = null;
  }

  document.querySelectorAll(".share-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => setTab(btn.dataset.shareTab));
  });

  closeBtn?.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  playerSelect?.addEventListener("change", () => {
    if (currentRoundId) loadMeta(currentRoundId).then(() => renderCard()).catch(() => {});
  });

  cardSizeGroup?.querySelectorAll(".card-size-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentCardSize = btn.dataset.cardSize || "xhs";
      cardSizeGroup.querySelectorAll(".card-size-btn").forEach((b) => {
        const active = b === btn;
        b.classList.toggle("border-gold/50", active);
        b.classList.toggle("bg-gold/20", active);
        b.classList.toggle("text-gold-light", active);
        b.classList.toggle("font-bold", active);
        b.classList.toggle("border-white/15", !active);
        b.classList.toggle("bg-white/5", !active);
        b.classList.toggle("text-green-200/80", !active);
        b.classList.toggle("font-semibold", !active);
      });
      renderCard();
    });
  });

  durationRange?.addEventListener("input", () => {
    durationLabel.textContent = `${durationRange.value} 秒`;
  });

  photoInput?.addEventListener("change", () => {
    const f = photoInput.files?.[0];
    photoFile = f || null;
    genPhotoBtn.disabled = !photoFile || !currentRoundId;
    if (!f) return;
    photoFilename.textContent = f.name;
    photoFilename.classList.remove("hidden");
    if (objectPreviewUrl) URL.revokeObjectURL(objectPreviewUrl);
    objectPreviewUrl = URL.createObjectURL(f);
    photoPreview.src = objectPreviewUrl;
    photoPreviewWrap.classList.remove("hidden");
  });

  videoInput?.addEventListener("change", () => {
    const f = videoInput.files?.[0];
    videoFile = f || null;
    genVideoBtn.disabled = !videoFile || !currentRoundId;
    if (!f) return;
    videoFilename.textContent = f.name;
    videoFilename.classList.remove("hidden");
  });

  genPhotoBtn?.addEventListener("click", async () => {
    if (!currentRoundId || !photoFile) return;
    genPhotoBtn.disabled = true;
    showStatus("正在套用高爾夫濾鏡並生成 4 種風格…", "info");

    const fd = new FormData();
    fd.append("round_id", currentRoundId);
    fd.append("photo", photoFile);
    if (playerSelect?.value) fd.append("player_name", playerSelect.value);

    try {
      const res = await fetch("/share/photo", { method: "POST", body: fd });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "生成失敗");

      photoGrid.innerHTML = (data.images || [])
        .map(
          (img) => `
        <article class="overflow-hidden rounded-xl border border-white/10 bg-black/30 ring-1 ring-gold/20">
          <img src="${escapeAttr(img.url)}" alt="${escapeAttr(img.style_label)}" class="w-full object-cover" loading="lazy" />
          <div class="flex items-center justify-between gap-2 px-3 py-2.5">
            <div>
              <p class="text-xs font-bold text-gold-light">${escapeHtml(img.style_label)}</p>
              <p class="text-[10px] text-green-200/50">${img.width}×${img.height}</p>
            </div>
            <a href="${escapeAttr(img.url)}" download="maison-golf-${img.style}.jpg"
               class="shrink-0 rounded-lg bg-gold px-3 py-1.5 text-xs font-bold text-fairway-dark no-underline hover:bg-gold-light">
              下載
            </a>
          </div>
        </article>`
        )
        .join("");

      photoResults.classList.remove("hidden");
      showStatus(`已生成 ${data.images.length} 張分享圖，可下載後發佈。`, "ok");

      if (navigator.share && data.images[0]) {
        /* 可选手機原生分享 — 不強制 */
      }
    } catch (e) {
      showStatus(e.message, "error");
    } finally {
      genPhotoBtn.disabled = !photoFile;
    }
  });

  genVideoBtn?.addEventListener("click", async () => {
    if (!currentRoundId || !videoFile) return;
    genVideoBtn.disabled = true;
    showStatus("正在合成短視頻（約 30–90 秒）…", "info");

    const fd = new FormData();
    fd.append("round_id", currentRoundId);
    fd.append("video", videoFile);
    fd.append("duration", durationRange?.value || "25");
    if (playerSelect?.value) fd.append("player_name", playerSelect.value);
    if (musicSelect?.value) fd.append("music_id", musicSelect.value);

    try {
      const res = await fetch("/share/video", { method: "POST", body: fd });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "合成失敗");

      videoPlayer.src = data.video_url;
      videoDownload.href = data.video_url;
      videoResult.classList.remove("hidden");
      showStatus(`短視頻已生成（${data.duration_sec} 秒），可預覽或下載。`, "ok");
    } catch (e) {
      showStatus(e.message, "error");
    } finally {
      genVideoBtn.disabled = !videoFile;
    }
  });

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".share-content-trigger");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    const roundId = btn.dataset.roundId;
    const tab = btn.dataset.shareTab || "card";
    if (roundId) openModal(roundId, tab);
  });

  /* 記分完成後 ?share=1 自動打開 */
  const params = new URLSearchParams(window.location.search);
  if (params.get("share") === "1") {
    const rid = document.getElementById("round-page-root")?.dataset.roundId;
    if (rid) {
      window.addEventListener("load", () => openModal(rid, "photo"));
    }
  }

  window.MaisonShareContent = { open: openModal, close: closeModal };
})();
