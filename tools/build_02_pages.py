# -*- coding: utf-8 -*-
"""Build 02.txt: monsters pages + schematic acquire maps/flows; bump mobile via CSS."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Desktop\ProjectSlayer2_WIKI")
LIVE = ROOT / "data" / "_live"
MAP_CLEAN = ROOT / "assets" / "ouwland-map-clean.png"
MAP_DIR = ROOT / "assets" / "wiki-maps"
MONSTER_DIR = ROOT / "p" / "monsters"
ICON_BOSS = ROOT / "assets" / "icons" / "bosses"
ICON_ITEM = ROOT / "assets" / "icons" / "items"
TL = (-3087.361, -3989.256)
BR = (2977.139, 1635.244)
CSS = "20260926s"

# Regions display name / Code -> NpcDataTable key
ALIASES = {
    "Bandit": "KaruVillageBandit",
    "Windy Peak Bandit": "KaruVillageBandit",
    "*Civilian*": "VillageSpy",
    "Villager (Spy)": "VillageSpy",
    "Duelist Hibiki": "SoundDuelist",
    "Reaper Trainee Kuzan": "ReaperTrainee",
    "Soryu Trainee Goki": "SoryuTrainee",
    "Tai Chi Trainee Suzume": "TaiChiTrainee",
    "Water Trainee Sabito": "WaterTrainee",
    "Flame Trainee": "FlameTrainee",
    "Thunder Trainee": "ThunderTrainee",
    "Wind Trainee": "WindTrainee",
    "Insect Trainee": "InsectTrainee",
    "Serpent Trainee": "SerpentTrainee",
    "Sound Trainee": "SoundTrainee",
    "Stone Trainee": "StoneTrainee",
    "Lesser Demon": "LesserDemon_ButterflyEstate",
    "Greater Demon": "GreaterDemon_ButterflyEstate",
    "Beast Born Demon": "BeastBornDemon_MistfallHarbor",
    "Blood Hounded Demon": "BloodHoundedDemon_MistfallHarbor",
    "Mizunoto": "Mizunoto_MistfallHarbor",
    "Fire Profound Demon": "FireProfoundDemon",
    "Ice Profound Demon": "IceProfoundDemon",
    "High Demon": "HighDemon",
    "Kanoe Demon Slayer": "KanoeDemonSlayer",
    "Mizunoe Demon Slayer": "MizunoeDemonSlayer",
    "Hoyuzo Subordinate": "HoyuzoSub",
    "Kaiden Subordinate": "KaidenSub",
    "Bear Cub": "BearCub",
    "Mother Bear": "MotherBear",
}

SKIP_CODES = {
    "Dummy",
    "DemonPhysicalAttacks",
    "FlameCaster",
    "FrostCaster",
    "GauntletBoss",
    "ReapingBladesBoss",
    "ScytheBoss",
    "SoryuBoss",
    "SpearBoss",
    "TaiChiBoss",
    "TantoBoss",
    "WarFansBoss",
    "TestBandit",
    "Horse",
    "Civilian",  # ambient; spy kept via VillageSpy
}

SKIP_NAMES = {
    "Horse",
    "Sealed Chest T1",
    "Sealed Chest T2",
    "Sealed Chest T3",
    "Black Marketer",
    "Study Props",
    "Serpent Box",
    "Boss Hunts",
    "Yeti Summon",
}

REGION_CN = {
    "Mistfall Harbor": "迷雾港湾",
    "Windy Peak": "风之峰",
    "Bamboo Grove": "竹林",
    "Butterfly Estate": "蝴蝶庄园",
    "Hidden Mist Village": "隐雾村",
    "Iceveil Valley": "冰纱谷",
    "Final Selection Plains": "最终选拔平原",
    "Final Selection": "最终选拔",
    "Misc": "多区域 / 世界",
    "Test": "测试",
}

STAT_CN = {
    "MaxHealth": "最大生命",
    "M1Damage": "普攻伤害",
    "BlockPoints": "格挡值",
    "M1BlockDamage": "对格挡伤害",
    "ScaleDamage": "伤害缩放",
    "BlockRegen": "格挡回复",
    "RegenRate": "回复速率",
    "M1Range": "普攻距离",
}


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
    for name in (
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        "msyh.ttc",
        "msyhbd.ttc",
        "simhei.ttf",
        "arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_markers(spots, title, subtitle, out_path, small=False):
    """Draw numbered circular markers. Number is centered inside the circle."""
    base = Image.open(MAP_CLEAN).convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_t = load_font(22)
    font_s = load_font(14)
    # Marker radius vs digit font — keep padding so 1–2 digits stay inside
    if small:
        r = 14
        font_n = load_font(12)
    else:
        r = 24
        font_n = load_font(14)
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
    for i, (num, x, z, label) in enumerate(spots):
        px, py = world_to_px(float(x), float(z), w, h)
        c = colors[i % len(colors)]
        draw.ellipse((px - r - 2, py - r - 2, px + r + 2, py + r + 2), fill=(0, 0, 0, 200))
        draw.ellipse((px - r, py - r, px + r, py + r), fill=c)
        # Prefer explicit number; fall back to index
        text = ""
        if isinstance(num, int) and num > 0:
            text = str(num)
        elif label and str(label).isdigit():
            text = str(label)
        elif label and not small:
            # side label for named markers (overview)
            draw.text((px + r + 4, py - 8), str(label)[:10], fill=(255, 255, 255, 230), font=font_n)
        if text:
            # center number inside circle
            bbox = draw.textbbox((0, 0), text, font=font_n)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = px - tw / 2 - bbox[0]
            ty = py - th / 2 - bbox[1]
            # slight shadow for contrast on bright fills
            draw.text((tx + 1, ty + 1), text, fill=(0, 0, 0, 160), font=font_n)
            draw.text((tx, ty), text, fill=(20, 16, 8, 255), font=font_n)
        elif label and small:
            # named overview: keep short side label
            draw.text((px + r + 3, py - 7), str(label)[:8], fill=(255, 255, 255, 230), font=font_n)
    out = Image.alpha_composite(base, overlay)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.convert("RGB").save(out_path, "PNG", optimize=True)


def page_shell(title: str, crumb: str, body: str, nav="", depth=1) -> str:
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>{esc(title)} · Slayers 2 Wiki</title>
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}css/wiki.css?v={CSS}">
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
    .flow{{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center;margin:.5rem 0}}
    .flow .step{{border:1px solid var(--line);background:rgba(255,255,255,.03);padding:.35rem .55rem;font-size:.82rem;color:var(--cream)}}
    .flow .arrow{{color:var(--gold-deep);font-size:.9rem}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.55rem}}
    .card{{display:flex;gap:.55rem;align-items:center;border:1px solid var(--line);padding:.55rem .65rem;background:rgba(255,255,255,.02)}}
    .card:hover{{border-color:var(--gold-deep)}}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="{prefix}"><span>Slayers 2 Wiki</span></a>
    <nav class="top-nav">{nav}</nav>
    <span class="top-ver">{esc(title)}</span>
  </header>
  <main class="page">
    <p class="crumb">{crumb}</p>
    {body}
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>{esc(title)}</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="{prefix}">返回主页</a>
  </footer>
  <script src="{prefix}js/i18n.js?v={CSS}"></script>
</body>
</html>
"""


