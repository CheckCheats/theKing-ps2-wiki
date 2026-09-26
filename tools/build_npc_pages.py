# -*- coding: utf-8 -*-
"""Build per-NPC archive pages with location maps, dialogue, roles, quests."""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Desktop\ProjectSlayer2_WIKI")
LIVE = ROOT / "data" / "_live"
MAP_CLEAN = ROOT / "assets" / "ouwland-map-clean.png"
MAP_DIR = ROOT / "assets" / "wiki-maps" / "npcs"
OUT = ROOT / "p" / "archive" / "npcs"
TL = (-3087.361, -3989.256)
BR = (2977.139, 1635.244)
CSS = "20260926w"

REGION_CN = {
    "Bamboo Grove": "竹林",
    "Butterfly Estate": "蝴蝶庄园",
    "Mistfall Harbor": "迷雾港",
    "Hidden Mist Village": "隐雾村",
    "Windy Peak": "风之峰",
    "Iceveil": "冰纱谷",
    "Bear Village": "熊村",
    "Misc": "杂项 / 全域",
    "Final Selection": "最终选拔",
}


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", str(name), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s.strip()) or "x"


def unique_slug(name: str, region: str, used: set[str]) -> str:
    base = slug(name)
    if base not in used:
        used.add(base)
        return base
    alt = slug(f"{name}-{region}")
    n = 2
    while alt in used:
        alt = slug(f"{name}-{region}-{n}")
        n += 1
    used.add(alt)
    return alt


def world_to_px(x, z, w, h):
    u = (x - TL[0]) / (BR[0] - TL[0])
    v = (z - TL[1]) / (BR[1] - TL[1])
    return u * w, v * h


def load_font(size: int):
    for name in (
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        "msyh.ttc",
        "arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_markers(spots, title, subtitle, out_path, small=False):
    if not MAP_CLEAN.exists() or not spots:
        return False
    base = Image.open(MAP_CLEAN).convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_t = load_font(20)
    font_s = load_font(13)
    font_n = load_font(11)
    draw.rectangle((0, 0, w, 48), fill=(0, 0, 0, 170))
    draw.text((12, 6), title, fill=(255, 208, 70, 255), font=font_t)
    draw.text((12, 28), subtitle, fill=(220, 220, 220, 230), font=font_s)
    r = 4 if small or len(spots) > 40 else 9
    for i, (num, x, z, label) in enumerate(spots):
        px, py = world_to_px(float(x), float(z), w, h)
        draw.ellipse((px - r - 1, py - r - 1, px + r + 1, py + r + 1), fill=(0, 0, 0, 180))
        draw.ellipse((px - r, py - r, px + r, py + r), fill=(94, 184, 255, 230))
        if not small and len(spots) <= 25:
            t = str(num)
            bb = draw.textbbox((0, 0), t, font=font_n)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            draw.text((px - tw / 2, py - th / 2 - 1), t, fill=(20, 20, 20, 255), font=font_n)
            if label:
                draw.text((px + r + 3, py - 8), label[:12], fill=(255, 255, 255, 230), font=font_n)
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path, "PNG", optimize=True)
    return True


def strip_rich(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"\[.*?\]", "", str(text))
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", t).strip()


def collect_dialogue_lines(mod: dict, limit=40) -> list[str]:
    lines = []
    if not isinstance(mod, dict):
        return lines

    def walk(node, depth=0):
        if depth > 8 or len(lines) >= limit:
            return
        if isinstance(node, dict):
            txt = node.get("Text")
            if isinstance(txt, str) and txt.strip():
                lines.append(strip_rich(txt))
            ans = node.get("Answers")
            if isinstance(ans, dict):
                for k in ans:
                    if k and k not in ("true", "True"):
                        lines.append(f"› {strip_rich(k)}")
            for v in node.values():
                walk(v, depth + 1)
        elif isinstance(node, list):
            for v in node:
                walk(v, depth + 1)

    walk(mod)
    # dedupe preserve order
    seen = set()
    out = []
    for L in lines:
        if L and L not in seen:
            seen.add(L)
            out.append(L)
    return out[:limit]


def item_a(name: str, items: dict) -> str:
    it = items.get(name) or {}
    label = it.get("NameCN") or name
    if name in items:
        return f'<a class="quest-link" href="../items/{slug(name)}.html">{esc(label)}</a>'
    return esc(label)


