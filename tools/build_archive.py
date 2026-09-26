# -*- coding: utf-8 -*-
"""Build PS2 Wiki Archive: items / chests / bosses pages + maps + icons."""
from __future__ import annotations

import html
import json
import re
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from archive_flows import FLOW_CSS, schematic_flow, usage_and_links

ROOT = Path(r"D:\Desktop\ProjectSlayer2_WIKI")
LIVE = ROOT / "data" / "_live"
OUT_ITEMS = ROOT / "p" / "archive" / "items"
OUT_CHESTS = ROOT / "p" / "archive" / "chests"
OUT_BOSSES = ROOT / "p" / "archive" / "bosses"
ICON_DIR = ROOT / "assets" / "icons" / "items"
BOSS_ICON_DIR = ROOT / "assets" / "icons" / "bosses"
CHEST_ICON_DIR = ROOT / "assets" / "icons" / "chests"
SKILL_ICON_DIR = ROOT / "assets" / "icons" / "skills"
MAP_DIR = ROOT / "assets" / "archive-maps"
CLEAN = ROOT / "assets" / "ouwland-map-clean.png"

# Bosses missing from WorldBosses.Get() but present in NpcDataTable / chest links
EXTRA_BOSS_POS = {
    # Final Selection spawn crystal / drowned chamber approach
    "Lost": [-2547.569, 278.0, 31.729],
    # Iceveil Settlement crystal
    "YetiDemon": [-208.841, 1352.665, -2596.467],
}

TL = (-3087.361, -3989.256)
BR = (2977.139, 1635.244)

RARITY = {
    1: ("常见", "#DCE4F0"),
    2: ("罕见", "#60D682"),
    3: ("稀有", "#5CAAFF"),
    4: ("史诗", "#B06BFF"),
    5: ("传奇", "#F0BE50"),
    6: ("神话", "#C878FF"),
    7: ("至高", "#FF5C78"),
}

CAT_CN = {
    "Haori": "羽织",
    "Face": "面饰",
    "Outfits": "服装",
    "Neck": "颈饰",
    "Head": "头饰",
    "Weapons": "武器",
    "Katana": "日轮刀",
    "Schematics": "图纸",
    "Quest Items": "任务物品",
    "Materials": "材料",
    "Fishing": "钓鱼",
    "Ear": "耳饰",
    "Evil Art Orbs": "邪术宝珠",
    "Waist": "腰饰",
    "Potions": "药水",
    "Back": "背饰",
    "Gourds": "葫芦",
    "Style": "风格",
    "Misc": "杂项",
    "Mounts": "坐骑",
    "Items": "物品",
}

CSS_VER = "20260926v"

SKILL_FIXED = {
    "Base/Combat": "普攻 / 近战连段",
    "Base/Dash": "冲刺",
    "Base/Blocking": "格挡",
}

REGION_CN = {
    "Mistfall Harbor": "迷雾港湾",
    "Windy Peak": "风之峰",
    "Bamboo Grove": "竹林",
    "Butterfly Estate": "蝴蝶庄园",
    "Hidden Mist Village": "隐雾村",
    "Iceveil Valley": "冰纱谷",
    "Misc": "多区域 / 活动",
}


def skill_label(path: str) -> str:
    if path in SKILL_FIXED:
        return SKILL_FIXED[path]
    if path.startswith("SlayerNpcs/"):
        return f"柱之技组 · {path.split('/', 1)[1]}"
    if path.startswith("SlayerUltimates/"):
        return f"柱之大招 · {path.split('/', 1)[1]}"
    if path.startswith("EvilArtNpcs/"):
        return f"邪术技组 · {path.split('/', 1)[1]}"
    if path.startswith("EvilArtUltimates/"):
        return f"邪术大招 · {path.split('/', 1)[1]}"
    if path.startswith("Clan/"):
        leaf = path.split("/", 1)[1]
        if leaf == "Indomitable Will":
            return "氏族技 · 不屈意志"
        return f"氏族技 · {leaf}"
    if path.startswith("SealedChest/"):
        return f"封印箱技 · {path}"
    if "/" in path:
        return f"技能组 · {path}"
    return f"专属技包 · {path}"


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", name, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s.strip())
    return s or "item"


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def world_to_px(x: float, z: float, w: int, h: int) -> tuple[float, float]:
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


def asset_id(icon: str | None) -> str | None:
    if not icon:
        return None
    m = re.search(r"(\d{6,})", str(icon))
    return m.group(1) if m else None


