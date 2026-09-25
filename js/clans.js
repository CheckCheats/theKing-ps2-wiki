(() => {
  const D = window.CLANS_DATA;
  if (!D) return;

  const rarById = Object.fromEntries(D.rarities.map((r) => [r.id, r]));
  const countByRarity = {};
  for (const c of D.clans) {
    countByRarity[c.rarity] = (countByRarity[c.rarity] || 0) + 1;
  }

  const boolCn = { true: "是", false: "否" };

  const rateGrid = document.getElementById("rate-grid");
  rateGrid.innerHTML = D.rarities
    .map(
      (r) => `
    <div class="rate-card" style="--rc:${r.color}">
      <div class="r-name"><span>${r.cn}</span><span class="r-pct">${r.pct}</span></div>
      <div class="r-en">${r.en}</div>
      <div class="r-count">${countByRarity[r.id] || 0} 个公会</div>
    </div>`
    )
    .join("");

  const spinBody = document.getElementById("spin-body");
  spinBody.innerHTML = D.spin_packages
    .map((p) => {
      const best = p.best ? '<span class="best-tag">超值</span>' : "";
      const name = p.name_cn || p.name;
      return `<tr>
        <td><strong>${name}</strong>${best}</td>
        <td>${p.spins}</td>
        <td>${p.robux} R$</td>
        <td>R$${p.robux_per_spin} / 次</td>
        <td>${p.ore} 矿石</td>
      </tr>`;
    })
    .join("");

  let race = "Demon";
  let selected = 0;
  const swatches = document.getElementById("skin-swatches");
  const big = document.getElementById("skin-big");
  const meta = document.getElementById("skin-meta");

  const rgbCss = (c) => `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
  const rgbHex = (c) =>
    "#" + c.map((n) => n.toString(16).padStart(2, "0")).join("").toUpperCase();

  function renderSkins() {
    const colors = D.skin_colors[race].colors;
    swatches.innerHTML = colors
      .map(
        (c, i) =>
          `<button type="button" class="swatch${i === selected ? " is-on" : ""}" data-i="${i}" style="background:${rgbCss(c)}" aria-label="肤色 ${i + 1}"></button>`
      )
      .join("");
    const c = colors[selected];
    big.style.background = rgbCss(c);
    meta.textContent = `${D.skin_colors[race].label} · #${String(selected + 1).padStart(2, "0")} · ${rgbHex(c)} · RGB(${c.join(", ")})`;
  }

  swatches.addEventListener("click", (e) => {
    const btn = e.target.closest(".swatch");
    if (!btn) return;
    selected = Number(btn.dataset.i);
    renderSkins();
  });

  document.querySelectorAll(".skin-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".skin-tab").forEach((t) => t.classList.remove("is-on"));
      tab.classList.add("is-on");
      race = tab.dataset.race;
      selected = 0;
      renderSkins();
    });
  });
  renderSkins();

  const filters = document.getElementById("clan-filters");
  const list = document.getElementById("clan-list");
  const qInput = document.getElementById("clan-q");
  let activeRarity = "all";

  filters.innerHTML =
    `<button type="button" class="filter-chip is-on" data-r="all">全部</button>` +
    D.rarities
      .map(
        (r) =>
          `<button type="button" class="filter-chip" data-r="${r.id}" style="--fc:${r.color}">${r.cn}</button>`
      )
      .join("");

  filters.addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    activeRarity = chip.dataset.r;
    filters.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("is-on"));
    chip.classList.add("is-on");
    renderClans();
  });

  function formatStatVal(v) {
    const s = String(v).trim();
    if (boolCn[s] != null) return boolCn[s];
    return s;
  }

  function statsHtml(c) {
    const stats = c.stats_cn || c.stats || {};
    const keys = Object.keys(stats);
    if (!keys.length) return '<p class="empty-note">无额外属性加成</p>';
    return keys
      .map((k) => `<p class="stat-row"><b>${k}</b> · ${formatStatVal(stats[k])}</p>`)
      .join("");
  }

  function abilitiesHtml(items, emptyLabel) {
    if (!items || !items.length) return `<p class="empty-note">${emptyLabel}</p>`;
    return items
      .map((a) => {
        const title = a.name_cn || a.name;
        const en = a.name_cn && a.name && a.name_cn !== a.name ? ` <span class="en-name">(${a.name})</span>` : "";
        const cd = a.cooldown != null ? `<span class="cd">冷却 ${a.cooldown}s</span>` : "";
        const mode = a.mode ? '<span class="cd">模式</span>' : "";
        const descText = a.description_cn || a.description || "";
        const desc = descText ? `<div>${descText}</div>` : "";
        return `<div class="ability"><b>${title}</b>${en}${cd}${mode}${desc}</div>`;
      })
      .join("");
  }

  function renderClans() {
    const q = (qInput.value || "").trim().toLowerCase();
    const rows = D.clans.filter((c) => {
      if (activeRarity !== "all" && String(c.rarity) !== String(activeRarity)) return false;
      if (!q) return true;
      const blob = `${c.name} ${c.name_cn} ${c.key} ${c.archetype || ""} ${c.archetype_cn || ""}`.toLowerCase();
      return blob.includes(q);
    });

    list.innerHTML = rows
      .map((c) => {
        const r = rarById[c.rarity] || { cn: "?", color: "#888", en: "" };
        const title = c.name_cn ? `${c.name_cn} · ${c.name}` : c.name;
        const arch = c.archetype_cn || c.archetype || "";
        return `<article class="clan-card" data-key="${c.key}">
          <button type="button" class="clan-head" aria-expanded="false">
            <span class="clan-dot" style="--rc:${r.color}"></span>
            <span class="clan-title"><strong>${title}</strong><span>${r.cn}${arch ? " · " + arch : ""}</span></span>
            <span class="clan-badge" style="--rc:${r.color}">${r.cn} ${r.pct || ""}</span>
          </button>
          <div class="clan-body">
            <h3>属性</h3>
            ${statsHtml(c)}
            <h3>技能</h3>
            ${abilitiesHtml(c.skills, "该公会无主动技能")}
            <h3>被动</h3>
            ${abilitiesHtml(c.passives, "该公会无被动技能")}
          </div>
        </article>`;
      })
      .join("");
  }

  list.addEventListener("click", (e) => {
    const head = e.target.closest(".clan-head");
    if (!head) return;
    const card = head.closest(".clan-card");
    const open = card.classList.toggle("is-open");
    head.setAttribute("aria-expanded", open ? "true" : "false");
  });

  qInput.addEventListener("input", renderClans);
  renderClans();
})();
