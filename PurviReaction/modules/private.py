# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatType

import config
from PurviReaction import database as db
from PurviReaction.utils import chunk_lines, get_tr, is_allowed_user

IN_CHAT = (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


@Client.on_message(filters.incoming, group=-6)
async def private_gate(client, message):
    """Private mode: strangers in DM and unapproved chats are ignored."""
    if not config.PRIVATE_MODE:
        return
    user = message.from_user
    if user and is_allowed_user(user.id):
        return
    if message.chat.type == ChatType.PRIVATE or not await db.is_approved(
        client.me.id, message.chat.id
    ):
        message.stop_propagation()


@Client.on_callback_query(group=-6)
async def private_gate_cb(client, query):
    if not config.PRIVATE_MODE or is_allowed_user(query.from_user.id):
        return
    msg = query.message
    if msg and msg.chat.type != ChatType.PRIVATE and await db.is_approved(client.me.id, msg.chat.id):
        return
    await query.answer()
    query.stop_propagation()


@Client.on_chat_member_updated(group=-6)
async def guard_new_chat(client, update):
    """Added by the owner -> approved. Added by anyone else -> leave."""
    if not config.PRIVATE_MODE:
        return
    new, old = update.new_chat_member, update.old_chat_member
    if not new or new.user.id != client.me.id or update.chat.type == ChatType.PRIVATE:
        return
    joined = new.status in IN_CHAT and not (old and old.status in IN_CHAT)
    if not joined:
        return
    bot_id, chat_id = client.me.id, update.chat.id
    adder = update.from_user
    if adder and is_allowed_user(adder.id):
        return await db.approve_chat(bot_id, chat_id)
    if await db.is_approved(bot_id, chat_id):
        return
    try:
        await client.leave_chat(chat_id)
    except Exception:
        pass
    await db.remove_chat(bot_id, chat_id)


def _allowed(message):
    return bool(message.from_user and is_allowed_user(message.from_user.id))


def _target_chat(message):
    if len(message.command) > 1 and message.command[1].lstrip("-").isdigit():
        return int(message.command[1])
    if message.chat.type != ChatType.PRIVATE:
        return message.chat.id
    return None


@Client.on_message(filters.command("approve"))
async def approve_cmd(client, message):
    if not _allowed(message):
        return
    t = await get_tr(client)
    chat_id = _target_chat(message)
    if chat_id is None:
        return await message.reply_text(
            t("**Use :** `/approve` **inside a group, or** `/approve chat_id` **in DM.**")
        )
    await db.approve_chat(client.me.id, chat_id)
    await message.reply_text(t("**✅ Chat approved :** `{c}`", c=chat_id))


@Client.on_message(filters.command("unapprove"))
async def unapprove_cmd(client, message):
    if not _allowed(message):
        return
    t = await get_tr(client)
    chat_id = _target_chat(message)
    if chat_id is None:
        return await message.reply_text(
            t("**Use :** `/unapprove` **inside a group, or** `/unapprove chat_id` **in DM.**")
        )
    await db.unapprove_chat(client.me.id, chat_id)
    await message.reply_text(t("**🚫 Chat removed :** `{c}`\nI will leave it now.", c=chat_id))
    try:
        await client.leave_chat(chat_id)
    except Exception:
        pass


@Client.on_message(filters.command("approved") & filters.private)
async def approved_cmd(client, message):
    if not _allowed(message):
        return
    t = await get_tr(client)
    ids = await db.get_approved(client.me.id)
    if not ids:
        return await message.reply_text(
            t("**No approved chats yet.** Add me to a group yourself, or use `/approve chat_id`.")
        )
    rows = []
    for cid in ids:
        try:
            title = (await client.get_chat(cid)).title or cid
        except Exception:
            title = "?"
        rows.append(f"• `{cid}` {str(title).replace('`', '')}")
    for text in chunk_lines(t("**Approved chats ({n}) :**\n\n", n=len(ids)), rows):
        await message.reply_text(text)


@Client.on_message(filters.command("approveall") & filters.private)
async def approveall_cmd(client, message):
    """One time: approve every chat the bot is already in."""
    if not _allowed(message):
        return
    t = await get_tr(client)
    n = await db.approve_all_served(client.me.id)
    await message.reply_text(t("**✅ Approved {n} existing chat(s).**", n=n))

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
