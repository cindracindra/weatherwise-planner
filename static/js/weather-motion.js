/*
 * Weather motion for the home page hero.
 *
 * The hero icon carries data-sky="rain|snow|cloudy|clear". Rain and snow fall
 * from the cloud on a canvas; a cursor passing over the hero is a gust of
 * wind in the direction it moves, which slants the rain (or blows the snow)
 * and nudges the icon, then dies away. Clear and cloudy only get the nudge.
 *
 * Runs only while the hero is on screen and the tab is visible. Under
 * prefers-reduced-motion it draws one still frame and does not move.
 */
(() => {
  const glyph = document.querySelector("[data-sky]");
  if (!glyph) return;
  const sky = glyph.dataset.sky;
  const icon = glyph.querySelector(".icon");
  const zone = glyph.closest("[data-wind-zone]") || glyph;
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Wind is horizontal speed in px per frame at 60fps. A gust sets the target;
  // the target dies away and the wind follows it smoothly.
  let wind = 0, gust = 0;
  const MAX_GUST = 2;

  let canvas = null, ctx = null, drops = [], w = 0, h = 0, top = 0, colour = "#2f80ff";
  const falling = sky === "rain" || sky === "snow";

  function size() {
    const r = glyph.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    w = r.width * 1.5;
    h = r.height * 1.35;
    top = r.height * 0.8; // the cloud's bottom edge
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function spawn(d, anywhere) {
    // Drops start at the cloud's bottom edge, across its width.
    const iw = w / 1.5;
    d.x = (w - iw) / 2 + iw * (0.22 + Math.random() * 0.56);
    d.y = anywhere ? top + Math.random() * (h - top) : top;
    d.v = sky === "snow" ? 0.45 + Math.random() * 0.3 : 1.3 + Math.random() * 0.7;
    d.len = sky === "snow" ? 0 : 5 + Math.random() * 4;
    d.a = 0.22 + Math.random() * 0.33;
    d.phase = Math.random() * Math.PI * 2;
    return d;
  }

  if (falling) {
    canvas = document.createElement("canvas");
    canvas.className = "today__weather-canvas";
    canvas.setAttribute("aria-hidden", "true");
    glyph.appendChild(canvas);
    ctx = canvas.getContext("2d");
    colour = getComputedStyle(glyph).color || colour;
    size();
    drops = Array.from({ length: sky === "snow" ? 16 : 18 }, () => spawn({}, true));
    window.addEventListener("resize", size);
  }

  function drawDrops(dt) {
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = colour;
    ctx.fillStyle = colour;
    ctx.lineCap = "round";
    ctx.lineWidth = 1.25;
    for (const d of drops) {
      if (dt) {
        d.phase += 0.05 * dt;
        const sway = sky === "snow" ? Math.sin(d.phase) * 0.4 : 0;
        d.x += (wind * (sky === "snow" ? 1.2 : 0.8) + sway) * dt;
        d.y += d.v * dt;
        if (d.y > h || d.x < -10 || d.x > w + 10) spawn(d, false);
      }
      // Fade in under the cloud and out near the bottom
      const t = (d.y - top) / (h - top);
      ctx.globalAlpha = d.a * Math.min(1, t * 4) * Math.min(1, (1 - t) * 3);
      if (sky === "snow") {
        ctx.beginPath();
        ctx.arc(d.x, d.y, 1.8, 0, Math.PI * 2);
        ctx.fill();
      } else {
        // The streak lies along the drop's velocity, so wind slants it
        const k = d.len / Math.hypot(wind * 0.8, d.v);
        ctx.beginPath();
        ctx.moveTo(d.x, d.y);
        ctx.lineTo(d.x - wind * 0.8 * k, d.y - d.v * k);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  }

  function nudge() {
    if (!icon) return;
    const turn = sky === "clear" ? wind * 2.5 : wind * 1;
    const shift = sky === "clear" ? 0 : wind * 1.5;
    icon.style.transform = `translateX(${shift.toFixed(2)}px) rotate(${turn.toFixed(2)}deg)`;
  }

  if (still) {
    if (falling) drawDrops(0);
    return;
  }

  let lastX = null, lastT = 0;
  zone.addEventListener("pointermove", (e) => {
    if (e.pointerType === "touch") return;
    const now = performance.now();
    if (lastX !== null && now - lastT < 100) {
      const speed = (e.clientX - lastX) / Math.max(8, now - lastT); // px per ms
      gust = Math.max(-MAX_GUST, Math.min(MAX_GUST, gust + speed * 1.2));
    }
    lastX = e.clientX;
    lastT = now;
    wake();
  });
  zone.addEventListener("pointerleave", () => { lastX = null; });

  let running = false, visible = true, prev = 0;
  function frame(now) {
    const dt = Math.min(3, (now - prev) / 16.67);
    prev = now;
    gust *= Math.pow(0.97, dt);
    wind += (gust - wind) * Math.min(1, 0.04 * dt);
    if (falling) drawDrops(dt);
    nudge();
    const settled = Math.abs(gust) < 0.01 && Math.abs(wind) < 0.01;
    if (visible && !document.hidden && (falling || !settled)) {
      requestAnimationFrame(frame);
    } else {
      running = false;
      if (settled) { wind = 0; gust = 0; nudge(); }
    }
  }
  function wake() {
    if (running || !visible || document.hidden) return;
    running = true;
    prev = performance.now();
    requestAnimationFrame(frame);
  }

  new IntersectionObserver((entries) => {
    visible = entries[0].isIntersecting;
    if (visible) wake();
  }).observe(glyph);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) wake(); });
  if (falling) wake();
})();
