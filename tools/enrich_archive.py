# -*- coding: utf-8 -*-
"""Rebuild full item sources + attach CN fields into items-enriched.json."""
from __future__ import annotations

import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\Desktop\ProjectSlayer2_WIKI")
LIVE = ROOT / "data" / "_live"


def load_py(path: Path, attr: str):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, attr)


def chance_of(val):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        c = val.get("Chance")
        return float(c) if isinstance(c, (int, float)) else None
    return None


def add_src(bucket: dict, where: str, chance=None, kind: str = "other", meta: dict | None = None):
    if not where:
        return
    entry = {"Where": where, "Chance": chance, "Kind": kind}
    if meta:
        entry["Meta"] = meta
    # merge same Where keep max chance
    for s in bucket:
        if s["Where"] == where and s.get("Kind") == kind:
            if chance is not None and (s.get("Chance") is None or chance > s["Chance"]):
                s["Chance"] = chance
            if meta:
                s["Meta"] = {**(s.get("Meta") or {}), **meta}
            return
    bucket.append(entry)


# Special non-ItemSources origins
SPECIAL = {
    "Horse": [{"Where": "TameWildHorse", "Chance": None, "Kind": "tame", "Meta": {"wen": 15000}}],
    # Nightfall schematics (from kit/nightfall-schematics.md)
    "Nightfall Katana Schematic": [{"Where": "StudyProp", "Kind": "special", "Meta": {"note": "地下 StudyProp 长按 Study≈3s", "pos": [-570, 815, 112]}}],
    "Nightfall Mask Schematic": [{"Where": "StudyProp", "Kind": "special", "Meta": {"note": "地下 StudyProp", "pos": [-1629, 1229, 1143]}}],
    "Nightfall Axe and Mace Schematic": [{"Where": "StudyProp", "Kind": "special", "Meta": {"note": "地下 StudyProp", "pos": [1083, 1584, -811]}}],
    "Nightfall Scythe Schematic": [{"Where": "StudyProp", "Kind": "special", "Meta": {"note": "冰纱侧 StudyProp", "pos": [-1205, 969, -3187]}}],
    "Nightfall Claws Schematic": [{"Where": "StudyProp", "Kind": "special", "Meta": {"note": "地下 StudyProp"}}],
    "Nightfall Sickles Schematic": [{"Where": "StudyProp", "Kind": "special", "Meta": {"note": "先扳完 10 根 SicklesLever 再 StudyProp"}}],
    "Nightfall Serpent Katana Schematic": [{"Where": "SerpentChest", "Kind": "special", "Meta": {"note": "蛇箱（需 Serpent Key）"}}],
    "Nightfall Gauntlet Schematic": [{"Where": "TobeiGauntlet", "Kind": "special", "Meta": {"note": "三座雕像进度满后找石匠 Tobei"}}],
    "Nightfall Cape Schematic": [{"Where": "HatsuCape", "Kind": "special", "Meta": {"note": "持有遗失披风找织匠 Hatsu 兑换"}}],
    "Nightfall Top Schematic": [{"Where": "ToganeCapstone", "Kind": "special", "Meta": {"note": "集齐 9 张暮落门槛图纸后找铁匠 Togane"}}],
    "Nightfall Bottom Schematic": [{"Where": "ToganeCapstone", "Kind": "special", "Meta": {"note": "集齐 9 张暮落门槛图纸后找铁匠 Togane"}}],
    # Starters / system
    "Combat": [{"Where": "Starter", "Kind": "special", "Meta": {"note": "开局默认赤拳架势"}}],
    "Fighting Style": [{"Where": "Starter", "Kind": "special", "Meta": {"note": "学会任一战斗风格后自动持有"}}],
    "Clan Skills": [{"Where": "ClanUnlock", "Kind": "special", "Meta": {"note": "拥有家族技法的血统自动出现"}}],
    "Crow": [{"Where": "Corps", "Kind": "special", "Meta": {"note": "队士鸟使：接令与猎杀联络"}}],
    "Slayer Uniform": [{"Where": "FinalSelection", "Kind": "special", "Meta": {"note": "通过最终选拔后发放"}}],
    "Crude Iron Ingot": [{"Where": "FinalSelection", "Kind": "special", "Meta": {"note": "通过最终选拔后发放，用于配初日轮刀"}}],
    # Quest carry / turn-in
    "Jewelry Box": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "隐雾村银造任务：带回珠宝匣（须持有在背包）"}}],
    "Gemstone": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "贝蒂河畔任务：拾取遗失宝石"}}],
    "Wagwan's Ring": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "瓦格万任务：洞穴中找回戒指"}}],
    "Permit Stamp": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "码头索芬任务：找回许可印章"}}],
    "Supply Box": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "雾落→汐织庄园：递送补给箱给志织"}}],
    "Letter": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "努特解码后交给查卡的信件"}}],
    "Package": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "农夫包裹：交给港边艾拉拉开店"}}],
    "Bandage": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "任务交付用绷带（野战包扎道具）"}}],
    "Bear Claws": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "竹林母熊相关任务物"}}],
    "Biwa Bell": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "无惨巢穴通路钥匙：琵琶铃"}}],
    "Serpent Key": [{"Where": "QuestCarry", "Kind": "special", "Meta": {"note": "水边区域获取，用于开启蛇箱"}}],
    "Drowned Lure": [{"Where": "QuestIsao", "Kind": "special", "Meta": {"note": "渔夫伊佐夫任务：沉河遗失的诱饵"}}],
    "Legendary Fishing Rod": [{"Where": "QuestIsao", "Kind": "special", "Meta": {"note": "伊佐夫任务奖励：传奇钓竿（可捞沉物）"}}],
    "Health Potion": [{"Where": "FieldUse", "Kind": "special", "Meta": {"note": "基础愈伤瓶（商店 / 任务补给常见；LiveConfig 未挂 ItemSources）"}}],
    "Everburn Lantern": [{"Where": "Iceveil", "Kind": "special", "Meta": {"note": "冰纱谷防冻灯笼（区域/任务发放）"}}],
    "Mushroom Lit Lantern": [{"Where": "Cave", "Kind": "special", "Meta": {"note": "洞窟蘑菇灯（洞穴探索获取）"}}],
    "Lost Shotgun Schematic": [{"Where": "LostRelated", "Kind": "special", "Meta": {"note": "与终选 Boss「遗失」相关的图纸；LiveConfig 未挂表"}}],
    "Yahari Outfit": [{"Where": "BossYahari", "Kind": "special", "Meta": {"note": "Boss 矢琶羽相关外观（表外掉落/兑换）"}}],
    # Cosmetics / misc without table
    "Black Cape": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "基础黑披风（外观；LiveConfig 未挂来源）"}}],
    "Black Sandogasa": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "黑三度笠（外观）"}}],
    "Ninja Headband": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "忍头带（外观）"}}],
    "Ninja Scroll": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "忍卷匣（外观）"}}],
    "Bandaged Eyepatch": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "绷带眼罩（外观）"}}],
    "Gleam Eyepatch": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "辉光眼罩（外观）"}}],
    "Stylish Glasses": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "潮酷墨镜（外观）"}}],
    "kagura Hat": [{"Where": "Cosmetic", "Kind": "special", "Meta": {"note": "神乐帽（外观）"}}],
}

