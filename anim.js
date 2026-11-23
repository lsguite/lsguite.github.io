const $ = (s) => document.querySelector(s);
// Hero animation: drifting network. Replace with your own GIF/video if you prefer.
const cv = $("#stage");
if (cv) {
  const ctx = cv.getContext("2d"), still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let W, H, pts = [], mouse = { x: -999, y: -999 }, run = true;
  const size = () => {
    const r = cv.getBoundingClientRect(), d = devicePixelRatio || 1;
    W = r.width; H = r.height; cv.width = W * d; cv.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0);
    pts = Array.from({ length: Math.round(W * H / 5500) }, () => ({
      x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .4, vy: (Math.random() - .5) * .4 }));
  };
  const frame = () => {
    ctx.clearRect(0, 0, W, H);
    for (const p of pts) {
      const dx = p.x - mouse.x, dy = p.y - mouse.y, d2 = dx * dx + dy * dy;
      if (d2 < 6400) { p.vx += dx / 900; p.vy += dy / 900; }
      p.vx *= .99; p.vy *= .99; p.x += p.vx + (Math.random() - .5) * .05; p.y += p.vy + (Math.random() - .5) * .05;
      if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1;
    }
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y, d = dx * dx + dy * dy;
        if (d < 4900) { ctx.strokeStyle = `rgba(120,215,225,${(1 - d / 4900) * .55})`; ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke(); }
      }
      ctx.fillStyle = "#bff3f7"; ctx.beginPath(); ctx.arc(pts[i].x, pts[i].y, 1.8, 0, 7); ctx.fill();
    }
    if (run && !still) requestAnimationFrame(frame);
  };
  cv.addEventListener("pointermove", e => { const r = cv.getBoundingClientRect(); mouse = { x: e.clientX - r.left, y: e.clientY - r.top }; });
  cv.addEventListener("pointerleave", () => mouse = { x: -999, y: -999 });
  new IntersectionObserver(([e]) => { const was = run; run = e.isIntersecting; if (run && !was) frame(); }).observe(cv);
  addEventListener("resize", size); size(); frame();
}
