# -*- coding: utf-8 -*-
"""Rebuild skill-tree.html with skill icons downloaded from Roblox thumbnails."""
from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(r"D:\Desktop\ProjectSlayer2_WIKI")
LIVE = ROOT / "data" / "_live"
ICON_DIR = ROOT / "assets" / "icons" / "skills"
CSS = "20260926w"

# Point costs / mastery gates for combat trees (nodes 1..5)
POINTS = [3, 6, 9, 12, 15]
MASTERY = [None, 14, 27, 40, 53]

BREATH_CN = {
    "Water": ("水之呼吸", "Giyen"),
    "Flame": ("炎之呼吸", "Rengu"),
    "Thunder": ("雷之呼吸", "Zentaro"),
    "Wind": ("风之呼吸", "Saneri"),
    "Insect": ("虫之呼吸", "Shinora"),
    "Serpent": ("蛇之呼吸", "Obari"),
    "Sound": ("音之呼吸", "Tengai"),
    "Stone": ("岩之呼吸", "Gyorei"),
}
DEMON_CN = {
    "Cryokinesis": ("冰结", "Domae"),
    "Blood Manipulation": ("血操", "Gyutai"),
    "Arrow": ("箭矢", "Yahari"),
    "Dream": ("梦境", "Enru"),
    "Obi Manipulation": ("带操", "Datai"),
    "Shockwave": ("冲击波", "Akazo"),
    "Pyrokenesis": ("火焰念动", "Rengu"),
    "Reaper": ("收割者", "Reaper"),
    "Tamari": ("玉", "Sumari"),
}

# CN skill names already on page — keep mapping by EN Name
SKILL_CN = {
    "Water Surface Slash": "水面斩",
    "Whirl Pool": "漩涡",
    "Water Wheel": "水车",
    "Constant Flux": "生生流转",
    "Dead Calm": "水面波纹·无静",
    "Unknowing Fire": "不知火",
    "Blazing Universe": "灼骨炎阳",
    "Flame Undulation": "炎天窑变",
    "Flame Tiger": "炼狱·炎虎",
    "Purgatory": "炼狱",
    "Thunder Clap and Flash": "霹雳一闪",
    "Lightning Fold": "稻魂",
    "Rice Spirit": "聚蚊成雷",
    "Godspeed": "神速",
    "Flaming Thunder God": "炎响·闪空",
    "Mountain Wind": "岚气抱树",
    "Purifying Claws": "净风爪",
    "Rising Dust Storm": "升尘岚",
    "Whirlwind Cutter": "旋风切割",
    "Idaten Typhoon": "韦陀天台风",
    "Compound Eye Hexagon": "复眼六角",
    "True Flutter": "真蝶",
    "Fluttering Sting": "舞蝶之刺",
    "Hundred-Legged Zigzag": "百足曲折",
    "Illusory Light": "幻光",
    "Serpent Slash": "蛇斩",
    "Coil Choke": "盘绞",
    "Venom Fangs": "毒牙",
    "Twin-Headed Reptile": "双头蜿蜒",
    "Slithering Serpent": "蜿蜒蛇",
    "Bursting Bloom": "爆响之华",
    "Roar": "轰鸣",
    "Exploding Beads": "爆珠",
    "Resounding Slashes": "残响斩",
    "String Performance": "弦之演奏",
    "Volcanic Conquest": "火山征伐",
    "Seismic Burst": "地鸣爆裂",
    "Upper Smash": "升砸",
    "Stone Wall": "岩壁",
    "Arcs of Justice": "正义之弧",
}


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def asset_id(icon) -> str | None:
    if not icon:
        return None
    m = re.search(r"(\d{6,})", str(icon))
    return m.group(1) if m else None


def download_icon(aid: str) -> bool:
    dest = ICON_DIR / f"{aid}.png"
    if dest.exists() and dest.stat().st_size > 80:
        return True
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    url = (
        "https://thumbnails.roblox.com/v1/assets"
        f"?assetIds={aid}&returnPolicy=PlaceHolder&size=150x150&format=Png&isCircular=false"
    )
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8"))
        img_url = (data.get("data") or [{}])[0].get("imageUrl")
        if not img_url:
            return False
        with urllib.request.urlopen(img_url, timeout=25) as r2:
            dest.write_bytes(r2.read())
        return True
    except Exception:
        return False


def skill_icon_html(icon_field) -> str:
    aid = asset_id(icon_field)
    if not aid:
        return ""
    download_icon(aid)
    if (ICON_DIR / f"{aid}.png").exists():
        return f'<img class="sk-icon" src="../assets/icons/skills/{aid}.png" alt="">'
    return ""