# Firstlight schematics — materials drop in chests; schematic props not in live ItemSources
for _fl in [
    "Firstlight Bladed Wagasa Schematic",
    "Firstlight Bottom Schematic",
    "Firstlight Haori Schematic",
    "Firstlight Insect Katana Schematic",
    "Firstlight Katana Schematic",
    "Firstlight Mask Schematic",
    "Firstlight Sound Cleavers Schematic",
    "Firstlight Spear Schematic",
    "Firstlight Tanto Schematic",
    "Firstlight Top Schematic",
    "Firstlight War Fans Schematic",
]:
    SPECIAL[_fl] = [{"Where": "FirstlightStudy", "Kind": "special", "Meta": {"note": "初光系列图纸：LiveConfig 未公开 Study 点；材料（初光星矿/锻锭/织丝）见对应宝箱掉落"}}]

# Wen-only Price with no shop row → likely Kuro / similar
WEN_SHOP_HINT = {
    "Black Amigasa": "Kuro",
    "Overdrive Necklace": "Kuro",
}

# Sealed cache unlockers (intel)
SEALED_NOTE = {
    "Sealed Cache T1": "封印箱 T1：由丛林袭击者 / 袭击队长等守卫解锁",
    "Sealed Cache T2": "封印箱 T2：由库藏枪兵 / 枪兵队长等解锁",
    "Sealed Cache T3": "封印箱 T3：由库藏潜行者 / 潜行队长等解锁",
    "Snow Chest": "雪原世界宝箱（无对应 Boss 箱字段）",
    "Common Chest": "常见 Boss / 试炼头目击杀后掉落的宝箱",
    "Rare Chest": "稀有 Boss / 试炼头目击杀后掉落的宝箱",
    "Ice Chest": "冰霜类 Boss / 试炼头目击杀后掉落的宝箱",
    "Lost Chest": "击败终选 Boss「遗失 Lost」后掉落",
    "World Events Chest": "世界头目击杀后掉落的事件宝箱",
    "Ouwigahara Chest": "奥乌兰爬塔宝箱",
    "Ouwigahara Cache": "奥乌兰缓存箱",
    "Ouwigahara Deep Cache": "奥乌兰深层缓存箱",
}


