# -*- coding: utf-8 -*-
"""Build 01.txt feature pages: sides, npcs map, evil-arts, breathings expand, black-market map."""
from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Desktop\ProjectSlayer2_WIKI")
LIVE = ROOT / "data" / "_live"
MAP_CLEAN = ROOT / "assets" / "ouwland-map-clean.png"
MAP_DIR = ROOT / "assets" / "wiki-maps"
ICON_DIR = ROOT / "assets" / "icons" / "powers"
ORB_DIR = ROOT / "assets" / "icons" / "items"
TL = (-3087.361, -3989.256)
BR = (2977.139, 1635.244)
CSS = "20260926r"


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", name, flags=re.UNICODE)
    return re.sub(r"\s+", "-", s.strip()) or "x"


def asset_id(icon) -> str | None:
    if not icon:
        return None
    m = re.search(r"(\d{6,})", str(icon))
    return m.group(1) if m else None


def world_to_px(x, z, w, h):
    u = (x - TL[0]) / (BR[0] - TL[0])
    v = (z - TL[1]) / (BR[1] - TL[1])
    return u * w, v * h


def load_font(size: int):
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_markers(spots, title, subtitle, out_path, small=False):
    base = Image.open(MAP_CLEAN).convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_t = load_font(22)
    font_s = load_font(14)
    font_n = load_font(11 if small else 13)
    font_l = load_font(11)
    draw.rectangle((0, 0, w, 52), fill=(0, 0, 0, 170))
    draw.text((12, 8), title, fill=(255, 208, 70, 255), font=font_t)
    draw.text((12, 32), subtitle, fill=(220, 220, 220, 230), font=font_s)
    colors = [
        (94, 184, 255, 230),
        (255, 208, 70, 230),
        (96, 214, 130, 230),
        (176, 107, 255, 230),
        (255, 92, 120, 230),
        (240, 190, 80, 230),
    ]
    r = 5 if small else 11
    for i, (num, x, z, label) in enumerate(spots):
        px, py = world_to_px(x, z, w, h)
        c = colors[i % len(colors)]
        draw.ellipse((px - r - 1, py - r - 1, px + r + 1, py + r + 1), fill=(0, 0, 0, 180))
        draw.ellipse((px - r, py - r, px + r, py + r), fill=c)
        if not small:
            t = str(num)
            bb = draw.textbbox((0, 0), t, font=font_n)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            draw.text((px - tw / 2, py - th / 2 - 1), t, fill=(20, 20, 20, 255), font=font_n)
        if label and (not small or len(spots) <= 25):
            lx, ly = px + 8, py - 8
            lb = draw.textbbox((lx, ly), label, font=font_l)
            draw.rectangle((lb[0] - 2, lb[1] - 1, lb[2] + 2, lb[3] + 1), fill=(0, 0, 0, 190))
            draw.text((lx, ly), label, fill=(255, 255, 255, 255), font=font_l)
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path, "PNG", optimize=True)


