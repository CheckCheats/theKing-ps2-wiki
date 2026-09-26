# -*- coding: utf-8 -*-
"""Build weapon-upgrade.html: Togane T2/T3 (V2/V3) materials + stat panels."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Desktop\ProjectSlayer2_WIKI")
LIVE = ROOT / "data" / "_live"
CSS = "20260926w"

TIER_MULT = {1: 1.0, 2: 1.15, 3: 1.3}

WEAPONS = {
    "Firstlight Katana": ["Volcanic Katana", "Tornadic Katana", "Tidal Katana", "Thundercloud Katana"],
    "Firstlight Insect Katana": ["Butterfly Katana"],
    "Firstlight Sound Cleavers": ["Reverb Cleavers"],
    "Firstlight Bladed Wagasa": ["Damascus Bladed Wagasa"],
    "Firstlight Spear": ["Damascus Spear"],
    "Firstlight Tanto": ["Damascus Tanto"],
    "Firstlight War Fans": ["Damascus War Fans"],
    "Nightfall Katana": ["Volcanic Katana", "Tornadic Katana", "Tidal Katana", "Thundercloud Katana"],
    "Nightfall Serpent Katana": ["Serpentine Katana"],
    "Nightfall Axe and Mace": ["Seismic Axe and Mace"],
    "Nightfall Claws": ["Damascus Claws"],
    "Nightfall Gauntlet": ["Damascus Gauntlet"],
    "Nightfall Scythe": ["Damascus Scythe"],
    "Nightfall Sickles": ["Damascus Sickles"],
}
WEARABLES = {
    "Firstlight": {
        "Materials": ["Firstlight Forged Ingot", "Firstlight Weaver's Silk", "Firstlight Star Ore"],
        "Pieces": ["Firstlight Haori", "Firstlight Mask", "Firstlight Lantern"],
    },
    "Nightfall": {
        "Materials": ["Nightfall Forged Ingot", "Nightfall Weaver's Cloth", "Nightfall Reinforced Plating"],
        "Pieces": ["Nightfall Cape", "Nightfall Mask", "Nightfall Top", "Nightfall Bottom"],
    },
}
TOWER_PIECES = ["Firstlight Top", "Firstlight Bottom"]
FISHED = {"Lost Shotgun": {2: 2, 3: 6}}
TIER_UPS = {
    2: {"Wen": 750_000, "MaterialEach": 5, "Generic": {"Metal Scraps": 750, "Silk Thread": 750}},
    3: {"Wen": 1_500_000, "MaterialEach": 15, "Generic": {}},
}

STAT_CN = {
    "Additional Damage": "额外伤害",
    "Additional Damage Factor": "额外伤害倍率",
    "Block Points": "格挡值",
    "Block Regen": "格挡回复",
    "Health Regen Speed": "生命回复速度",
    "Illumination": "照明",
    "Max Health": "最大生命",
    "Max Health Factor": "最大生命倍率",
    "Max Stamina": "最大体力",
    "Movement Speed Factor": "移速倍率",
    "Stamina Regen Speed": "体力回复速度",
}


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", str(name), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s.strip()) or "x"


def item_a(name: str, items: dict, qty=None) -> str:
    it = items.get(name) or {}
    label = it.get("NameCN") or name
    q = f" ×{qty}" if qty is not None else ""
    if name in items:
        return f'<a class="quest-link" href="archive/items/{slug(name)}.html">{esc(label)}</a>{q}'
    return f"{esc(label)}{q}"


def fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.4f}".rstrip("0").rstrip(".")


def base_stats(name: str, combat: dict, items: dict) -> dict:
    c = combat.get(name) or {}
    ats = c.get("ActiveToolStats")
    if isinstance(ats, dict) and ats:
        return dict(ats)
    st = (items.get(name) or {}).get("Stats")
    if isinstance(st, dict) and st:
        return dict(st)
    return {}


def series_of(name: str) -> str | None:
    if name.startswith("Nightfall"):
        return "Nightfall"
    if name.startswith("Firstlight"):
        return "Firstlight"
    if name == "Lost Shotgun":
        return "Fished"
    return None


def mats_for_tier(name: str, tier: int) -> list[tuple[str, int]]:
    conf = TIER_UPS[tier]
    out: list[tuple[str, int]] = [("Wen", conf["Wen"])]
    fished = FISHED.get(name)
    if fished:
        amt = fished[tier]
        for series in WEARABLES.values():
            for m in series["Materials"]:
                out.append((m, amt))
        return out
    for g, a in conf["Generic"].items():
        out.append((g, a))
    ser = series_of(name)
    if ser and ser in WEARABLES:
        for m in WEARABLES[ser]["Materials"]:
            out.append((m, conf["MaterialEach"]))
    return out


def panel_rows(stats: dict) -> str:
    if not stats:
        return "<tr><td colspan=4>无数值面板（未录入 ActiveToolStats / Stats）</td></tr>"
    rows = []
    for k in sorted(stats.keys(), key=lambda x: STAT_CN.get(x, x)):
        base = float(stats[k])
        cn = STAT_CN.get(k, k)
        rows.append(
            "<tr>"
            f"<td>{esc(cn)}<br><span class='en'>{esc(k)}</span></td>"
            f"<td><code>{esc(fmt_num(base * TIER_MULT[1]))}</code></td>"
            f"<td><code>{esc(fmt_num(base * TIER_MULT[2]))}</code></td>"
            f"<td><code>{esc(fmt_num(base * TIER_MULT[3]))}</code></td>"
            "</tr>"
        )
    return "".join(rows)


def main():
    items = json.loads((LIVE / "items-enriched.json").read_text(encoding="utf-8"))
    combat = json.loads((LIVE / "wiki-item-combat.json").read_text(encoding="utf-8"))

    ordered: list[str] = []
    seen: set[str] = set()
    for n in list(WEAPONS.keys()) + [p for w in WEARABLES.values() for p in w["Pieces"]] + TOWER_PIECES + list(FISHED):
        if n not in seen:
            seen.add(n)
            ordered.append(n)

    toc = "".join(
        f'<a href="#{slug(n)}">{esc((items.get(n) or {}).get("NameCN") or n)}</a> ' for n in ordered
    )

    secs = []
    for name in ordered:
        cn = (items.get(name) or {}).get("NameCN") or name
        ser = series_of(name)
        stats = base_stats(name, combat, items)
        icon = ""
        ic = (items.get(name) or {}).get("Icon") or ""
        m = re.search(r"(\d{6,})", str(ic))
        if m:
            aid = m.group(1)
            if (ROOT / "assets" / "icons" / "items" / f"{aid}.png").exists():
                icon = f'<img class="icon" src="../assets/icons/items/{aid}.png" alt="">'

        pre = []
        if name in WEAPONS:
            bases = " / ".join(item_a(b, items) for b in WEAPONS[name])
            pre.append(
                f"T1：持有 {bases} + {item_a(name + ' Schematic', items)}，"
                f"交 {item_a('Metal Scraps', items, 1000)} + {item_a('Silk Thread', items, 1000)} + "
                f"<strong>1,000,000</strong> 文（需持有底座武器才显示配方）。"
            )
        elif name in TOWER_PIECES:
            pre.append(
                f"T1（奥乌兰台）：{item_a('Metal Scraps', items, 750)} + {item_a('Silk Thread', items, 750)} + "
                f"RunPoints <code>500000</code> + 文 <code>500000</code>。"
            )
        elif ser in WEARABLES:
            mats = " + ".join(item_a(m, items, 5) for m in WEARABLES[ser]["Materials"])
            pre.append(
                f"T1：{mats} + {item_a('Metal Scraps', items, 1000)} + {item_a('Silk Thread', items, 1000)} + "
                f"<strong>1,000,000</strong> 文 + {item_a(name + ' Schematic', items)}。"
            )
        elif name == "Lost Shotgun":
            pre.append("钓鱼获取本体后，在 Togane 处升 T2/T3。")

        def mats_html(tier: int) -> str:
            return " + ".join(
                item_a(n, items, q) if n != "Wen" else f"<strong>{q:,}</strong> 文"
                for n, q in mats_for_tier(name, tier)
            )

        passive = ""
        if ser == "Nightfall":
            passive = (
                "<p class='callout'><strong>系列被动 · Nightfall Bleed</strong>："
                "攻击叠流血（最多 3 层）。被动在 <strong>T3</strong> 解锁。</p>"
            )
        elif ser == "Firstlight":
            passive = (
                "<p class='callout'><strong>系列被动 · Block Ward</strong>："
                "格挡回血并反伤（约每秒一次）。被动在 <strong>T3</strong> 解锁。</p>"
            )

        secs.append(f"""
    <article class="sec" id="{slug(name)}">
      <div class="head">{icon}<div>
        <h2>{esc(cn)} <span class="en">({esc(name)})</span></h2>
        <p>系列 <strong>{esc(ser or "—")}</strong> · 铁匠 Togane（Ouwland）可升 T2 / T3</p>
      </div></div>
      <h3>前置 / T1</h3>
      <ul>{"".join(f"<li>{p}</li>" for p in pre) or "<li>—</li>"}</ul>
      <h3>升阶材料</h3>
      <table>
        <tr><th>阶</th><th>角标</th><th>材料</th></tr>
        <tr><td><strong>T2</strong></td><td>V2 / T2</td><td>{mats_html(2)}</td></tr>
        <tr><td><strong>T3</strong></td><td>V3 / T3</td><td>{mats_html(3)}</td></tr>
      </table>
      <p class="note">升阶消耗本体 ×1（精炼进度保留）；武器类需持有该装备才会出现在列表。</p>
      {passive}
      <h3>数据面板（× 系列阶乘）</h3>
      <p>基数：ActiveToolStats / Stats；阶乘 T1×1 · T2×1.15 · T3×1.3。</p>
      <table>
        <tr><th>属性</th><th>T1</th><th>T2 (×1.15)</th><th>T3 (×1.3)</th></tr>
        {panel_rows(stats)}
      </table>
      <p>档案：{item_a(name, items)}</p>
    </article>""")

    overview_rows = "".join(
        f'<tr><td><a href="#{slug(n)}">{esc((items.get(n) or {}).get("NameCN") or n)}</a></td>'
        f"<td>{esc(series_of(n) or '—')}</td><td>T2 文 750,000 · T3 文 1,500,000</td></tr>"
        for n in ordered
    )

    body = f"""
    <article class="sec" id="overview">
      <h1>武器 / 装备升阶 · V2 / V3</h1>
      <p>隐雾村铁匠 <strong>Blacksmith Togane</strong> 的 <code>Ouwland</code> 台可对暮落 / 初光系列与遗失霰弹枪升阶。角标 <strong>T2 / T3</strong>（俗称 V2 / V3）。</p>
      <ul>
        <li>MaxTier = 3；属性乘区 <code>1 / 1.15 / 1.3</code>。</li>
        <li>T2 起消耗系列高级材料；T3 材料量更大且不再收废料/丝线。</li>
        <li>系列被动在 <strong>T3</strong> 生效。</li>
        <li><a class="quest-link" href="forge.html">锻造</a> · <a class="quest-link" href="schematics.html">图纸</a> · <a class="quest-link" href="refinement.html">精炼</a></li>
      </ul>
      <img class="map-img" src="../assets/wiki-maps/forge-togane.png" alt="Togane">
      <h2>可升阶一览（{len(ordered)}）</h2>
      <table><tr><th>装备</th><th>系列</th><th>文费用</th></tr>{overview_rows}</table>
      <nav class="toc" style="margin-top:.75rem">{toc}</nav>
    </article>
    {"".join(secs)}