def flatten_skill(sk: dict) -> dict:
    """Prefer Default branch for dual-state skills."""
    if not isinstance(sk, dict):
        return {}
    if isinstance(sk.get("Default"), dict):
        d = dict(sk["Default"])
        for k in ("Key", "Name", "Boss"):
            if k in sk and k not in d:
                d[k] = sk[k]
        return d
    return sk


def combat_rows(skills: dict, cn_map: dict | None = None) -> str:
    cn_map = cn_map or SKILL_CN
    # skip blocking F
    entries = []
    for k in sorted(skills.keys(), key=lambda x: int(x) if str(x).isdigit() else 99):
        sk = flatten_skill(skills[k])
        name = sk.get("Name") or ""
        if not name or name == "Blocking" or sk.get("Key") == "F":
            continue
        entries.append(sk)
    rows = []
    for i, sk in enumerate(entries[:5]):
        en = sk.get("Name") or ""
        cn = cn_map.get(en) or en
        key = sk.get("Key") or "—"
        cd = sk.get("CoolDown")
        stam = sk.get("Stamina")
        boss = sk.get("Boss") or "—"
        pts = POINTS[i] if i < len(POINTS) else "—"
        mast = MASTERY[i] if i < len(MASTERY) else "—"
        mast_s = "—" if mast is None else mast
        ic = skill_icon_html(sk.get("icon"))
        rows.append(
            f"<tr><td>{i+1}</td><td>{ic}<strong>{esc(cn)}</strong><br><span class='en'>{esc(en)}</span></td>"
            f"<td>{esc(key)}</td><td>{pts}</td><td>{mast_s}</td>"
            f"<td>{esc(cd if cd is not None else '—')}</td>"
            f"<td>{esc(stam if stam is not None else '—')}</td>"
            f"<td>{esc(boss)}</td></tr>"
        )
    return "".join(rows) or "<tr><td colspan=8>无</td></tr>"