def chance_text(v):
    if v is None:
        return "—"
    if isinstance(v, dict):
        ch = v.get("Chance")
        pity = v.get("Pity")
        qty = v.get("Quantity")
        lvl = v.get("Level")
        bits = []
        if isinstance(ch, (int, float)):
            pct = ch * 100 if ch <= 1 else ch
            bits.append(f"{pct:g}%")
        if pity:
            bits.append(f"保底 {pity}")
        if qty:
            bits.append(f"×{qty}")
        if lvl:
            bits.append(f"Lv{lvl}+")
        return " · ".join(bits) if bits else "—"
    if isinstance(v, (int, float)):
        return str(v)
    return str(v)


def resolve_nd(name, code, nd):
    if code and code in nd:
        return code, nd[code]
    if name in ALIASES and ALIASES[name] in nd:
        return ALIASES[name], nd[ALIASES[name]]
    for c, row in nd.items():
        if row.get("Name") == name:
            return c, row
    # fuzzy collapse spaces
    key = re.sub(r"\s+", "", name or "")
    for c, row in nd.items():
        if re.sub(r"\s+", "", row.get("Name") or "") == key or re.sub(r"\s+", "", c) == key:
            return c, row
    return code, None


def build_monsters():
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    MONSTER_DIR.mkdir(parents=True, exist_ok=True)
    raw = json.loads((LIVE / "wiki-monsters.json").read_text(encoding="utf-8"))
    monsters_raw = raw.get("monsters") or []
    bosses_wb = {b["Code"]: b for b in (raw.get("bosses") or []) if b.get("Code")}
    nd = json.loads((LIVE / "wiki-npc-data-full.json").read_text(encoding="utf-8"))
    items = json.loads((LIVE / "items-enriched.json").read_text(encoding="utf-8"))
    world_bosses = {b["Code"]: b for b in json.loads((LIVE / "world-bosses.json").read_text(encoding="utf-8"))}

    # index region spawns by name and code
    by_name: dict[str, list] = {}
    for m in monsters_raw:
        by_name.setdefault(m.get("Name") or "", []).append(m)

    entries = []
    seen_codes = set()

    for m in monsters_raw:
        name = m.get("Name") or ""
        if name in SKIP_NAMES or m.get("HasShop") or m.get("TimedVendor"):
            continue
        if "Trainer" in name or "Expert" in name or name.endswith("Sofen") or "Marketer" in name:
            continue
        # skip pure dialogue NPCs without combat code unless aliased hostile
        code, row = resolve_nd(name, m.get("Code"), nd)
        if not row:
            continue
        if code in SKIP_CODES or (row.get("Region") == "Test" and code in SKIP_CODES):
            continue
        if code in seen_codes:
            # merge spawns
            for e in entries:
                if e["code"] == code:
                    e["spawns"].extend(m.get("Spawns") or [])
                    break
            continue
        seen_codes.add(code)
        spawns = list(m.get("Spawns") or [])
        if not spawns and m.get("Position"):
            spawns = [m["Position"]]
        # world boss position fallback
        wb = world_bosses.get(code) or bosses_wb.get(code)
        if not spawns and wb and wb.get("Position"):
            spawns = [wb["Position"]]
        entries.append(
            {
                "code": code,
                "name": row.get("Name") or name,
                "region": m.get("Region") or row.get("Region") or "Misc",
                "row": row,
                "spawns": spawns,
                "quantity": m.get("Quantity"),
                "spawn_time": m.get("SpawnTime") or row.get("SpawnTime"),
                "icon": row.get("Icon") or (wb or {}).get("Icon"),
                "is_boss": code in world_bosses or code in bosses_wb,
            }
        )

    # add NpcDataTable entries missing from regions (sealed cache mobs etc.)
    for code, row in nd.items():
        if code in seen_codes or code in SKIP_CODES:
            continue
        if row.get("Region") == "Test":
            continue
        name = row.get("Name") or code
        spawns = []
        wb = world_bosses.get(code) or bosses_wb.get(code)
        if wb and wb.get("Position"):
            spawns = [wb["Position"]]
        # try find by name in by_name
        for m in by_name.get(name) or []:
            spawns.extend(m.get("Spawns") or [])
        entries.append(
            {
                "code": code,
                "name": name,
                "region": row.get("Region") or "Misc",
                "row": row,
                "spawns": spawns,
                "quantity": None,
                "spawn_time": row.get("SpawnTime"),
                "icon": row.get("Icon") or (wb or {}).get("Icon"),
                "is_boss": code in world_bosses or code in bosses_wb,
            }
        )
        seen_codes.add(code)

    # dedupe spawns
    for e in entries:
        uniq = []
        seen = set()
        for p in e["spawns"]:
            if not p or len(p) < 3:
                continue
            key = (round(float(p[0]), 1), round(float(p[2]), 1))
            if key in seen:
                continue
            seen.add(key)
            uniq.append([float(p[0]), float(p[1]), float(p[2])])
        e["spawns"] = uniq

    entries.sort(key=lambda e: (0 if e["is_boss"] else 1, e["region"] or "", e["name"]))

    # overview map — all spawn points (small)
    all_spots = []
    for i, e in enumerate(entries, 1):
        for p in e["spawns"]:
            all_spots.append((i, p[0], p[2], ""))
        if not e["spawns"] and e.get("is_boss"):
            continue
    # overview: numbered circles (not tiny dots)
    overview_spots = []
    for i, e in enumerate([x for x in entries if x["spawns"]], 1):
        p = e["spawns"][0]
        overview_spots.append((i, p[0], p[2], ""))
    draw_markers(
        overview_spots,
        f"怪物刷新总览 · {len(overview_spots)}",
        "圆内数字对应下方表行号；详情见各自怪物页多点图",
        MAP_DIR / "monsters-all.png",
        small=False,
    )
    if all_spots:
        draw_markers(
            [(n, x, z, "") for n, x, z, _ in all_spots],
            f"全部刷新点 · {len(all_spots)}",
            "含同种怪的多个 Locations（圆内为怪种序号）",
            MAP_DIR / "monsters-all-points.png",
            small=True,
        )

    # per-monster pages
    rows_html = []
    for e in entries:
        s = slug(e["code"])
        name = e["name"]
        region = e["region"]
        row = e["row"]
        spawns = e["spawns"]
        map_name = f"monster-{s}.png"
        if spawns:
            # number centered in circle; no side digit label
            spots = [(i, p[0], p[2], "") for i, p in enumerate(spawns, 1)]
            draw_markers(spots, f"{name} · 刷新", f"{REGION_CN.get(region, region)} · {len(spawns)} 点", MAP_DIR / map_name)
            map_block = f'<img class="map-img" src="../../assets/wiki-maps/{esc(map_name)}" alt="刷新点">'
            pos_s = f"{spawns[0][0]:.0f}, {spawns[0][1]:.0f}, {spawns[0][2]:.0f}" + (f" 等 {len(spawns)} 点" if len(spawns) > 1 else "")
        else:
            map_block = "<p>暂无 Regions.Locations 坐标（可能为事件刷新 / 测试体）。</p>"
            pos_s = "—"

        # rewards
        rew = row.get("Rewards") or {}
        reward_rows = []
        if isinstance(rew, dict):
            for k, v in rew.items():
                if k in ("Exp", "Wen"):
                    continue
                link = k
                if k in items:
                    link = f'<a class="quest-link" href="../archive/items/{slug(k)}.html">{esc(items[k].get("NameCN") or k)}</a>'
                else:
                    # boss archive?
                    blink = ROOT / "p" / "archive" / "bosses" / f"{slug(e['code'])}.html"
                    link = esc(k)
                reward_rows.append(f"<tr><td>{link}</td><td>{esc(chance_text(v))}</td></tr>")
            if rew.get("Exp") is not None or rew.get("Wen") is not None:
                reward_rows.insert(
                    0,
                    f"<tr><td>经验 / 文</td><td><code>{esc(rew.get('Exp'))}</code> Exp · <code>{esc(rew.get('Wen'))}</code> 文</td></tr>",
                )
        rewards_html = (
            f"<table><tr><th>掉落</th><th>概率 / 备注</th></tr>{''.join(reward_rows)}</table>"
            if reward_rows
            else "<p>无掉落表（或仅任务用途）。</p>"
        )

        # stats
        stats = row.get("Stats") or {}
        stat_rows = ""
        if isinstance(stats, dict) and stats:
            stat_rows = "".join(
                f"<tr><td>{esc(STAT_CN.get(k, k))}</td><td><code>{esc(v)}</code></td></tr>"
                for k, v in stats.items()
                if not isinstance(v, dict)
            )
        stats_html = (
            f"<table><tr><th>属性</th><th>值</th></tr>{stat_rows}</table>" if stat_rows else "<p>无战斗属性表。</p>"
        )

        skills = row.get("Skills") or []
        skills_html = ""
        if skills:
            skills_html = "<ul>" + "".join(f"<li><code>{esc(sk)}</code></li>" for sk in skills) + "</ul>"

        aid = asset_id(e.get("icon"))
        icon = ""
        if aid:
            local = ICON_BOSS / f"{aid}.png"
            if local.exists():
                icon = f'<img class="icon" src="../../assets/icons/bosses/{aid}.png" alt="">'
            else:
                icon = f'<img class="icon" src="https://www.roblox.com/asset-thumbnail/image?assetId={aid}&width=150&height=150&format=png" alt="">'

        boss_link = ""
        if (ROOT / "p" / "archive" / "bosses" / f"{slug(e['code'])}.html").exists():
            boss_link = f' · <a class="quest-link" href="../archive/bosses/{slug(e["code"])}.html">档案 Boss 页</a>'

        body = f"""
    <article class="sec">
      <div class="head">{icon}<div>
        <h1>{esc(name)}</h1>
        <p class="i18n-en" hidden><code>{esc(e['code'])}</code></p>
        <p>{esc(REGION_CN.get(region, region))} · <code>{esc(e['code'])}</code>{boss_link}</p>
        <p>代表坐标 <code>{esc(pos_s)}</code>
          {" · 同时存在约 " + str(e["quantity"]) + " 只" if e.get("quantity") else ""}
          {" · 刷新冷却 " + str(e["spawn_time"]) + "s" if e.get("spawn_time") else ""}</p>
      </div></div>
      <p>{esc(row.get("Description") or "（无描述）")}</p>
    </article>
    <article class="sec">
      <h2>刷新点位</h2>
      {map_block}
    </article>
    <article class="sec">
      <h2>掉落</h2>
      {rewards_html}
    </article>
    <article class="sec">
      <h2>战斗数据</h2>
      {stats_html}
      {"<h3>技能模块</h3>" + skills_html if skills_html else ""}
      <p>装备 / 武器：<code>{esc(row.get("Equipped_Tool") or "—")}</code></p>
    </article>
"""
        (MONSTER_DIR / f"{s}.html").write_text(
            page_shell(
                name,
                f'<a href="../../">主页</a> / <a href="../monsters.html">怪物</a> / {esc(name)}',
                body,
                depth=2,
            ),
            encoding="utf-8",
        )

        kind = "Boss" if e["is_boss"] else "普通"
        rows_html.append(
            f'<tr><td><a class="quest-link" href="monsters/{esc(s)}.html"><strong>{esc(name)}</strong></a></td>'
            f"<td>{esc(kind)}</td><td>{esc(REGION_CN.get(region, region))}</td>"
            f"<td><code>{esc(pos_s)}</code></td><td>{len(spawns)}</td></tr>"
        )

    # overview page
    cards = []
    for e in entries:
        if not e["spawns"] and not e["is_boss"]:
            continue
        s = slug(e["code"])
        cards.append(
            f'<a class="card" href="monsters/{esc(s)}.html"><span><strong>{esc(e["name"])}</strong><br>'
            f'<span style="color:var(--muted);font-size:.8rem">{esc(REGION_CN.get(e["region"], e["region"]))} · '
            f'{len(e["spawns"])} 点</span></span></a>'
        )

    overview = f"""
    <article class="sec">
      <h1>怪物</h1>
      <p>汇总 Regions 刷新点 + NpcDataTable 战斗/掉落。共 <strong>{len(entries)}</strong> 种；总览图按「每种怪一个代表点」绘制，点开条目可见全部 Locations。</p>
      <img class="map-img" src="../assets/wiki-maps/monsters-all.png" alt="怪物总览">
      <p class="callout">含全部点位的密集图见 <a class="quest-link" href="../assets/wiki-maps/monsters-all-points.png">monsters-all-points.png</a>。世界柱级 Boss 另见 <a class="quest-link" href="bosses.html">Boss</a> 档案。</p>
    </article>
    <article class="sec" id="list">
      <h2>一览表</h2>
      <table><tr><th>名称</th><th>类型</th><th>区域</th><th>坐标</th><th>点数</th></tr>{"".join(rows_html)}</table>
    </article>
    <article class="sec" id="cards">
      <h2>快速入口</h2>
      <div class="grid">{"".join(cards)}</div>
    </article>
"""
    (ROOT / "p" / "monsters.html").write_text(
        page_shell("怪物", '<a href="../">主页</a> / 怪物', overview, '<a href="#list">一览</a><a href="#cards">入口</a>'),
        encoding="utf-8",
    )
    print(f"monsters pages {len(entries)}")
    return entries


