(() => {
  const KEY = "ps2-wiki-lang";
  const apply = (lang) => {
    const root = document.documentElement;
    root.lang = lang === "en" ? "en" : "zh-CN";
    root.dataset.lang = lang === "en" ? "en" : "zh";
    document.querySelectorAll("[data-zh][data-en]").forEach((el) => {
      const zh = el.getAttribute("data-zh");
      const en = el.getAttribute("data-en");
      if (lang === "en") {
        if (en != null) el.textContent = en;
      } else if (zh != null) {
        el.textContent = zh;
      }
    });
    document.querySelectorAll(".i18n-zh, .i18n-en").forEach((el) => {
      const isEn = el.classList.contains("i18n-en");
      el.hidden = lang === "en" ? !isEn : isEn;
    });
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.lang === lang);
      btn.setAttribute("aria-pressed", btn.dataset.lang === lang ? "true" : "false");
    });
    try {
      localStorage.setItem(KEY, lang);
    } catch (_) {}
  };

  const ensureToggle = () => {
    let bar = document.querySelector(".lang-switch");
    if (!bar) {
      const host = document.querySelector("header.top");
      if (!host) return null;
      bar = document.createElement("div");
      bar.className = "lang-switch";
      bar.setAttribute("role", "group");
      bar.setAttribute("aria-label", "Language");
      bar.innerHTML =
        '<button type="button" class="lang-btn" data-lang="zh" aria-pressed="true">中文</button>' +
        '<button type="button" class="lang-btn" data-lang="en" aria-pressed="false">EN</button>';
      const ver = host.querySelector(".top-ver");
      if (ver) host.insertBefore(bar, ver);
      else host.appendChild(bar);
    }
    bar.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.addEventListener("click", () => apply(btn.dataset.lang));
    });
    return bar;
  };

  const boot = () => {
    ensureToggle();
    let lang = "zh";
    try {
      lang = localStorage.getItem(KEY) || "zh";
    } catch (_) {}
    apply(lang === "en" ? "en" : "zh");
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
