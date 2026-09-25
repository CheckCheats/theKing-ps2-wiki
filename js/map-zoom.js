(() => {
  const stage = document.getElementById("map-stage");
  const viewport = document.getElementById("map-viewport");
  const img = document.getElementById("map-img");
  const lbl = document.getElementById("map-zoom-label");
  const btnIn = document.getElementById("map-zoom-in");
  const btnOut = document.getElementById("map-zoom-out");
  const btnReset = document.getElementById("map-zoom-reset");
  if (!stage || !viewport || !img) return;

  const MIN = 1;
  const MAX = 8;
  const STEP = 0.2;

  let scale = 1;
  let tx = 0;
  let ty = 0;
  let baseW = 0;
  let baseH = 0;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let pointers = new Map();
  let pinchStartDist = 0;
  let pinchStartScale = 1;

  function measure() {
    const sw = stage.clientWidth;
    const sh = stage.clientHeight;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;
    if (!nw || !sw || !sh) return;
    const fit = Math.min(sw / nw, sh / nh);
    baseW = nw * fit;
    baseH = nh * fit;
    viewport.style.width = `${baseW}px`;
    viewport.style.height = `${baseH}px`;
    clamp();
    apply();
  }

  function clamp() {
    if (!baseW) return;
    const sw = stage.clientWidth;
    const sh = stage.clientHeight;
    const halfW = (baseW * scale) / 2;
    const halfH = (baseH * scale) / 2;
    // keep map covering stage center; allow edge peek with small slack
    const maxX = Math.max(0, halfW - sw / 2 + 8);
    const maxY = Math.max(0, halfH - sh / 2 + 8);
    tx = Math.max(-maxX, Math.min(maxX, tx));
    ty = Math.max(-maxY, Math.min(maxY, ty));
  }

  function apply() {
    viewport.style.transform = `translate(calc(-50% + ${tx}px), calc(-50% + ${ty}px)) scale(${scale})`;
    stage.classList.toggle("is-zoomed", scale > 1.01);
    stage.style.cursor = dragging ? "grabbing" : scale > 1.01 ? "grab" : "default";
    if (lbl) lbl.textContent = `${Math.round(scale * 100)}%`;
  }

  function zoomAt(clientX, clientY, nextScale) {
    const rect = stage.getBoundingClientRect();
    const cx = clientX - rect.left - rect.width / 2;
    const cy = clientY - rect.top - rect.height / 2;
    const prev = scale;
    scale = Math.max(MIN, Math.min(MAX, nextScale));
    if (Math.abs(scale - prev) < 1e-6) return;
    const k = scale / prev;
    tx = cx - (cx - tx) * k;
    ty = cy - (cy - ty) * k;
    if (scale <= 1.001) {
      scale = 1;
      tx = 0;
      ty = 0;
    }
    clamp();
    apply();
  }

  function reset() {
    scale = 1;
    tx = 0;
    ty = 0;
    apply();
  }

  function centerPoint() {
    const r = stage.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }

  img.addEventListener("load", measure);
  if (img.complete && img.naturalWidth) measure();
  window.addEventListener("resize", measure);

  stage.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      const dir = e.deltaY < 0 ? 1 : -1;
      zoomAt(e.clientX, e.clientY, scale * (1 + dir * STEP));
    },
    { passive: false }
  );

  stage.addEventListener("pointerdown", (e) => {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    stage.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    if (pointers.size === 2) {
      const pts = [...pointers.values()];
      pinchStartDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
      pinchStartScale = scale;
      dragging = false;
      return;
    }

    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
    apply();
  });

  stage.addEventListener("pointermove", (e) => {
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

    if (pointers.size === 2) {
      const pts = [...pointers.values()];
      const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
      if (pinchStartDist > 0) {
        const midX = (pts[0].x + pts[1].x) / 2;
        const midY = (pts[0].y + pts[1].y) / 2;
        zoomAt(midX, midY, pinchStartScale * (dist / pinchStartDist));
      }
      return;
    }

    if (!dragging) return;
    const dx = e.clientX - lastX;
    const dy = e.clientY - lastY;
    lastX = e.clientX;
    lastY = e.clientY;
    tx += dx;
    ty += dy;
    clamp();
    apply();
  });

  function endPointer(e) {
    if (!pointers.has(e.pointerId)) return;
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinchStartDist = 0;
    if (pointers.size === 0) {
      dragging = false;
      apply();
    } else if (pointers.size === 1) {
      const remaining = [...pointers.values()][0];
      lastX = remaining.x;
      lastY = remaining.y;
      dragging = true;
    }
  }

  stage.addEventListener("pointerup", endPointer);
  stage.addEventListener("pointercancel", endPointer);

  stage.addEventListener("dragstart", (e) => e.preventDefault());
  stage.addEventListener("dblclick", (e) => {
    e.preventDefault();
    if (scale > 1.05) reset();
    else zoomAt(e.clientX, e.clientY, 2.8);
  });

  btnIn?.addEventListener("click", () => {
    const c = centerPoint();
    zoomAt(c.x, c.y, scale * (1 + STEP * 1.5));
  });
  btnOut?.addEventListener("click", () => {
    const c = centerPoint();
    zoomAt(c.x, c.y, scale / (1 + STEP * 1.5));
  });
  btnReset?.addEventListener("click", reset);
})();
