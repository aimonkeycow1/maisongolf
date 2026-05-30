/* Maison Golf — 慶祝彈窗 + 輕量 canvas 彩帶（無外部套件）
   觸發：頁面存在 #celebrate-modal 時自動開啟並灑彩帶。
   尊重 prefers-reduced-motion（不灑彩帶，但仍顯示彈窗）。 */
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    const modal = document.getElementById("celebrate-modal");
    if (!modal) return;

    const reduce =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function close() {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
      // 清掉網址上的 celebrate，避免重整再次彈出
      try {
        const url = new URL(window.location.href);
        url.searchParams.delete("celebrate");
        window.history.replaceState({}, "", url);
      } catch (e) {}
    }

    modal.querySelectorAll("[data-celebrate-close]").forEach((el) => {
      el.addEventListener("click", (e) => {
        if (e.target === el || el.hasAttribute("data-celebrate-close-btn")) close();
      });
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });

    // 顯示
    modal.classList.remove("hidden");
    modal.classList.add("flex");

    if (!reduce) confetti(2600);
  });

  function confetti(durationMs) {
    const canvas = document.createElement("canvas");
    canvas.style.cssText =
      "position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:120";
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");
    let W = (canvas.width = window.innerWidth);
    let H = (canvas.height = window.innerHeight);
    const onResize = () => {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", onResize);

    const colors = ["#d9b78c", "#f6e7c5", "#eab308", "#22c55e", "#e3b7a0", "#ffffff"];
    const N = 150;
    const parts = [];
    for (let i = 0; i < N; i++) {
      parts.push({
        x: Math.random() * W,
        y: -20 - Math.random() * H * 0.5,
        w: 6 + Math.random() * 6,
        h: 8 + Math.random() * 8,
        c: colors[(Math.random() * colors.length) | 0],
        vy: 2 + Math.random() * 3.5,
        vx: -1.5 + Math.random() * 3,
        rot: Math.random() * Math.PI,
        vr: -0.2 + Math.random() * 0.4,
      });
    }

    const start = performance.now();
    function frame(now) {
      const t = now - start;
      ctx.clearRect(0, 0, W, H);
      parts.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        p.rot += p.vr;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.c;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      });
      // 後段淡出
      if (t > durationMs) {
        canvas.style.transition = "opacity .6s";
        canvas.style.opacity = "0";
      }
      if (t < durationMs + 700) {
        requestAnimationFrame(frame);
      } else {
        window.removeEventListener("resize", onResize);
        canvas.remove();
      }
    }
    requestAnimationFrame(frame);
  }

  // 供其他模組呼叫（progress 成就彈窗等）
  window.MaisonConfetti = confetti;
})();
