# -*- coding: utf-8 -*-
"""Build regions / spawn-crystals / fishing spot maps pages."""
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
P = ROOT / "p"
CSS = "20260926x"
TL = (-3087.361, -3989.256)
BR = (2977.139, 1635.244)


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", str(name), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s.strip()) or "x"


def load(name, default=None):
    p = LIVE / name
    if not p.exists():
        return {} if default is None else default
    return json.loads(p.read_text(encoding="utf-8"))


def world_to_px(x: float, z: float, w: int, h: int):
    px = (float(x) - TL[0]) / (BR[0] - TL[0]) * w
    py = (float(z) - TL[1]) / (BR[1] - TL[1]) * h
    return px, py


def font(size=18):
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_markers(spots, title, subtitle, out_path, small=False):
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    base = Image.open(MAP_CLEAN).convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    f, fs = font(20), font(14)
    r = 7 if small else 11
    for i, (idx, x, z, lab) in enumerate(spots):
        px, py = world_to_px(x, z, w, h)
        d.ellipse((px - r, py - r, px + r, py + r), fill=(255, 196, 72, 230), outline=(20, 16, 8, 255), width=2)
        label = str(lab if lab is not None else idx)
        d.text((px + r + 3, py - 8), label, fill=(255, 240, 200, 255), font=fs)
    d.rectangle((12, 12, min(w - 12, 720), 78), fill=(12, 10, 8, 200))
    d.text((24, 20), title, fill=(255, 210, 120, 255), font=f)
    d.text((24, 46), subtitle, fill=(200, 190, 170, 255), font=fs)
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path, quality=90)
    return True


def draw_region_map(name, grids, crystal, shrines, out_path, title=None):
    """Draw region area rectangles + crystal + shrine markers."""
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    base = Image.open(MAP_CLEAN).convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    f, fs = font(20), font(13)
    # Area grids: Center/Radius are XZ as Vector2 (X,Z)
    for g in grids or []:
        c = g.get("Center")
        rad = g.get("Radius")
        if not c or not rad:
            continue
        cx, cz = float(c[0]), float(c[1])
        rx, rz = float(rad[0]), float(rad[1])
        x0, z0 = cx - rx, cz - rz
        x1, z1 = cx + rx, cz + rz
        px0, py0 = world_to_px(x0, z0, w, h)
        px1, py1 = world_to_px(x1, z1, w, h)
        box = [min(px0, px1), min(py0, py1), max(px0, px1), max(py0, py1)]
        d.rectangle(box, outline=(94, 184, 255, 220), width=3, fill=(94, 184, 255, 35))
        kids = g.get("ChildAreas") or {}
        for cn, ca in kids.items():
            for cg in ca.get("Grid") or []:
                cc, cr = cg.get("Center"), cg.get("Radius")
                if not cc or not cr:
                    continue
                kx0, kz0 = float(cc[0]) - float(cr[0]), float(cc[1]) - float(cr[1])
                kx1, kz1 = float(cc[0]) + float(cr[0]), float(cc[1]) + float(cr[1])
                ax0, ay0 = world_to_px(kx0, kz0, w, h)
                ax1, ay1 = world_to_px(kx1, kz1, w, h)
                d.rectangle(
                    [min(ax0, ax1), min(ay0, ay1), max(ax0, ax1), max(ay0, ay1)],
                    outline=(255, 196, 72, 200),
                    width=2,
                    fill=(255, 196, 72, 28),
                )
                d.text((min(ax0, ax1) + 4, min(ay0, ay1) + 4), str(cn)[:18], fill=(255, 230, 160, 255), font=fs)
    if crystal and len(crystal) >= 3:
        px, py = world_to_px(crystal[0], crystal[2], w, h)
        d.ellipse((px - 10, py - 10, px + 10, py + 10), fill=(220, 120, 255, 230), outline=(255, 255, 255, 255), width=2)
        d.text((px + 12, py - 8), "重生水晶", fill=(230, 180, 255, 255), font=fs)
    for i, sh in enumerate(shrines or [], 1):
        pos = sh.get("Position")
        if not pos or len(pos) < 3:
            continue
        px, py = world_to_px(pos[0], pos[2], w, h)
        d.rectangle((px - 7, py - 7, px + 7, py + 7), fill=(120, 220, 160, 230), outline=(20, 40, 20, 255), width=2)
        d.text((px + 10, py - 8), (sh.get("Name") or f"神庙{i}")[:14], fill=(160, 240, 190, 255), font=fs)
    d.rectangle((12, 12, min(w - 12, 640), 72), fill=(12, 10, 8, 200))
    d.text((24, 18), title or name, fill=(255, 210, 120, 255), font=f)
    d.text((24, 44), "蓝框=区域范围 · 紫点=重生水晶 · 绿方=神庙", fill=(200, 190, 170, 255), font=fs)
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path, quality=90)


