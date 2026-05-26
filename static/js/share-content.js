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

  let currentRoundId = null;
  let metaCache = null;
  let photoFile = null;
  let videoFile = null;
  let objectPreviewUrl = null;

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
    document.getElementById("share-panel-photo")?.classList.toggle("hidden", tab !== "photo");
    document.getElementById("share-panel-video")?.classList.toggle("hidden", tab !== "video");
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

    setTab(tab || "photo");
    loadMeta(roundId).catch((e) => showStatus(e.message, "error"));
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
    if (currentRoundId) loadMeta(currentRoundId).catch(() => {});
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
    const tab = btn.dataset.shareTab || "photo";
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
