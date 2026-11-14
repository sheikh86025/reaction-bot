# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from pyrogram import Client, filters

import config
from PurviReaction import database as db
from PurviReaction.utils import chunk_lines, get_tr, is_bot_owner, resolve_target


@Client.on_message(filters.incoming, group=-5)
async def ban_gate(client, message):
    user = message.from_user
    if user and user.id != config.OWNER_ID and await db.is_banned(client.me.id, user.id):
        message.stop_propagation()


@Client.on_callback_query(group=-5)
async def ban_gate_cb(client, query):
    user = query.from_user
    if user and user.id != config.OWNER_ID and await db.is_banned(client.me.id, user.id):
        t = await get_tr(client)
        await query.answer(t.v("You are banned from using this bot."), show_alert=True)
        query.stop_propagation()


async def _owner_target(client, message, global_scope):
    t = await get_tr(client)
    user = message.from_user
    allowed = (
        user.id == config.OWNER_ID if (user and global_scope)
        else bool(user and await is_bot_owner(client.me.id, user.id))
    )
    if not allowed:
        await message.reply_text(t("**You are not authorized to use this.**"))
        return t, None
    target = await resolve_target(client, message)
    if not target:
        cmd = message.command[0]
        await message.reply_text(t("**Reply to a user or use** `/{c} user_id`", c=cmd))
        return t, None
    if target[0] == config.OWNER_ID:
        await message.reply_text(t("**You can't ban the owner.**"))
        return t, None
    return t, target


@Client.on_message(filters.command("ban") & filters.private)
async def ban_cmd(client, message):
    t, target = await _owner_target(client, message, False)
    if target:
        await db.ban_user(client.me.id, target[0])
        await message.reply_text(t("**🚫 Banned :** {u}", u=target[1]))


@Client.on_message(filters.command("unban") & filters.private)
async def unban_cmd(client, message):
    t, target = await _owner_target(client, message, False)
    if target:
        await db.unban_user(client.me.id, target[0])
        await message.reply_text(t("**✅ Unbanned :** {u}", u=target[1]))


@Client.on_message(filters.command("gban") & filters.private)
async def gban_cmd(client, message):
    t, target = await _owner_target(client, message, True)
    if target:
        await db.ban_user(0, target[0])
        await message.reply_text(t("**🚫 Globally banned (all bots) :** {u}", u=target[1]))


@Client.on_message(filters.command("ungban") & filters.private)
async def ungban_cmd(client, message):
    t, target = await _owner_target(client, message, True)
    if target:
        await db.unban_user(0, target[0])
        await message.reply_text(t("**✅ Global ban removed :** {u}", u=target[1]))


async def _list(client, message, scope_id, title, global_scope):
    t = await get_tr(client)
    user = message.from_user
    ok = (
        bool(user and user.id == config.OWNER_ID) if global_scope
        else bool(user and await is_bot_owner(client.me.id, user.id))
    )
    if not ok:
        return await message.reply_text(t("**You are not authorized to use this.**"))
    ids = await db.get_bans(scope_id)
    if not ids:
        return await message.reply_text(t("**Nobody is banned.**"))
    for text in chunk_lines(t("**{h} ({n}) :**\n", h=title, n=len(ids)), [f"• `{i}`" for i in ids]):
        await message.reply_text(text)


@Client.on_message(filters.command("banlist") & filters.private)
async def banlist_cmd(client, message):
    await _list(client, message, client.me.id, "Banned users", False)


@Client.on_message(filters.command("gbanlist") & filters.private)
async def gbanlist_cmd(client, message):
    await _list(client, message, 0, "Globally banned users", True)

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