PAGE_CSS = f"""
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
    .callout{{border-left:3px solid var(--gold);padding:.35rem 0 .35rem .75rem;margin:.5rem 0;color:var(--muted);font-size:.9rem}}
    .top-nav{{display:flex;flex-wrap:wrap;gap:.65rem;font-size:.82rem}}
    .top-nav a{{color:var(--muted)}}
    .top-nav a:hover{{color:var(--gold)}}
    .grid-cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.75rem;margin-top:.6rem}}
    .grid-cards a{{border:1px solid var(--line);background:rgba(255,255,255,.02);padding:.7rem .8rem;color:var(--muted)}}
    .grid-cards a:hover{{border-color:var(--gold);color:var(--cream)}}
    .grid-cards strong{{display:block;color:var(--cream);margin-bottom:.25rem}}
"""


def page_shell(title, crumb, body, extra_nav=""):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" dark">
  <title>{esc(title)} · Slayers 2 Wiki</title>
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/wiki.css?v={CSS}">
  <style>{PAGE_CSS}</style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="../"><span>Slayers 2 Wiki</span></a>
    {extra_nav}
    <span class="top-ver" data-zh="{esc(title)}" data-en="{esc(title)}">{esc(title)}</span>
  </header>
  <main class="page">
    <p class="crumb"><a href="../" data-zh="主页" data-en="Home">主页</a> / {crumb}</p>
    {body}
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span data-zh="{esc(title)}" data-en="{esc(title)}">{esc(title)}</span>
      <span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="../" data-zh="返回主页" data-en="Back to home">返回主页</a>
  </footer>
  <script src="../js/i18n.js?v={CSS}"></script>
