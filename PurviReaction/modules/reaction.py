# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

import asyncio

from pyrogram import Client, errors, filters
from pyrogram.enums import ChatType

import config
from PurviReaction import database as db
from PurviReaction.emojis import ALLOWED_SET, default_pool, show, variants
from PurviReaction.rules import (
    chance_ok, choose, delay_value, keyword_match, msg_kind, next_counter,
)
from PurviReaction.utils import (
    GROUPS, admin_ids, can_manage, get_tr, title_of,
)

DEFAULT_POOL = default_pool(config.REACTIONS)
INVALID = getattr(errors, "ReactionInvalid", ())
_TASKS = set()


async def pool_for(bot_id, cfg):
    """chat emojis -> bot default emojis -> config.REACTIONS"""
    pool = [e for e in cfg["emojis"] if e in ALLOWED_SET]
    if pool:
        return pool
    bcfg = await db.get_bot_cfg(bot_id)
    pool = [e for e in bcfg.get("emojis") or [] if e in ALLOWED_SET]
    return pool or DEFAULT_POOL


async def should_react(client, message, cfg):
    chat, user = message.chat, message.from_user
    if not cfg["types"].get(msg_kind(message), True):
        return False
    if not keyword_match(message.text or message.caption, cfg["keywords"]):
        return False
    if chat.type != ChatType.CHANNEL:
        if user and user.id in cfg["ignored"]:
            return False
        if cfg["ignore_admins"] and chat.type in GROUPS:
            anonymous = message.sender_chat and message.sender_chat.id == chat.id
            if anonymous or (user and user.id in await admin_ids(client, chat.id)):
                return False
    return chance_ok(cfg["chance"])


async def send_reaction(message, emoji):
    last = None
    for form in variants(emoji):
        try:
            return await message.react(form)
        except INVALID as e:
            last = e
    if last:
        raise last


async def deliver(client, message, emoji, delay):
    if delay:
        await asyncio.sleep(delay)
    for _ in range(2):
        try:
            await send_reaction(message, emoji)
            db.bump_reaction(client.me.id, message.chat.id, title_of(message.chat))
            return
        except errors.FloodWait as e:
            if e.value > 60:
                return
            await asyncio.sleep(e.value)
        except Exception:
            return


@Client.on_message(filters.incoming & ~filters.service & ~filters.regex(r"^/"), group=1)
async def react(client, message):
    bot_id = client.me.id
    cfg = await db.get_cfg(bot_id, message.chat.id)
    if not cfg["enabled"] or not await should_react(client, message, cfg):
        return
    pool = await pool_for(bot_id, cfg)
    emoji = choose(pool, cfg["mode"], next_counter((bot_id, message.chat.id)))
    task = asyncio.create_task(
        deliver(client, message, emoji, delay_value(cfg["dmin"], cfg["dmax"]))
    )
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)


@Client.on_message(
    filters.command("reaction") & (filters.private | filters.group | filters.channel)
)
async def reaction_switch(client, message):
    t = await get_tr(client)
    if not await can_manage(client, message.chat, message.from_user, message.sender_chat):
        return await message.reply_text(t("**You are not authorized to use this.**"))

    bot_id, chat_id = client.me.id, message.chat.id
    arg = message.command[1].lower() if len(message.command) > 1 else None
    if arg in ("on", "off"):
        await db.set_reaction(bot_id, chat_id, arg == "on")

    on = await db.reaction_enabled(bot_id, chat_id)
    text = t("**Reactions in this chat are {state}.**", state=t.v("ON ✅" if on else "OFF ❌"))
    if arg not in ("on", "off"):
        text += t("\n\n**Use :** `/reaction on` or `/reaction off`\n**More :** `/settings`")
    await message.reply_text(text)

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