def download_icon(aid: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 100:
        return True
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


def chance_text(c) -> str:
    if c is None:
        return "—"
    try:
        c = float(c)
    except (TypeError, ValueError):
        return str(c)
    if c <= 0:
        return "—"
    if c >= 1:
        return "100%" if c == 1 else f"×{c:g}"
    pct = c * 100
    if pct >= 1:
        return f"{pct:.2g}%"
    return f"{pct:.2f}%"


def parse_reward(val):
    if isinstance(val, (int, float)):
        return float(val), None
    if isinstance(val, dict):
        return val.get("Chance"), val.get("Pity")
    return None, None


def page_shell(title: str, crumb: str, body: str, extra_style: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>{esc(title)} · Slayers 2 Wiki</title>
  <link rel="icon" href="../../../favicon.svg" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../../css/wiki.css?v={CSS_VER}">
  <style>
    .page{{max-width:var(--max);margin:0 auto;padding:0 1.25rem 3rem;position:relative;z-index:1}}
    .crumb{{color:var(--muted);font-size:.85rem;margin:.5rem 0 1.25rem}}
    .crumb a{{color:var(--gold)}}
    .sec{{margin-bottom:1.25rem;border:1px solid var(--line);background:var(--panel);padding:1rem 1.1rem}}
    .sec h1,.sec h2{{margin:0 0 .65rem;font-size:1.15rem}}
    .sec h1{{font-size:1.35rem}}
    .sec p,.sec li{{color:var(--muted);font-size:.92rem}}
    .sec ul{{margin:.35rem 0 0;padding-left:1.2rem}}
    .sec strong{{color:var(--cream)}}
    .sec table{{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}}
    .sec th,.sec td{{border:1px solid var(--line);padding:.4rem .5rem;text-align:left;vertical-align:top}}
    .sec th{{color:var(--gold-deep);font-weight:600;background:rgba(255,255,255,.03)}}
    .sec td{{color:var(--muted)}}
    .sec code{{color:var(--gold-deep)}}
    .icon{{width:72px;height:72px;object-fit:contain;border:1px solid var(--line);background:#0a0a0a;border-radius:6px}}
    .icon-sm{{width:40px;height:40px}}
    .icon-missing{{display:inline-block;width:40px;height:40px;border:1px dashed var(--line);background:rgba(255,255,255,.03);border-radius:6px;vertical-align:middle}}
    .head{{display:flex;gap:1rem;align-items:flex-start}}
    .rarity{{display:inline-block;padding:.12rem .5rem;border-radius:4px;font-size:.8rem;font-weight:700;letter-spacing:.02em;color:#0a0a0a;text-shadow:0 0 1px rgba(255,255,255,.45)}}
    .map-img{{display:block;width:100%;height:auto;border:1px solid var(--line);margin-top:.55rem}}
    {FLOW_CSS}
    {extra_style}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="../../../"><span>Slayers 2 Wiki</span></a>
    <span class="top-ver">档案</span>
  </header>
  <main class="page">
    <p class="crumb">{crumb}</p>
    {body}
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>档案</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="../../../">返回主页</a>
  </footer>
<script src="../../../js/i18n.js?v={CSS_VER}"></script>
</body>
</html>
"""


def shallow_shell(title: str, crumb: str, body: str, depth: int = 1) -> str:
    """depth=1 for p/*.html, depth=0 unused."""
    prefix = "../" * depth
    fav = f"{prefix}favicon.svg"
    css = f"{prefix}css/wiki.css?v={CSS_VER}"
    home = f"{prefix}" if depth else "./"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>{esc(title)} · Slayers 2 Wiki</title>
  <link rel="icon" href="{fav}" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{css}">
  <style>
    .page{{max-width:var(--max);margin:0 auto;padding:0 1.25rem 3rem;position:relative;z-index:1}}
    .crumb{{color:var(--muted);font-size:.85rem;margin:.5rem 0 1.25rem}}
    .crumb a{{color:var(--gold)}}
    .sec{{margin-bottom:1.25rem;border:1px solid var(--line);background:var(--panel);padding:1rem 1.1rem}}
    .sec h1,.sec h2{{margin:0 0 .65rem;font-size:1.15rem}}
    .sec h1{{font-size:1.35rem}}
    .sec h3{{margin:1rem 0 .4rem;font-size:1rem;color:var(--cream)}}
    .sec p,.sec li{{color:var(--muted);font-size:.92rem}}
    .sec ul{{margin:.35rem 0 0;padding-left:1.2rem}}
    .sec strong{{color:var(--cream)}}
    .sec table{{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}}
    .sec th,.sec td{{border:1px solid var(--line);padding:.4rem .5rem;text-align:left;vertical-align:top}}
    .sec th{{color:var(--gold-deep);font-weight:600;background:rgba(255,255,255,.03)}}
    .sec td{{color:var(--muted)}}
    .sec code{{color:var(--gold-deep)}}
    .icon{{width:56px;height:56px;object-fit:contain;border:1px solid var(--line);background:#0a0a0a;border-radius:6px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.65rem}}
    .card{{display:flex;gap:.65rem;align-items:center;border:1px solid var(--line);padding:.55rem .65rem;background:rgba(255,255,255,.02);color:inherit;text-decoration:none}}
    .card:hover{{border-color:rgba(255,208,70,.4)}}
    .card strong{{display:block;color:var(--cream);font-size:.9rem}}
    .card span{{font-size:.78rem;color:var(--muted)}}
    .map-toolbar{{display:flex;flex-wrap:wrap;gap:.45rem;align-items:center;margin:.55rem 0 .35rem}}
    .map-toolbar button{{appearance:none;border:1px solid var(--line);background:rgba(255,255,255,.04);color:var(--cream);font:inherit;font-size:.82rem;padding:.35rem .7rem;cursor:pointer}}
    .map-zoom-label{{font-size:.82rem;color:var(--muted);min-width:3.2rem}}
    .map-stage{{position:relative;margin-top:.35rem;border:1px solid var(--line);overflow:hidden;background:#0a0a0a;touch-action:none;user-select:none;height:min(72vh,820px);min-height:320px}}
    .map-viewport{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(1);transform-origin:center center;will-change:transform}}
    .map-viewport img.map-img{{display:block;width:100%;height:100%;object-fit:fill;pointer-events:none;-webkit-user-drag:none}}
    .map-hint{{margin:.55rem 0 0;font-size:.82rem;color:var(--muted)}}
    .rarity,.card span.rarity{{display:inline-block;padding:.12rem .5rem;border-radius:4px;font-size:.8rem;font-weight:700;letter-spacing:.02em;color:#0a0a0a;text-shadow:0 0 1px rgba(255,255,255,.45)}}
    .head{{display:flex;gap:1rem;align-items:flex-start}}
    .map-img.static{{display:block;width:100%;height:auto;border:1px solid var(--line);margin-top:.55rem}}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="{home}"><span>Slayers 2 Wiki</span></a>
    <span class="top-ver">档案</span>
  </header>
  <main class="page">
    <p class="crumb">{crumb}</p>
    {body}
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>档案</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="{home}">返回主页</a>
  </footer>
</body>
</html>
"""


def skill_display_name(sk: str) -> str:
    """Turn NDT skill path into readable name."""
    if not sk:
        return ""
    # drop wildcards / folder prefixes; keep leaf
    leaf = sk.split("/")[-1].replace("*", "").strip()
    if not leaf or leaf in ("Base", "Combat", "Dash", "Blocking"):
        return ""
    return leaf


def draw_markers(spots: list[tuple], title: str, subtitle: str, out_path: Path):
    base = Image.open(CLEAN).convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_title = load_font(20)
    font_sub = load_font(13)
    font_num = load_font(12)
    font_lab = load_font(11)
    draw.rectangle((0, 0, w, 48), fill=(8, 8, 10, 210))
    draw.text((12, 6), title, fill=(255, 220, 120, 255), font=font_title)
    draw.text((12, 28), subtitle, fill=(200, 200, 200, 255), font=font_sub)
    colors = [
        (255, 196, 60),
        (255, 120, 100),
        (100, 200, 255),
        (140, 220, 140),
        (200, 150, 255),
        (255, 160, 80),
        (80, 220, 200),
        (255, 100, 160),
    ]
    for i, (num, x, z, label) in enumerate(spots):
        px, py = world_to_px(x, z, w, h)
        c = colors[i % len(colors)] + (255,)
        r = 11 if len(spots) > 15 else 13
        draw.ellipse((px - r - 2, py - r - 2, px + r + 2, py + r + 2), fill=(0, 0, 0, 180))
        draw.ellipse((px - r, py - r, px + r, py + r), fill=c)
        t = str(num)
        bb = draw.textbbox((0, 0), t, font=font_num)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        draw.text((px - tw / 2, py - th / 2 - 1), t, fill=(20, 20, 20, 255), font=font_num)
        if len(spots) <= 20 and label:
            lx, ly = px + 14, py - 10
            lb = draw.textbbox((lx, ly), label, font=font_lab)
            pad = 2
            draw.rectangle((lb[0] - pad, lb[1] - pad, lb[2] + pad, lb[3] + pad), fill=(0, 0, 0, 190))
            draw.text((lx, ly), label, fill=(255, 255, 255, 255), font=font_lab)
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path, "PNG", optimize=True)


def main():
    enriched_path = LIVE / "items-enriched.json"
    items = json.loads(
        (enriched_path if enriched_path.exists() else LIVE / "items-catalog.json").read_text(encoding="utf-8")
    )
    bosses = json.loads((LIVE / "world-bosses.json").read_text(encoding="utf-8"))
    chests = json.loads((LIVE / "chests-loot.json").read_text(encoding="utf-8"))
    meta = {}
    meta_path = LIVE / "archive-meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    CHEST_CN = meta.get("chest_cn") or {}
    BOSS_CN = meta.get("boss_cn") or {}
    shops = []
    shops_path = LIVE / "shops.json"
    if shops_path.exists():
        shops = json.loads(shops_path.read_text(encoding="utf-8"))
    npc_data = {}
    for ndt_name in ("wiki-npc-data-full.json", "npc-data.json"):
        ndt_path = LIVE / ndt_name
        if ndt_path.exists():
            npc_data = json.loads(ndt_path.read_text(encoding="utf-8"))
            break
    chest_spawns = {}
    cs_path = LIVE / "chest-spawns.json"
    if cs_path.exists():
        chest_spawns = json.loads(cs_path.read_text(encoding="utf-8"))

    # Merge bosses linked by chests / NpcData but missing from WorldBosses
    known_codes = {b.get("Code") for b in bosses if b.get("Code")}
    extra_codes: dict[str, str] = {}  # code -> display name
    ctb = meta.get("chest_to_bosses") or {}
    if isinstance(ctb, dict):
        for _chest, blist in ctb.items():
            for b in blist or []:
                code = b.get("Code")
                if code and code not in known_codes:
                    extra_codes[code] = b.get("Name") or code
    cb_path = LIVE / "chest-bosses.json"
    if cb_path.exists():
        raw_cb = json.loads(cb_path.read_text(encoding="utf-8"))
        if isinstance(raw_cb, list):
            for row in raw_cb:
                code = row.get("Code")
                if code and code not in known_codes:
                    extra_codes[code] = row.get("Name") or code
    # Always ensure Lost
    if "Lost" not in known_codes:
        extra_codes["Lost"] = "Lost"

    for code, dname in sorted(extra_codes.items()):
        nd = npc_data.get(code) or {}
        pos = EXTRA_BOSS_POS.get(code)
        if not pos:
            # try Final Selection crystal from spawn crystals dump
            sc_path = LIVE / "wiki-spawn-crystals.json"
            if sc_path.exists():
                for c in json.loads(sc_path.read_text(encoding="utf-8")):
                    if "Final" in str(c.get("Name") or "") and c.get("Position"):
                        pos = c["Position"]
                        break
        if not pos:
            pos = [0, 0, 0]
        icon = nd.get("Icon") or ""
        if not icon and nd.get("Equipped_Tool"):
            tool = items.get(nd["Equipped_Tool"]) or {}
            icon = tool.get("Icon") or ""
        bosses.append(
            {
                "Name": nd.get("Name") or dname,
                "DisplayName": nd.get("Name") or dname,
                "Code": code,
                "Icon": icon,
                "Position": pos,
                "Rewards": nd.get("Rewards") or {},
            }
        )
        known_codes.add(code)
    print(f"bosses {len(bosses)} (extra {len(extra_codes)}: {', '.join(sorted(extra_codes)) or '—'})")

    for d in (OUT_ITEMS, OUT_CHESTS, OUT_BOSSES, ICON_DIR, BOSS_ICON_DIR, CHEST_ICON_DIR, SKILL_ICON_DIR, MAP_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # Index helpers
    item_slugs = {name: slug(name) for name in items}
    boss_by_name = {}
    boss_by_code = {}
    for b in bosses:
        boss_by_code[b["Code"]] = b
        boss_by_name[b.get("DisplayName") or b["Name"]] = b
        boss_by_name[b["Name"]] = b

    chest_slugs = {name: slug(name) for name in chests}
    shop_by_npc = {s["Name"]: s for s in shops if s.get("Name")}

    # Reverse: item -> sold by with pos (support multi Positions)
    sold_pos: dict[str, list] = defaultdict(list)

    def _shop_entries(s: dict) -> list:
        name = s.get("Name")
        region = s.get("Region")
        positions = s.get("Positions") or []
        if not positions and s.get("Position"):
            positions = [s["Position"]]
        rows = []
        for pos in positions:
            rows.append({"npc": name, "pos": pos, "region": region})
        if not rows:
            rows.append({"npc": name, "pos": None, "region": region})
        return rows

    for s in shops:
        entries = _shop_entries(s)
        names = set(s.get("Items") or [])
        shop = s.get("Shop") or {}
        if isinstance(shop, dict):
            names |= set(shop.keys())
        for it in names:
            for e in entries:
                sold_pos[it].append(e)
    # ---------- icons ----------
    icon_jobs = []
    for name, it in items.items():
        aid = asset_id(it.get("Icon"))
        if aid:
            icon_jobs.append((aid, ICON_DIR / f"{aid}.png"))
        for sk in it.get("Skills") or []:
            if isinstance(sk, dict):
                said = asset_id(sk.get("icon") or sk.get("Icon"))
                if said:
                    icon_jobs.append((said, SKILL_ICON_DIR / f"{said}.png"))
    for b in bosses:
        aid = asset_id(b.get("Icon"))
        if aid:
            icon_jobs.append((aid, BOSS_ICON_DIR / f"{aid}.png"))
    for cname, c in chests.items():
        aid = asset_id(c.get("icon"))
        if aid:
            icon_jobs.append((aid, CHEST_ICON_DIR / f"{aid}.png"))

    # unique by dest path
    seen = set()
    uniq = []
    for aid, dest in icon_jobs:
        key = str(dest)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((aid, dest))

    print(f"download icons {len(uniq)}…")
    ok_n = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(download_icon, a, d): a for a, d in uniq}
        for fut in as_completed(futs):
            if fut.result():
                ok_n += 1
    print(f"icons ok {ok_n}/{len(uniq)}")

    def icon_img(aid: str | None, kind: str, *, small: bool = False) -> str:
        if not aid:
            return ""
        folder = {"item": "items", "boss": "bosses", "chest": "chests", "skill": "skills"}.get(kind, "items")
        rel = f"../../../assets/icons/{folder}/{aid}.png"
        path = ROOT / "assets" / "icons" / folder / f"{aid}.png"
        # skill icons also try items folder (shared asset ids)
        if not path.exists() and kind == "skill":
            alt = ICON_DIR / f"{aid}.png"
            if alt.exists():
                path = alt
                rel = f"../../../assets/icons/items/{aid}.png"
        cls = "icon icon-sm" if small else "icon"
        if path.exists() and path.stat().st_size > 100:
            return f'<img class="{cls}" src="{rel}" alt="">'
        # last resort: leave empty placeholder (CDN asset-thumbnail 404s for many skill ids)
        return f'<span class="{cls} icon-missing" title="icon {esc(aid)}"></span>'

    SPECIAL_CN = {
        "TameWildHorse": ('驯服野马', '<a class="quest-link" href="../../mounts.html">坐骑页</a>'),
        "StudyProp": ("地下研习点", "长按 Study 领取图纸"),
        "SerpentChest": ("蛇箱", "需蛇之钥匙 Serpent Key"),
        "TobeiGauntlet": ("石匠 Tobei", "三座雕像进度满后领取拳套图纸"),
        "HatsuCape": ("织匠 Hatsu", "持遗失披风兑换披风图纸"),
        "ToganeCapstone": ("铁匠 Togane", "集齐 9 张暮落门槛图纸后领取上衣/下装图纸"),
        "Starter": ("开局获得", "角色初始持有"),
        "ClanUnlock": ("家族解锁", "有技法的血统自动出现"),
        "Corps": ("鬼杀队", "队士鸟使与猎杀联络"),
        "FinalSelection": ("最终选拔", "通关终选后发放"),
        "QuestCarry": ("任务携带物", "任务过程中拾取并持有交付"),
        "QuestIsao": ("渔夫伊佐夫", "钓鱼线相关任务"),
        "FieldUse": ("野外消耗品", "补给 / 商店常见"),
        "Iceveil": ("冰纱谷", "寒冷区域相关发放"),
        "Cave": ("洞窟探索", "洞穴区域获取"),
        "LostRelated": ("遗失相关", "终选 Boss「遗失」关联"),
        "BossYahari": ("Boss 矢琶羽", "表外掉落或兑换"),
        "Cosmetic": ("外观装扮", "LiveConfig 未挂 ItemSources"),
        "FirstlightStudy": ("初光研习", "图纸点未公开；材料见宝箱"),
    }
    NPC_CN = {
        "Black Marketer": "黑商",
        "Kuro": "黑",
        "Rika": "理香",
        "Raze": "雷兹",
        "Ginzo": "银造",
        "Alchemist Meku": "炼金术师·梅库",
        "Fisherman Jeso": "渔夫·杰索",
        "Ren": "莲",
        "Elara": "艾拉拉",
        "Winter Store Rep Lynx": "冬店代表·林克斯",
        "Baitmonger Nori": "饵贩·海苔",
    }
    STATION_CN = {"Ouwland": "奥乌兰锻造", "Ouwigahara": "奥乌兰爬塔锻造", "Hidden Mist": "隐雾村锻造"}

    def boss_label(name_or_code: str) -> str:
        return BOSS_CN.get(name_or_code) or name_or_code

    def chest_label(cname: str) -> str:
        return CHEST_CN.get(cname) or cname

    def format_source(s: dict) -> str:
        where = s.get("Where") or ""
        kind = s.get("Kind") or "other"
        ch = chance_text(s.get("Chance"))
        meta = s.get("Meta") or {}
        if kind == "tame" or where == "TameWildHorse":
            title, link = SPECIAL_CN["TameWildHorse"]
            wen = meta.get("wen") or 15000
            return f'{title} · {link}（{wen:,} 文）'
        if kind == "special" or where in SPECIAL_CN:
            title, note = SPECIAL_CN.get(where, (where, meta.get("note") or ""))
            extra = meta.get("note") or note
            return f'{esc(title)} · {esc(extra)}'
        if kind == "boss":
            bcode = meta.get("bossCode")
            bname = meta.get("bossName") or where
            label = boss_label(bname)
            if not bcode:
                for key, b in boss_by_name.items():
                    if where == key or where == b.get("DisplayName") or where == b["Code"]:
                        bcode = b["Code"]
                        label = boss_label(b.get("DisplayName") or b["Name"])
                        break
            pity = meta.get("pity")
            pity_s = f' · 保底 {pity}' if pity else ""
            if bcode:
                href = f'../bosses/{esc(slug(bcode))}.html'
                return f'Boss 掉落 · <a class="quest-link" href="{href}">{esc(label)}</a> · {esc(ch)}{esc(pity_s)}'
            return f'Boss 掉落 · <strong>{esc(label)}</strong> · {esc(ch)}{esc(pity_s)}'
        if kind == "chest" or where in chests:
            cname = meta.get("chest") or where
            cl = chest_label(cname)
            href = f'../chests/{esc(chest_slugs.get(cname, slug(cname)))}.html'
            line = f'宝箱 · <a class="quest-link" href="{href}">{esc(cl)}</a>'
            if meta.get("guaranteed"):
                line += " · <strong>保底</strong>"
            else:
                line += f" · {esc(ch)}"
            note = meta.get("note")
            bosses = meta.get("bosses") or []
            if bosses:
                links = []
                for b in bosses[:12]:
                    bn = boss_label(b.get("Name") or b.get("Code"))
                    bc = b.get("Code")
                    if bc:
                        links.append(f'<a class="quest-link" href="../bosses/{esc(slug(bc))}.html">{esc(bn)}</a>')
                    else:
                        links.append(esc(bn))
                more = f' 等 {len(bosses)} 个' if len(bosses) > 12 else ""
                line += f'<br><span style="font-size:.82rem;opacity:.85">击杀下列 Boss 后掉落该箱：{"、".join(links)}{more}</span>'
            elif note:
                line += f'<br><span style="font-size:.82rem;opacity:.85">{esc(note)}</span>'
            return line
        if kind == "shop" or where.startswith("Sold by "):
            npc = meta.get("npc") or where.replace("Sold by ", "")
            npc_l = NPC_CN.get(npc, npc)
            price = meta.get("price")
            wen = meta.get("wen")
            price_s = ""
            if isinstance(price, dict) and price:
                bits = []
                for k, v in price.items():
                    if k == "Wen":
                        bits.append(f"{v} 文")
                    elif isinstance(v, (int, float)):
                        bits.append(f"{NPC_CN.get(k, k) if False else k} ×{v}" if k != "Wen" else f"{v} 文")
                        if k != "Wen":
                            bits[-1] = f"{k}×{v}"
                    else:
                        bits.append(str(k))
                # simplify
                bits = []
                for k, v in price.items():
                    if k == "Wen":
                        bits.append(f"{v} 文")
                    elif isinstance(v, (int, float)):
                        bits.append(f"{k}×{v}")
                price_s = " · " + " / ".join(bits) if bits else ""
            elif wen:
                price_s = f" · {wen} 文"
            region = meta.get("region")
            reg_s = f" · {esc(region)}" if region else ""
            return f'商店购买 · <strong>{esc(npc_l)}</strong>{esc(price_s)}{reg_s}'
        if kind == "craft" or where.startswith("Crafted"):
            station = meta.get("station") or where.replace("Crafted at ", "")
            price = meta.get("price")
            mat = ""
            if isinstance(price, dict) and price:
                bits = []
                for k, v in price.items():
                    if k == "Wen":
                        bits.append(f"{v} 文")
                    else:
                        bits.append(f"{k}×{v}")
                mat = " · 材料 " + " / ".join(bits)
            return f'锻造 · <strong>{esc(STATION_CN.get(station, station))}</strong>{esc(mat)}'
        if kind == "fish" or where == "Fished up":
            return f'钓鱼获得 · {esc(ch)}'
        if kind == "quest" or where.startswith("Quest:"):
            q = meta.get("quest") or where.replace("Quest:", "").strip()
            qslug = re.sub(r"[^\w\s\-]", "", q, flags=re.UNICODE)
            qslug = re.sub(r"\s+", "-", qslug.strip()) or "x"
            return (
                f'任务奖励 · <a class="quest-link" href="../../quests.html#q-{esc(qslug)}">{esc(q)}</a>'
                f' · {esc(ch)}'
            )
        return f"{esc(where)} · {esc(ch)}"

    # ---------- item pages ----------
    by_cat: dict[str, list] = defaultdict(list)
    for name, it in sorted(items.items(), key=lambda x: ((x[1].get("Rarity") or 0), x[0])):
        cat = it.get("InventoryCategory") or it.get("Category") or "Items"
        by_cat[cat].append(name)
        s = item_slugs[name]
        name_cn = it.get("NameCN") or name
        rar = it.get("Rarity") or 0
        rar_name, rar_color = RARITY.get(rar, (f"R{rar}", "#888"))
        aid = asset_id(it.get("Icon"))
        stats_cn = it.get("StatsCN") or it.get("Stats") or {}
        if isinstance(stats_cn, dict) and stats_cn:
            stats_rows = "".join(
                f"<tr><td>{esc(k)}</td><td><code>{esc(v)}</code></td></tr>" for k, v in stats_cn.items()
            )
            stats_block = f"<h2>数据 / 加成</h2><table><tr><th>属性</th><th>数值</th></tr>{stats_rows}</table>"
        else:
            stats_block = "<h2>数据 / 加成</h2><p>无额外属性表（或仅作外观 / 任务物）。</p>"

        # weapon / tool skills
        skills = it.get("Skills") or []
        skills_block = ""
        if isinstance(skills, list) and skills:
            srows = []
            for sk in skills:
                if not isinstance(sk, dict):
                    continue
                sn = sk.get("Name") or "?"
                key = sk.get("Key") or "—"
                cd = sk.get("CoolDown")
                stam = sk.get("Stamina")
                hold = sk.get("Max_Hold")
                boss = sk.get("Boss")
                icon = sk.get("icon") or ""
                sk_aid = asset_id(icon) if icon else None
                ic = icon_img(sk_aid, "skill", small=True) if sk_aid else ""
                bits = []
                if cd is not None:
                    bits.append(f"CD {cd}s")
                if stam is not None:
                    bits.append(f"体力 {stam}")
                if hold is not None:
                    bits.append(f"蓄力 ≤{hold}s")
                if boss:
                    bits.append(f"关联 {boss}")
                srows.append(
                    f"<tr><td>{ic}</td><td><strong>{esc(sn)}</strong></td><td><code>{esc(key)}</code></td>"
                    f"<td>{esc(' · '.join(bits) if bits else '—')}</td></tr>"
                )
            if srows:
                skills_block = (
                    "<h2>关联技能</h2>"
                    "<table><tr><th></th><th>技能</th><th>键位</th><th>数据</th></tr>"
                    + "".join(srows)
                    + "</table>"
                )

        # combat meta line
        meta_bits = []
        for label, key in (
            ("精通", "Mastery"),
            ("职业", "Class"),
            ("呼吸", "Breathing"),
            ("邪术", "DemonArt"),
            ("系列", "Series"),
            ("技能分类", "SkillCategory"),
        ):
            if it.get(key):
                meta_bits.append(f"{label} <code>{esc(it[key])}</code>")
        if it.get("RefineStats"):
            rs = it["RefineStats"]
            if isinstance(rs, list):
                meta_bits.append("可精炼属性 " + " / ".join(f"<code>{esc(x)}</code>" for x in rs))
        combat_meta = ("<p>" + " · ".join(meta_bits) + "</p>") if meta_bits else ""

        # potion effect note
        pe = it.get("PotionEffect") or {}
        potion_block = ""
        if pe:
            potion_block = f"<h2>药水效果</h2><p>{esc(pe.get('note') or '见数据表')}</p>"
            if pe.get("heal") is not None:
                potion_block += f"<p>瞬回生命：<code>+{esc(pe['heal'])}</code></p>"
            if pe.get("stat"):
                potion_block += (
                    f"<p>增益属性：<code>{esc(pe['stat'])}</code>"
                    f" · 强度 <code>{esc(pe.get('magnitude'))}</code>"
                    f" · 持续 <code>{esc(pe.get('duration'))}</code> 秒</p>"
                )

        price = it.get("Price") or {}
        price_txt = "—"
        if isinstance(price, dict) and price:
            bits = []
            for k, v in price.items():
                if k == "Product":
                    bits.append(f"罗宝商品 #{v}")
                elif k == "Wen":
                    bits.append(f"{v} 文")
                else:
                    bits.append(f"{k} ×{v}" if isinstance(v, (int, float)) else f"{k} {v}")
            price_txt = " / ".join(bits)

        # fallback: shop table price (Elixir 等只在 Shop 里标价)
        purchases = sold_pos.get(name) or []
        if price_txt == "—" and purchases:
            for p in purchases:
                npc = p.get("npc")
                shop = (shop_by_npc.get(npc) or {}).get("Shop") or {}
                row = shop.get(name)
                if isinstance(row, dict) and row:
                    bits = []
                    for k, v in row.items():
                        if k in ("SuccessDialogue", "FailDialogue", "Model", "RequiresSide"):
                            continue
                        if k == "Wen":
                            bits.append(f"{v} 文")
                        elif isinstance(v, (int, float)):
                            bits.append(f"{k}×{v}")
                    if bits:
                        price_txt = " / ".join(bits)
                        break

        sources = it.get("Sources") or []
        src_lis = "".join(f"<li>{format_source(s)}</li>" for s in sources) or "<li>来源待补充</li>"

        # purchase map if sold
        buy_map = ""
        spots = []
        for i, p in enumerate(purchases, 1):
            pos = p.get("pos")
            if pos and len(pos) >= 3:
                spots.append((i, float(pos[0]), float(pos[2]), NPC_CN.get(p.get("npc") or "", p.get("npc") or "")))
        if spots:
            map_path = MAP_DIR / f"buy-{s}.png"
            draw_markers(spots, f"购买点 · {name_cn}", f"价格 {price_txt}", map_path)
            buy_map = f'<h2>购买位置</h2><p>价格：<strong>{esc(price_txt)}</strong></p><img class="map-img" src="../../../assets/archive-maps/buy-{esc(s)}.png" alt="购买点">'

        # schematic acquire flow
        acquire_block = ""
        if cat == "Schematics" or name.endswith("Schematic"):
            acquire_block = schematic_flow(name, it, items, draw_markers)

        detail_block = usage_and_links(name, it, items, item_slugs)

        # price with blue links in intro
        price_linked = price_txt
        if isinstance(price, dict) and price:
            pl = []
            for k, v in price.items():
                if k == "Product":
                    pl.append(f"罗宝商品 #{v}")
                elif k == "Wen":
                    pl.append(f"{v} 文")
                elif k in item_slugs:
                    pl.append(
                        f'<a class="quest-link" href="{esc(item_slugs[k])}.html">{esc((items.get(k) or {}).get("NameCN") or k)}</a>×{esc(v)}'
                    )
                else:
                    pl.append(f"{esc(k)}×{esc(v)}")
            price_linked = " / ".join(pl)

        body = f"""
    <article class="sec">
      <div class="head">
        {icon_img(aid, "item")}
        <div>
          <h1>{esc(name_cn)}</h1>
          <p class="en" style="margin:.15rem 0;font-size:.85rem;opacity:.7"><code>{esc(name)}</code></p>
          <p><span class="rarity" style="background:{rar_color}">{esc(rar_name)}</span>
            · {esc(CAT_CN.get(cat, cat))}</p>
        </div>
      </div>
    </article>
    <article class="sec">
      <h2>介绍</h2>
      <p>{esc(it.get("DescriptionCN") or it.get("Description") or "（无描述）")}</p>
      <p>标价：<strong>{price_linked}</strong></p>
      {combat_meta}
    </article>
    <article class="sec">{stats_block}{skills_block}{potion_block}</article>
    {acquire_block}
    {detail_block}
    <article class="sec">
      <h2>来源</h2>
      <ul>{src_lis}</ul>
      {buy_map}
    </article>
"""
        html_out = page_shell(name_cn, f'<a href="../../../">主页</a> / <a href="../../archive.html">档案</a> / {esc(name_cn)}', body)
        (OUT_ITEMS / f"{s}.html").write_text(html_out, encoding="utf-8")

    print(f"item pages {len(items)}")

    chest_to_bosses = meta.get("chest_to_bosses") or {}
    sealed_note = meta.get("sealed_note") or {}

    # ---------- chest pages ----------
    for cname, c in chests.items():
        s = chest_slugs[cname]
        cname_cn = chest_label(cname)
        aid = asset_id(c.get("icon"))
        loot = c.get("loot") or []
        guar = c.get("guaranteed") or []

        def loot_row(entry, guaranteed=False):
            iid = entry.get("itemId") or entry.get("item") or "?"
            ch = "保底" if guaranteed else chance_text(entry.get("chance"))
            icn = (items.get(iid) or {}).get("NameCN") or iid
            if iid in item_slugs:
                link = f'<a class="quest-link" href="../items/{esc(item_slugs[iid])}.html">{esc(icn)}</a>'
            else:
                link = esc(icn)
            return f"<tr><td>{link}</td><td>{esc(ch)}</td></tr>"

        rows = "".join(loot_row(e, True) for e in guar) + "".join(loot_row(e) for e in loot)
        linked_bosses = chest_to_bosses.get(cname) or []
        if linked_bosses:
            blinks = []
            for b in linked_bosses:
                bn = boss_label(b.get("Name") or b.get("Code"))
                bc = b.get("Code")
                blinks.append(f'<a class="quest-link" href="../bosses/{esc(slug(bc))}.html">{esc(bn)}</a>' if bc else esc(bn))
            where_note = f"击杀下列 Boss 后掉落本箱：{'、'.join(blinks)}。"
        else:
            where_note = sealed_note.get(cname) or "刷新位置随活动 / 区域而定。"

        body = f"""
    <article class="sec">
      <div class="head">
        {icon_img(aid, "chest")}
        <div>
          <h1>{esc(cname_cn)}</h1>
          <p class="en" style="font-size:.85rem;opacity:.7"><code>{esc(cname)}</code></p>
          <p>稀有度值 <code>{esc(c.get("rarityValue"))}</code> · 经验 <code>{esc(c.get("exp"))}</code></p>
        </div>
      </div>
      <p>{where_note}</p>
    </article>
    <article class="sec">
      <h2>掉落表</h2>
      <table><tr><th>物品</th><th>概率 / 保底</th></tr>{rows or "<tr><td colspan=2>无数据</td></tr>"}</table>
    </article>
"""
        (OUT_CHESTS / f"{s}.html").write_text(
            page_shell(cname_cn, f'<a href="../../../">主页</a> / <a href="../../archive.html">档案</a> / 宝箱 / {esc(cname_cn)}', body),
            encoding="utf-8",
        )
    print(f"chest pages {len(chests)}")

    # ---------- boss pages + maps ----------
    def boss_max_hp(b: dict) -> int:
        nd = npc_data.get(b.get("Code") or "") or {}
        hp = (nd.get("Stats") or {}).get("MaxHealth")
        try:
            return int(hp) if hp is not None else 10**12
        except (TypeError, ValueError):
            return 10**12

    # list / overview map: low MaxHealth → high（无数据排末）
    bosses_by_hp = sorted(bosses, key=lambda b: (boss_max_hp(b), boss_label(b.get("DisplayName") or b.get("Name") or "")))

    all_boss_spots = []
    for i, b in enumerate(bosses_by_hp, 1):
        code = b["Code"]
        s = slug(code)
        name = b.get("DisplayName") or b["Name"]
        name_cn = boss_label(name)
        pos = b.get("Position") or [0, 0, 0]
        all_boss_spots.append((i, float(pos[0]), float(pos[2]), name_cn))
        map_path = MAP_DIR / f"boss-{s}.png"
        draw_markers([(1, float(pos[0]), float(pos[2]), name_cn)], f"Boss · {name_cn}", f"坐标 {pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}", map_path)

        aid = asset_id(b.get("Icon"))
        rewards = b.get("Rewards") or {}
        drop_rows = []
        chest_id = None
        # find chest from meta
        for cid, blist in chest_to_bosses.items():
            if any(x.get("Code") == code for x in blist):
                chest_id = cid
                break
        for k, v in rewards.items():
            if k in ("Wen", "Exp"):
                lab = "文" if k == "Wen" else "经验"
                drop_rows.append(f"<tr><td>{esc(lab)}</td><td><code>{esc(v)}</code></td><td>—</td></tr>")
                continue
            ch, pity = parse_reward(v)
            icn = (items.get(k) or {}).get("NameCN") or k
            link = (
                f'<a class="quest-link" href="../items/{esc(item_slugs[k])}.html">{esc(icn)}</a>'
                if k in item_slugs
                else esc(icn)
            )
            pity_s = f"保底 {pity}" if pity else "—"
            drop_rows.append(f"<tr><td>{link}</td><td>{esc(chance_text(ch))}</td><td>{esc(pity_s)}</td></tr>")

        chest_line = ""
        if chest_id:
            chest_line = f'<p>击杀后掉落宝箱：<a class="quest-link" href="../chests/{esc(chest_slugs.get(chest_id, slug(chest_id)))}.html">{esc(chest_label(chest_id))}</a></p>'

        # combat / skills from NpcDataTable
        nd = npc_data.get(code) or {}
        if not nd:
            for _k, _v in npc_data.items():
                if _v.get("Name") == name or _v.get("Name") == b.get("DisplayName"):
                    nd = _v
                    break
        st = nd.get("Stats") or {}
        desc = nd.get("Description") or ""
        tool = nd.get("Equipped_Tool") or "—"
        spawn_cd = nd.get("SpawnTime")
        skills = nd.get("Skills") or []
        skill_rows = "".join(
            f"<tr><td>{esc(skill_label(sk))}</td><td><code>{esc(sk)}</code></td></tr>" for sk in skills
        )
        combat_rows = []
        if st.get("MaxHealth") is not None:
            combat_rows.append(f"<tr><td>生命</td><td><code>{esc(st.get('MaxHealth'))}</code></td></tr>")
        if st.get("M1Damage") is not None:
            combat_rows.append(f"<tr><td>普攻伤害</td><td><code>{esc(st.get('M1Damage'))}</code></td></tr>")
        if st.get("BlockPoints") is not None:
            combat_rows.append(f"<tr><td>格挡值</td><td><code>{esc(st.get('BlockPoints'))}</code></td></tr>")
        if st.get("M1BlockDamage") is not None:
            combat_rows.append(f"<tr><td>对格挡伤害倍率</td><td><code>{esc(st.get('M1BlockDamage'))}</code></td></tr>")
        if st.get("ScaleDamage") is not None:
            combat_rows.append(f"<tr><td>伤害缩放系数</td><td><code>{esc(st.get('ScaleDamage'))}</code></td></tr>")
        combat_rows.append(f"<tr><td>装备 / 武器</td><td><code>{esc(tool)}</code></td></tr>")
        if spawn_cd is not None:
            combat_rows.append(f"<tr><td>刷新冷却</td><td><code>{esc(spawn_cd)}</code> 秒</td></tr>")
        region = nd.get("Region") or ""
        region_s = REGION_CN.get(region, region) if region else ""
        desc_block = f"<p>{esc(desc)}</p>" if desc else ""
        combat_block = f"""
    <article class="sec">
      <h2>战斗数据</h2>
      {desc_block}
      <table><tr><th>项</th><th>值</th></tr>{"".join(combat_rows)}</table>
      {"<p>区域：" + esc(region_s) + "</p>" if region_s else ""}
    </article>
    <article class="sec">
      <h2>攻击方式 / 技能组</h2>
      <p>来自 NpcDataTable.Skills（模块路径）。专属技包 / 柱技 / 邪术大招为该 Boss 主要压制手段；普攻、冲刺、格挡为通用底盘。</p>
      <table><tr><th>说明</th><th>模块</th></tr>{skill_rows or "<tr><td colspan=2>无技能表</td></tr>"}</table>
    </article>
"""

        body = f"""
    <article class="sec">
      <div class="head">
        {icon_img(aid, "boss")}
        <div>
          <h1>{esc(name_cn)}</h1>
          <p class="en" style="font-size:.85rem;opacity:.7"><code>{esc(name)}</code> · {esc(code)}</p>
          <p>坐标 <code>{esc(f"{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}")}</code></p>
        </div>
      </div>
      {chest_line}
    </article>
    <article class="sec">
      <h2>刷新位置</h2>
      <img class="map-img" src="../../../assets/archive-maps/boss-{esc(s)}.png" alt="{esc(name_cn)} 位置">
    </article>
    {combat_block}
    <article class="sec">
      <h2>掉落</h2>
      <table><tr><th>掉落</th><th>概率</th><th>保底</th></tr>{"".join(drop_rows) or "<tr><td colspan=3>无</td></tr>"}</table>
    </article>
"""
        (OUT_BOSSES / f"{s}.html").write_text(
            page_shell(name_cn, f'<a href="../../../">主页</a> / <a href="../../bosses.html">Boss</a> / {esc(name_cn)}', body),
            encoding="utf-8",
        )

    overview = MAP_DIR / "bosses-all.png"
    draw_markers(all_boss_spots, f"Ouwland 全部 Boss / 头目 · {len(bosses)}", "编号对应 Boss 总览表", overview)
    print(f"boss pages {len(bosses)}")

    # ---------- shops overview map ----------
    shop_spots = []
    shop_rows_html = []
    si = 0
    for s in shops:
        name = s.get("Name") or "?"
        if name in ("Elara",):  # rotating / empty catalog stub
            continue
        positions = s.get("Positions") or ([] if not s.get("Position") else [s["Position"]])
        if not positions:
            continue
        si += 1
        label = NPC_CN.get(name, name)
        # primary mark
        p0 = positions[0]
        shop_spots.append((si, float(p0[0]), float(p0[2]), label))
        # extra marks for multi-pos vendors (black market / Ren patrol)
        for j, p in enumerate(positions[1:], 2):
            shop_spots.append((si, float(p[0]), float(p[2]), f"{label}·{j}" if len(positions) <= 4 else label))
        region = REGION_CN.get(s.get("Region") or "", s.get("Region") or "—")
        shop = s.get("Shop") or {}
        items_sold = sorted(set(s.get("Items") or []) | (set(shop.keys()) if isinstance(shop, dict) else set()))
        links = []
        for itn in items_sold[:10]:
            if itn in item_slugs:
                icn = (items.get(itn) or {}).get("NameCN") or itn
                links.append(f'<a class="quest-link" href="archive/items/{esc(item_slugs[itn])}.html">{esc(icn)}</a>')
            else:
                links.append(esc(itn))
        more = f" 等 {len(items_sold)} 种" if len(items_sold) > 10 else ""
        npos = len(positions)
        pos_note = f"{p0[0]:.0f}, {p0[1]:.0f}, {p0[2]:.0f}" + (f" · {npos} 点" if npos > 1 else "")
        shop_rows_html.append(
            f"<tr><td>{si}</td><td><strong>{esc(label)}</strong><br><code>{esc(name)}</code></td>"
            f"<td>{esc(region)}</td><td><code>{esc(pos_note)}</code></td>"
            f"<td>{'、'.join(links)}{esc(more)}</td></tr>"
        )
    if shop_spots:
        draw_markers(shop_spots, f"Ouwland NPC 商店 · {si}", "编号对应价目表；多点 NPC 同号", MAP_DIR / "shops-all.png")
    print(f"shop overview {si}")

    # ---------- archive index ----------
    cat_sections = []
    for cat in sorted(by_cat.keys(), key=lambda c: (-len(by_cat[c]), c)):
        cards = []
        for name in by_cat[cat]:
            it = items[name]
            name_cn = it.get("NameCN") or name
            aid = asset_id(it.get("Icon"))
            rar = it.get("Rarity") or 0
            rar_name, rar_color = RARITY.get(rar, (f"R{rar}", "#888"))
            icon = ""
            if aid and (ICON_DIR / f"{aid}.png").exists():
                icon = f'<img class="icon" src="../assets/icons/items/{aid}.png" alt="">'
            cards.append(
                f'<a class="card" href="archive/items/{esc(item_slugs[name])}.html">{icon}'
                f'<span><strong>{esc(name_cn)}</strong><span class="rarity" style="background:{rar_color}">{esc(rar_name)}</span></span></a>'
            )
        cat_sections.append(
            f'<article class="sec" id="cat-{esc(slug(cat))}"><h2>{esc(CAT_CN.get(cat, cat))} <span style="color:var(--muted);font-size:.9rem">({len(by_cat[cat])})</span></h2>'
            f'<div class="grid">{"".join(cards)}</div></article>'
        )

    chest_cards = []
    for cname in sorted(chests.keys()):
        aid = asset_id(chests[cname].get("icon"))
        icon = ""
        if aid and (CHEST_ICON_DIR / f"{aid}.png").exists():
            icon = f'<img class="icon" src="../assets/icons/chests/{aid}.png" alt="">'
        chest_cards.append(
            f'<a class="card" href="archive/chests/{esc(chest_slugs[cname])}.html">{icon}<span><strong>{esc(chest_label(cname))}</strong></span></a>'
        )

    boss_rows = []
    for i, b in enumerate(bosses_by_hp, 1):
        name = b.get("DisplayName") or b["Name"]
        name_cn = boss_label(name)
        s = slug(b["Code"])
        pos = b.get("Position") or [0, 0, 0]
        nd = npc_data.get(b["Code"]) or {}
        hp = (nd.get("Stats") or {}).get("MaxHealth")
        hp_s = esc(hp) if hp is not None else "—"
        boss_rows.append(
            f'<tr><td>{i}</td><td><a class="quest-link" href="archive/bosses/{esc(s)}.html">{esc(name_cn)}</a></td>'
            f'<td><code>{hp_s}</code></td>'
            f'<td><code>{esc(f"{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}")}</code></td></tr>'
        )

    archive_body = f"""
    <article class="sec">
      <h1>档案</h1>
      <p>收录可在游戏档案中出现的物品（已过滤礼包 / 不可获取 / 无图标）。共 <strong>{len(items)}</strong> 件，
        宝箱 <strong>{len(chests)}</strong>，世界 Boss/头目 <strong>{len(bosses)}</strong>。</p>
      <p>
        <a class="quest-link" href="#cats">物品分类</a> ·
        <a class="quest-link" href="#chests">宝箱</a> ·
        <a class="quest-link" href="bosses.html">Boss / 头目</a>
      </p>
    </article>
    <div id="cats">{"".join(cat_sections)}</div>
    <article class="sec" id="chests">
      <h2>宝箱</h2>
      <div class="grid">{"".join(chest_cards)}</div>
    </article>
"""
    (ROOT / "p" / "archive.html").write_text(
        shallow_shell("档案", '<a href="../">主页</a> / 档案', archive_body, depth=1).replace(
            'href="archive/', 'href="archive/'
        ),
        encoding="utf-8",
    )
    # fix card paths in archive.html - they use archive/ relative to p/
    # shallow_shell is correct with depth=1; cards use archive/items which is correct from p/archive.html

    bosses_body = f"""
    <article class="sec">
      <h1>Boss / 头目</h1>
      <p class="i18n-zh">世界可追踪的 Boss 与试炼头目（WorldBosses），共 <strong>{len(bosses)}</strong>。下表按最大生命（MaxHealth）由低到高排序；无生命数据者排末。点击名称进入单独介绍与刷新地图。</p>
      <p class="i18n-en" hidden>World bosses and trial heads ({len(bosses)}). Sorted by MaxHealth ascending. Click a name for the detail page and spawn map.</p>
    </article>
    <article class="sec">
      <h2>总览地图</h2>
      <div class="map-toolbar">
        <button type="button" id="map-zoom-out">−</button>
        <button type="button" id="map-zoom-in">+</button>
        <button type="button" id="map-zoom-reset">重置</button>
        <span class="map-zoom-label" id="map-zoom-label">100%</span>
      </div>
      <div class="map-stage" id="map-stage">
        <div class="map-viewport" id="map-viewport">
          <img class="map-img" id="map-img" src="../assets/archive-maps/bosses-all.png" alt="全部 Boss" draggable="false">
        </div>
      </div>
      <p class="map-hint">滚轮缩放 · 拖动 · <a href="../assets/archive-maps/bosses-all.png">下载</a></p>
    </article>
    <article class="sec">
      <h2>一览</h2>
      <p>按最大生命由低到高。名称已统一汉化。</p>
      <table><tr><th>#</th><th>名称</th><th>生命</th><th>坐标</th></tr>{"".join(boss_rows)}</table>
    </article>
    <script src="../js/map-zoom.js?v={CSS_VER}"></script>
"""
    (ROOT / "p" / "bosses.html").write_text(
        shallow_shell("Boss / 头目", '<a href="../">主页</a> / Boss', bosses_body, depth=1),
        encoding="utf-8",
    )

    # ---------- patch shops.html NPC section ----------
    shops_html_path = ROOT / "p" / "shops.html"
    if shops_html_path.exists() and shop_rows_html:
        npc_block = f"""    <article class="sec" id="npc">
      <h2>世界 NPC 商店（文）</h2>
      <p>与菜单罗宝商店不同，下列用游戏内货币<strong>文</strong>（及材料）交易。点击物品名进档案；地图编号与下表一致。</p>
      <p><img class="map-img" src="../assets/archive-maps/shops-all.png" alt="NPC 商店位置" style="display:block;width:100%;height:auto;border:1px solid var(--line);margin:.6rem 0"></p>
      <table>
        <tr><th>#</th><th>NPC</th><th>区域</th><th>坐标</th><th>主要商品</th></tr>
        {"".join(shop_rows_html)}
      </table>
      <p>黑商为限时活动多点轮换；莲（Ren）在蝴蝶庄园一带多点巡逻。详细单价见各物品档案页。</p>
    </article>"""
        raw = shops_html_path.read_text(encoding="utf-8")
        raw2, nsub = re.subn(
            r'    <article class="sec" id="npc">.*?</article>',
            npc_block,
            raw,
            count=1,
            flags=re.S,
        )
        if nsub:
            shops_html_path.write_text(raw2, encoding="utf-8")
            print("shops.html NPC section updated")
        else:
            print("WARN: shops.html NPC section not found")

    print("done archive index + bosses overview")


if __name__ == "__main__":
    main()