</body>
</html>""".replace('<meta name="color-scheme" dark">', '<meta name="color-scheme" content="dark">')


REGION_META = {
    "Mistfall Harbor": {
        "cn": "迷雾港湾",
        "levels": "1 – 35",
        "traits": "新手港镇与主线起步区；码头、渔夫、补给商店密集。",
        "has": "钓鱼证 Sofen · 鱼竿 Jeso · 银造 Ginzo · 野兽/血猎低阶鬼 · 码头任务",
        "tips": "拿钓鱼证、买基础竿、清港口周边低阶怪。",
    },
    "Butterfly Estate": {
        "cn": "蝴蝶屋 / 蝶屋敷",
        "levels": "20 – 55",
        "traits": "鬼杀队驻地与治疗/补给核心；呼吸训练与队务任务集中。",
        "has": "Ren 葫芦店 · 医疗任务 · 低/高阶鬼练级 · 呼吸相关导师入口",
        "tips": "阵营进度、回复药、队士任务中转站。",
    },
    "Bamboo Grove": {
        "cn": "竹林",
        "levels": "25 – 60",
        "traits": "竹林与圣所地貌；含子区域「竹林圣所」重生水晶。",
        "has": "区域任务 NPC · 竹林圣所水晶 · 中阶野怪",
        "tips": "适合中期刷怪与路过传送。",
    },
    "Hidden Mist Village": {
        "cn": "隐雾村",
        "levels": "45 – 85",
        "traits": "锻造 / 精炼 / 暮落装备枢纽；地势较高。",
        "has": "铁匠 Togane · 精炼 Hagane · 石匠 Tobei · 饵贩 Nori · 拳套雕像",
        "tips": "图纸锻造、精炼、暮落进度必经。",
    },
    "Windy Peak": {
        "cn": "风之峰",
        "levels": "40 – 75",
        "traits": "高地风区；土匪与山路战斗点较多。",
        "has": "山贼刷新 · 风相关任务 · 神庙",
        "tips": "注意悬崖地形与群怪。",
    },
    "Iceveil Valley": {
        "cn": "冰纱谷",
        "levels": "70 – 110",
        "traits": "严寒谷地；钓鱼交付与高难冬区内容。",
        "has": "冰纱聚落水晶 · 冬店 Lynx · 雪人/冰系内容 · 鱼类交付点",
        "tips": "带御寒/高伤装；渔获可交付聚落。",
    },
    "Final Selection Plains": {
        "cn": "最终选拔平原",
        "levels": "90 – 120+",
        "traits": "终选试炼场地；高危 Boss「遗失」与终局路线。",
        "has": "终选水晶 · Lost Boss · 选拔相关任务",
        "tips": "组队或高配再进；掉落见遗失宝箱。",
    },
    "Verdant Cliffs": {
        "cn": "翠绿悬崖",
        "levels": "30 – 65",
        "traits": "悬崖绿地过渡带，连通港湾与内陆。",
        "has": "区域范围标记 · 路过怪群",
        "tips": "赶路时注意落差。",
    },
    "Stone Sanctuary": {
        "cn": "石之圣所",
        "levels": "50 – 80",
        "traits": "岩石圣域地貌，偏中后期探索。",
        "has": "区域范围 · 探索向内容",
        "tips": "可与隐雾村路线衔接。",
    },
    "Forgotten Ruins": {
        "cn": "遗忘遗迹",
        "levels": "55 – 90",
        "traits": "废墟探索区，战斗与搜刮并重。",
        "has": "遗迹范围 · 精英怪倾向",
        "tips": "注意伏击与狭窄通道。",
    },
    "Misc": {
        "cn": "杂项 / 游荡",
        "levels": "全等级",
        "traits": "不绑固定区域的 NPC、限时商人与跨区事件。",
        "has": "黑商多点 · 部分导师/特殊对话",
        "tips": "黑商见专题页；坐标随事件变化。",
    },
}


def quest_levels_by_region():
    qh = load("wiki-quest-holder.json", {})
    npcs = load("wiki-npcs.json", [])
    nr = {n.get("Name"): n.get("Region") for n in npcs if n.get("Name")}
    levels = {k: [] for k in REGION_META}
    for qname, q in (qh.items() if isinstance(qh, dict) else []):
        if not isinstance(q, dict):
            continue
        m = re.search(r"\(Lv\s*(\d+)\)", str(qname), re.I)
        lv = int(m.group(1)) if m else q.get("Level") or q.get("ReqLevel")
        if not lv:
            continue
        # find region via deliver/target npc
        regs = set()
        specs = q.get("TaskSpecs") or {}
        for sp in specs.values() if isinstance(specs, dict) else []:
            t = (sp or {}).get("TargetNpc")
            if t and nr.get(t):
                regs.add(nr[t])
        giver = q.get("Giver") or q.get("Npc")
        if giver and nr.get(giver):
            regs.add(nr[giver])
        for r in regs:
            if r in levels:
                levels[r].append(int(lv))
    return levels


def build_regions():
    detail = load("wiki-regions-detail.json", {})
    crystals_ws = load("wiki-spawn-crystals.json", [])
    qlv = quest_levels_by_region()
    monsters = (load("wiki-monsters.json", {}) or {}).get("monsters") or []
    mob_count = {}
    for m in monsters:
        r = m.get("Region") or "Misc"
        if m.get("HasShop") or m.get("TimedVendor"):
            continue
        mob_count[r] = mob_count.get(r, 0) + 1

    # overview map: all crystals + region centers
    overview_spots = []
    for i, c in enumerate(crystals_ws, 1):
        p = c.get("Position")
        if p and len(p) >= 3:
            overview_spots.append((i, p[0], p[2], (c.get("Name") or "").replace("SpawnCrystal - ", "")[:10] or str(i)))
    if overview_spots:
        draw_markers(overview_spots, "Ouwland 区域 · 重生水晶", f"{len(overview_spots)} 座水晶", MAP_DIR / "regions-crystals-overview.png")

    # all-region outline map
    base_spots = []
    for i, (name, row) in enumerate(sorted(detail.items()), 1):
        grids = row.get("AreaGrid") or []
        if grids and grids[0].get("Center"):
            c = grids[0]["Center"]
            base_spots.append((i, c[0], c[1], (REGION_META.get(name) or {}).get("cn") or name)[:8])
        elif row.get("CrystalAt"):
            c = row["CrystalAt"]
            base_spots.append((i, c[0], c[2], (REGION_META.get(name) or {}).get("cn") or name)[:8])
    if base_spots:
        draw_markers(base_spots, "Ouwland 区域中心", "编号对应下方表", MAP_DIR / "regions-all.png")

    cards = []
    sections = []
    for name in sorted(detail.keys(), key=lambda n: (REGION_META.get(n) or {}).get("cn") or n):
        row = detail[name]
        meta = REGION_META.get(name) or {"cn": name, "levels": "—", "traits": "", "has": "", "tips": ""}
        cn = meta["cn"]
        sid = slug(name)
        # refine levels with quest data
        lv_txt = meta["levels"]
        if qlv.get(name):
            qs = sorted(qlv[name])
            lv_txt = f"{qs[0]} – {qs[-1]}（任务标级）· 参考 {meta['levels']}"
        map_file = f"region-{sid}.png"
        draw_region_map(
            name,
            row.get("AreaGrid") or [],
            row.get("CrystalAt"),
            row.get("Shrines") or [],
            MAP_DIR / map_file,
            title=f"{cn} · {name}",
        )
        crystal = row.get("CrystalAt")
        crystal_s = (
            f"<code>{crystal[0]:.0f}, {crystal[1]:.0f}, {crystal[2]:.0f}</code>"
            if crystal
            else "见子区域 / 总览图（部分水晶挂在子区）"
        )
        shrine_lis = ""
        for sh in row.get("Shrines") or []:
            pos = sh.get("Position")
            price = sh.get("Price") or {}
            wen = price.get("Wen")
            shrine_lis += f"<li>{esc(sh.get('Name') or '神庙')}"
            if wen:
                shrine_lis += f" · {esc(wen)} 文"
            if pos:
                shrine_lis += f" · <code>{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}</code>"
            shrine_lis += "</li>"
        cards.append(
            f'<a href="#{esc(sid)}"><strong>{esc(cn)}</strong><span data-zh="等级 {esc(lv_txt)}" data-en="Level {esc(lv_txt)}">等级 {esc(lv_txt)}</span></a>'
        )
        sections.append(
            f"""
    <article class="sec" id="{esc(sid)}">
      <h2 data-zh="{esc(cn)}" data-en="{esc(name)}">{esc(cn)}</h2>
      <p class="en" style="opacity:.75;font-size:.85rem"><code>{esc(name)}</code></p>
      <table>
        <tr><th data-zh="等级范围" data-en="Level range">等级范围</th><td>{esc(lv_txt)}</td></tr>
        <tr><th data-zh="特性" data-en="Traits">特性</th><td>{esc(meta.get("traits") or "—")}</td></tr>
        <tr><th data-zh="主要有什么" data-en="Highlights">主要有什么</th><td>{esc(meta.get("has") or "—")}</td></tr>
        <tr><th data-zh="刷新实体约" data-en="Spawn entries">刷新实体约</th><td>{mob_count.get(name, 0)}（Regions 条目，含水晶/事件体）</td></tr>
        <tr><th data-zh="重生水晶" data-en="Spawn crystal">重生水晶</th><td>{crystal_s}</td></tr>
        <tr><th data-zh="提示" data-en="Tip">提示</th><td>{esc(meta.get("tips") or "—")}</td></tr>
      </table>
      {"<h3>神庙</h3><ul>" + shrine_lis + "</ul>" if shrine_lis else ""}
      <img class="map-img" src="../assets/wiki-maps/{esc(map_file)}" alt="{esc(cn)}">
    </article>"""
        )

    body = f"""
    <article class="sec">
      <h1 data-zh="区域" data-en="Regions">区域</h1>
      <p data-zh="Ouwland 主世界分区。蓝框为 Area 碰撞范围，紫点为重生水晶，绿方为付费神庙。"
         data-en="Ouwland world regions. Blue = area bounds, purple = spawn crystals, green = shrines.">
        Ouwland 主世界分区。蓝框为 Area 碰撞范围，紫点为重生水晶，绿方为付费神庙。</p>
      <img class="map-img" src="../assets/wiki-maps/regions-all.png" alt="区域总览">
      <p class="callout">重生水晶专题：<a class="quest-link" href="spawn-crystals.html">重生水晶</a>
        · 怪物刷新：<a class="quest-link" href="monsters.html">怪物</a></p>
      <div class="grid-cards">{"".join(cards)}</div>
    </article>
    {"".join(sections)}