def main():
    items = json.loads((LIVE / "items-catalog.json").read_text(encoding="utf-8"))
    ndt = json.loads((LIVE / "npc-data.json").read_text(encoding="utf-8"))
    chests = json.loads((LIVE / "chests-loot.json").read_text(encoding="utf-8"))
    shops = json.loads((LIVE / "shops.json").read_text(encoding="utf-8")) if (LIVE / "shops.json").exists() else []
    chest_bosses = json.loads((LIVE / "chest-bosses.json").read_text(encoding="utf-8"))

    NAME_CN = load_py(ROOT / "data" / "archive-name-cn.py", "NAME_CN")
    CHEST_CN = load_py(ROOT / "data" / "archive-name-cn.py", "CHEST_CN")
    BOSS_CN = load_py(ROOT / "data" / "archive-name-cn.py", "BOSS_CN")
    DESC_CN = load_py(ROOT / "data" / "archive-desc-cn.py", "DESC_CN")
    try:
        STAT_CN = load_py(ROOT / "data" / "archive-desc-cn.py", "STAT_CN")
    except Exception:
        STAT_CN = {}

    # chest -> bosses
    chest_to_bosses: dict[str, list[dict]] = defaultdict(list)
    for row in chest_bosses:
        chest_to_bosses[row["Chest"]].append({"Code": row["Code"], "Name": row["Name"]})

    sources: dict[str, list] = {name: [] for name in items}

    # 1) existing ItemSources
    for name, it in items.items():
        for s in it.get("Sources") or []:
            where = s.get("Where") or ""
            ch = s.get("Chance")
            kind = "other"
            meta = {}
            if where in chests:
                kind = "chest"
                bosses = chest_to_bosses.get(where) or []
                meta = {
                    "chest": where,
                    "bosses": bosses,
                    "note": SEALED_NOTE.get(where),
                }
            elif where.startswith("Sold by "):
                kind = "shop"
                meta = {"npc": where[8:]}
            elif where.startswith("Crafted at "):
                kind = "craft"
                meta = {"station": where[11:]}
            elif where.startswith("Quest:"):
                kind = "quest"
                meta = {"quest": where[6:].strip()}
            elif where == "Fished up":
                kind = "fish"
            else:
                # boss display name?
                kind = "boss"
                meta = {"bossName": where}
            add_src(sources[name], where, ch, kind, meta)

    # 2) reverse boss rewards
    for code, row in ndt.items():
        if not isinstance(row, dict):
            continue
        bname = row.get("Name") or code
        for k, v in (row.get("Rewards") or {}).items():
            if k in ("Wen", "Exp") or k not in items:
                continue
            ch = chance_of(v)
            pity = v.get("Pity") if isinstance(v, dict) else None
            add_src(
                sources[k],
                bname,
                ch,
                "boss",
                {"bossCode": code, "bossName": bname, "pity": pity},
            )

    # 3) reverse chest loot (ensure all)
    for cname, c in chests.items():
        bosses = chest_to_bosses.get(cname) or []
        meta_base = {"chest": cname, "bosses": bosses, "note": SEALED_NOTE.get(cname)}
        for e in c.get("guaranteed") or []:
            iid = e.get("itemId")
            if iid in sources:
                add_src(sources[iid], cname, None, "chest", {**meta_base, "guaranteed": True})
        for e in c.get("loot") or []:
            iid = e.get("itemId")
            if iid in sources:
                add_src(sources[iid], cname, e.get("chance"), "chest", meta_base)

    # 4) shops with prices
    for s in shops:
        npc = s.get("Name")
        shop = s.get("Shop") or {}
        for it_name, price in shop.items() if isinstance(shop, dict) else []:
            if it_name not in sources:
                continue
            wen = None
            if isinstance(price, dict):
                wen = price.get("Wen")
            add_src(
                sources[it_name],
                f"Sold by {npc}",
                None,
                "shop",
                {"npc": npc, "price": price, "wen": wen, "region": s.get("Region"), "pos": s.get("Position")},
            )
        for it_name in s.get("Items") or []:
            if it_name in sources and it_name not in shop:
                add_src(sources[it_name], f"Sold by {npc}", None, "shop", {"npc": npc, "region": s.get("Region"), "pos": s.get("Position")})

    # 5) specials
    for name, lst in SPECIAL.items():
        if name not in sources:
            continue
        for s in lst:
            add_src(sources[name], s["Where"], s.get("Chance"), s.get("Kind", "special"), s.get("Meta"))

    # 6) Price materials → craft (when still empty of craft/shop)
    for name, it in items.items():
        price = it.get("Price")
        if not isinstance(price, dict) or not price:
            continue
        has_craft_or_shop = any(s.get("Kind") in ("craft", "shop") for s in sources[name])
        if has_craft_or_shop:
            continue
        if set(price.keys()) == {"Wen"} or (len(price) == 1 and "Wen" in price):
            npc = WEN_SHOP_HINT.get(name)
            if npc:
                add_src(
                    sources[name],
                    f"Sold by {npc}",
                    None,
                    "shop",
                    {"npc": npc, "price": price, "wen": price.get("Wen")},
                )
            continue
        # material cost → forge
        add_src(
            sources[name],
            "Crafted at Ouwland",
            None,
            "craft",
            {"station": "Ouwland", "price": price, "note": "按物品 Price 材料配方锻造（默认奥乌兰锻台）"},
        )

    # sort sources: boss > chest > shop > craft > fish > quest > special > other; then by chance desc
    kind_rank = {"boss": 0, "chest": 1, "shop": 2, "tame": 3, "special": 4, "craft": 5, "fish": 6, "quest": 7, "other": 8}

    def sort_key(s):
        return (kind_rank.get(s.get("Kind"), 9), -(s.get("Chance") or -1), s.get("Where") or "")

    enriched = {}
    empty = 0
    for name, it in items.items():
        src = sorted(sources[name], key=sort_key)
        if not src:
            empty += 1
        out = dict(it)
        out["Sources"] = src
        out["NameCN"] = NAME_CN.get(name, name)
        out["DescriptionCN"] = DESC_CN.get(name) or it.get("Description") or ""
        # localize stats keys
        stats = it.get("Stats")
        if isinstance(stats, dict):
            out["StatsCN"] = {STAT_CN.get(k, k): v for k, v in stats.items()}
        enriched[name] = out

    meta = {
        "chest_to_bosses": {k: v for k, v in chest_to_bosses.items()},
        "chest_cn": CHEST_CN,
        "boss_cn": BOSS_CN,
        "stat_cn": STAT_CN,
        "sealed_note": SEALED_NOTE,
    }
    (LIVE / "items-enriched.json").write_text(json.dumps(enriched, ensure_ascii=False, indent=None), encoding="utf-8")
    (LIVE / "archive-meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"enriched {len(enriched)} empty_src={empty}")


if __name__ == "__main__":
    main()