def build_schematics():
    items = json.loads((LIVE / "items-enriched.json").read_text(encoding="utf-8"))
    study = json.loads((LIVE / "wiki-study-props.json").read_text(encoding="utf-8"))
    props = json.loads((LIVE / "wiki-world-props.json").read_text(encoding="utf-8"))
    npcs = json.loads((LIVE / "wiki-npcs.json").read_text(encoding="utf-8"))

    study_by_item = {}
    for s in study:
        item = s.get("Item")
        if item:
            study_by_item[item] = s
            study_by_item[f"{item} Schematic"] = s

    def npc_pos(name):
        for n in npcs:
            if n.get("Name") == name and n.get("Position"):
                return n["Position"]
        return None

    togane = npc_pos("Blacksmith Togane") or [1732.07, 694, -764.55]
    tobei = npc_pos("Stonemason Tobei") or [1860, 694, -500]
    hatsu = npc_pos("Weaver Hatsu")
    # world props
    serpent = (props.get("SerpentBox") or [{}])[0].get("Position")
    levers = [x.get("Position") for x in (props.get("SicklesLever") or []) if x.get("Position")]
    statues = props.get("GauntletStatue") or []

    # maps: levers, statues, study overview
    if levers:
        draw_markers(
            [(i, p[0], p[2], str(i)) for i, p in enumerate(levers, 1)],
            "Sickles 拉杆 · 10",
            "扳完全部后解锁 Nightfall Sickles StudyProp",
            MAP_DIR / "schematic-sickles-levers.png",
        )
    if statues:
        draw_markers(
            [(i, s["Position"][0], s["Position"][2], (s.get("Name") or "")[:8]) for i, s in enumerate(statues, 1) if s.get("Position")],
            "拳套三雕像",
            "进度满后找 Tobei 领 Gauntlet 图纸",
            MAP_DIR / "schematic-gauntlet-statues.png",
        )
    study_spots = [(i, s["Position"][0], s["Position"][2], (s.get("Item") or "")[:8]) for i, s in enumerate(study, 1) if s.get("Position")]
    if study_spots:
        draw_markers(study_spots, "StudyProp 研习点", "长按 Study ≈3s 领取对应 Schematic", MAP_DIR / "schematic-study-all.png")

    FLOW = {
        "StudyProp": {
            "title": "地下 / 野外研习点",
            "steps": ["前往地图标记的 StudyProp", "确认背包尚无该 Schematic", "长按 Study 约 3 秒领取图纸"],
        },
        "FirstlightStudy": {
            "title": "初光研习点",
            "steps": ["前往对应 Firstlight StudyProp（见本页地图）", "长按 Study 领取初光图纸", "锻造材料（星矿/锻锭/织丝）来自宝箱"],
        },
        "Sickles": {
            "title": "双镰图纸",
            "steps": ["跑图扳动全部 10 根 SicklesLever", "回到 Sickles StudyProp（锁解除）", "长按 Study 领取 Nightfall Sickles Schematic"],
        },
        "SerpentChest": {
            "title": "蛇箱图纸",
            "steps": ["获取 Serpent Key（水边任务物）", "打开蛇箱 Serpent Box", "领取 Nightfall Serpent Katana Schematic"],
        },
        "TobeiGauntlet": {
            "title": "拳套图纸",
            "steps": ["灌满武器 / 力量 / 格斗三座雕像", "找隐雾村石匠 Tobei", "领取 Nightfall Gauntlet Schematic"],
        },
        "HatsuCape": {
            "title": "披风图纸",
            "steps": ["持有遗失披风相关任务物", "找织匠 Hatsu", "兑换 Nightfall Cape Schematic"],
        },
        "ToganeCapstone": {
            "title": "暮落上下装",
            "steps": ["集齐 9 张暮落「门槛」武器/面饰图纸", "找铁匠 Togane", "领取 Top / Bottom Schematic"],
        },
        "Lost": {
            "title": "霰弹枪图纸",
            "steps": ["挑战终选 Boss「遗失」Lost", "有概率掉落 Shotgun Schematic", "Lost Shotgun Schematic 为关联表外图纸"],
        },
        "QuestLantern": {
            "title": "初光灯笼图纸",
            "steps": ["完成任务 The Plate Trial", "获得 Firstlight Lantern Schematic"],
        },
    }

    schematics = {
        n: it
        for n, it in items.items()
        if (it.get("InventoryCategory") or it.get("Category")) == "Schematics" or n.endswith("Schematic")
    }

    # Per-schematic acquire flows are generated by build_archive.py (archive_flows).
    # This function only builds overview maps + schematics.html hub.
    updated = 0
    for name, it in sorted(schematics.items()):
        # ensure maps exist for known study hits (hub links)
        base = name.replace(" Schematic", "")
        study_hit = study_by_item.get(name) or study_by_item.get(base)
        if study_hit and study_hit.get("Position"):
            p = study_hit["Position"]
            map_file = MAP_DIR / f"schematic-get-{slug(name)}.png"
            if not map_file.exists():
                draw_markers([(1, float(p[0]), float(p[2]), "Study")], f"获取 · {it.get('NameCN') or name}", "StudyProp", map_file)
                updated += 1

    # schematics hub
    hub = f"""
    <article class="sec">
      <h1>图纸获取总览</h1>
      <p>共 <strong>{len(schematics)}</strong> 张 Schematic。StudyProp / 拉杆 / 雕像点位如下；每张图纸档案页含完整流程图与成品蓝链。</p>
      <img class="map-img" src="../assets/wiki-maps/schematic-study-all.png" alt="StudyProp">
      <p class="callout">拉杆图见下方 · 雕像图见下方 · 锻台交接点见 <a class="quest-link" href="forge.html">锻造</a></p>
"""
    if (MAP_DIR / "schematic-sickles-levers.png").exists():
        hub += '<img class="map-img" src="../assets/wiki-maps/schematic-sickles-levers.png" alt="Sickles 拉杆">'
    if (MAP_DIR / "schematic-gauntlet-statues.png").exists():
        hub += '<img class="map-img" src="../assets/wiki-maps/schematic-gauntlet-statues.png" alt="拳套雕像">'
    hub += """
    </article>
    <article class="sec">
      <h2>图纸列表</h2>
      <table><tr><th>图纸</th><th>英文</th><th>获取类型</th></tr>
"""
    for name, it in sorted(schematics.items(), key=lambda x: x[0]):
        cn = it.get("NameCN") or name
        where = " / ".join((s.get("Where") or "?") for s in (it.get("Sources") or [])[:2]) or "—"
        hub += (
            f'<tr><td><a class="quest-link" href="archive/items/{slug(name)}.html">{esc(cn)}</a></td>'
            f"<td><code>{esc(name)}</code></td><td>{esc(where)}</td></tr>\n"
        )
    hub += "</table></article>"

    (ROOT / "p" / "schematics.html").write_text(
        page_shell("图纸", '<a href="../">主页</a> / 图纸', hub, '<a href="archive.html#cat-Schematics">档案分类</a>'),
        encoding="utf-8",
    )
    print(f"schematics hub {len(schematics)} maps_touched={updated}")
    return


