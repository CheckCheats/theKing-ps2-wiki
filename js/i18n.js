(() => {
  const KEY = "ps2-wiki-lang";
  const CSS_VER = "20260926u";

  /** Exact / common UI phrase map ZH → EN */
  const DICT = {
    "主页": "Home",
    "返回主页": "Back to home",
    "基础知识": "Basics",
    "进阶内容": "Advanced",
    "常用入口": "Shortcuts",
    "站点更新": "Changelog",
    "区域": "Regions",
    "重生水晶": "Spawn Crystals",
    "NPC 任务": "NPC Quests",
    "操控": "Controls",
    "界面加成": "HUD Buffs",
    "等级 / 精通": "Levels / Mastery",
    "组队 / 猎杀": "Party / Hunts",
    "技能树": "Skill Tree",
    "标题 / 称号": "Titles",
    "派系": "Factions",
    "阵营 / 声望": "Sides / Reputation",
    "公会 / 肤色": "Clans / Skins",
    "呼吸法": "Breathings",
    "邪恶艺术": "Evil Arts",
    "怪物": "Monsters",
    "Boss 掉落": "Boss Drops",
    "图纸": "Schematics",
    "商店价目": "Shop Prices",
    "货币": "Currency",
    "黑商": "Black Market",
    "锻造 / 爬塔": "Forge / Tower",
    "档案": "Archive",
    "道具 / 药水": "Items / Potions",
    "锻炼": "Training",
    "钓鱼": "Fishing",
    "神庙": "Temples",
    "坐骑": "Mounts",
    "重要地点": "Key Locations",
    "技能树全图": "Skill Tree Map",
    "战斗风格": "Fighting Styles",
    "精炼": "Refinement",
    "拳套雕像": "Gauntlet Statues",
    "巢穴猎杀": "Boss Hunts",
    "武器升阶链": "Weapon Upgrade",
    "奥乌兰爬塔": "Ouwigahara Tower",
    "任务阶梯": "Quest Ladder",
    "公会图鉴": "Clan Index",
    "全息地图": "Holo Map",
    "NPC 总览": "NPC Overview",
    "玩家资料维基": "Player Wiki",
    "Wiki 所有者 · theKing": "Wiki owner · theKing",
    "介绍": "Description",
    "来源": "Sources",
    "数据 / 加成": "Stats / Bonuses",
    "用途与说明": "Usage",
    "获取提示": "How to obtain",
    "作为材料用于": "Used as material in",
    "配方 / 标价明细": "Recipe / Price",
    "获取流程": "Acquire flow",
    "关联技能": "Related skills",
    "药水效果": "Potion effects",
    "购买位置": "Buy locations",
    "掉落": "Drops",
    "刷新点": "Spawn points",
    "战斗数据": "Combat data",
    "等级范围": "Level range",
    "特性": "Traits",
    "主要有什么": "Highlights",
    "提示": "Tip",
    "点位表": "Locations",
    "鱼竿": "Rods",
    "鱼类与推荐钓点": "Fish & recommended spots",
    "流程": "Guide",
    "中文": "中文",
    "资料": "Info",
    "日志": "Log",
  };

  const storeOrig = (el) => {
    if (!el.dataset.i18nOrig) el.dataset.i18nOrig = el.textContent;
  };

  const translateTextNode = (node, lang) => {
    const raw = node.nodeValue;
    if (raw == null) return;
    const trimmed = raw.trim();
    if (!trimmed) return;
    if (lang === "en") {
      if (DICT[trimmed]) {
        const lead = raw.match(/^\s*/)[0];
        const trail = raw.match(/\s*$/)[0];
        node.nodeValue = lead + DICT[trimmed] + trail;
      }
    }
  };

  const walkText = (root, lang) => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        const p = n.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        const tag = p.tagName;
        if (tag === "SCRIPT" || tag === "STYLE" || tag === "CODE" || tag === "PRE") {
          return NodeFilter.FILTER_REJECT;
        }
        if (p.closest("[data-zh][data-en], .lang-switch, .i18n-skip, code, pre")) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    if (lang === "zh") {
      nodes.forEach((n) => {
        const p = n.parentElement;
        if (p && p.dataset.i18nTextZh != null) n.nodeValue = p.dataset.i18nTextZh;
      });
      return;
    }
    nodes.forEach((n) => {
      const p = n.parentElement;
      if (!p) return;
      if (p.dataset.i18nTextZh == null) p.dataset.i18nTextZh = n.nodeValue;
      // restore ZH base then map
      n.nodeValue = p.dataset.i18nTextZh;
      translateTextNode(n, "en");
    });
  };

  const applyAttrs = (lang) => {
    document.querySelectorAll("[data-zh][data-en]").forEach((el) => {
      const zh = el.getAttribute("data-zh");
      const en = el.getAttribute("data-en");
      if (lang === "en") {
        if (en != null) el.textContent = en;
      } else if (zh != null) {
        el.textContent = zh;
      }
    });
  };

  const applyDualBlocks = (lang) => {
    // .i18n-zh / .i18n-en pairs — but never hide .dial (NPC dialogue is English source)
    document.querySelectorAll(".i18n-zh, .i18n-en").forEach((el) => {
      if (el.classList.contains("dial")) {
        el.hidden = false;
        return;
      }
      const isEn = el.classList.contains("i18n-en");
      el.hidden = lang === "en" ? !isEn : isEn;
    });
  };

  const applyArchiveTitles = (lang) => {
    // Item/boss pages: h1 is CN, sibling .en code has English id
    document.querySelectorAll("article.sec .head h1, article.sec > h1").forEach((h1) => {
      storeOrig(h1);
      if (lang !== "en") {
        h1.textContent = h1.dataset.i18nOrig;
        return;
      }
      const box = h1.parentElement;
      const code = box && box.querySelector("p.en code, .en code, code");
      if (code && code.textContent.trim()) {
        h1.textContent = code.textContent.trim();
      }
    });
  };

  const applyDocumentTitle = (lang) => {
    const t = document.querySelector("title");
    if (!t) return;
    storeOrig(t);
    if (lang === "zh") {
      t.textContent = t.dataset.i18nOrig;
      return;
    }
    // swap leading CN segment before · if dict knows it
    const orig = t.dataset.i18nOrig;
    const m = orig.match(/^(.+?)\s*·\s*(Slayers 2 Wiki)$/i);
    if (m && DICT[m[1].trim()]) {
      t.textContent = DICT[m[1].trim()] + " · " + m[2];
    }
  };

  const apply = (lang) => {
    const root = document.documentElement;
    root.lang = lang === "en" ? "en" : "zh-CN";
    root.dataset.lang = lang === "en" ? "en" : "zh";
    applyAttrs(lang);
    applyDualBlocks(lang);
    walkText(document.body, lang);
    applyArchiveTitles(lang);
    applyDocumentTitle(lang);
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
      btn.onclick = () => apply(btn.dataset.lang);
    });
    return bar;
  };

  const injectLangCss = () => {
    if (document.getElementById("ps2-i18n-css")) return;
    const s = document.createElement("style");
    s.id = "ps2-i18n-css";
    s.textContent =
      ".lang-switch{display:inline-flex;gap:0;margin-left:auto;margin-right:.75rem;border:1px solid var(--line, #333);border-radius:6px;overflow:hidden}" +
      ".lang-btn{background:transparent;border:0;color:var(--muted,#aaa);padding:.25rem .55rem;font:inherit;cursor:pointer;font-size:.8rem}" +
      ".lang-btn.is-active{background:rgba(255,196,72,.15);color:var(--gold,#ffc448)}" +
      "html[data-lang=en] .zh-only{display:none!important}" +
      "html[data-lang=zh] .en-only{display:none!important}";
    document.head.appendChild(s);
  };

  const boot = () => {
    injectLangCss();
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