def download_icon(aid: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 80:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = (
        "https://thumbnails.roblox.com/v1/assets"
        f"?assetIds={aid}&returnPolicy=PlaceHolder&size=150x150&format=Png&isCircular=false"
    )
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        img_url = (data.get("data") or [{}])[0].get("imageUrl")
        if not img_url:
            return False
        with urllib.request.urlopen(img_url, timeout=20) as r2:
            dest.write_bytes(r2.read())
        return True
    except Exception:
        return False


def page_shell(title: str, crumb: str, body: str, nav="") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>{esc(title)} · Slayers 2 Wiki</title>
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/wiki.css?v={CSS}">
  <style>
    .page{{max-width:var(--max);margin:0 auto;padding:0 1.25rem 3rem;position:relative;z-index:1}}
    .crumb{{color:var(--muted);font-size:.85rem;margin:.5rem 0 1.25rem}}
    .crumb a{{color:var(--gold)}}
    .sec{{margin-bottom:1.25rem;border:1px solid var(--line);background:var(--panel);padding:1rem 1.1rem;scroll-margin-top:4.5rem}}
    .sec h1,.sec h2{{margin:0 0 .65rem;font-size:1.15rem}}
    .sec h1{{font-size:1.35rem}}
    .sec h3{{margin:1rem 0 .4rem;font-size:1rem;color:var(--cream)}}
    .sec p,.sec li{{color:var(--muted);font-size:.92rem}}
    .sec ul,.sec ol{{margin:.35rem 0 0;padding-left:1.2rem}}
    .sec strong{{color:var(--cream)}}
    .sec table{{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}}
    .sec th,.sec td{{border:1px solid var(--line);padding:.4rem .5rem;text-align:left;vertical-align:top}}
    .sec th{{color:var(--gold-deep);font-weight:600;background:rgba(255,255,255,.03)}}
    .sec td{{color:var(--muted)}}
    .sec code{{color:var(--gold-deep)}}
    .map-img{{display:block;width:100%;height:auto;border:1px solid var(--line);margin-top:.55rem}}
    .icon{{width:56px;height:56px;object-fit:contain;border:1px solid var(--line);background:#0a0a0a;border-radius:6px}}
    .head{{display:flex;gap:.85rem;align-items:flex-start}}
    .top-nav{{display:flex;flex-wrap:wrap;gap:.65rem;font-size:.82rem}}
    .top-nav a{{color:var(--muted)}}
    .top-nav a:hover{{color:var(--gold)}}
    .callout{{border-left:3px solid var(--gold);padding:.35rem 0 .35rem .75rem;margin:.5rem 0;color:var(--muted);font-size:.9rem}}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="../"><span>Slayers 2 Wiki</span></a>
    <nav class="top-nav">{nav}</nav>
    <span class="top-ver">{esc(title)}</span>
  </header>
  <main class="page">
    <p class="crumb">{crumb}</p>
    {body}
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>{esc(title)}</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="../">返回主页</a>
  </footer>
  <script src="../js/i18n.js?v={CSS}"></script>
</body>
</html>
"""


BREATH_CN = {
    "Thunder": ("雷之呼吸", "Thunder Trainer Zentaro", "Zentaro", 7000, "鬼角×10", ["meditation", "cup", "pushups", "aim", "split"], "ThunderTrainee"),
    "Water": ("水之呼吸", "Water Trainer Urokodaki", "Giyen", 5000, "鬼角×30", ["parkour", "pushups", "push", "aim", "underwater"], "WaterTrainee"),
    "Flame": ("炎之呼吸", "Flame Trainer Rengu", "Rengu", 6000, "鬼角×10", ["meditation", "pushups", "split", "aim", "cup"], "FlameTrainee"),
    "Wind": ("风之呼吸", "Wind Trainer Saneri", "Saneri", 3000, "鬼角×50", ["pushups", "split", "push", "aim", "meditation"], "WindTrainee"),
    "Insect": ("虫之呼吸", "Insect Trainer Shinora", "Shinora", 3500, "鬼角×15 + 兽核×3", ["meditation", "cup", "aim", "split", "pushups"], "InsectTrainee"),
    "Serpent": ("蛇之呼吸", "Serpent Trainer Obari", "Obari", 1000, "鬼角×20 + 兽核×5", ["push", "split", "aim", "cup", "meditation"], "SerpentTrainee"),
    "Sound": ("音之呼吸", "Sound Trainer Tengai", "Tengai", 4000, "鬼角×10 + 兽核×3", ["cup", "aim", "pushups", "split", "meditation"], "SoundTrainee"),
    "Stone": ("岩之呼吸", "Stone Trainer Gyorei", "Gyorei", 4000, "兽核×4（需斧锤）", ["pushups", "push", "split", "aim", "meditation"], "StoneTrainee"),
}

TRAIN_ANCHOR = {
    "meditation": ("冥想", "training.html#meditation"),
    "cup": ("杯戏", "training.html#cup"),
    "pushups": ("俯卧撑", "training.html#pushups"),
    "aim": ("瞄准射击", "training.html#aim"),
    "split": ("劈石", "training.html#split"),
    "push": ("推石", "training.html#push"),
    "parkour": ("跑酷地牢", "training.html#parkour"),
    "underwater": ("水下岩石", "training.html#underwater"),
}

DEMON_CN = {
    "Shockwave": "冲击波",
    "Cryokinesis": "冰冻",
    "Pyrokenesis": "火焰念动",
    "Blood Manipulation": "血液操纵",
    "Obi Manipulation": "带操纵",
    "Reaper": "收割者",
    "Arrow": "箭矢",
    "Dream": "梦境",
    "Tamari": "玉",
}

LILY_HINTS = [
    (677.33, 1021, 29.64, "彼岸花·1"),
    (348.09, 1021.4, -38.41, "彼岸花·2"),
    (2712.06, 1075.6, -554.52, "彼岸花·3"),
    (1233.89, 980.1, -76.53, "彼岸花·4"),
    (1451.5, 1248, -220, "彼岸花·医生附近"),
]
HIGOSHIMA = (1451.5, 1248, -220)
SAFE_ZONE = (-1159.569, 1195.055, -1008.914)
BM_SPAWNS = [
    (-132.676, 804, 101.24),
    (2161.963, 823.459, -900.676),
    (1795.511, 659.399, -523.103),
    (-464.862, 1356.974, -3497.761),
    (-2089.845, 62.241, -408.465),
    (-864.695, 1389, -1639.538),
    (-118.712, 1379.275, -1861.278),
    (-1045.371, 1282, -1312.49),
    (-1775.234, 141.75, 1297.076),
    (-2736.262, 143.75, 833.486),
    (-1946.007, 311.5, -282.891),
]


def skill_rows(skills: dict) -> str:
    rows = []
    for k in sorted(skills.keys(), key=lambda x: int(x) if str(x).isdigit() else 99):
        sk = skills[k]
        if not isinstance(sk, dict):
            continue
        name = sk.get("Name") or sk.get("Default", {}).get("Name") if isinstance(sk.get("Default"), dict) else sk.get("Name")
        if isinstance(sk.get("Default"), dict) and not name:
            name = sk["Default"].get("Name")
        key = sk.get("Key") or "—"
        stam = sk.get("Stamina")
        if stam is None and isinstance(sk.get("Default"), dict):
            stam = sk["Default"].get("Stamina")
        cd = sk.get("CoolDown")
        if cd is None and isinstance(sk.get("Default"), dict):
            cd = sk["Default"].get("CoolDown")
        stats = sk.get("SkillStats") or {}
        if isinstance(sk.get("Default"), dict) and not stats:
            stats = sk["Default"].get("SkillStats") or {}
        extra = []
        if isinstance(stats, dict):
            if stats.get("additional_damage_scale") is not None:
                extra.append(f"额外伤害倍率 +{stats['additional_damage_scale']}")
            if stats.get("strict_stun"):
                extra.append("硬直")
            if stats.get("counter") is not None:
                extra.append(f"反击×{stats['counter']}")
        boss = sk.get("Boss") or (sk.get("Default") or {}).get("Boss") if isinstance(sk.get("Default"), dict) else None
        if boss:
            extra.append(f"Boss 大招关联 {boss}")
        rows.append(
            f"<tr><td><code>{esc(key)}</code></td><td><strong>{esc(name)}</strong></td>"
            f"<td>{esc(stam if stam is not None else '—')}</td><td>{esc(cd if cd is not None else '—')}</td>"
            f"<td>{esc(' · '.join(extra) if extra else '—')}</td></tr>"
        )
    return "".join(rows) or "<tr><td colspan=5>无</td></tr>"


def main():
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    bosses = {b["Code"]: b for b in json.loads((LIVE / "world-bosses.json").read_text(encoding="utf-8"))}
    breathings = json.loads((LIVE / "wiki-breathings.json").read_text(encoding="utf-8"))
    demon_arts = json.loads((LIVE / "wiki-demon-arts.json").read_text(encoding="utf-8"))
    npcs = json.loads((LIVE / "wiki-npcs.json").read_text(encoding="utf-8"))
    items = json.loads((LIVE / "items-enriched.json").read_text(encoding="utf-8"))
    shops = json.loads((LIVE / "shops.json").read_text(encoding="utf-8"))

    # ---------- maps ----------
    # prefer live trainer NPC coords for breath map
    breath_spots = []
    for i, (code, meta) in enumerate(BREATH_CN.items(), 1):
        trainer = meta[1]
        pos = None
        for n in npcs:
            if n.get("Name") == trainer and n.get("Position"):
                pos = n["Position"]
                break
        if not pos:
            b = bosses.get(meta[2])
            if b:
                pos = b["Position"]
        if not pos:
            continue
        breath_spots.append((i, pos[0], pos[2], meta[0]))
    draw_markers(breath_spots, "呼吸导师位置", "编号对应呼吸一览", MAP_DIR / "breathings-trainers.png")

    lily_spots = [(i, x, z, lab) for i, (x, _y, z, lab) in enumerate(LILY_HINTS, 1)]
    lily_spots.append((len(LILY_HINTS) + 1, HIGOSHIMA[0], HIGOSHIMA[2], "医生 Higoshima"))
    lily_spots.append((len(LILY_HINTS) + 2, SAFE_ZONE[0], SAFE_ZONE[2], "交付安全区"))
    draw_markers(lily_spots, "成鬼 · 彼岸花 / 医生 / 交付点", "采 9 朵彼岸花 → 交 Dr. Higoshima → 安全区放置", MAP_DIR / "demon-lily-path.png")

    bm_spots = [(i, x, z, f"黑商·{i}") for i, (x, _y, z) in enumerate(BM_SPAWNS, 1)]
    draw_markers(bm_spots, "黑商刷新点 · 11", "限时活动 BlackMarketArrival · 每次 lasting 1800s", MAP_DIR / "black-market-spawns.png")

    npc_spots = []
    for i, n in enumerate(sorted([x for x in npcs if x.get("Position")], key=lambda x: x.get("Name") or ""), 1):
        p = n["Position"]
        label = (n.get("Name") or "")[:10]
        npc_spots.append((i, float(p[0]), float(p[2]), label if i <= 40 else ""))
    draw_markers(npc_spots, f"Ouwland NPC · {len(npc_spots)}", "标记点较小；详表见 NPC 页", MAP_DIR / "npcs-all.png", small=True)

    # ---------- download power icons ----------
    for code, data in list(breathings.items()) + list(demon_arts.items()):
        aid = asset_id(data.get("Icon") if isinstance(data, dict) else None)
        if aid:
            download_icon(aid, ICON_DIR / f"{aid}.png")
        if isinstance(data, dict):
            for sk in (data.get("Skills") or {}).values():
                if not isinstance(sk, dict):
                    continue
                for cand in (sk, sk.get("Default") if isinstance(sk.get("Default"), dict) else None):
                    if not cand:
                        continue
                    aid2 = asset_id(cand.get("icon"))
                    if aid2:
                        download_icon(aid2, ICON_DIR / f"{aid2}.png")

    for orb in [k for k in items if k.endswith(" Orb")]:
        aid = asset_id(items[orb].get("Icon"))
        if aid:
            download_icon(aid, ORB_DIR / f"{aid}.png")

    # ---------- sides.html ----------
    sides_body = f"""
    <article class="sec" id="overview">
      <h1>阵营</h1>
      <p class="i18n-zh">玩家种族侧：<strong>鬼杀队（Slayer）</strong>与<strong>鬼（Demon）</strong>。混血可两边都有进度。玩家公会组织见 <a class="quest-link" href="factions.html">派系</a>；血脉见 <a class="quest-link" href="clans.html">公会图鉴</a>。</p>
      <p class="i18n-en" hidden>Player sides: <strong>Slayer Corps</strong> vs <strong>Demon</strong>. Hybrid can progress both. Player orgs → <a class="quest-link" href="factions.html">Factions</a>; bloodline clans → <a class="quest-link" href="clans.html">Clans</a>.</p>
      <nav class="top-nav" style="margin-top:.6rem">
        <a href="#slayer">鬼杀队</a>
        <a href="#demon">鬼</a>
        <a href="#reputation">声望</a>
        <a href="#related-bosses">关联 Boss</a>
      </nav>
    </article>
    <article class="sec" id="slayer">
      <h2>鬼杀队 · Slayer</h2>
      <ul>
        <li>可学<strong>呼吸法</strong>（见 <a class="quest-link" href="breathings.html">呼吸</a>），用人形日轮刀路线。</li>
        <li>阵营进度靠葫芦：小 +25 / 中 +100 / 大 +300（<a class="quest-link" href="archive/items/Small-Gourd.html">小葫芦</a> 等，蝴蝶屋 Ren 出售）。</li>
        <li>满级解锁 Breathing Boost；属性累加生命 / 体力。</li>
      </ul>
      <h3>进度等级奖励</h3>
      <table>
        <tr><th>等级</th><th>条容量</th><th>经验</th><th>文</th><th>属性</th></tr>
        <tr><td>1</td><td>2000</td><td>—</td><td>—</td><td>—</td></tr>
        <tr><td>2</td><td>3000</td><td>2000</td><td>1800</td><td>生命+50 · 生命倍率+0.05 · 体力+15</td></tr>
        <tr><td>3</td><td>7000</td><td>5000</td><td>4000</td><td>生命+75 · 倍率+0.07 · 体力+25</td></tr>
        <tr><td>4</td><td>1</td><td>12000</td><td>10000</td><td>生命+100 · 倍率+0.08 · Breathing Boost</td></tr>
      </table>
    </article>
    <article class="sec" id="demon">
      <h2>鬼 · Demon</h2>
      <ul>
        <li>可使用<strong>邪恶艺术魔球</strong>（见 <a class="quest-link" href="evil-arts.html">邪恶艺术</a>）。</li>
        <li>成鬼流程：压低声望 → 无惨领琵琶铃 → 夜访 → <code>Muzan Quest</code> 采彼岸花交医生。</li>
        <li>进度靠灵魂：弱 +5 / 强 +10 / 勇 +25；商店 2x Souls 可翻倍。</li>
      </ul>
      <h3>进度等级奖励</h3>
      <table>
        <tr><th>等级</th><th>属性</th></tr>
        <tr><td>2</td><td>生命+50 · 倍率+0.05 · Illumination +0.2</td></tr>
        <tr><td>3</td><td>生命+75 · 倍率+0.07 · 生命回复 +0.1</td></tr>
        <tr><td>4</td><td>生命+100 · 倍率+0.08 · Illumination +0.15 · 邪术伤害倍率 +0.04 · 额外伤害 +2</td></tr>
      </table>
    </article>
    <article class="sec" id="reputation">
      <h2>声望 Reputation（善恶值）</h2>
      <p><strong>越低越恶</strong>。独立于阵营进度条。商店可「重置声望」→ 0（50 罗宝 / 4 矿石）。</p>
      <table>
        <tr><th>阈值</th><th>效果</th></tr>
        <tr><td>≤ −10 / −20 / −30 / −40</td><td>无惨低语阶段</td></tr>
        <tr><td>≤ −40</td><td>可获琵琶铃资格（EligibleReputation）</td></tr>
        <tr><td>&lt; −20</td><td>可入无惨巢穴；进入声望 +5（LairEntryCost）</td></tr>
      </table>
      <p>详流程与地图见 <a class="quest-link" href="evil-arts.html#become-demon">成鬼</a>。</p>
    </article>
    <article class="sec" id="related-bosses">
      <h2>关联 Boss / 头目</h2>
      <p>鬼杀队侧常见柱与试炼头目；鬼侧常见上弦风格世界 Boss。完整列表见 <a class="quest-link" href="bosses.html">Boss</a>。</p>
      <ul>
        <li>呼吸试炼对手：各流派 Trainee（Common Chest）。</li>
        <li>柱级世界 Boss：Rengu / Giyen / Saneri / Shinora / Obari / Tengai / Gyorei / Zentaro 等（World Events Chest）。</li>
        <li>鬼艺术相关：Akazo（冲击波）、Reaper、Domae、Gyutai、Datai、Enru、Nezura 等。</li>
      </ul>
    </article>
"""
    (ROOT / "p" / "sides.html").write_text(
        page_shell("阵营", '<a href="../">主页</a> / 阵营', sides_body, '<a href="#slayer">鬼杀队</a><a href="#demon">鬼</a><a href="#reputation">声望</a>'),
        encoding="utf-8",
    )

    # ---------- evil-arts.html ----------
    orb_cards = []
    for name, cn in DEMON_CN.items():
        orb_name = f"{name} Orb" if name != "Pyrokenesis" else "Pyrokenesis Orb"
        # fix spelling in items
        if orb_name not in items:
            for k in items:
                if k.replace(" ", "").lower().startswith(name.replace(" ", "").lower()) and k.endswith("Orb"):
                    orb_name = k
                    break
        it = items.get(orb_name) or {}
        aid = asset_id(it.get("Icon") or (demon_arts.get(name) or {}).get("Icon"))
        icon_html = ""
        if aid and (ORB_DIR / f"{aid}.png").exists():
            icon_html = f'<img class="icon" src="../assets/icons/items/{aid}.png" alt="">'
        elif aid and (ICON_DIR / f"{aid}.png").exists():
            icon_html = f'<img class="icon" src="../assets/icons/powers/{aid}.png" alt="">'
        art = demon_arts.get(name) or {}
        skills = art.get("Skills") or {}
        cores = {
            "Shockwave": "俯卧撑→深蹲架→推石→劈石→灭水之十×5",
            "Cryokinesis": "冥想→劈石→水下岩石→灭水之十×5",
            "Pyrokenesis": "俯卧撑→推石→瞄准→灭水之十×5",
            "Blood Manipulation": "杯戏→俯卧撑→瞄准→灭水之十×5",
            "Obi Manipulation": "深蹲→推石→劈石→灭水之十×5",
            "Reaper": "杯戏→瞄准→劈石→灭水之十×5",
            "Arrow": "冥想→瞄准→推石→灭水之十×5",
            "Dream": "冥想→杯戏→瞄准→灭水之十×5",
            "Tamari": "杯戏→俯卧撑→劈石→灭水之十×5",
        }
        href = f"archive/items/{slug(orb_name)}.html" if orb_name in items else "#"
        orb_cards.append(f"""
    <article class="sec" id="{esc(slug(name))}">
      <div class="head">{icon_html}<div>
        <h2>{esc(cn)} <span style="opacity:.7;font-size:.85rem">/ {esc(name)}</span></h2>
        <p>魔球：<a class="quest-link" href="{esc(href)}">{esc(orb_name)}</a> · 捏碎后开启核心训练（键 <code>I will train my {esc(name)} core</code>）</p>
      </div></div>
      <p>训练链：{esc(cores.get(name, "见 EvilArtCores"))}。器械跳转 <a class="quest-link" href="training.html">锻炼</a>。</p>
      <h3>技能</h3>
      <table><tr><th>键</th><th>名称</th><th>体力</th><th>CD</th><th>备注</th></tr>{skill_rows(skills)}</table>
    </article>""")

    evil_body = f"""
    <article class="sec" id="overview">
      <h1>邪恶艺术 · 魔球</h1>
      <p>仅<strong>鬼 / 混血</strong>可使用。魔球从各类宝箱低概率掉落；捏碎后接核心训练，完成后获得对应 Demon Art。</p>
      <nav class="top-nav">
        <a href="#become-demon">成鬼</a>
        <a href="#orbs">魔球一览</a>
        {" ".join(f'<a href="#{slug(k)}">{DEMON_CN[k]}</a>' for k in DEMON_CN)}
      </nav>
    </article>
    <article class="sec" id="become-demon">
      <h2>如何成为鬼</h2>
      <ol>
        <li>将声望压到 ≤ <strong>−40</strong>（见 <a class="quest-link" href="sides.html#reputation">阵营 · 声望</a>）。</li>
        <li>夜间找漫游无惨，领取 <a class="quest-link" href="archive/items/Biwa-Bell.html">琵琶铃 Biwa Bell</a>。</li>
        <li>使用铃铛进入无惨巢穴（进门声望 &lt; −20；入场声望 +5）。</li>
        <li>接取 <code>Muzan Quest</code>：采集 <strong>彼岸花 ×9</strong>，交给 <strong>Dr. Higoshima</strong>，再在安全区放置。</li>
        <li>完成转化后可捏碎魔球训练邪恶艺术。</li>
      </ol>
      <img class="map-img" src="../assets/wiki-maps/demon-lily-path.png" alt="彼岸花与医生路线">
      <p>医生坐标约 <code>1451.5, 1248, -220</code>；交付安全区约 <code>-1159.6, 1195.1, -1008.9</code>（半径 10）。</p>
    </article>
    <article class="sec" id="orbs">
      <h2>魔球获取</h2>
      <p>九种魔球均主要来自宝箱（Common / Rare / Ice / Sealed / World Events / Lost / Snow 等，概率约 0.67%～2%）。档案条目可点名称跳转。</p>
    </article>
    {"".join(orb_cards)}
"""
    (ROOT / "p" / "evil-arts.html").write_text(
        page_shell("邪恶艺术", '<a href="../">主页</a> / 邪恶艺术', evil_body, '<a href="#become-demon">成鬼</a><a href="#orbs">魔球</a>'),
        encoding="utf-8",
    )

    # ---------- npcs.html ----------
    shop_by = {s["Name"]: s for s in shops}
    rows = []
    for i, n in enumerate(sorted(npcs, key=lambda x: ((x.get("Region") or ""), x.get("Name") or "")), 1):
        name = n.get("Name") or "?"
        region = n.get("Region") or "—"
        pos = n.get("Position")
        pos_s = f"{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}" if pos else "—"
        role = []
        if n.get("Shop") or n.get("HasShop") or shop_by.get(name):
            role.append("商店")
        if n.get("TimedVendor") or n.get("RotatingShop"):
            role.append("限时摊")
        if "Trainer" in name or "Expert" in name:
            role.append("导师")
        if "Togane" in name or "Blacksmith" in name:
            role.append("锻造")
        if "Hagane" in name or "Refiner" in name:
            role.append("精炼")
        if "Marketer" in name:
            role.append("黑商")
        if "Sofen" in name:
            role.append("钓鱼许可")
        req = n.get("Requirements") or {}
        if isinstance(req, dict) and req.get("Level"):
            role.append(f"Lv{req['Level']}")
        qs = n.get("Quests") or []
        qn = len(qs) if isinstance(qs, list) else 0
        rows.append(
            f"<tr><td>{i}</td><td><strong>{esc(name)}</strong></td><td>{esc(region)}</td>"
            f"<td><code>{esc(pos_s)}</code></td><td>{esc(' / '.join(role) or '对话 / 任务')}</td><td>{qn or '—'}</td></tr>"
        )

    npc_body = f"""
    <article class="sec">
      <h1>NPC</h1>
      <p>Regions 配置共 <strong>{len(npcs)}</strong> 名；有坐标可标点 <strong>{sum(1 for n in npcs if n.get('Position'))}</strong>。特殊：<a class="quest-link" href="forge.html">锻造 Togane</a> · <a class="quest-link" href="refinement.html">精炼 Hagane</a> · <a class="quest-link" href="black-market.html">黑商</a> · <a class="quest-link" href="fishing.html">Sofen 钓鱼证</a>。</p>
      <img class="map-img" src="../assets/wiki-maps/npcs-all.png" alt="NPC 总图">
    </article>
    <article class="sec">
      <h2>一览</h2>
      <table><tr><th>#</th><th>名称</th><th>区域</th><th>坐标</th><th>作用</th><th>任务数</th></tr>{"".join(rows)}</table>
    </article>
"""
    (ROOT / "p" / "npcs.html").write_text(
        page_shell("NPC", '<a href="../">主页</a> / NPC', npc_body),
        encoding="utf-8",
    )

    # ---------- breathings rewrite ----------
    breath_secs = []
    for code, (cn, trainer, bcode, wen, mats, steps, trainee) in BREATH_CN.items():
        data = breathings.get(code) or {}
        aid = asset_id(data.get("Icon"))
        icon = f'<img class="icon" src="../assets/icons/powers/{aid}.png" alt="">' if aid and (ICON_DIR / f"{aid}.png").exists() else ""
        b = bosses.get(bcode)
        pos = b["Position"] if b else None
        pos_s = f"{pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}" if pos else "—"
        step_lis = "".join(
            f'<li><a class="quest-link" href="{TRAIN_ANCHOR[s][1]}">{esc(TRAIN_ANCHOR[s][0])}</a></li>' for s in steps if s in TRAIN_ANCHOR
        )
        step_lis += f'<li>击败 <a class="quest-link" href="archive/bosses/{trainee}.html">{esc(trainee)}</a></li>'
        breath_secs.append(f"""
    <article class="sec" id="{esc(code.lower())}">
      <div class="head">{icon}<div>
        <h2>{esc(cn)}</h2>
        <p class="i18n-zh">导师 <strong>{esc(trainer)}</strong> · Lv25 · {esc(mats)} · {wen} 文</p>
        <p class="i18n-en" hidden>Trainer <strong>{esc(trainer)}</strong> · Lv25 · {esc(mats)} · {wen} Wen</p>
        <p>活动区坐标（柱/Boss 点）<code>{esc(pos_s)}</code> · <a class="quest-link" href="archive/bosses/{esc(bcode)}.html">Boss 页</a></p>
      </div></div>
      <h3>解锁任务步骤</h3>
      <ol>{step_lis}</ol>
      <h3>技能数据</h3>
      <table><tr><th>键</th><th>名称</th><th>体力</th><th>CD</th><th>备注</th></tr>{skill_rows(data.get("Skills") or {})}</table>
    </article>""")

    breath_body = f"""
    <article class="sec" id="table">
      <h1>呼吸法</h1>
      <p>八大呼吸均 Lv25 起接取。导师位置见下图（取对应世界柱坐标）。消耗鬼角 / 兽核与文后完成锻炼链并击败 Trainee。</p>
      <img class="map-img" src="../assets/wiki-maps/breathings-trainers.png" alt="呼吸导师位置">
      <table>
        <tr><th>流派</th><th>导师</th><th>文</th><th>材料</th></tr>
        {"".join(f'<tr><td><a href="#{c.lower()}">{esc(BREATH_CN[c][0])}</a></td><td>{esc(BREATH_CN[c][1])}</td><td>{BREATH_CN[c][3]}</td><td>{esc(BREATH_CN[c][4])}</td></tr>' for c in BREATH_CN)}
      </table>
    </article>
    {"".join(breath_secs)}
"""
    (ROOT / "p" / "breathings.html").write_text(
        page_shell(
            "呼吸法",
            '<a href="../">主页</a> / 呼吸法',
            breath_body,
            " ".join(f'<a href="#{c.lower()}">{BREATH_CN[c][0][:1]}</a>' for c in BREATH_CN),
        ),
        encoding="utf-8",
    )

    # ---------- patch black-market with map + stock links ----------
    always = ["Frozen Heart", "Refinement Guard"]
    stock = [
        "Heavenly Boa", "Heavenly Crown", "Akatsuki Straw Hat", "Azure Guard Armour", "Gauntlet",
        "Golden Folk Mask", "Wind Earrings", "Heart of Night Earrings", "Azure Earrings",
        "Crimson Earrings", "Mimic Earrings", "Ying Yang Haori", "Black Dragon Tail", "Fox Mask",
        "Tidal Necklace", "Healing Gem Earrings", "Feather Tassel", "Dragon Kesa", "Eye Patch", "Shades",
    ]

    def item_link(name):
        if name in items:
            return f'<a class="quest-link" href="archive/items/{slug(name)}.html">{esc(items[name].get("NameCN") or name)}</a>'
        # fuzzy without special chars
        for k in items:
            if k.replace("'", "'").replace("'", "'") == name or k.replace("'", "") == name.replace("'", "").replace("'", ""):
                return f'<a class="quest-link" href="archive/items/{slug(k)}.html">{esc(items[k].get("NameCN") or k)}</a>'
        return esc(name)

    bm_path = ROOT / "p" / "black-market.html"
    bm_body = f"""
    <article class="sec" id="overview">
      <h1>黑商 Black Marketer</h1>
      <p>限时活动 <code>BlackMarketArrival</code>：在场约 <strong>1800</strong> 秒；货架 <strong>4～6</strong> 格。必出冻结之心 / 精炼护符等，其余按稀有度权重抽 Stock。</p>
      <img class="map-img" src="../assets/wiki-maps/black-market-spawns.png" alt="黑商刷新点">
    </article>
    <article class="sec" id="always">
      <h2>必带 / Always</h2>
      <ul>
        <li>{item_link("Frozen Heart")} / Frozen Heart Cache（及 ×5）</li>
        <li>{item_link("Refinement Guard")}（罗宝商品）及 ×5</li>
      </ul>
    </article>
    <article class="sec" id="stock">
      <h2>可能出现 · Stock</h2>
      <ul>{"".join(f"<li>{item_link(n)}</li>" for n in stock)}</ul>
      <p>稀有度权重：Mythic 5 / Legendary 10 / Epic 20 / Rare 30 / Common 35。</p>
    </article>
    <article class="sec" id="coords">
      <h2>刷新坐标</h2>
      <table><tr><th>#</th><th>坐标</th></tr>
      {"".join(f"<tr><td>{i}</td><td><code>{x:.2f}, {y:.2f}, {z:.2f}</code></td></tr>" for i,(x,y,z) in enumerate(BM_SPAWNS,1))}
      </table>
    </article>
"""
    bm_path.write_text(page_shell("黑商", '<a href="../">主页</a> / 黑商', bm_body, '<a href="#always">必带</a><a href="#stock">库存</a><a href="#coords">坐标</a>'), encoding="utf-8")

    # ---------- fishing expand ----------
    fish_names = [k for k, v in items.items() if (v.get("InventoryCategory") == "Fishing" or v.get("Category") == "Fishing")]
    rods = [k for k in items if "Fishing Rod" in k]
    jeso = next((s for s in shops if s.get("Name") == "Fisherman Jeso"), None)
    sofen = next((s for s in shops if "Sofen" in (s.get("Name") or "")), None)
    # Sofen may not be in shops - use hub pos
    sofen_pos = [-160.806, 796.250, 703.288]
    jeso_pos = (jeso or {}).get("Position") or [-192.001, 806.932, 602.667]
    fish_spots = [
        (1, sofen_pos[0], sofen_pos[2], "Sofen 许可"),
        (2, jeso_pos[0], jeso_pos[2], "Jeso 渔具"),
    ]
    nori = next((s for s in shops if "Nori" in (s.get("Name") or "")), None)
    if nori and nori.get("Position"):
        p = nori["Position"]
        fish_spots.append((3, p[0], p[2], "Nori 鱼饵"))
    draw_markers(fish_spots, "钓鱼相关 NPC", "许可证 Sofen · 鱼竿 Jeso · 饵 Nori", MAP_DIR / "fishing-npcs.png")

    rod_rows = []
    for r in rods:
        it = items[r]
        price = it.get("Price") or {}
        wen = price.get("Wen", "—")
        rod_rows.append(
            f'<tr><td><a class="quest-link" href="archive/items/{slug(r)}.html">{esc(it.get("NameCN") or r)}</a></td>'
            f"<td>{esc(wen)}</td><td>{esc(it.get('Rarity'))}</td></tr>"
        )
    fish_rows = []
    for f in sorted(fish_names, key=lambda x: items[x].get("Rarity") or 0, reverse=True):
        it = items[f]
        aid = asset_id(it.get("Icon"))
        ic = f'<img src="../assets/icons/items/{aid}.png" width="36" height="36" alt="">' if aid and (ORB_DIR / f"{aid}.png").exists() else ""
        fish_rows.append(
            f'<tr><td>{ic}</td><td><a class="quest-link" href="archive/items/{slug(f)}.html">{esc(it.get("NameCN") or f)}</a></td>'
            f"<td>{esc(it.get('Rarity'))}</td></tr>"
        )

    fish_body = f"""
    <article class="sec" id="how">
      <h1>钓鱼</h1>
      <ol>
        <li>找码头<strong>Dock Master Sofen</strong>（迷雾港湾），接 <code>Ill find the permit stamp(Lv 45)</code>，付 <strong>5000 文</strong>。</li>
        <li>在码头区域拾取 <a class="quest-link" href="archive/items/Permit-Stamp.html">Permit Stamp</a>，交回 Sofen → 获得 <a class="quest-link" href="archive/items/Fishing-Permit.html">Fishing Permit</a>。</li>
        <li>向 <strong>Fisherman Jeso</strong> 买竿；向 <strong>Baitmonger Nori</strong> 买饵（可选）。</li>
        <li>装备鱼竿，在可钓水域对水按提示抛竿、收竿。</li>
      </ol>
      <img class="map-img" src="../assets/wiki-maps/fishing-npcs.png" alt="钓鱼 NPC">
      <p>Sofen 约 <code>{sofen_pos[0]:.1f}, {sofen_pos[1]:.1f}, {sofen_pos[2]:.1f}</code> · Jeso 约 <code>{jeso_pos[0]:.1f}, {jeso_pos[1]:.1f}, {jeso_pos[2]:.1f}</code></p>
    </article>
    <article class="sec" id="rods">
      <h2>鱼竿</h2>
      <table><tr><th>竿</th><th>标价（文）</th><th>稀有度</th></tr>{"".join(rod_rows)}</table>
    </article>
    <article class="sec" id="fish">
      <h2>鱼类图鉴（档案）</h2>
      <table><tr><th></th><th>鱼</th><th>稀有度</th></tr>{"".join(fish_rows) or "<tr><td colspan=3>暂无</td></tr>"}</table>
    </article>
"""
    (ROOT / "p" / "fishing.html").write_text(
        page_shell("钓鱼", '<a href="../">主页</a> / 钓鱼', fish_body, '<a href="#how">流程</a><a href="#rods">鱼竿</a><a href="#fish">鱼类</a>'),
        encoding="utf-8",
    )

    # slim factions page pointer
    fac = (ROOT / "p" / "factions.html").read_text(encoding="utf-8")
    if "sides.html" not in fac:
        fac = fac.replace(
            "<h1>派系相关系统对照</h1>",
            '<h1>派系相关系统对照</h1>\n      <p class="callout">阵营进度与声望已拆至独立页：<a class="quest-link" href="sides.html">阵营</a>。</p>',
            1,
        )
        (ROOT / "p" / "factions.html").write_text(fac, encoding="utf-8")

    # ---------- forge.html ----------
    def npc_pos(name: str):
        for n in npcs:
            if n.get("Name") == name and n.get("Position"):
                return n["Position"]
        return None

    togane = npc_pos("Blacksmith Togane") or [1732.068, 694, -764.554]
    draw_markers([(1, float(togane[0]), float(togane[2]), "Togane")], "锻造 · Togane", "隐雾村铁匠", MAP_DIR / "forge-togane.png")

    craft_rows = []
    for name, it in sorted(items.items(), key=lambda x: ((x[1].get("Rarity") or 0), x[0])):
        price = it.get("Price") or {}
        if not isinstance(price, dict) or not price:
            continue
        mat_keys = [k for k in price if k not in ("Wen", "Product")]
        if not mat_keys:
            continue
        bits = []
        for k, v in price.items():
            if k == "Wen":
                bits.append(f"{v} 文")
                continue
            if k == "Product":
                continue
            link = (
                f'<a class="quest-link" href="archive/items/{slug(k)}.html">'
                f'{esc((items.get(k) or {}).get("NameCN") or k)}</a>×{esc(v)}'
            )
            bits.append(link)
        cn = it.get("NameCN") or name
        rar = it.get("Rarity") or 0
        craft_rows.append(
            f'<tr><td><a class="quest-link" href="archive/items/{slug(name)}.html">{esc(cn)}</a></td>'
            f"<td><code>{esc(name)}</code></td><td>R{rar}</td><td>{' · '.join(bits)}</td></tr>"
        )

    forge_body = f"""
    <article class="sec" id="how">
      <h1>锻造</h1>
      <p class="i18n-zh">隐雾村铁匠 <strong>Blacksmith Togane</strong> 提供锻造台。Lv65 前置任务「寻找另一座锻造台」用于开启奥乌兰侧锻台；日常图纸/武器用材料在此合成。暮落 / 初光可升阶见 <a class="quest-link" href="weapon-upgrade.html">V2 / V3</a>。</p>
      <p class="i18n-en" hidden>Blacksmith Togane in Hidden Mist Village. Lv65 quest unlocks the second Ouwland forge.</p>
      <ul>
        <li>坐标约 <code>{togane[0]:.1f}, {togane[1]:.1f}, {togane[2]:.1f}</code></li>
        <li>材料价写在物品 <code>Price</code> 字段（非纯文价）→ 下表</li>
        <li>相关：<a class="quest-link" href="refinement.html">精炼</a> · <a class="quest-link" href="ouwigahara.html">奥乌兰</a></li>
      </ul>
      <img class="map-img" src="../assets/wiki-maps/forge-togane.png" alt="Togane">
    </article>
    <article class="sec" id="recipes">
      <h2>材料配方一览（可跳转）</h2>
      <table><tr><th>成品</th><th>英文</th><th>稀有</th><th>材料</th></tr>{"".join(craft_rows) or "<tr><td colspan=4>暂无</td></tr>"}</table>
    </article>
"""
    (ROOT / "p" / "forge.html").write_text(
        page_shell("锻造", '<a href="../">主页</a> / 锻造', forge_body, '<a href="#how">流程</a><a href="#recipes">配方</a>'),
        encoding="utf-8",
    )

    # ---------- refinement.html ----------
    refine = {}
    rp = LIVE / "wiki-refinement.json"
    if rp.exists():
        refine = json.loads(rp.read_text(encoding="utf-8"))
    hagane = (refine.get("Npc") or {}).get("Position") or npc_pos("Refiner Hagane") or [1865.274, 694, -434.26]
    draw_markers([(1, float(hagane[0]), float(hagane[2]), "Hagane")], "精炼 · Hagane", "Lv65+", MAP_DIR / "refine-hagane.png")
    mults = refine.get("Multipliers") or [1, 1.05, 1.1, 1.2, 1.3, 1.4, 1.55, 1.7, 1.9, 2, 3]
    rungs = refine.get("Rungs") or {}
    rung_rows = []
    for lv in range(10):
        r = rungs.get(str(lv)) or rungs.get(lv) or {}
        ore = r.get("Ore") or "—"
        ore_link = f'<a class="quest-link" href="archive/items/{slug(ore)}.html">{esc(ore)}</a>' if ore != "—" else "—"
        fail = (r.get("FailBp") or 0) / 100
        suc = (r.get("SuccessBp") or 0) / 100
        great = (r.get("GreatBp") or 0) / 100
        mult = mults[lv] if lv < len(mults) else "—"
        next_m = mults[lv + 1] if lv + 1 < len(mults) else "—"
        rung_rows.append(
            f"<tr><td>+{lv} → +{lv+1}</td><td><code>{esc(r.get('Wen'))}</code> 文</td>"
            f"<td>{ore_link} ×{esc(r.get('OreCount'))}</td>"
            f"<td>失败 {fail:.2f}% / 成功 {suc:.2f}% / 大成功 {great:.2f}%</td>"
            f"<td><code>{esc(mult)}</code> → <code>{esc(next_m)}</code></td></tr>"
        )
    guard = refine.get("GuardItem") or "Refinement Guard"
    smelt = refine.get("SmeltRate") or {}
    refine_notes = "".join(f"<li>{esc(x)}</li>" for x in (refine.get("Notes") or {}).get("zh") or [])
    refine_body = f"""
    <article class="sec" id="how">
      <h1>精炼</h1>
      <p>精炼师 <strong>Refiner Hagane</strong>（隐雾村）· 需求等级 <strong>{esc((refine.get("Npc") or {}).get("LevelReq") or 65)}</strong>。</p>
      <p>坐标约 <code>{hagane[0]:.1f}, {hagane[1]:.1f}, {hagane[2]:.1f}</code></p>
      <img class="map-img" src="../assets/wiki-maps/refine-hagane.png" alt="Hagane">
      <ul>{refine_notes}</ul>
      <p>守护道具：<a class="quest-link" href="archive/items/{slug(guard)}.html">{esc(guard)}</a>
        · 熔炼：<a class="quest-link" href="archive/items/{slug(smelt.get('From') or 'Refinement Ore')}.html">{esc(smelt.get('From') or 'Refinement Ore')}</a>×{esc(smelt.get('FromCount') or 5)}
        → <a class="quest-link" href="archive/items/{slug(smelt.get('To') or 'Mythic Refinement Ore')}.html">{esc(smelt.get('To') or 'Mythic Refinement Ore')}</a>×{esc(smelt.get('ToCount') or 1)}</p>
    </article>
    <article class="sec" id="rungs">
      <h2>每级消耗与概率</h2>
      <p>当前等级 → 下一等级。倍率列为精炼后主属性乘数（RefineStats 第 1 项全额；第 2 项半额）。</p>
      <table><tr><th>阶</th><th>文</th><th>矿</th><th>概率（万分比÷100）</th><th>主属性倍率</th></tr>{"".join(rung_rows)}</table>
    </article>
"""
    (ROOT / "p" / "refinement.html").write_text(
        page_shell("精炼", '<a href="../">主页</a> / 精炼', refine_body, '<a href="#how">说明</a><a href="#rungs">等级表</a>'),
        encoding="utf-8",
    )

    # ---------- quests.html ----------
    qstates = {}
    qsp = LIVE / "wiki-quest-states.json"
    if qsp.exists():
        qstates = json.loads(qsp.read_text(encoding="utf-8"))

    QUEST_FLOW = [
        {
            "id": "ladder",
            "title": "主线刷怪阶梯",
            "npc": "Krue",
            "steps": [
                "风之峰 Krue：1–6 击败 3 Bandits → 7–9 击败 Zuko",
                "竹林 Tom：10–17 Bear Cub → 18–25 Mother Bear",
                "竹林 Chaka：26–33 Kaiden Sub×4 → 34–39 Kaiden（需先帮 Kazu/Noote）",
                "竹林 Wagwan：40–49 Hoyuzo Sub×4 → 50+ Hoyuzo",
            ],
        },
        {
            "id": "forge-unlock",
            "title": "锻造前置（Lv65）",
            "npc": "Blacksmith Togane",
            "steps": ["找隐雾村 Togane 接「寻找另一座锻造台」", "开启奥乌兰第二锻台", "之后可锻造高阶图纸"],
        },
        {
            "id": "sell-unlock",
            "title": "出售前置 · Ginzo 珠宝盒（Lv45）",
            "npc": "Ginzo",
            "quest": "Retrieve Ginzo's Jewelry Box",
            "steps": ["港湾 Ginzo 接取找回珠宝盒", "按任务标记取回并交还", "解锁向其出售物品"],
        },
        {
            "id": "fish-permit",
            "title": "钓鱼许可证（Lv45 · 5000 文）",
            "npc": "Dock Master Sofen",
            "quest": "Earn a Fishing Permit",
            "steps": [
                "Sofen 付 5000 文接 Ill find the permit stamp",
                "码头区拾取 Permit Stamp",
                "交回获得 Fishing Permit → 见钓鱼页",
            ],
            "link": "fishing.html",
        },
        {
            "id": "muzan",
            "title": "成鬼 · Muzan Quest",
            "npc": "Muzan",
            "quest": "Muzan Quest",
            "steps": ["声望 ≤ −40", "夜间领 Biwa Bell", "巢穴交彼岸花×9 给医生", "详见邪恶艺术页"],
            "link": "evil-arts.html#become-demon",
        },
    ]

    # quest map: ladder NPCs
    q_spots = []
    for i, nm in enumerate(["Krue", "Tom", "Chaka", "Wagwan", "Dock Master Sofen", "Ginzo", "Blacksmith Togane", "Refiner Hagane"], 1):
        p = npc_pos(nm)
        if p:
            q_spots.append((i, float(p[0]), float(p[2]), nm.split()[-1][:8]))
    if q_spots:
        draw_markers(q_spots, "关键任务 NPC", "阶梯 / 许可 / 锻造", MAP_DIR / "quests-key-npcs.png")

    flow_html = []
    for q in QUEST_FLOW:
        p = npc_pos(q["npc"])
        pos_s = f"{p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f}" if p else "—"
        more = f' · <a class="quest-link" href="{q["link"]}">详页</a>' if q.get("link") else ""
        qname = q.get("quest")
        qextra = ""
        if qname and qname in qstates:
            tasks = qstates[qname].get("Tasks") or {}
            if isinstance(tasks, dict) and tasks:
                qextra = "<p>任务键： " + " · ".join(f"<code>{esc(k)}</code>" for k in tasks) + "</p>"
        flow_html.append(f"""
    <article class="sec" id="{esc(q['id'])}">
      <h2>{esc(q['title'])}</h2>
      <p>接取 NPC：<strong>{esc(q['npc'])}</strong> · 坐标 <code>{esc(pos_s)}</code>{more}</p>
      <ol>{"".join(f"<li>{esc(s)}</li>" for s in q["steps"])}</ol>
      {qextra}
    </article>""")

    # all quest states table
    state_rows = []
    for qname, st in sorted(qstates.items(), key=lambda x: x[0]):
        tasks = st.get("Tasks") if isinstance(st, dict) else None
        if isinstance(tasks, dict):
            ttxt = " · ".join(str(k) for k in tasks.keys()) or "—"
        elif isinstance(tasks, list):
            ttxt = " / ".join(str(x) for x in tasks)
        else:
            ttxt = esc(str(st)[:120])
        aid = slug(qname)
        state_rows.append(f"<tr id=\"q-{esc(aid)}\"><td><strong>{esc(qname)}</strong></td><td>{esc(ttxt)}</td></tr>")

    quest_body = f"""
    <article class="sec">
      <h1>任务</h1>
      <p>接任务时对话选项文字即任务名。静态 NPC 可能需靠近区域才加载。下图为常用任务 NPC。</p>
      <img class="map-img" src="../assets/wiki-maps/quests-key-npcs.png" alt="任务 NPC">
      <p class="callout">呼吸训练任务见 <a class="quest-link" href="breathings.html">呼吸法</a>；魔球训练见 <a class="quest-link" href="evil-arts.html">邪恶艺术</a>。</p>
    </article>
    {"".join(flow_html)}
    <article class="sec" id="all">
      <h2>QuestStates 全表（{len(qstates)}）</h2>
      <p>来自游戏 QuestStates 模块的任务进度键；详细对话步骤仍按上方流程与各系统页展开。</p>
      <table><tr><th>任务</th><th>任务键 / 阶段</th></tr>{"".join(state_rows) or "<tr><td colspan=2>无数据</td></tr>"}</table>
    </article>
"""
    (ROOT / "p" / "quests.html").write_text(
        page_shell(
            "任务",
            '<a href="../">主页</a> / 任务',
            quest_body,
            '<a href="#ladder">阶梯</a><a href="#fish-permit">钓鱼证</a><a href="#muzan">成鬼</a><a href="#all">全表</a>',
        ),
        encoding="utf-8",
    )

    print("maps + pages done")


if __name__ == "__main__":
    main()