def main():
    breathings = json.loads((LIVE / "wiki-breathings.json").read_text(encoding="utf-8"))
    demons = json.loads((LIVE / "wiki-demon-arts.json").read_text(encoding="utf-8"))
    combat = json.loads((LIVE / "wiki-item-combat.json").read_text(encoding="utf-8"))

    # also download character tree icons from SkillTreeConfig if present
    cfg_path = LIVE / "skilltree-config.json"
    char_icons = {}
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        for k, v in cfg.items() if isinstance(cfg, dict) else []:
            if isinstance(v, dict) and v.get("Icon"):
                aid = asset_id(v["Icon"])
                if aid:
                    download_icon(aid)
                    char_icons[k] = aid

    breath_html = []
    for code, (cn, boss) in BREATH_CN.items():
        data = breathings.get(code) or {}
        tree_ic = skill_icon_html(data.get("Icon"))
        breath_html.append(
            f"<h3>{tree_ic}{esc(cn)} <span class='en'>({esc(code)})</span></h3>"
            f"<p class='note'>猎杀队 / 人类 / 混血 · 终极大招 Boss：<strong>{esc(boss)}</strong></p>"
            "<table><tr><th>#</th><th>技能</th><th>键</th><th>技能点</th><th>精通</th><th>冷却</th><th>体力</th><th>Boss</th></tr>"
            f"{combat_rows(data.get('Skills') or {})}</table>"
        )

    demon_html = []
    for code, (cn, boss) in DEMON_CN.items():
        data = demons.get(code) or demons.get(code.replace("Pyrokenesis", "Pyrokinesis")) or {}
        # try alternate keys
        if not data:
            for k, v in demons.items():
                if k.lower().replace(" ", "") == code.lower().replace(" ", ""):
                    data = v
                    break
        tree_ic = skill_icon_html(data.get("Icon") if isinstance(data, dict) else None)
        skills = (data.get("Skills") or {}) if isinstance(data, dict) else {}
        demon_html.append(
            f"<h3>{tree_ic}{esc(cn)} <span class='en'>({esc(code)})</span></h3>"
            f"<p class='note'>鬼 / 混血 · 终极大招 Boss：<strong>{esc(boss)}</strong></p>"
            "<table><tr><th>#</th><th>技能</th><th>键</th><th>技能点</th><th>精通</th><th>冷却</th><th>体力</th><th>Boss</th></tr>"
            f"{combat_rows(skills)}</table>"
        )

    # weapon skill trees from combat items with multi skills
    weapon_names = [
        "Nightfall Gauntlet",
        "Damascus Gauntlet",
        "Nightfall Sickles",
        "Damascus Sickles",
        "Nightfall Scythe",
        "Damascus Scythe",
        "Nightfall Claws",
        "Damascus Claws",
        "Firstlight War Fans",
        "Damascus War Fans",
        "Firstlight Spear",
        "Damascus Spear",
        "Firstlight Tanto",
        "Damascus Tanto",
        "Firstlight Bladed Wagasa",
        "Damascus Bladed Wagasa",
        "Lost Shotgun",
        "Damascus Shotgun",
        "Shotgun",
    ]
    seen_cat = set()
    weapon_html = []
    for wn in weapon_names:
        it = combat.get(wn) or {}
        skills = it.get("Skills")
        if not isinstance(skills, list) or len(skills) < 2:
            continue
        cat = it.get("SkillCategory") or wn
        if cat in seen_cat:
            continue
        seen_cat.add(cat)
        # convert list to dict-like for combat_rows
        sk_map = {str(i + 1): s for i, s in enumerate(skills) if isinstance(s, dict)}
        cn = (json.loads((LIVE / "items-enriched.json").read_text(encoding="utf-8")).get(wn) or {}).get("NameCN") or wn
        weapon_html.append(
            f"<h3>{esc(cn)} <span class='en'>({esc(cat)})</span></h3>"
            "<table><tr><th>#</th><th>技能</th><th>键</th><th>技能点</th><th>精通</th><th>冷却</th><th>体力</th><th>Boss</th></tr>"
            f"{combat_rows(sk_map)}</table>"
        )

    # keep character section from existing static content (no icons needed much)
    char_section = """
<article class="sec" id="character">
  <h2>角色树 · Character</h2>
  <p>所有角色都会显示。包含<strong>先天技能</strong>与<strong>属性链</strong>。属性节点无精通 / Boss 要求。</p>
  <h3>先天技能</h3>
  <table>
    <tr><th>#</th><th>技能</th><th>技能点</th><th>冷却</th><th>体力</th><th>说明</th></tr>
    <tr><td>1</td><td><strong>二段跳</strong><br><span class="en">Double Jump</span></td><td>3</td><td>2</td><td>10</td><td>空中再跳一次</td></tr>
    <tr><td>2</td><td><strong>攀墙</strong><br><span class="en">Wall Climb</span></td><td>6</td><td>2</td><td>—</td><td>需先解锁二段跳</td></tr>
  </table>
  <h3>属性加成链</h3>
  <p>满级 225。每级获得 3 技能点。数值为解锁该节点后的累计效果。</p>
  <table>
    <tr><th>属性</th><th>节点数</th><th>各节点技能点</th><th>累计效果</th></tr>
    <tr><td>生命回复速度</td><td>6</td><td>3 / 6 / 9 / 12 / 15 / 18</td><td>1× → 1.15× → 1.3× → 1.45× → 1.6× → 1.75×</td></tr>
    <tr><td>最大生命</td><td>6</td><td>7 / 16 / 25 / 34 / 43 / 52</td><td>+40 → +115 → +192 → +271 → +352 → +435</td></tr>
    <tr><td>最大体力</td><td>8</td><td>4 / 8 / 12 / 16 / 20 / 24 / 28 / 32</td><td>+15 起，逐步提升至约 +176</td></tr>
    <tr><td>体力回复速度</td><td>6</td><td>6 / 12 / 18 / 24 / 30 / 36</td><td>1.17× → 1.32× → 1.46× → 1.58× → 1.7× → 1.8×</td></tr>
    <tr><td>格挡值</td><td>6</td><td>12 / 24 / 36 / 48 / 60 / 72</td><td>1 → 约 8.25</td></tr>
    <tr><td>格挡回复</td><td>4</td><td>12 / 24 / 36 / 48</td><td>1× → 约 1.45×</td></tr>
    <tr><td>额外伤害</td><td>5</td><td>12 / 24 / 36 / 48 / 60</td><td>0.5 → 约 3.1</td></tr>
  </table>
</article>
"""

    styles = """
<article class="sec" id="styles">
  <h2>战斗风格 · Fighting Styles</h2>
  <p>见习试炼详见任务 / 导师 NPC。技能图标随武器/风格数据补全。</p>
  <p>Soryu / Tai Chi / Reaping Blades — 接取见 <a href="quests.html">任务</a> · <a href="npcs.html">NPC</a>。</p>
</article>
"""

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>技能树 · Slayers 2 Wiki</title>
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/wiki.css?v={CSS}">
  <style>
    .page{{max-width:var(--max);margin:0 auto;padding:0 1.25rem 3rem;position:relative;z-index:1}}
    .crumb{{color:var(--muted);font-size:.85rem;margin:.5rem 0 1.25rem}}
    .crumb a{{color:var(--gold)}}
    .sec{{margin-bottom:1.25rem;border:1px solid var(--line);background:var(--panel);padding:1rem 1.1rem}}
    .sec h1,.sec h2{{margin:0 0 .65rem;font-size:1.15rem}}
    .sec h1{{font-size:1.35rem}}
    .sec h3{{margin:1rem 0 .4rem;font-size:1rem;color:var(--cream);display:flex;align-items:center;gap:.45rem}}
    .sec p,.sec li{{color:var(--muted);font-size:.92rem}}
    .sec ul{{margin:.35rem 0 0;padding-left:1.2rem}}
    .sec strong{{color:var(--cream)}}
    .sec table{{width:100%;border-collapse:collapse;font-size:.84rem;margin:.35rem 0 .85rem}}
    .sec th,.sec td{{border:1px solid var(--line);padding:.35rem .45rem;text-align:left;vertical-align:middle}}
    .sec th{{color:var(--gold-deep);font-weight:600;background:rgba(255,255,255,.03)}}
    .sec td{{color:var(--muted)}}
    .sec code{{color:var(--gold-deep)}}
    .en{{color:var(--muted);font-size:.78rem;opacity:.85}}
    .note{{font-size:.86rem!important;margin:.15rem 0 .4rem!important}}
    .toc{{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:.75rem}}
    .toc a{{border:1px solid var(--line);padding:.3rem .55rem;color:var(--gold);font-size:.82rem;text-decoration:none}}
    .top-nav{{display:flex;gap:.75rem;align-items:center;font-size:.82rem}}
    .top-nav a{{color:var(--muted)}}
    .sk-icon{{width:28px;height:28px;object-fit:contain;vertical-align:middle;margin-right:.35rem;border:1px solid var(--line);background:#0a0a0a}}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="../"><span>Slayers 2 Wiki</span></a>
    <nav class="top-nav" aria-label="本页">
      <a href="#rules">规则</a>
      <a href="#character">角色</a>
      <a href="#breathings">呼吸</a>
      <a href="#demon-arts">邪恶艺术</a>
      <a href="#styles">体术</a>
      <a href="#weapons">武器</a>
    </nav>
    <span class="top-ver">技能树</span>
  </header>
  <main class="page">
    <p class="crumb"><a href="../">主页</a> / 技能树</p>

<article class="sec" id="rules">
  <h1>技能树系统</h1>
  <p>菜单 → <strong>技能树</strong>。按已装备 / 已学习内容动态显示分支。下列含<strong>技能图标</strong>（来自游戏技能配置）。</p>
  <h2>规则速查</h2>
  <ul>
    <li><strong>技能点</strong>：每升 1 级 +3 点（满级 225）。商店可重置技能点。</li>
    <li><strong>解锁顺序</strong>：同分支须先解锁上一节点。</li>
    <li><strong>战斗技能点价</strong>：第 1～5 节点一般为 <code>3 / 6 / 9 / 12 / 15</code>。</li>
    <li><strong>精通门槛</strong>：第 2 起约 <code>14 / 27 / 40 / 53</code>。</li>
    <li><strong>终极大招</strong>：多为第 5 技能（B），需击败对应 Boss。</li>
  </ul>
  <nav class="toc">
    <a href="#character">角色树</a>
    <a href="#breathings">呼吸法</a>
    <a href="#demon-arts">邪恶艺术</a>
    <a href="#styles">战斗风格</a>
    <a href="#weapons">武器技能</a>
  </nav>
</article>

{char_section}

<article class="sec" id="breathings">
  <h2>呼吸法</h2>
  <p>导师接取见 <a href="breathings.html">呼吸法</a>。</p>
  {"".join(breath_html)}
</article>

<article class="sec" id="demon-arts">
  <h2>邪恶艺术</h2>
  <p>成鬼与魔球见 <a href="evil-arts.html">邪恶艺术</a>。</p>
  {"".join(demon_html)}
</article>

{styles}

<article class="sec" id="weapons">
  <h2>武器技能树</h2>
  <p>有主动技能的武器成枝；日轮刀系等仅格挡者不成树。</p>
  {"".join(weapon_html) or "<p>暂无多技能武器数据。</p>"}
</article>

  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>技能树</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="../">返回主页</a>
  </footer>
  <script src="../js/i18n.js?v={CSS}"></script>
</body>
</html>
"""
    (ROOT / "p" / "skill-tree.html").write_text(page, encoding="utf-8")
    n_icons = len(list(ICON_DIR.glob("*.png"))) if ICON_DIR.exists() else 0
    print(f"skill-tree.html icons_dir={n_icons}")


if __name__ == "__main__":
    main()
