/**
 * AI 教練分析 — 共用前端邏輯
 */
(function () {
  if (window.MaisonAICoach) return;

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function renderAnalysis(data, source) {
    const badge =
      source === "grok"
        ? '<span class="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-200 ring-1 ring-emerald-400/30">Grok AI</span>'
        : '<span class="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-semibold text-green-200/80 ring-1 ring-white/15">智能教練 · 本機分析</span>';

    const list = (items, icon) =>
      (items || [])
        .map(
          (t) =>
            `<li class="flex gap-2 text-sm leading-relaxed text-green-100/90"><span class="mt-0.5 shrink-0">${icon}</span><span>${escapeHtml(t)}</span></li>`
        )
        .join("");

    return `
      <div class="ai-coach-result mt-4 overflow-hidden rounded-2xl border border-emerald-400/25 bg-gradient-to-br from-fairway-dark via-[#0f2918] to-fairway-dark shadow-xl ring-1 ring-emerald-500/20">
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 bg-black/20 px-5 py-3">
          <div class="flex items-center gap-2">
            <span class="text-lg" aria-hidden="true">🏌️</span>
            <p class="text-sm font-bold text-gold-light">AI 教練總結</p>
            ${badge}
          </div>
          <button type="button" class="ai-coach-copy rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-semibold text-green-100 transition hover:bg-white/10">
            複製全文
          </button>
        </div>
        <div class="space-y-5 p-5 sm:p-6">
          <section>
            <h4 class="mb-2 text-xs font-bold uppercase tracking-wider text-emerald-300">本場亮點 · Strong points</h4>
            <ul class="space-y-2">${list(data.highlights, "✓")}</ul>
          </section>
          <section>
            <h4 class="mb-2 text-xs font-bold uppercase tracking-wider text-amber-300">需要改進 · Areas to improve</h4>
            <ul class="space-y-2">${list(data.improvements, "→")}</ul>
          </section>
          <section>
            <h4 class="mb-2 text-xs font-bold uppercase tracking-wider text-sky-300">具體建議 · Actionable tips</h4>
            <ul class="space-y-2">${list(data.tips, "•")}</ul>
          </section>
          <section class="rounded-xl border border-gold/30 bg-gold/10 p-4">
            <h4 class="mb-2 text-xs font-bold uppercase tracking-wider text-gold-light">整體評價</h4>
            <p class="text-sm leading-relaxed text-green-50/95">${escapeHtml(data.summary || "")}</p>
          </section>
        </div>
      </div>`;
  }

  function fullText(data) {
    const sec = (title, items) =>
      title + "\n" + (items || []).map((x) => "• " + x).join("\n");
    return [
      "【AI 教練總結】",
      sec("本場亮點", data.highlights),
      "",
      sec("需要改進", data.improvements),
      "",
      sec("具體建議", data.tips),
      "",
      "整體評價：",
      data.summary || "",
    ].join("\n");
  }

  async function fetchAnalysis(roundId, playerName) {
    const res = await fetch("/ai_analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        round_id: roundId,
        player_name: playerName || null,
      }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "分析失敗");
    }
    return data;
  }

  function bindWidget(root) {
    const roundId = root.dataset.roundId;
    const btn = root.querySelector(".ai-coach-trigger");
    const panel = root.querySelector(".ai-coach-panel");
    const select = root.querySelector(".ai-coach-player");
    if (!btn || !panel || !roundId) return;

    btn.addEventListener("click", async () => {
      const playerName = select ? select.value : null;
      btn.disabled = true;
      const label = btn.querySelector(".ai-coach-label");
      const prev = label ? label.textContent : "";
      if (label) label.textContent = "分析中…";
      panel.classList.remove("hidden");
      panel.innerHTML = `
        <div class="mt-4 flex items-center justify-center gap-3 rounded-2xl border border-white/10 bg-black/30 py-10 text-sm text-green-200/80">
          <svg class="h-5 w-5 animate-spin text-gold-light" fill="none" viewBox="0 0 24 24" aria-hidden="true">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3 3V4a8 8 0 100 16v-4l-3 3 3-3v-4z"></path>
          </svg>
          AI 教練正在閱讀記分卡…
        </div>`;

      try {
        const data = await fetchAnalysis(roundId, playerName);
        panel.innerHTML = renderAnalysis(data.analysis, data.source);
        const copyBtn = panel.querySelector(".ai-coach-copy");
        if (copyBtn) {
          copyBtn.addEventListener("click", async () => {
            try {
              await navigator.clipboard.writeText(fullText(data.analysis));
              copyBtn.textContent = "已複製 ✓";
              setTimeout(() => {
                copyBtn.textContent = "複製全文";
              }, 2000);
            } catch {
              copyBtn.textContent = "複製失敗";
            }
          });
        }
      } catch (err) {
        panel.innerHTML = `
          <div class="mt-4 rounded-xl border border-red-400/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
            ${escapeHtml(err.message)}
          </div>`;
      } finally {
        btn.disabled = false;
        if (label) label.textContent = prev || "AI 教練分析";
      }
    });
  }

  function init() {
    document.querySelectorAll("[data-ai-coach]").forEach(bindWidget);

    if (new URLSearchParams(window.location.search).get("ai") === "1") {
      const widget = document.querySelector("[data-ai-coach]");
      const trigger = widget?.querySelector(".ai-coach-trigger");
      if (trigger) {
        setTimeout(() => trigger.click(), 500);
      }
    }
    document.querySelectorAll(".ai-coach-trigger-standalone").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const roundId = btn.dataset.roundId;
        const modal = document.getElementById("ai-coach-modal");
        const body = document.getElementById("ai-coach-modal-body");
        if (!modal || !body || !roundId) return;

        modal.classList.remove("hidden");
        modal.classList.add("flex");
        document.body.style.overflow = "hidden";
        body.innerHTML = `
          <div data-ai-coach data-round-id="${escapeHtml(roundId)}" class="ai-coach-inline">
            <button type="button" class="ai-coach-trigger w-full rounded-xl bg-gradient-to-r from-emerald-700 to-fairway px-5 py-3.5 text-sm font-bold text-white shadow-lg ring-2 ring-emerald-400/40">
              <span class="ai-coach-label">開始 AI 教練分析</span>
            </button>
            <div class="ai-coach-panel"></div>
          </div>`;
        const widget = body.querySelector("[data-ai-coach]");
        bindWidget(widget);
        widget.querySelector(".ai-coach-trigger").click();
      });
    });

    const closeBtn = document.getElementById("ai-coach-modal-close");
    const modal = document.getElementById("ai-coach-modal");
    if (closeBtn && modal) {
      const close = () => {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
        document.body.style.overflow = "";
      };
      closeBtn.addEventListener("click", close);
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }
  }

  window.MaisonAICoach = { init, fetchAnalysis, renderAnalysis };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
