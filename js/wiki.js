(() => {
  const track = document.getElementById("banner-track");
  if (!track) return;
  const items = Array.from(track.children);
  if (items.length < 2) return;

  let i = 0;
  const show = (idx) => {
    items.forEach((el, n) => {
      el.hidden = n !== idx;
    });
  };
  show(0);
  setInterval(() => {
    i = (i + 1) % items.length;
    show(i);
  }, 4200);
})();