def page_shell(title: str, crumb: str, body: str) -> str:
    # Depth: p/archive/npcs/*.html → root is ../../../ (same as archive/items)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>{esc(title)} · Slayers 2 Wiki</title>
  <link rel="icon" href="../../../favicon.svg" type="image/svg+xml">
  <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../../css/wiki.css?v={CSS}">
  <style>
    .page{{max-width:var(--max);margin:0 auto;padding:0 1.25rem 3rem;position:relative;z-index:1}}
    .crumb{{color:var(--muted);font-size:.85rem;margin:.5rem 0 1.25rem}}
    .crumb a{{color:var(--gold)}}
    .sec{{margin-bottom:1.25rem;border:1px solid var(--line);background:var(--panel);padding:1rem 1.1rem}}
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
    .map-img{{display:block;width:100%;height:auto;border:1px solid var(--line);margin-top:.55rem;background:#0a0a0a}}
    .dial{{border-left:2px solid rgba(232,184,74,.4);padding:.3rem 0 .3rem .7rem;margin:.3rem 0;color:var(--muted);font-size:.88rem;line-height:1.45}}
    .en{{opacity:.75;font-size:.8rem}}
    .head{{display:flex;flex-wrap:wrap;gap:.55rem;align-items:center;margin:.15rem 0 .55rem}}
    .badge{{display:inline-block;padding:.12rem .5rem;border:1px solid var(--line);font-size:.78rem;color:var(--gold);background:rgba(255,208,70,.06)}}
    .table-scroll{{max-height:min(52vh,420px);overflow:auto;border:1px solid var(--line);margin-top:.45rem}}
    .table-scroll table{{margin:0}}
    .table-scroll th{{position:sticky;top:0;background:#121212;z-index:1}}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="../../../"><span>Slayers 2 Wiki</span></a>
    <span class="top-ver">NPC</span>
  </header>
  <main class="page">
    <p class="crumb">{crumb}</p>
    {body}
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>NPC</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="../../../">返回主页</a>
  </footer>
  <script src="../../../js/i18n.js?v={CSS}"></script>
</body>
</html>
"""


def roles_for(n: dict, name: str, shop_by: dict, offered: dict) -> list[str]:
    role = []
    if shop_by.get(name) or n.get("TimedVendor"):
        role.append("商店 / 限时摊" if n.get("TimedVendor") else "商店")
    if "Trainer" in name or "Expert" in name:
        role.append("导师")
    if "Blacksmith" in name or "Togane" in name or "Yagane" in name:
        role.append("锻造")
    if "Refiner" in name or "Hagane" in name:
        role.append("精炼")
    if "Marketer" in name:
        role.append("黑商")
    if "Sofen" in name:
        role.append("钓鱼许可")
    if name == "Muzan":
        role.append("成鬼 / 游走")
    if offered.get(name):
        role.append("任务")
    if "Sealed Chest" in name:
        role.append("封印箱点")
    if not role:
        role.append("对话 / 氛围")
    return role


def main():
    npcs = json.loads((LIVE / "wiki-npcs.json").read_text(encoding="utf-8"))
    dialogues = json.loads((LIVE / "wiki-dialogues.json").read_text(encoding="utf-8"))
    holder = json.loads((LIVE / "wiki-quest-holder.json").read_text(encoding="utf-8"))
    items = json.loads((LIVE / "items-enriched.json").read_text(encoding="utf-8"))
    shops = json.loads((LIVE / "shops.json").read_text(encoding="utf-8")) if (LIVE / "shops.json").exists() else []
    muzan_extra = json.loads((LIVE / "wiki-muzan.json").read_text(encoding="utf-8")) if (LIVE / "wiki-muzan.json").exists() else {}

    shop_by = {s.get("Name"): s for s in shops if isinstance(s, dict)}
    dial_by: dict[str, list] = defaultdict(list)
    for key, mod in dialogues.items():
        leaf = key.split("/")[-1].replace("_", " ")
        dial_by[leaf].append((key, mod))
        # also raw leaf without spaces variant
        dial_by[key.split("/")[-1]].append((key, mod))

    offered: dict[str, list[str]] = defaultdict(list)
    for qname, q in holder.items():
        if isinstance(q, dict) and isinstance(q.get("OfferNpc"), str):
            offered[q["OfferNpc"]].append(qname)

    OUT.mkdir(parents=True, exist_ok=True)
    MAP_DIR.mkdir(parents=True, exist_ok=True)

    hub_rows = []
    made = 0
    used_slugs: set[str] = set()
    for n in sorted(npcs, key=lambda x: ((x.get("Region") or ""), x.get("Name") or "")):
        name = n.get("Name") or "?"
        region = n.get("Region") or "—"
        s = unique_slug(name, region, used_slugs)
        region_cn = REGION_CN.get(region, region)
        roles = roles_for(n, name, shop_by, offered)
        pos = n.get("Position")
        spawns = n.get("Spawns") or n.get("Positions") or []
        if not isinstance(spawns, list):
            spawns = []
        # normalize spawn list
        pts = []
        for p in spawns:
            if isinstance(p, (list, tuple)) and len(p) >= 3:
                pts.append((float(p[0]), float(p[1]), float(p[2])))
        if not pts and isinstance(pos, (list, tuple)) and len(pos) >= 3:
            pts.append((float(pos[0]), float(pos[1]), float(pos[2])))

        # maps (reuse existing PNG if present)
        map_html = ""
        if pts:
            small = len(pts) > 30
            spots = [(i, x, z, "" if small else f"#{i}") for i, (x, _y, z) in enumerate(pts, 1)]
            mpath = MAP_DIR / f"{s}.png"
            subtitle = f"{len(pts)} 点 · {region_cn}"
            if not mpath.exists():
                draw_markers(spots, name[:28], subtitle, mpath, small=small)
            if mpath.exists():
                map_html = f'<img class="map-img" src="../../../assets/wiki-maps/npcs/{esc(s)}.png" alt="{esc(name)}">'
            if name == "Muzan" and len(pts) > 1:
                map_html = (
                    f'<p>无惨在主世界<strong>游走</strong>，配置刷新点 <strong>{len(pts)}</strong> 个'
                    f"（迷雾港 / 隐雾路 / 冰纱谷等路径）。下图标出全部可遇点位。</p>{map_html}"
                    f'<p class="en">巢穴（Sunless / Muzan\'s Lair）不在大地图范围内，故不绘制点位图；'
                    f'持琵琶铃夜访后由铃铛传送进入。</p>'
                )

        # coords table (scroll when many)
        coord_rows = "".join(
            f"<tr><td>{i}</td><td><code>{x:.1f}, {y:.1f}, {z:.1f}</code></td></tr>"
            for i, (x, y, z) in enumerate(pts[:120], 1)
        ) or "<tr><td colspan=2>无固定坐标</td></tr>"
        coord_wrap_open = '<div class="table-scroll">' if len(pts) > 8 else ""
        coord_wrap_close = "</div>" if len(pts) > 8 else ""

        # functions — links relative to p/archive/npcs → ../../page.html
        funcs = []
        funcs.append(f"区域：<strong>{esc(region_cn)}</strong> <span class='en'>({esc(region)})</span>")
        funcs.append(f"作用：{' · '.join(esc(r) for r in roles)}")
        if name == "Blacksmith Togane":
            funcs.append(
                '锻造台 Station=<code>Ouwland</code>：图纸打造、暮落/初光 T1、'
                '<a class="quest-link" href="../../weapon-upgrade.html">V2/V3 升阶</a>。'
            )
        if "Refiner" in name or "Hagane" in name:
            funcs.append('<a class="quest-link" href="../../refinement.html">精炼</a>装备。')
        if "Marketer" in name:
            funcs.append('<a class="quest-link" href="../../black-market.html">黑商</a>限时货架。')
        if "Sofen" in name:
            funcs.append('<a class="quest-link" href="../../fishing.html">钓鱼许可</a>相关。')
        if name == "Muzan":
            elig = muzan_extra.get("EligibleReputation", -40)
            entry = muzan_extra.get("LairEntryReputation", -20)
            cost = muzan_extra.get("LairEntryCost", 5)
            funcs = [
                f"区域：<strong>{esc(region_cn)}</strong> <span class='en'>({esc(region)})</span>",
                f"作用：{' · '.join(esc(r) for r in roles)}",
                (
                    f'<strong>成鬼门槛</strong>：声望必须 ≤ <strong>{esc(elig)}</strong>'
                    f'（<code>EligibleReputation</code>）。未达标无法接成鬼 / 领琵琶铃。'
                    f'详见 <a class="quest-link" href="../../sides.html#reputation">阵营 · 声望</a>。'
                ),
                (
                    '夜间在主世界游走路线上遇见无惨，领取 '
                    '<a class="quest-link" href="../items/Biwa-Bell.html">琵琶铃 Biwa Bell</a>；'
                    f'使用铃铛进入巢穴（进门另需声望 &lt; <strong>{esc(entry)}</strong>；入场声望 +{esc(cost)}）。'
                ),
                (
                    '巢穴内完成 <a class="quest-link" href="../../quests.html#q-Muzan-Quest">Muzan Quest</a>'
                    '（彼岸花 → 医生 → 安全区），详 '
                    '<a class="quest-link" href="../../evil-arts.html#become-demon">邪恶艺术 · 成鬼</a>。'
                ),
                (
                    '耳语阈值（Whispers）：声望 −10 / −20 / −30 / −40 逐步加深；'
                    '至 −40 提示 “Find me at nightfall.”'
                ),
            ]
        if "Trainer" in name:
            funcs.append('<a class="quest-link" href="../../breathings.html">呼吸法</a> / 风格导师。')

        # shop stock
        shop_html = ""
        shop = shop_by.get(name)
        if shop:
            stock = shop.get("Items") or list((shop.get("Shop") or {}).keys())
            if stock:
                shop_html = (
                    "<h2>商店货架</h2><ul>"
                    + "".join(f"<li>{item_a(x, items)}</li>" for x in stock[:40])
                    + "</ul>"
                )

        func_extra = ""
        if name == "Muzan":
            elig = muzan_extra.get("EligibleReputation", -40)
            entry = muzan_extra.get("LairEntryReputation", -20)
            cost = muzan_extra.get("LairEntryCost", 5)
            func_extra = f"""
      <h3>成鬼流程摘要</h3>
      <ol>
        <li>用猎杀平民 / 鬼杀任务等方式把声望压到 ≤ <strong>{esc(elig)}</strong>。</li>
        <li>夜里在主世界游走点遇见无惨，领取 <a class="quest-link" href="../items/Biwa-Bell.html">琵琶铃</a>。</li>
        <li>使用铃铛进巢穴（进门声望 &lt; <strong>{esc(entry)}</strong>，入场 +{esc(cost)} 声望）。</li>
        <li>完成 <a class="quest-link" href="../../quests.html#q-Muzan-Quest">Muzan Quest</a>：采彼岸花 ×9 → 交 Dr. Higoshima → 安全区放置。</li>
        <li>成鬼后可学邪恶艺术 / 魔球，见 <a class="quest-link" href="../../evil-arts.html">邪恶艺术</a>。</li>
      </ol>
      <p>巢穴不在 Ouwland 大地图内，本页不提供巢穴点位图。</p>
"""

        # quests
        qlist = offered.get(name) or []
        quest_html = ""
        if qlist:
            quest_html = (
                "<h2>可接任务</h2><ul>"
                + "".join(
                    f'<li><a class="quest-link" href="../../quests.html#q-{slug(q)}">{esc(q)}</a></li>'
                    for q in sorted(qlist)
                )
                + "</ul>"
            )

        # dialogue — match by name variants
        dial_lines = []
        for key in (name, name.replace(" ", "_"), name.replace("Trainer ", ""), name.split()[-1] if " " in name else name):
            for _k, mod in dial_by.get(key) or []:
                dial_lines.extend(collect_dialogue_lines(mod))
        if not dial_lines:
            for key, mod in dialogues.items():
                if name in key or name.replace(" ", "_") in key:
                    dial_lines.extend(collect_dialogue_lines(mod))
        seen_d = set()
        dial_uniq = []
        for L in dial_lines:
            if L not in seen_d:
                seen_d.add(L)
                dial_uniq.append(L)
        if dial_uniq:
            dial_html = "<h2>对话摘录</h2>" + "".join(f'<div class="dial">{esc(L)}</div>' for L in dial_uniq[:35])
        else:
            dial_html = "<h2>对话摘录</h2><p>暂无对话模块转储（可能是纯刷怪点 / 环境实体）。</p>"

        badges = "".join(f'<span class="badge">{esc(r)}</span>' for r in roles)
        body = f"""
    <article class="sec">
      <h1>{esc(name)}</h1>
      <p class="en"><code>{esc(name)}</code></p>
      <div class="head">{badges}</div>
      <ul>{"".join(f"<li>{f}</li>" for f in funcs)}</ul>
    </article>
    <article class="sec">
      <h2>地点</h2>
      {map_html or "<p>无坐标数据。</p>"}
      <h3>坐标一览{"（" + str(len(pts)) + "）" if pts else ""}</h3>
      {coord_wrap_open}<table><tr><th>#</th><th>坐标</th></tr>{coord_rows}</table>{coord_wrap_close}
    </article>
    <article class="sec">
      <h2>功能与用处</h2>
      <ul>{"".join(f"<li>{esc(r)}</li>" for r in roles)}</ul>
      {func_extra}
      {shop_html}
      {quest_html}
    </article>
    <article class="sec">
      {dial_html}
    </article>
"""
        (OUT / f"{s}.html").write_text(
            page_shell(
                name,
                f'<a href="../../../">主页</a> / <a href="../../npcs.html">NPC</a> / {esc(name)}',
                body,
            ),
            encoding="utf-8",
        )
        made += 1
        pos_s = f"{pts[0][0]:.0f}, {pts[0][1]:.0f}, {pts[0][2]:.0f}" if pts else "—"
        multi = f" · {len(pts)}点" if len(pts) > 1 else ""
        hub_rows.append(
            f'<tr><td>{made}</td><td><a class="quest-link" href="archive/npcs/{esc(s)}.html"><strong>{esc(name)}</strong></a></td>'
            f"<td>{esc(region_cn)}</td><td><code>{esc(pos_s)}</code>{esc(multi)}</td>"
            f"<td>{esc(' / '.join(roles))}</td><td>{len(qlist) or '—'}</td></tr>"
        )

    # rewrite npcs.html hub
    hub = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>NPC · Slayers 2 Wiki</title>
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
    .sec p,.sec li{{color:var(--muted);font-size:.92rem}}
    .sec table{{width:100%;border-collapse:collapse;font-size:.84rem;margin-top:.4rem}}
    .sec th,.sec td{{border:1px solid var(--line);padding:.35rem .45rem;text-align:left;vertical-align:top}}
    .sec th{{color:var(--gold-deep);background:rgba(255,255,255,.03)}}
    .sec code{{color:var(--gold-deep)}}
    .map-img{{display:block;width:100%;height:auto;border:1px solid var(--line);margin-top:.55rem}}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="../"><span>Slayers 2 Wiki</span></a>
    <span class="top-ver">NPC</span>
  </header>
  <main class="page">
    <p class="crumb"><a href="../">主页</a> / NPC</p>
    <article class="sec">
      <h1>NPC</h1>
      <p>Regions 配置共 <strong>{made}</strong> 名；每人独立介绍页（地点图 · 功能 · 对话 · 任务 / 商店）。
        游走型如 <a class="quest-link" href="archive/npcs/Muzan.html">Muzan</a> 标出全部刷新点。</p>
      <p>专项：<a class="quest-link" href="forge.html">锻造 Togane</a> ·
        <a class="quest-link" href="weapon-upgrade.html">V2/V3 升阶</a> ·
        <a class="quest-link" href="refinement.html">精炼</a> ·
        <a class="quest-link" href="black-market.html">黑商</a> ·
        <a class="quest-link" href="fishing.html">钓鱼</a></p>
      <img class="map-img" src="../assets/wiki-maps/npcs-all.png" alt="全部 NPC">
    </article>
    <article class="sec">
      <h2>一览</h2>
      <table><tr><th>#</th><th>名称</th><th>区域</th><th>坐标</th><th>作用</th><th>任务数</th></tr>
      {"".join(hub_rows)}
      </table>
    </article>
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>NPC</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="../">返回主页</a>
  </footer>
  <script src="../js/i18n.js?v={CSS}"></script>
</body>
</html>
"""
    (ROOT / "p" / "npcs.html").write_text(hub, encoding="utf-8")

    # overview map all fixed positions
    all_spots = []
    i = 0
    for n in npcs:
        pos = n.get("Position")
        if isinstance(pos, (list, tuple)) and len(pos) >= 3:
            i += 1
            all_spots.append((i, float(pos[0]), float(pos[2]), ""))
    overview = ROOT / "assets" / "wiki-maps" / "npcs-all.png"
    if not overview.exists():
        draw_markers(all_spots, f"NPC · {i}", "有坐标落点（多点游走见个人页）", overview, small=True)
    print(f"npc pages {made}")


if __name__ == "__main__":
    main()
