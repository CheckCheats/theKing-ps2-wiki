# -*- coding: utf-8 -*-
"""Build full quests.html + expand npcs.html from Holder + Dialogues dumps."""
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
MAP_DIR = ROOT / "assets" / "wiki-maps"
TL = (-3087.361, -3989.256)
BR = (2977.139, 1635.244)
CSS = "20260926s"

CAT_CN = {
    "Fishing": "钓鱼",
    "Breathing": "呼吸",
    "Training": "锻炼 / 流派",
    "Muzan": "无惨 / 成鬼",
    "BossHunt": "Boss 猎杀",
    "Boss Hunts": "Boss 猎杀",
    "Side": "支线",
    "Main": "主线",
    "Story": "剧情",
    "Combat": "战斗",
    "Delivery": "运送",
    "Misc": "杂项",
    "Core": "魔球训练",
    "EvilArt": "邪恶艺术",
    "Style": "流派",
}


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", str(name), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s.strip()) or "x"


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


def draw_markers(spots, title: str, subtitle: str, out: Path, small=False):
    """spots: list of (i, x, z, label)"""
    if not MAP_CLEAN.exists() or not spots:
        return False
    im = Image.open(MAP_CLEAN).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(overlay)
    font = load_font(14 if small else 16)
    title_f = load_font(22)
    r = 5 if small else 8
    for i, x, z, label in spots:
        px, py = world_to_px(float(x), float(z), w, h)
        if px < -20 or py < -20 or px > w + 20 or py > h + 20:
            continue
        dr.ellipse((px - r, py - r, px + r, py + r), fill=(232, 184, 74, 230), outline=(20, 16, 10, 255))
        if not small:
            dr.text((px + r + 3, py - 8), f"{i}.{label}", fill=(245, 240, 230, 255), font=font)
        else:
            dr.text((px + 4, py - 6), str(i), fill=(245, 240, 230, 220), font=font)
    dr.rectangle((12, 12, min(w - 12, 520), 70), fill=(12, 10, 8, 200))
    dr.text((22, 18), title, fill=(232, 184, 74, 255), font=title_f)
    dr.text((22, 44), subtitle, fill=(200, 195, 185, 255), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(im, overlay).convert("RGB").save(out, quality=90)
    return True


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
    .top-nav{{display:flex;flex-wrap:wrap;gap:.65rem;font-size:.82rem}}
    .top-nav a{{color:var(--muted)}}
    .top-nav a:hover{{color:var(--gold)}}
    .callout{{border-left:3px solid var(--gold);padding:.35rem 0 .35rem .75rem;margin:.5rem 0;color:var(--muted);font-size:.9rem}}
    .toc a{{display:inline-block;margin:.15rem .45rem .15rem 0;font-size:.84rem}}
    .dial{{border-left:2px solid rgba(232,184,74,.35);padding-left:.65rem;margin:.35rem 0;font-size:.88rem;color:var(--muted)}}
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


def item_link(name: str, items: dict) -> str:
    if not name or name in ("Exp", "Wen"):
        return esc(name)
    it = items.get(name) or {}
    cn = it.get("NameCN") or name
    return f'<a class="quest-link" href="archive/items/{slug(name)}.html">{esc(cn)}</a>'


def format_rewards(rewards, items: dict) -> str:
    if not isinstance(rewards, dict) or not rewards:
        return "—"
    bits = []
    for k, v in rewards.items():
        if k == "Exp":
            bits.append(f"经验 <code>{esc(v)}</code>")
        elif k == "Wen":
            bits.append(f"<code>{esc(v)}</code> 文")
        elif isinstance(v, dict):
            qty = v.get("Quantity") or v.get("Amount") or 1
            bits.append(f"{item_link(k, items)} ×{esc(qty)}")
        elif isinstance(v, (int, float)):
            bits.append(f"{item_link(k, items)} ×{esc(v)}")
        else:
            bits.append(f"{item_link(k, items)} {esc(v)}")
    return " · ".join(bits)


def collect_task_positions(task: dict) -> list[tuple[float, float, float]]:
    out = []
    if not isinstance(task, dict):
        return out
    pos = task.get("Position")
    if isinstance(pos, (list, tuple)) and len(pos) >= 3:
        out.append((float(pos[0]), float(pos[1]), float(pos[2])))
    for p in task.get("Positions") or []:
        if isinstance(p, (list, tuple)) and len(p) >= 3:
            out.append((float(p[0]), float(p[1]), float(p[2])))
    return out


def extract_dialogue_lines(mod: dict, limit: int = 12) -> list[str]:
    """Pull readable Text lines from a dialogue module."""
    lines = []
    if not isinstance(mod, dict):
        return lines

    def walk(node, depth=0):
        if depth > 4 or len(lines) >= limit:
            return
        if isinstance(node, dict):
            text = node.get("Text")
            if isinstance(text, str) and text.strip():
                # strip rich tags lightly
                clean = re.sub(r"\[[^\]]*\]", "", text)
                clean = re.sub(r"<[^>]+>", "", clean)
                clean = re.sub(r"\s+", " ", clean).strip()
                if clean and clean not in lines:
                    lines.append(clean)
            for v in node.values():
                walk(v, depth + 1)
        elif isinstance(node, list):
            for v in node:
                walk(v, depth + 1)

    walk(mod)
    return lines[:limit]


def npc_pos_lookup(npcs: list) -> dict:
    m = {}
    for n in npcs:
        name = n.get("Name")
        if name and n.get("Position"):
            m[name] = n["Position"]
    return m


def main():
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    holder_path = LIVE / "wiki-quest-holder.json"
    if not holder_path.exists():
        # fallback
        holder_path = LIVE / "wiki-quests-mod.json"
        raw = json.loads(holder_path.read_text(encoding="utf-8"))
        holder = raw.get("Holder") or raw
    else:
        holder = json.loads(holder_path.read_text(encoding="utf-8"))

    dialogues = {}
    dp = LIVE / "wiki-dialogues.json"
    if dp.exists():
        dialogues = json.loads(dp.read_text(encoding="utf-8"))

    npcs = json.loads((LIVE / "wiki-npcs.json").read_text(encoding="utf-8"))
    items = json.loads((LIVE / "items-enriched.json").read_text(encoding="utf-8"))
    shops = json.loads((LIVE / "shops.json").read_text(encoding="utf-8"))
    pos_of = npc_pos_lookup(npcs)

    # ---------- QUESTS ----------
    by_cat: dict[str, list[str]] = defaultdict(list)
    for qname, q in holder.items():
        if not isinstance(q, dict):
            continue
        cat = q.get("Category") or "Misc"
        by_cat[str(cat)].append(qname)

    toc_bits = []
    for cat in sorted(by_cat, key=lambda c: (-len(by_cat[c]), c)):
        toc_bits.append(
            f'<a href="#cat-{slug(cat)}">{esc(CAT_CN.get(cat, cat))} ({len(by_cat[cat])})</a>'
        )

    sections = []
    maps_made = 0
    for cat in sorted(by_cat, key=lambda c: (-len(by_cat[c]), c)):
        sections.append(f'<article class="sec" id="cat-{slug(cat)}"><h2>{esc(CAT_CN.get(cat, cat))} · {len(by_cat[cat])}</h2></article>')
        for qname in sorted(by_cat[cat]):
            q = holder[qname]
            qid = slug(qname)
            offer = q.get("OfferNpc")
            if offer is False or offer is None:
                offer_s = "—"
            else:
                offer_s = str(offer)
            req = q.get("Requirements") or {}
            lvl = req.get("Level") if isinstance(req, dict) else None
            wen_cost = q.get("WenCostOnAccept")
            item_cost = q.get("ItemCostOnAccept")
            rewards = q.get("Rewards")
            tasks = q.get("TaskSpecs") or {}
            hint = q.get("Hint")
            grant = q.get("GrantItemOnAccept")

            meta_bits = []
            if lvl is not None:
                meta_bits.append(f"等级 <strong>Lv{esc(lvl)}</strong>")
            if offer_s != "—":
                meta_bits.append(f"接取 <strong>{esc(offer_s)}</strong>")
                p = pos_of.get(offer_s)
                if p:
                    meta_bits.append(f"约 <code>{p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f}</code>")
            if wen_cost:
                meta_bits.append(f"接取费用 <code>{esc(wen_cost)}</code> 文")
            if isinstance(item_cost, dict) and item_cost:
                bits = [f"{item_link(k, items)}×{esc(v)}" for k, v in item_cost.items()]
                meta_bits.append("接取材料 " + " · ".join(bits))
            if grant:
                if isinstance(grant, str):
                    meta_bits.append(f"接取发放 {item_link(grant, items)}")
                elif isinstance(grant, dict):
                    meta_bits.append(
                        "接取发放 "
                        + " · ".join(f"{item_link(k, items)}×{esc(v)}" for k, v in grant.items())
                    )

            # tasks
            task_lis = []
            spots = []
            if isinstance(tasks, dict) and tasks:
                for ti, (tname, tspec) in enumerate(tasks.items(), 1):
                    if not isinstance(tspec, dict):
                        task_lis.append(f"<li>{esc(tname)}</li>")
                        continue
                    ttype = tspec.get("Type") or ""
                    detail = []
                    if tspec.get("RequiredItem"):
                        detail.append(f"物品 {item_link(tspec['RequiredItem'], items)}")
                    if tspec.get("GrantItem"):
                        detail.append(f"获得 {item_link(tspec['GrantItem'], items)}")
                    if tspec.get("TargetNpc"):
                        detail.append(f"目标 NPC <strong>{esc(tspec['TargetNpc'])}</strong>")
                    if tspec.get("Training"):
                        detail.append(f"锻炼 <code>{esc(tspec['Training'])}</code>")
                    if tspec.get("Need"):
                        detail.append(f"需求 <code>{esc(tspec['Need'])}</code>")
                    notify = tspec.get("CompletionNotify") or {}
                    if isinstance(notify, dict) and notify.get("Text"):
                        detail.append(f"提示「{esc(notify['Text'][:80])}」")
                    for px, py, pz in collect_task_positions(tspec):
                        spots.append((len(spots) + 1, px, pz, tname[:10]))
                        detail.append(f"坐标 <code>{px:.0f}, {py:.0f}, {pz:.0f}</code>")
                    # Markers may have npc
                    det = (" · ".join(detail)) if detail else ""
                    task_lis.append(
                        f"<li><strong>{esc(tname)}</strong>"
                        + (f" <code>{esc(ttype)}</code>" if ttype else "")
                        + (f" — {det}" if det else "")
                        + "</li>"
                    )
            elif q.get("Position"):
                pos = q["Position"]
                if isinstance(pos, (list, tuple)) and len(pos) >= 3:
                    spots.append((1, float(pos[0]), float(pos[2]), "目标"))
                    task_lis.append(
                        f"<li>前往 / 击杀目标 · 坐标 <code>{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}</code></li>"
                    )
            # Markers Npc positions
            markers = q.get("Markers") or {}
            if isinstance(markers, dict):
                for mk, mv in markers.items():
                    if isinstance(mv, dict):
                        npc = mv.get("Npc")
                        if npc and npc in pos_of and not any(s[3] == npc[:10] for s in spots):
                            p = pos_of[npc]
                            spots.append((len(spots) + 1, float(p[0]), float(p[2]), str(npc)[:10]))
                        mpos = mv.get("Position")
                        if isinstance(mpos, (list, tuple)) and len(mpos) >= 3:
                            spots.append((len(spots) + 1, float(mpos[0]), float(mpos[2]), str(mk)[:10]))

            map_html = ""
            if spots:
                # dedupe by rounded xz
                seen = set()
                uniq = []
                for s in spots:
                    key = (round(s[1]), round(s[2]))
                    if key in seen:
                        continue
                    seen.add(key)
                    uniq.append((len(uniq) + 1, s[1], s[2], s[3]))
                mpath = MAP_DIR / f"quest-{qid}.png"
                if draw_markers(uniq, qname[:40], "任务路线 / 目标点", mpath):
                    maps_made += 1
                    map_html = f'<img class="map-img" src="../assets/wiki-maps/quest-{esc(qid)}.png" alt="{esc(qname)}">'

            if not task_lis:
                # boss eliminate style
                if qname.startswith("Eliminate "):
                    task_lis.append(f"<li>击败 <strong>{esc(qname.replace('Eliminate ', ''))}</strong>（Boss 猎杀）</li>")
                else:
                    task_lis.append("<li>按任务标记完成（无细分 TaskSpecs）</li>")

            hint_html = f'<p class="callout i18n-en" data-en="{esc(hint)}">{esc(hint)}</p>' if hint else ""
            # also show EN name prominently
            sections.append(f"""
    <article class="sec" id="q-{qid}">
      <h2><span class="i18n-zh">{esc(qname)}</span></h2>
      <p class="i18n-en" hidden><code>{esc(qname)}</code></p>
      <p>{" · ".join(meta_bits) or "—"}</p>
      {hint_html}
      <h3>流程</h3>
      <ol>{"".join(task_lis)}</ol>
      <h3>奖励</h3>
      <p>{format_rewards(rewards, items)}</p>
      {map_html}
    </article>""")

    quest_body = f"""
    <article class="sec">
      <h1>任务</h1>
      <p>共 <strong>{len(holder)}</strong> 条（Quests.Holder）。接任务时对话选项文字即为任务名。同时最多 <strong>1</strong> 条进行中，冷却约 30 秒。</p>
      <p class="callout">呼吸训练详见 <a class="quest-link" href="breathings.html">呼吸法</a>；魔球训练详见 <a class="quest-link" href="evil-arts.html">邪恶艺术</a>；Boss 猎杀见 <a class="quest-link" href="boss-hunts.html">Boss 猎杀</a>。</p>
      <div class="toc">{"".join(toc_bits)}</div>
    </article>
    {"".join(sections)}
"""
    (ROOT / "p" / "quests.html").write_text(
        page_shell("任务", '<a href="../">主页</a> / 任务', quest_body, "".join(toc_bits[:8])),
        encoding="utf-8",
    )
    print(f"quests.html written n={len(holder)} maps={maps_made}")

    # ---------- NPC expand ----------
    shop_by = {s.get("Name"): s for s in shops if isinstance(s, dict)}
    # index dialogues by NPC leaf name
    dial_by_npc: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for key, mod in dialogues.items():
        leaf = key.split("/")[-1]
        dial_by_npc[leaf].append((key, mod))

    # quests offered by npc
    offered: dict[str, list[str]] = defaultdict(list)
    for qname, q in holder.items():
        if isinstance(q, dict) and isinstance(q.get("OfferNpc"), str):
            offered[q["OfferNpc"]].append(qname)

    rows = []
    detail_secs = []
    npc_spots = []
    for i, n in enumerate(sorted(npcs, key=lambda x: ((x.get("Region") or ""), x.get("Name") or "")), 1):
        name = n.get("Name") or "?"
        region = n.get("Region") or "—"
        pos = n.get("Position")
        pos_s = f"{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}" if pos else "—"
        if pos:
            npc_spots.append((i, float(pos[0]), float(pos[2]), str(name)[:8]))
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
        qlist = offered.get(name) or []
        rows.append(
            f'<tr><td>{i}</td><td><a href="#npc-{slug(name)}"><strong>{esc(name)}</strong></a></td>'
            f"<td>{esc(region)}</td><td><code>{esc(pos_s)}</code></td>"
            f"<td>{esc(' / '.join(role) or '对话')}</td><td>{len(qlist) or '—'}</td></tr>"
        )

        # detail card
        quest_links = ""
        if qlist:
            quest_links = (
                "<h3>可接任务</h3><ul>"
                + "".join(
                    f'<li><a class="quest-link" href="quests.html#q-{slug(qn)}">{esc(qn)}</a></li>'
                    for qn in sorted(qlist)
                )
                + "</ul>"
            )
        shop_html = ""
        shop = n.get("Shop") if isinstance(n.get("Shop"), dict) else (shop_by.get(name) or {}).get("Shop")
        if isinstance(shop, dict) and shop:
            srows = []
            for iname, row in shop.items():
                price = ""
                if isinstance(row, dict):
                    bits = []
                    for k, v in row.items():
                        if k in ("SuccessDialogue", "FailDialogue", "Model", "RequiresSide", "AlsoSoldBy"):
                            continue
                        if k == "Wen":
                            bits.append(f"{v} 文")
                        elif isinstance(v, (int, float)):
                            bits.append(f"{k}×{v}")
                    price = " / ".join(bits) or "—"
                srows.append(
                    f"<tr><td>{item_link(iname, items)}</td><td>{esc(price)}</td></tr>"
                )
            shop_html = (
                "<h3>商店</h3><table><tr><th>物品</th><th>价格</th></tr>"
                + "".join(srows)
                + "</table>"
            )

        dial_html = ""
        # match dialogue modules
        mods = dial_by_npc.get(name) or []
        # also try without titles
        if not mods:
            for leaf, lst in dial_by_npc.items():
                if leaf in name or name in leaf:
                    mods.extend(lst)
        lines = []
        for _k, mod in mods[:3]:
            lines.extend(extract_dialogue_lines(mod, limit=8))
        # unique preserve order
        seen_l = set()
        uniq_l = []
        for L in lines:
            if L not in seen_l:
                seen_l.add(L)
                uniq_l.append(L)
        if uniq_l:
            dial_html = (
                "<h3>对话摘录</h3>"
                + "".join(f'<p class="dial i18n-en" data-en="{esc(L)}">{esc(L)}</p>' for L in uniq_l[:10])
            )

        special = ""
        if "Togane" in name:
            special = '<p>锻造台与图纸配方见 <a class="quest-link" href="forge.html">锻造</a>。</p>'
        if "Hagane" in name:
            special = '<p>精炼等级消耗见 <a class="quest-link" href="refinement.html">精炼</a>。</p>'
        if "Marketer" in name:
            special = '<p>刷新点与库存见 <a class="quest-link" href="black-market.html">黑商</a>。</p>'
        if "Sofen" in name:
            special = '<p>钓鱼许可流程见 <a class="quest-link" href="fishing.html">钓鱼</a>。</p>'

        detail_secs.append(f"""
    <article class="sec" id="npc-{slug(name)}">
      <h2>{esc(name)}</h2>
      <p>区域 <strong>{esc(region)}</strong> · 坐标 <code>{esc(pos_s)}</code>
        {" · " + esc(" / ".join(role)) if role else ""}</p>
      {special}
      {quest_links}
      {shop_html}
      {dial_html}
    </article>""")

    draw_markers(
        [(i, x, z, lab) for i, x, z, lab in npc_spots],
        f"Ouwland NPC · {len(npc_spots)}",
        "小标记；点表内名称跳转详情",
        MAP_DIR / "npcs-all.png",
        small=True,
    )

    npc_body = f"""
    <article class="sec">
      <h1>NPC</h1>
      <p>Regions 共 <strong>{len(npcs)}</strong> 名；可标点 <strong>{len(npc_spots)}</strong>。
        对话模块已解析 <strong>{len(dialogues)}</strong> 份。特殊：
        <a class="quest-link" href="forge.html">锻造</a> ·
        <a class="quest-link" href="refinement.html">精炼</a> ·
        <a class="quest-link" href="black-market.html">黑商</a> ·
        <a class="quest-link" href="fishing.html">钓鱼证</a> ·
        <a class="quest-link" href="quests.html">任务全表</a>。</p>
      <img class="map-img" src="../assets/wiki-maps/npcs-all.png" alt="NPC 总图">
    </article>
    <article class="sec">
      <h2>一览</h2>
      <table><tr><th>#</th><th>名称</th><th>区域</th><th>坐标</th><th>作用</th><th>任务</th></tr>{"".join(rows)}</table>
    </article>
    {"".join(detail_secs)}
"""
    (ROOT / "p" / "npcs.html").write_text(
        page_shell("NPC", '<a href="../">主页</a> / NPC', npc_body),
        encoding="utf-8",
    )
    print(f"npcs.html written details={len(detail_secs)}")


if __name__ == "__main__":
    main()
