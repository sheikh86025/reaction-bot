# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

import asyncio
import time

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

import config

if not config.MONGO_URL:
    raise SystemExit("MONGO_URL is not set.")

_db = AsyncIOMotorClient(config.MONGO_URL)[config.DB_NAME]

clones = _db.clonebotdb
chats = _db.served_chats
users = _db.served_users
settings = _db.reaction_off_groups  # old on/off list (kept for migration)
chat_cfg = _db.chat_settings
bot_cfg = _db.bot_settings
bans = _db.banned_users
rstats = _db.reaction_stats

_known_chats = set()
_known_users = set()
_off = {}
_cfg = {}
_bcfg = {}
_bans = {}
_pending = {}

DEFAULT_TYPES = {
    "text": True, "photo": True, "video": True, "sticker": True,
    "voice": True, "doc": True, "anim": True, "other": True,
}


def _default_cfg():
    return {
        "enabled": True,
        "emojis": [],
        "mode": "random",
        "chance": 100,
        "dmin": 0,
        "dmax": 0,
        "types": dict(DEFAULT_TYPES),
        "keywords": [],
        "ignore_admins": False,
        "ignored": [],
    }


async def setup():
    await chats.create_index([("bot_id", 1), ("chat_id", 1)], unique=True)
    await users.create_index([("bot_id", 1), ("user_id", 1)], unique=True)
    await settings.create_index([("bot_id", 1), ("chat_id", 1)], unique=True)
    await chat_cfg.create_index([("bot_id", 1), ("chat_id", 1)], unique=True)
    await bot_cfg.create_index("bot_id", unique=True)
    await bans.create_index([("bot_id", 1), ("user_id", 1)], unique=True)
    await rstats.create_index([("bot_id", 1), ("chat_id", 1)], unique=True)
    await rstats.create_index([("bot_id", 1), ("count", -1)])


# ------------------------------------------------------------ served chats/users
async def add_chat(bot_id, chat_id):
    if (bot_id, chat_id) in _known_chats:
        return
    await chats.update_one(
        {"bot_id": bot_id, "chat_id": chat_id},
        {"$setOnInsert": {"added_at": int(time.time())}},
        upsert=True,
    )
    _known_chats.add((bot_id, chat_id))


async def remove_chat(bot_id, chat_id):
    _known_chats.discard((bot_id, chat_id))
    await chats.delete_one({"bot_id": bot_id, "chat_id": chat_id})


async def add_user(bot_id, user_id):
    if (bot_id, user_id) in _known_users:
        return
    await users.update_one(
        {"bot_id": bot_id, "user_id": user_id},
        {"$setOnInsert": {"added_at": int(time.time())}},
        upsert=True,
    )
    _known_users.add((bot_id, user_id))


async def remove_user(bot_id, user_id):
    _known_users.discard((bot_id, user_id))
    await users.delete_one({"bot_id": bot_id, "user_id": user_id})


async def get_chats(bot_id):
    return [d["chat_id"] async for d in chats.find({"bot_id": bot_id})]


async def get_users(bot_id):
    return [d["user_id"] async for d in users.find({"bot_id": bot_id})]


async def count_chats(bot_id):
    return await chats.count_documents({"bot_id": bot_id})


async def count_users(bot_id):
    return await users.count_documents({"bot_id": bot_id})


# ------------------------------------------------------------------- clones
async def get_clones():
    return await clones.find().to_list(length=None)


async def get_clone(bot_id):
    return await clones.find_one({"bot_id": bot_id})


async def get_clone_by_token(token):
    return await clones.find_one({"token": token})


async def get_clones_by_owner(user_id):
    return await clones.find({"user_id": user_id}).to_list(length=None)


async def find_clone(arg):
    """Find a clone by bot id or @username."""
    arg = str(arg).strip().lstrip("@")
    if arg.isdigit():
        return await clones.find_one({"bot_id": int(arg)})
    return await clones.find_one({"username": {"$regex": f"^{arg}$", "$options": "i"}})


async def add_clone(details):
    await clones.update_one(
        {"bot_id": details["bot_id"]}, {"$set": details}, upsert=True
    )


async def update_clone(bot_id, **fields):
    await clones.update_one({"bot_id": bot_id}, {"$set": fields})


async def delete_clone(bot_id):
    await clones.delete_many({"bot_id": bot_id})
    for col in (chats, users, settings, chat_cfg, bot_cfg, bans, rstats):
        await col.delete_many({"bot_id": bot_id})
    _known_chats.difference_update({k for k in _known_chats if k[0] == bot_id})
    _known_users.difference_update({k for k in _known_users if k[0] == bot_id})
    for k in [k for k in _cfg if k[0] == bot_id]:
        _cfg.pop(k, None)
    for k in [k for k in _pending if k[0] == bot_id]:
        _pending.pop(k, None)
    _off.pop(bot_id, None)
    _bcfg.pop(bot_id, None)
    _bans.pop(bot_id, None)


