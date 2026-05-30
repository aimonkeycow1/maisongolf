/* Maison Golf — 微互動引擎（漸進增強，無 JS 也能正常顯示）
   1) 進場揭示：.reveal → 進入視窗時加 .in
   2) 數字 count-up：[data-countup] 從 0 滾到最終值
   3) 等級環填充：[data-ring] 由 0 動畫到目標百分比
   尊重 prefers-reduced-motion。 */
(function () {
  "use strict";
  const reduce =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- 進場揭示 + 觸發內部動畫 ---- */
  function fireExtras(el) {
    el.querySelectorAll("[data-countup]").forEach(countUp);
    el.querySelectorAll("[data-ring]").forEach(fillRing);
  }

  function setupReveal() {
    const items = Array.from(document.querySelectorAll(".reveal"));
    if (!items.length) return;

    if (reduce || !("IntersectionObserver" in window)) {
      items.forEach((el) => {
        el.classList.add("in");
        fireExtras(el);
      });
      return;
    }

    let stagger = 0;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          io.unobserve(el);
          el.classList.add("in");
          fireExtras(el);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );

    items.forEach((el) => {
      if (!el.style.getPropertyValue("--reveal-delay")) {
        el.style.setProperty("--reveal-delay", Math.min(stagger, 360) + "ms");
        stagger += 80;
      }
      io.observe(el);
    });
  }

  /* ---- 數字 count-up ---- */
  function countUp(el) {
    if (el.dataset.done) return;
    el.dataset.done = "1";
    const target = parseFloat(el.dataset.countup);
    if (isNaN(target)) return;
    const decimals = (el.dataset.countup.split(".")[1] || "").length;
    const prefix = el.dataset.prefix || "";
    const suffix = el.dataset.suffix || "";
    if (reduce) {
      el.textContent = prefix + target.toFixed(decimals) + suffix;
      return;
    }
    const dur = 1100;
    const start = performance.now();
    el.classList.add("counting");
    function tick(now) {
      const t = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - t, 3);
      const val = target * eased;
      el.textContent = prefix + val.toFixed(decimals) + suffix;
      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = prefix + target.toFixed(decimals) + suffix;
        el.classList.remove("counting");
      }
    }
    requestAnimationFrame(tick);
  }

  /* ---- 等級環填充 ---- */
  function fillRing(el) {
    if (el.dataset.done) return;
    el.dataset.done = "1";
    const pct = Math.max(0, Math.min(100, parseFloat(el.dataset.ring) || 0));
    requestAnimationFrame(() => {
      el.setAttribute("stroke-dasharray", pct + " 100");
    });
  }

  function init() {
    setupReveal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
