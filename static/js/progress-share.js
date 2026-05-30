/* Maison Golf — 分享「我的進步」差點曲線圖卡（純前端 canvas · 免上傳） */
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
    const modal = document.getElementById("progress-share-modal");
    const dataEl = document.getElementById("progress-share-data");
    const canvas = document.getElementById("progress-card-canvas");
    const openBtn = document.getElementById("progress-share-open");
    const closeBtn = document.getElementById("progress-share-close");
    const download = document.getElementById("progress-card-download");
    const sizeGroup = document.getElementById("progress-card-size-group");
    if (!modal || !dataEl || !canvas) return;

    let data;
    try {
      data = JSON.parse(dataEl.textContent);
    } catch (e) {
      return;
    }

    const SIZES = { xhs: [1080, 1440], story: [1080, 1920], square: [1080, 1080] };
    let currentSize = "xhs";
    let fontsReady = false;

    function open() {
      modal.classList.remove("hidden");
      modal.classList.add("flex");
      document.body.style.overflow = "hidden";
      render();
    }
    function close() {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
      document.body.style.overflow = "";
    }

    openBtn?.addEventListener("click", open);
    closeBtn?.addEventListener("click", close);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) close();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !modal.classList.contains("hidden")) close();
    });

    sizeGroup?.querySelectorAll(".progress-size-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentSize = btn.dataset.cardSize || "xhs";
        sizeGroup.querySelectorAll(".progress-size-btn").forEach((b) => {
          const active = b === btn;
          b.classList.toggle("border-champ/50", active);
          b.classList.toggle("bg-champ/20", active);
          b.classList.toggle("text-champ-light", active);
          b.classList.toggle("font-bold", active);
          b.classList.toggle("border-white/15", !active);
          b.classList.toggle("bg-white/5", !active);
          b.classList.toggle("text-green-200/80", !active);
          b.classList.toggle("font-semibold", !active);
        });
        render();
      });
    });

    async function ensureFonts() {
      if (fontsReady) return;
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
        /* fallback to system fonts */
      }
      fontsReady = true;
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

    async function render() {
      await ensureFonts();
      const [W, H] = SIZES[currentSize] || SIZES.xhs;
      canvas.width = W;
      canvas.height = H;
      const ctx = canvas.getContext("2d");
      const cx = W / 2;

      // 背景
      const bg = ctx.createLinearGradient(0, 0, 0, H);
      bg.addColorStop(0, "#0c2418");
      bg.addColorStop(0.55, "#0a1c12");
      bg.addColorStop(1, "#06120b");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);
      const glow = ctx.createRadialGradient(cx, H * 0.2, 40, cx, H * 0.2, W * 0.85);
      glow.addColorStop(0, "rgba(217,183,140,0.22)");
      glow.addColorStop(1, "rgba(217,183,140,0)");
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, W, H);
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
      ctx.letterSpacing = "6px";
      ctx.fillText("MAISON GOLF · 我的進步", cx, 128);
      ctx.restore();

      // 差點指數標籤
      ctx.fillStyle = "rgba(246,231,197,0.7)";
      ctx.font = '600 34px "Noto Sans TC", sans-serif';
      ctx.fillText("差點指數 Handicap Index", cx, 208);

      // 大數字
      const hasIndex = data.index !== null && data.index !== undefined;
      ctx.font = '700 240px "Playfair Display", "Noto Serif TC", serif';
      const numGrad = ctx.createLinearGradient(0, 240, 0, 470);
      numGrad.addColorStop(0, "#f6e7c5");
      numGrad.addColorStop(1, "#d9b78c");
      ctx.fillStyle = hasIndex ? numGrad : "rgba(255,255,255,0.3)";
      ctx.textBaseline = "middle";
      const numText = hasIndex ? Number(data.index).toFixed(1) : "?";
      ctx.fillText(numText, cx, 350);
      ctx.textBaseline = "alphabetic";

      // 進步幅度徽章
      if (hasIndex && data.delta !== null && data.delta !== undefined && data.delta !== 0) {
        const improving = data.improving;
        const dtxt = (improving ? "▼ " : "▲ ") + Math.abs(data.delta).toFixed(1);
        ctx.font = '700 36px "Noto Sans TC", sans-serif';
        const bw = ctx.measureText(dtxt).width + 56;
        const bh = 64;
        const by = 460;
        ctx.fillStyle = improving ? "rgba(34,197,94,0.2)" : "rgba(234,179,8,0.16)";
        roundRect(ctx, cx - bw / 2, by, bw, bh, bh / 2);
        ctx.fill();
        ctx.fillStyle = improving ? "#86efac" : "#fcd34d";
        ctx.textBaseline = "middle";
        ctx.fillText(dtxt, cx, by + bh / 2 + 1);
        ctx.textBaseline = "alphabetic";
      }

      // 副標
      ctx.fillStyle = "rgba(200,224,210,0.65)";
      ctx.font = '400 30px "Noto Sans TC", sans-serif';
      const subtitle = hasIndex
        ? `依最佳 ${data.index_used} 場成績 · 數字越低越強`
        : `再 ${data.rounds_needed} 場（共需 ${data.min_rounds} 場）即可解鎖`;
      ctx.fillText(subtitle, cx, 565);

      const topBlockBottom = 600;
      const footerTop = H - 180;

      // —— 成長曲線 ——
      const pts = (data.points || []).map((p) => ({
        v: typeof p.to_par === "number" ? p.to_par : 0,
        date: p.date || "",
        total: p.total,
        best: !!p.is_best,
      }));

      // 數據列（在頁腳上方）
      const statsCenterY = footerTop - 70;
      const chartTop = topBlockBottom + 30;
      const chartBottom = statsCenterY - 120;

      if (pts.length) {
        ctx.fillStyle = "rgba(246,231,197,0.7)";
        ctx.font = '600 28px "Noto Sans TC", sans-serif';
        ctx.fillText("成長曲線 · 相對標準桿（越高越好）", cx, chartTop + 6);

        const bx0 = 110;
        const bx1 = W - 110;
        const by0 = chartTop + 50;
        const by1 = chartBottom;
        const vals = pts.map((p) => p.v);
        const vmin = Math.min(...vals);
        const vmax = Math.max(...vals);
        const span = vmax - vmin || 1;
        const n = pts.length;
        const xOf = (i) => (n === 1 ? (bx0 + bx1) / 2 : bx0 + (i * (bx1 - bx0)) / (n - 1));
        const yOf = (v) => by0 + ((v - vmin) / span) * (by1 - by0);

        // 標準桿線
        if (vmin <= 0 && 0 <= vmax) {
          const py = yOf(0);
          ctx.strokeStyle = "rgba(255,255,255,0.18)";
          ctx.lineWidth = 2;
          ctx.setLineDash([10, 10]);
          ctx.beginPath();
          ctx.moveTo(bx0, py);
          ctx.lineTo(bx1, py);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = "rgba(255,255,255,0.4)";
          ctx.font = '400 24px "Noto Sans TC", sans-serif';
          ctx.textAlign = "left";
          ctx.fillText("E", bx0, py - 10);
          ctx.textAlign = "center";
        }

        // 面積
        const coords = pts.map((p, i) => [xOf(i), yOf(p.v)]);
        const areaGrad = ctx.createLinearGradient(0, by0, 0, by1);
        areaGrad.addColorStop(0, "rgba(217,183,140,0.35)");
        areaGrad.addColorStop(1, "rgba(217,183,140,0)");
        ctx.beginPath();
        ctx.moveTo(coords[0][0], coords[0][1]);
        coords.forEach(([x, y]) => ctx.lineTo(x, y));
        ctx.lineTo(coords[coords.length - 1][0], by1);
        ctx.lineTo(coords[0][0], by1);
        ctx.closePath();
        ctx.fillStyle = areaGrad;
        ctx.fill();

        // 線
        const lineGrad = ctx.createLinearGradient(bx0, 0, bx1, 0);
        lineGrad.addColorStop(0, "#f6e7c5");
        lineGrad.addColorStop(1, "#d9b78c");
        ctx.strokeStyle = lineGrad;
        ctx.lineWidth = 6;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        ctx.beginPath();
        coords.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
        ctx.stroke();

        // 點
        coords.forEach(([x, y], i) => {
          ctx.beginPath();
          ctx.arc(x, y, pts[i].best ? 16 : 11, 0, Math.PI * 2);
          ctx.fillStyle = pts[i].best ? "#f6e7c5" : "#0a1c12";
          ctx.fill();
          ctx.lineWidth = 5;
          ctx.strokeStyle = pts[i].best ? "#eab308" : "#d9b78c";
          ctx.stroke();
        });
      }

      // —— 數據列 ——
      const cols = [
        { label: "總場次", value: String(data.total_rounds) },
        { label: "平均總桿", value: String(data.avg_total) },
        { label: "最佳總桿", value: String(data.best_total) },
      ];
      const colX = [cx - 320, cx, cx + 320];
      cols.forEach((c, i) => {
        ctx.fillStyle = "#ffffff";
        ctx.font = '700 60px "Noto Sans TC", sans-serif';
        ctx.fillText(c.value, colX[i], statsCenterY);
        ctx.fillStyle = "rgba(246,231,197,0.6)";
        ctx.font = '600 28px "Noto Sans TC", sans-serif';
        ctx.fillText(c.label, colX[i], statsCenterY + 50);
      });

      // —— 頁腳 ——
      ctx.fillStyle = "rgba(246,231,197,0.95)";
      ctx.font = '700 46px "Playfair Display", "Noto Serif TC", serif';
      ctx.fillText("Maison Golf", cx, H - 110);
      ctx.fillStyle = "rgba(200,224,210,0.55)";
      ctx.font = '400 28px "Noto Sans TC", sans-serif';
      const foot = hasIndex
        ? `${data.player_name} · 差點 ${Number(data.index).toFixed(1)}`
        : `${data.player_name} · 高爾夫隨身球僮`;
      ctx.fillText(foot, cx, H - 64);

      // 下載
      try {
        canvas.toBlob((blob) => {
          if (!blob || !download) return;
          if (download._url) URL.revokeObjectURL(download._url);
          const url = URL.createObjectURL(blob);
          download._url = url;
          download.href = url;
          download.download = `maison-golf-progress-${currentSize}.png`;
        }, "image/png");
      } catch (e) {
        /* 長按圖片仍可儲存 */
      }
    }
  });
})();