"""

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="description" content="铁匠 Togane 处装备 V2/V3（T2/T3）升阶：全部可升级装备、数据面板与材料。">
  <title>武器升阶 · V2 / V3 · Slayers 2 Wiki</title>
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
    .sec ul{{margin:.35rem 0 0;padding-left:1.2rem}}
    .sec strong{{color:var(--cream)}}
    .sec table{{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}}
    .sec th,.sec td{{border:1px solid var(--line);padding:.4rem .5rem;text-align:left;vertical-align:top}}
    .sec th{{color:var(--gold-deep);font-weight:600;background:rgba(255,255,255,.03)}}
    .sec td{{color:var(--muted)}}
    .sec code{{color:var(--gold-deep)}}
    .en{{color:var(--muted);font-size:.78rem;opacity:.85}}
    .note{{font-size:.86rem!important}}
    .callout{{border-left:3px solid var(--gold);padding:.35rem 0 .35rem .75rem;margin:.5rem 0;color:var(--muted);font-size:.9rem}}
    .map-img{{display:block;width:100%;height:auto;border:1px solid var(--line);margin-top:.55rem}}
    .head{{display:flex;gap:.75rem;align-items:flex-start}}
    .head .icon{{width:48px;height:48px;object-fit:contain;border:1px solid var(--line);background:#0a0a0a}}
    .toc a{{display:inline-block;margin:.15rem .4rem .15rem 0;font-size:.82rem;color:var(--gold)}}
    .top-nav{{display:flex;flex-wrap:wrap;gap:.65rem;font-size:.82rem}}
    .top-nav a{{color:var(--muted)}}
  </style>
</head>
<body>
  <div class="bg" aria-hidden="true"><div class="bg-base"></div><div class="bg-key"></div></div>
  <header class="top">
    <a class="brand" href="../"><span>Slayers 2 Wiki</span></a>
    <nav class="top-nav"><a href="#overview">总览</a><a href="forge.html">锻造</a><a href="schematics.html">图纸</a></nav>
    <span class="top-ver">升阶</span>
  </header>
  <main class="page">
    <p class="crumb"><a href="../">主页</a> / 武器升阶 · V2 / V3</p>
    {body}
  </main>
  <footer class="foot">
    <div><strong>Slayers 2 Wiki</strong><span>升阶</span><span class="foot-owner">Wiki 所有者 · theKing</span></div>
    <a href="../">返回主页</a>
  </footer>
  <script src="../js/i18n.js?v={CSS}"></script>
</body>
</html>
"""
    (ROOT / "p" / "weapon-upgrade.html").write_text(page, encoding="utf-8")
    print(f"weapon-upgrade.html n={len(ordered)}")


if __name__ == "__main__":
    main()
