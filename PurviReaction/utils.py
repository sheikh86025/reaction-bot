# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

import time

from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType

import config
from PurviReaction import app
from PurviReaction import database as db
from PurviReaction.fonts import Tr

GROUPS = (ChatType.GROUP, ChatType.SUPERGROUP)
_ADMINS = {}


def is_allowed_user(user_id):
    """Owner or someone the owner allowed (ALLOWED_USERS)."""
    return user_id == config.OWNER_ID or user_id in config.ALLOWED_USERS


def is_private_main(client):
    """True when this is the main bot and PRIVATE_MODE is on."""
    return bool(config.PRIVATE_MODE and app.me and client.me.id == app.me.id)


async def is_bot_owner(bot_id, user_id):
    if user_id == config.OWNER_ID:
        return True
    clone = await db.get_clone(bot_id)
    return bool(clone and clone.get("user_id") == user_id)


def readable_time(seconds):
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    text = f"{hours}h {minutes}m {secs}s"
    return f"{days}d {text}" if days else text


def chunk_lines(header, lines, limit=4000):
    text = header
    for line in lines:
        if len(text) + len(line) + 1 > limit:
            yield text
            text = ""
        text += line + "\n"
    if text.strip():
        yield text


async def get_tr(client):
    """Translator for this bot (small caps or normal text)."""
    cfg = await db.get_bot_cfg(client.me.id)
    return Tr(cfg.get("style", "sc") == "sc")


async def is_chat_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)


async def admin_ids(client, chat_id, ttl=300):
    """Admin ids of a group (cached for a few minutes)."""
    key, now = (client.me.id, chat_id), time.time()
    hit = _ADMINS.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    ids = set()
    try:
        async for m in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
            if m.user:
                ids.add(m.user.id)
    except Exception:
        pass
    _ADMINS[key] = (now, ids)
    return ids


async def can_manage(client, chat, user=None, sender_chat=None):
    """Who may change settings: DM owner, group/channel admins, bot owner."""
    if chat.type == ChatType.PRIVATE:
        return True
    if sender_chat and sender_chat.id == chat.id:
        return True
    if not user:
        return False
    if await is_bot_owner(client.me.id, user.id):
        return True
    return await is_chat_admin(client, chat.id, user.id)


async def resolve_target(client, message):
    """(user_id, label) from a reply, a user id or a @username."""
    rep = message.reply_to_message
    if rep and rep.from_user:
        return rep.from_user.id, rep.from_user.mention
    if len(message.command) > 1:
        arg = message.command[1].strip()
        is_id = arg.lstrip("-").isdigit()
        try:
            user = await client.get_users(int(arg) if is_id else arg)
            return user.id, user.mention
        except Exception:
            if is_id:
                return int(arg), f"`{arg}`"
    return None


def title_of(chat):
    return (chat.title or chat.first_name or str(chat.id)).replace("`", "'")

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