"""
    nav = '<nav class="top-nav"><a href="#Mistfall-Harbor">港湾</a><a href="#Butterfly-Estate">蝴蝶屋</a><a href="#Hidden-Mist-Village">隐雾</a><a href="#Iceveil-Valley">冰纱</a><a href="spawn-crystals.html">水晶</a></nav>'
    (P / "regions.html").write_text(
        page_shell("区域", '<span data-zh="区域" data-en="Regions">区域</span>', body, nav),
        encoding="utf-8",
    )
    print(f"regions {len(detail)}")


def build_crystals():
    detail = load("wiki-regions-detail.json", {})
    crystals_ws = load("wiki-spawn-crystals.json", [])
    # merge named list
    rows = []
    for c in crystals_ws:
        p = c.get("Position")
        if not p:
            continue
        name = (c.get("Name") or "SpawnCrystal").replace("SpawnCrystal - ", "").replace("SpawnCrystal", "未命名")
        if name == "未命名":
            # try match region crystal
            for rn, row in detail.items():
                ca = row.get("CrystalAt")
                if ca and abs(ca[0] - p[0]) < 2 and abs(ca[2] - p[2]) < 2:
                    name = rn
                    break
        rows.append({"Name": name, "Position": p, "RegionHint": name})

    spots = [(i, r["Position"][0], r["Position"][2], r["Name"][:12]) for i, r in enumerate(rows, 1)]
    draw_markers(spots, "重生水晶 · 全部", "靠近按 T 长按 Set Spawn", MAP_DIR / "spawn-crystals-all.png")

    table = "<tr><th>#</th><th data-zh=\"名称\" data-en=\"Name\">名称</th><th>XYZ</th></tr>"
    for i, r in enumerate(rows, 1):
        p = r["Position"]
        table += (
            f"<tr><td>{i}</td><td>{esc(r['Name'])}</td>"
            f"<td><code>{p[0]:.1f}, {p[1]:.1f}, {p[2]:.1f}</code></td></tr>"
        )

    body = f"""
    <article class="sec">
      <h1 data-zh="重生水晶" data-en="Spawn Crystals">重生水晶</h1>
      <p data-zh="游戏内称为 Spawn Crystal。靠近后出现交互「Set Spawn」（默认键 <strong>T</strong>，长按约 1 秒），把你的重生点设到该水晶。"
         data-en="In-game Spawn Crystal. Hold <strong>T</strong> (~1s) on the Set Spawn prompt to save your respawn here.">
        游戏内称为 Spawn Crystal。靠近后出现交互「Set Spawn」（默认键 <strong>T</strong>，长按约 1 秒），把你的重生点设到该水晶。</p>
      <ul>
        <li data-zh="死亡或使用回城类效果时，会在<strong>当前设定的水晶附近</strong>重生（区域 Spawns 点）。"
            data-en="On death you respawn near your saved crystal (region spawn pads).">死亡或使用回城类效果时，会在<strong>当前设定的水晶附近</strong>重生（区域 Spawns 点）。</li>
        <li data-zh="换图进度前建议先在目标区域水晶设点，减少跑尸。"
            data-en="Set a crystal in your target region before long treks.">换图进度前建议先在目标区域水晶设点，减少跑尸。</li>
        <li data-zh="部分水晶挂在子区域名下（如竹林圣所、冰纱聚落、终选）。"
            data-en="Some crystals belong to child areas (Bamboo Grove Sanctuary, Iceveil Settlement, Final Selection).">部分水晶挂在子区域名下（如竹林圣所、冰纱聚落、终选）。</li>
        <li data-zh="与付费神庙不同：水晶免费设重生；神庙另见各区域页。"
            data-en="Unlike paid shrines, crystals free-set spawn.">与付费神庙不同：水晶免费设重生；神庙另见各区域页。</li>
      </ul>
      <img class="map-img" src="../assets/wiki-maps/spawn-crystals-all.png" alt="重生水晶">
      <p class="callout">区域范围图见 <a class="quest-link" href="regions.html">区域</a>。</p>
    </article>
    <article class="sec">
      <h2 data-zh="点位表" data-en="Locations">点位表</h2>
      <p>共 <strong>{len(rows)}</strong> 座（实机 Workspace 扫描）。</p>
      <table>{table}</table>
    </article>