def wire_nav():
    idx = ROOT / "index.html"
    t = idx.read_text(encoding="utf-8")
    t = t.replace("css/wiki.css?v=20260926i", f"css/wiki.css?v={CSS}")
    t = t.replace("css/wiki.css?v=20260926a", f"css/wiki.css?v={CSS}")
    if "p/monsters.html" not in t:
        t = t.replace(
            '<a class="sfx" href="p/bosses.html">Boss 掉落</a>',
            '<a class="sfx" href="p/monsters.html">怪物</a>\n          <a class="sfx" href="p/bosses.html">Boss 掉落</a>\n          <a class="sfx" href="p/schematics.html">图纸</a>',
            1,
        )
    news = '<li><time>09-26</time><span class="news-body"><a href="p/monsters.html">怪物</a> · <a href="p/schematics.html">图纸流程</a> · 移动端适配</span></li>\n'
    if "p/monsters.html\">怪物</a> · <a href=\"p/schematics.html\"" not in t:
        t = t.replace(
            '<ul class="news">',
            '<ul class="news">\n' + news,
            1,
        )
    idx.write_text(t, encoding="utf-8")

    clog = ROOT / "p" / "changelog.html"
    c = clog.read_text(encoding="utf-8")
    block = """<article class="sec"><h2>2026-09-26 · 02 清单 · 怪物 / 图纸 / 移动端</h2>
<ul>
  <li>全站 CSS 加强手机适配（表格横滑、双列折叠、触控热区）。</li>
  <li>新增 <a href="monsters.html">怪物</a>：总览图 + 每种怪独立页（刷新点图 / 掉落 / 战斗数据）。</li>
  <li>新增 <a href="schematics.html">图纸</a>总览；25 张 Schematic 档案页补获取流程图与点位图（StudyProp / 拉杆 / 雕像 / Togane）。</li>
</ul></article>
"""
    if "02 清单" not in c:
        c = c.replace(
            '<article class="sec"><h2>2026-09-26 · 档案战斗字段',
            block + '<article class="sec"><h2>2026-09-26 · 档案战斗字段',
            1,
        )
        clog.write_text(c, encoding="utf-8")


def main():
    build_monsters()
    build_schematics()
    wire_nav()
    # refresh enrich specials with live study coords then leave archive as-is (pages patched)
    print("02 done")


if __name__ == "__main__":
    main()
