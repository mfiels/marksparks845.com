// Brand lockup: fine-tune the M⚡S mark, amber rule, and trades line so all four rows share the
// name's exact painted edges. CSS gets them within a few pixels; browsers round glyph positions
// at some sizes, so this measures the rendered text and corrects the remainder. Corrections are
// transforms only, so they never reflow the page, and run before first paint when Inter is
// already loaded (it's preloaded in the page head).
(function () {
  const wrap = document.querySelector(".hero-text");
  const name = wrap && wrap.querySelector("h1");
  const rule = wrap && wrap.querySelector(".brand-rule");
  const trades = wrap && wrap.querySelector(".trades");
  const mark = wrap && wrap.querySelector(".brand-mark");
  if (!name || !rule || !trades) return;
  const canvas = document.createElement("canvas").getContext("2d");

  // Painted horizontal extent of an element's text, relative to the wrapper's left edge.
  function ink(el) {
    const cs = getComputedStyle(el), ls = parseFloat(cs.letterSpacing) || 0;
    const r = document.createRange();
    r.selectNodeContents(el);
    const box = r.getBoundingClientRect(), x0 = box.left - wrap.getBoundingClientRect().left;
    canvas.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    canvas.letterSpacing = cs.letterSpacing;
    const m = canvas.measureText(el.textContent.toUpperCase());
    const bearL = -m.actualBoundingBoxLeft, bearR = m.width - ls - m.actualBoundingBoxRight;
    return { left: x0 + bearL, right: x0 + box.width - ls - bearR };
  }

  // Scale el about its left edge so the painted span [left, right] lands on [x0, x0 + width].
  function align(el, left, right, x0, width, uniform) {
    const k = width / (right - left);
    const edge = el.getBoundingClientRect().left - wrap.getBoundingClientRect().left;
    el.style.transformOrigin = "0 0";
    el.style.transform = `translateX(${x0 - edge - (left - edge) * k}px) ${uniform ? "scale" : "scaleX"}(${k})`;
  }

  function fit() {
    for (const el of [mark, rule, trades]) if (el) el.style.transform = "";
    const n = ink(name), target = n.right - n.left, wx = wrap.getBoundingClientRect().left;
    for (const el of [mark, rule]) {
      if (!el) continue;
      const b = el.getBoundingClientRect();
      align(el, b.left - wx, b.right - wx, n.left, target, el === mark);
    }
    const t = ink(trades);
    align(trades, t.left, t.right, n.left, target, false);
  }

  const weight = getComputedStyle(name).fontWeight;
  if (document.fonts.check(`${weight} 16px Inter`)) fit();
  document.fonts.ready.then(() => {
    fit();
    new ResizeObserver(fit).observe(wrap);
  });
})();