"""
    (P / "spawn-crystals.html").write_text(
        page_shell("重生水晶", '<span data-zh="重生水晶" data-en="Spawn Crystals">重生水晶</span>', body),
        encoding="utf-8",
    )
    print(f"crystals {len(rows)}")


# Fish -> recommended spots (world XYZ clusters). Based on item text + quests + docks.
FISH_SPOTS = {
    "OuwFish": {
        "cn": "奥乌鱼",
        "tier": "Common",
        "rod": "Basic Fishing Rod",
        "bait": "Worm",
        "where": "迷雾港湾码头浅水",
        "spots": [(-192.0, 806.9, 602.7), (-160.8, 796.2, 703.3), (136.5, 874, 733.4)],
    },
    "OuwFwesh": {
        "cn": "奥乌鲜鱼",
        "tier": "Common",
        "rod": "Basic Fishing Rod",
        "bait": "Worm",
        "where": "迷雾港湾日常水域",
        "spots": [(-192.0, 806.9, 602.7), (140.7, 873.5, 728.2)],
    },
    "Sea Horse": {
        "cn": "海马",
        "tier": "Common",
        "rod": "Basic Fishing Rod",
        "bait": "Worm",
        "where": "港湾近岸",
        "spots": [(-160.8, 796.2, 703.3), (144.2, 873.5, 735.1)],
    },
    "Coral": {
        "cn": "珊瑚",
        "tier": "Common",
        "rod": "Basic Fishing Rod",
        "bait": "Worm",
        "where": "港湾礁石带",
        "spots": [(136.5, 874, 733.4), (-192.0, 806.9, 602.7)],
    },
    "Clown Fish": {
        "cn": "小丑鱼",
        "tier": "Rare",
        "rod": "Rare Fishing Rod",
        "bait": "Fish Head",
        "where": "港湾 / 冰纱交付相关渔获",
        "spots": [(-192.0, 806.9, 602.7), (-208.8, 1352.7, -2596.5), (-114.4, 1354, -2520.9)],
    },
    "Zebra Fish": {
        "cn": "斑马鱼",
        "tier": "Rare",
        "rod": "Rare Fishing Rod",
        "bait": "Fish Head",
        "where": "港湾中层 · 可交冰纱仓储",
        "spots": [(-192.0, 806.9, 602.7), (-114.4, 1354, -2520.9)],
    },
    "Golden Fish": {
        "cn": "金鱼",
        "tier": "Rare",
        "rod": "Rare Fishing Rod",
        "bait": "Fish Head",
        "where": "港湾；用于换更好竿 / 冰纱交付",
        "spots": [(-192.0, 806.9, 602.7), (-114.4, 1354, -2520.9)],
    },
    "Fish Head": {
        "cn": "鱼头",
        "tier": "Bait",
        "rod": "Rare Fishing Rod",
        "bait": "—",
        "where": "饵 · Nori / 渔获拆分；钓点同港湾",
        "spots": [(1640, 606, -125), (-192.0, 806.9, 602.7)],
    },
    "Krathulon": {
        "cn": "克拉苏隆",
        "tier": "Legendary",
        "rod": "Legendary Fishing Rod",
        "bait": "Golden Tentacle",
        "where": "深水 / 冰纱一带珍品",
        "spots": [(-208.8, 1352.7, -2596.5), (-114.4, 1354, -2520.9), (-192.0, 806.9, 602.7)],
    },
    "Crustadon": {
        "cn": "甲壳兽",
        "tier": "Legendary",
        "rod": "Legendary Fishing Rod",
        "bait": "Golden Tentacle",
        "where": "深水传奇渔获",
        "spots": [(-192.0, 806.9, 602.7), (-208.8, 1352.7, -2596.5), (1640, 606, -125)],
    },
    "Golden Tentacle": {
        "cn": "金色触手",
        "tier": "Bait/Legendary",
        "rod": "Legendary Fishing Rod",
        "bait": "—",
        "where": "深水饵；传奇竿才能稳住",
        "spots": [(-192.0, 806.9, 602.7), (-208.8, 1352.7, -2596.5)],
    },
    "Drowned Lure": {
        "cn": "溺毙鱼饵",
        "tier": "Special",
        "rod": "Legendary Fishing Rod",
        "bait": "—",
        "where": "特殊饵（高 BaitTier）；深水点",
        "spots": [(-192.0, 806.9, 602.7), (-208.8, 1352.7, -2596.5)],
    },
}


def build_fishing():
    items = load("items-enriched.json", {})
    fish_items = load("wiki-fishing-items.json", {})
    # NPC spots
    npcs = load("wiki-npcs.json", [])
    pos = {n["Name"]: n["Position"] for n in npcs if n.get("Name") and n.get("Position")}
    fish_npc_spots = []
    for i, name in enumerate(["Dock Master Sofen", "Fisherman Jeso", "Baitmonger Nori"], 1):
        if name in pos:
            p = pos[name]
            fish_npc_spots.append((i, p[0], p[2], name.split()[-1]))
    if fish_npc_spots:
        draw_markers(fish_npc_spots, "钓鱼相关 NPC", "Sofen 证 · Jeso 竿 · Nori 饵", MAP_DIR / "fishing-npcs.png")

    # per-fish maps
    fish_sections = []
    catalog_rows = []
    for fname, meta in FISH_SPOTS.items():
        spots = [(i, s[0], s[2], str(i)) for i, s in enumerate(meta["spots"], 1)]
        map_name = f"fish-{slug(fname)}.png"
        draw_markers(spots, f"推荐钓点 · {meta['cn']}", meta["where"][:40], MAP_DIR / map_name)
        it = items.get(fname) or {}
        icon = ""
        aid = (it.get("Icon") or "").replace("rbxassetid://", "")
        if aid.isdigit():
            icon = f'<img src="../assets/icons/items/{aid}.png" width="40" height="40" alt="">'
        rod = meta.get("rod") or ""
        bait = meta.get("bait") or ""
        rod_a = (
            f'<a class="quest-link" href="archive/items/{slug(rod)}.html">{esc((items.get(rod) or {}).get("NameCN") or rod)}</a>'
            if rod and rod != "—"
            else "—"
        )
        bait_a = (
            f'<a class="quest-link" href="archive/items/{slug(bait)}.html">{esc((items.get(bait) or {}).get("NameCN") or bait)}</a>'
            if bait and bait != "—"
            else "—"
        )
        desc = (fish_items.get(fname) or {}).get("Description") or it.get("Description") or ""
        fish_sections.append(
            f"""
    <article class="sec" id="fish-{esc(slug(fname))}">
      <div class="head" style="display:flex;gap:.75rem;align-items:flex-start">
        {icon}
        <div>
          <h2>{esc(meta['cn'])}</h2>
          <p style="opacity:.75;font-size:.85rem"><code>{esc(fname)}</code> · {esc(meta['tier'])}</p>
        </div>
      </div>
      <p>{esc(desc)}</p>
      <table>
        <tr><th>推荐水域</th><td>{esc(meta['where'])}</td></tr>
        <tr><th>推荐竿</th><td>{rod_a}</td></tr>
        <tr><th>推荐饵</th><td>{bait_a}</td></tr>
      </table>
      <img class="map-img" src="../assets/wiki-maps/{esc(map_name)}" alt="{esc(meta['cn'])} 钓点">
    </article>"""
        )
        catalog_rows.append(
            f'<tr><td>{icon}</td><td><a class="quest-link" href="#fish-{esc(slug(fname))}">{esc(meta["cn"])}</a></td>'
            f'<td>{esc(meta["tier"])}</td><td>{esc(meta["where"])}</td></tr>'
        )

    # rods table from items
    rods = [k for k in items if "Fishing Rod" in k]
    rod_rows = ""
    for r in sorted(rods):
        it = items[r]
        price = (it.get("Price") or {}).get("Wen")
        rod_rows += (
            f'<tr><td><a class="quest-link" href="archive/items/{slug(r)}.html">{esc(it.get("NameCN") or r)}</a></td>'
            f'<td>{esc(price if price is not None else "—")}</td><td>{esc(it.get("Rarity") or "")}</td></tr>'
        )

    body = f"""
    <article class="sec" id="how">
      <h1 data-zh="钓鱼" data-en="Fishing">钓鱼</h1>
      <ol>
        <li>找码头 <strong>Dock Master Sofen</strong>（迷雾港湾），接证任务，付 <strong>5000 文</strong>。</li>
        <li>拾取 <a class="quest-link" href="archive/items/Permit-Stamp.html">许可证印章</a>，交回 Sofen → <a class="quest-link" href="archive/items/Fishing-Permit.html">钓鱼许可证</a>。</li>
        <li>向 <strong>Fisherman Jeso</strong> 买竿；向 <strong>Baitmonger Nori</strong>（隐雾村）买高级饵。</li>
        <li>装备竿（可选饵），对水面抛竿；按提示收线。</li>
      </ol>
      <p class="callout">竿阶：基础竿捞小鱼 · 稀有竿 + 鱼头饵中层 · 传奇竿 + 金色触手深水传奇。</p>
      <img class="map-img" src="../assets/wiki-maps/fishing-npcs.png" alt="钓鱼 NPC">
    </article>
    <article class="sec" id="rods">
      <h2 data-zh="鱼竿" data-en="Rods">鱼竿</h2>
      <table><tr><th>竿</th><th>标价（文）</th><th>稀有度</th></tr>{rod_rows}</table>
    </article>
    <article class="sec" id="fish">
      <h2 data-zh="鱼类与推荐钓点" data-en="Fish & recommended spots">鱼类与推荐钓点</h2>
      <p>每条鱼下方附推荐钓点图（码头 / 隐雾 / 冰纱交付带）。实机掉落表在服务端，点位为游玩向推荐。</p>
      <table><tr><th></th><th>鱼</th><th>档位</th><th>推荐水域</th></tr>{"".join(catalog_rows)}</table>
    </article>
    {"".join(fish_sections)}