async def delete_all_clones():
    for clone in await get_clones():
        await delete_clone(clone["bot_id"])


# ------------------------------------------------------ per chat reaction settings
async def _disabled(bot_id):
    if bot_id not in _off:
        _off[bot_id] = {d["chat_id"] async for d in settings.find({"bot_id": bot_id})}
    return _off[bot_id]


async def get_cfg(bot_id, chat_id):
    key = (bot_id, chat_id)
    cfg = _cfg.get(key)
    if cfg is None:
        cfg = _default_cfg()
        doc = await chat_cfg.find_one({"bot_id": bot_id, "chat_id": chat_id}, {"_id": 0})
        if doc:
            for k, v in doc.items():
                if k == "types":
                    cfg["types"].update(v)
                elif k in cfg:
                    cfg[k] = v
        elif chat_id in await _disabled(bot_id):
            cfg["enabled"] = False  # was switched off in the old version
        _cfg[key] = cfg
    return cfg


async def save_cfg(bot_id, chat_id):
    cfg = _cfg.get((bot_id, chat_id))
    if cfg is not None:
        await chat_cfg.update_one(
            {"bot_id": bot_id, "chat_id": chat_id}, {"$set": cfg}, upsert=True
        )


async def reaction_enabled(bot_id, chat_id):
    return (await get_cfg(bot_id, chat_id))["enabled"]


async def set_reaction(bot_id, chat_id, enabled):
    cfg = await get_cfg(bot_id, chat_id)
    cfg["enabled"] = bool(enabled)
    await save_cfg(bot_id, chat_id)


# ------------------------------------------------------------- per bot settings
async def get_bot_cfg(bot_id):
    cfg = _bcfg.get(bot_id)
    if cfg is None:
        cfg = {"emojis": [], "style": "sc", "start_text": None, "start_photo": None}
        doc = await bot_cfg.find_one({"bot_id": bot_id}, {"_id": 0, "bot_id": 0})
        if doc:
            cfg.update(doc)
        _bcfg[bot_id] = cfg
    return cfg


async def set_bot_cfg(bot_id, **changes):
    cfg = await get_bot_cfg(bot_id)
    cfg.update(changes)
    await bot_cfg.update_one({"bot_id": bot_id}, {"$set": changes}, upsert=True)


# ------------------------------------------------------------------------ bans
async def _ban_set(bot_id):
    s = _bans.get(bot_id)
    if s is None:
        s = {d["user_id"] async for d in bans.find({"bot_id": bot_id})}
        _bans[bot_id] = s
    return s


async def is_banned(bot_id, user_id):
    return user_id in await _ban_set(0) or user_id in await _ban_set(bot_id)


async def ban_user(bot_id, user_id):
    (await _ban_set(bot_id)).add(user_id)
    await bans.update_one(
        {"bot_id": bot_id, "user_id": user_id},
        {"$setOnInsert": {"at": int(time.time())}},
        upsert=True,
    )


async def unban_user(bot_id, user_id):
    (await _ban_set(bot_id)).discard(user_id)
    await bans.delete_one({"bot_id": bot_id, "user_id": user_id})


async def get_bans(bot_id):
    return sorted(await _ban_set(bot_id))


# ------------------------------------------------------------- reaction stats
def bump_reaction(bot_id, chat_id, title=None):
    item = _pending.setdefault((bot_id, chat_id), [0, None])
    item[0] += 1
    if title:
        item[1] = title


async def flush_stats():
    if not _pending:
        return
    batch = dict(_pending)
    _pending.clear()
    ops = []
    for (bot_id, chat_id), (n, title) in batch.items():
        upd = {"$inc": {"count": n}, "$set": {"last": int(time.time())}}
        if title:
            upd["$set"]["title"] = title
        ops.append(UpdateOne({"bot_id": bot_id, "chat_id": chat_id}, upd, upsert=True))
    try:
        await rstats.bulk_write(ops, ordered=False)
    except Exception:
        for key, (n, title) in batch.items():
            item = _pending.setdefault(key, [0, None])
            item[0] += n
            item[1] = item[1] or title


async def stats_flush_loop():
    while True:
        await asyncio.sleep(30)
        try:
            await flush_stats()
        except Exception:
            pass


async def total_reactions(bot_id):
    await flush_stats()
    docs = await rstats.aggregate(
        [{"$match": {"bot_id": bot_id}}, {"$group": {"_id": None, "n": {"$sum": "$count"}}}]
    ).to_list(1)
    return docs[0]["n"] if docs else 0


async def chat_reactions(bot_id, chat_id):
    await flush_stats()
    doc = await rstats.find_one({"bot_id": bot_id, "chat_id": chat_id})
    return doc["count"] if doc else 0


async def top_chats(bot_id, limit=10):
    await flush_stats()
    return await rstats.find({"bot_id": bot_id}).sort("count", -1).limit(limit).to_list(limit)

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