// Photos from window.GALLERY (gallery.js): a carousel in the hero, an optional grid
// further down, and a shared full-screen lightbox.
(function () {
  const photos = window.GALLERY || [];
  const label = (p) => [p.caption, p.town && `${p.town}, NY`].filter(Boolean).join(", ");
  const carousel = document.getElementById("carousel");

  if (!photos.length) {
    carousel.hidden = true;
    document.getElementById("work").hidden = true;
    return;
  }

  const preload = (i) => (new Image().src = photos[(i + photos.length) % photos.length].full);

  // ---- Lightbox ----
  const box = document.getElementById("lightbox");
  const boxImg = document.getElementById("lb-img");
  const boxCap = document.getElementById("lb-cap");
  let lbIndex = 0;

  function lbShow(i) {
    lbIndex = (i + photos.length) % photos.length;
    const p = photos[lbIndex];
    boxImg.src = p.full;
    boxImg.alt = label(p);
    boxCap.textContent = label(p);
    preload(lbIndex + 1);
  }
  function lbOpen(i) {
    lbShow(i);
    box.showModal();
  }

  box.addEventListener("click", (e) => {
    const action = e.target.dataset.lb;
    if (action === "close" || e.target === box) box.close();
    else if (action === "prev") lbShow(lbIndex - 1);
    else if (action === "next") lbShow(lbIndex + 1);
  });
  box.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") lbShow(lbIndex - 1);
    if (e.key === "ArrowRight") lbShow(lbIndex + 1);
  });
  // Leave the carousel on whatever photo was last viewed full-size.
  box.addEventListener("close", () => carShow(lbIndex));

  // ---- Swipe (carousel and lightbox) ----
  function onSwipe(el, fn) {
    let x = null;
    el.addEventListener("touchstart", (e) => (x = e.touches[0].clientX), { passive: true });
    el.addEventListener("touchend", (e) => {
      if (x === null) return;
      const dx = e.changedTouches[0].clientX - x;
      if (Math.abs(dx) > 50) fn(dx < 0 ? 1 : -1);
      x = null;
    });
  }
  onSwipe(box, (d) => lbShow(lbIndex + d));

  // ---- Carousel ----
  const carImg = document.getElementById("car-img");
  const carCap = document.getElementById("car-cap");
  const carCount = document.getElementById("car-count");
  let carIndex = -1;

  function carShow(i) {
    i = (i + photos.length) % photos.length;
    if (i === carIndex) return;
    carIndex = i;
    const p = photos[i];
    carImg.classList.add("fading");
    carImg.onload = () => carImg.classList.remove("fading");
    carImg.srcset = `${p.thumb} 800w, ${p.full} 2000w`;
    carImg.src = p.thumb;
    carImg.alt = label(p);
    // Portraits would lose their top and bottom in the landscape frame; show them whole.
    carImg.classList.toggle("portrait", p.h > p.w);
    carCap.textContent = label(p);
    carCount.textContent = `${i + 1} / ${photos.length}`;
    preload(i + 1);
  }

  const single = photos.length < 2;
  document.getElementById("car-prev").hidden = single;
  document.getElementById("car-next").hidden = single;
  if (single) carCount.hidden = true;

  document.getElementById("car-prev").addEventListener("click", () => carShow(carIndex - 1));
  document.getElementById("car-next").addEventListener("click", () => carShow(carIndex + 1));
  document.getElementById("car-open").addEventListener("click", () => lbOpen(carIndex));
  carousel.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") carShow(carIndex - 1);
    if (e.key === "ArrowRight") carShow(carIndex + 1);
  });
  onSwipe(carousel, (d) => carShow(carIndex + d));
  carShow(0);

  // ---- Grid (only when the #work section isn't hidden) ----
  const section = document.getElementById("work");
  if (section.hidden) return;

  const PAGE = 12;
  const grid = document.getElementById("gallery");
  const sentinel = document.getElementById("gallery-sentinel");
  let shown = 0;

  function renderNext() {
    photos.slice(shown, shown + PAGE).forEach((p, j) => {
      const idx = shown + j;
      const tile = document.createElement("button");
      tile.className = "tile";
      tile.type = "button";
      tile.setAttribute("aria-label", `View photo: ${label(p) || "project photo"}`);

      const img = document.createElement("img");
      img.src = p.thumb;
      img.alt = label(p);
      img.loading = "lazy";
      img.decoding = "async";
      img.width = p.w;
      img.height = p.h;
      img.addEventListener("load", () => img.classList.add("loaded"), { once: true });
      tile.appendChild(img);

      if (p.caption) {
        const cap = document.createElement("span");
        cap.className = "tile-cap";
        cap.textContent = p.caption;
        if (p.town) {
          const town = document.createElement("span");
          town.textContent = p.town;
          cap.appendChild(town);
        }
        tile.appendChild(cap);
      }

      tile.addEventListener("click", () => lbOpen(idx));
      grid.appendChild(tile);
    });
    shown = Math.min(shown + PAGE, photos.length);
    if (shown >= photos.length) observer.disconnect();
  }

  const observer = new IntersectionObserver(
    (entries) => entries.some((e) => e.isIntersecting) && renderNext(),
    { rootMargin: "600px 0px" }
  );
  renderNext();
  if (shown < photos.length) observer.observe(sentinel);
})();

document.getElementById("year").textContent = new Date().getFullYear();