"""
    nav = '<nav class="top-nav"><a href="#how">流程</a><a href="#rods">鱼竿</a><a href="#fish">鱼类</a></nav>'
    (P / "fishing.html").write_text(
        page_shell("钓鱼", '<span data-zh="钓鱼" data-en="Fishing">钓鱼</span>', body, nav),
        encoding="utf-8",
    )
    print(f"fishing fish={len(FISH_SPOTS)} rods={len(rods)}")


def wire_index():
    idx = ROOT / "index.html"
    t = idx.read_text(encoding="utf-8")
    if "spawn-crystals.html" not in t:
        t = t.replace(
            '<a class="sfx" href="p/regions.html">区域</a>',
            '<a class="sfx" href="p/regions.html">区域</a>\n          <a class="sfx" href="p/spawn-crystals.html">重生水晶</a>',
            1,
        )
    news = '<li><time>09-26</time><span class="news-body"><a href="p/regions.html">区域地图</a> · <a href="p/spawn-crystals.html">重生水晶</a> · 钓鱼推荐钓点 · 双语优化 · <a href="p/monsters.html">怪物</a></span></li>\n'
    if "spawn-crystals.html\">重生水晶" not in t.split("news-body")[1][:800] if "news-body" in t else True:
        t = t.replace('<ul class="news">', '<ul class="news">\n            ' + news, 1) if '<ul class="news">' in t else t
        # fallback: insert after first news li
        if news.strip() not in t:
            t = t.replace(
                '<li><time>09-26</time><span class="news-body"><a href="p/monsters.html">怪物</a>',
                news + '<li><time>09-26</time><span class="news-body"><a href="p/monsters.html">怪物</a>',
                1,
            )
    # bump i18n
    t = re.sub(r"js/i18n\.js\?v=[^\"]+", f"js/i18n.js?v={CSS}", t)
    idx.write_text(t, encoding="utf-8")


def main():
    build_regions()
    build_crystals()
    build_fishing()
    wire_index()
    print("done world pages")


if __name__ == "__main__":
    main()
