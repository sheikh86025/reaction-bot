# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from pyrogram import Client, filters

from PurviReaction import database as db
from PurviReaction.emojis import extract, show
from PurviReaction.utils import get_tr, is_bot_owner


async def _owner(client, message):
    t = await get_tr(client)
    user = message.from_user
    if user and await is_bot_owner(client.me.id, user.id):
        return t
    await message.reply_text(t("**You are not authorized to use this.**"))
    return None


@Client.on_message(filters.command("setstart") & filters.private)
async def setstart_cmd(client, message):
    t = await _owner(client, message)
    if not t:
        return
    parts = (message.text or "").split(None, 1)
    rep = message.reply_to_message
    if len(parts) > 1:
        text = parts[1].strip()
    elif rep and rep.text:
        text = rep.text.markdown
    else:
        return await message.reply_text(
            t("**Use :** `/setstart your text`\nOr reply to a text message with `/setstart`\n\n"
              "**Placeholders :** `{mention}` `{name}` `{bot}`")
        )
    if len(text) > 900:
        return await message.reply_text(t("**Text is too long (max 900 characters).**"))
    await db.set_bot_cfg(client.me.id, start_text=text)
    await message.reply_text(t("**✅ Start text saved. Send** /start **to preview.**"))


@Client.on_message(filters.command("setphoto") & filters.private)
async def setphoto_cmd(client, message):
    t = await _owner(client, message)
    if not t:
        return
    rep = message.reply_to_message
    if rep and rep.photo:
        value = rep.photo.file_id
    elif len(message.command) > 1 and message.command[1].startswith("http"):
        value = message.command[1]
    else:
        return await message.reply_text(
            t("**Reply to a photo with** `/setphoto` **or use** `/setphoto https://link/photo.jpg`")
        )
    await db.set_bot_cfg(client.me.id, start_photo=value)
    await message.reply_text(t("**✅ Start photo saved. Send** /start **to preview.**"))


@Client.on_message(filters.command("resetstart") & filters.private)
async def resetstart_cmd(client, message):
    t = await _owner(client, message)
    if not t:
        return
    await db.set_bot_cfg(client.me.id, start_text=None, start_photo=None)
    await message.reply_text(t("**✅ Start text and photo reset to default.**"))


@Client.on_message(filters.command("style") & filters.private)
async def style_cmd(client, message):
    t = await _owner(client, message)
    if not t:
        return
    cfg = await db.get_bot_cfg(client.me.id)
    arg = message.command[1].lower() if len(message.command) > 1 else ""
    if arg in ("sc", "smallcaps", "small"):
        new = "sc"
    elif arg in ("normal", "plain"):
        new = "normal"
    else:
        new = "normal" if cfg.get("style", "sc") == "sc" else "sc"
    await db.set_bot_cfg(client.me.id, style=new)
    t2 = await get_tr(client)
    await message.reply_text(
        t2("**✅ Text style : {s}**\nUse `/style` again to switch.", s=t2.v("Small caps" if new == "sc" else "Normal"))
    )


@Client.on_message(filters.command("defaultreactions") & filters.private)
async def defaultreactions_cmd(client, message):
    t = await _owner(client, message)
    if not t:
        return
    parts = (message.text or "").split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    cfg = await db.get_bot_cfg(client.me.id)
    if arg.lower() == "reset":
        await db.set_bot_cfg(client.me.id, emojis=[])
        return await message.reply_text(t("**✅ Default emojis reset.**"))
    emojis = extract(arg)
    if not emojis:
        current = " ".join(show(e) for e in cfg.get("emojis") or []) or t.v("built-in list")
        return await message.reply_text(
            t("**Default emojis for all chats (chats can still choose their own).**\n\n"
              "**Now :** {cur}\n\n**Use :** `/defaultreactions 🔥 ❤️ 🤣` or `/defaultreactions reset`",
              cur=current)
        )
    await db.set_bot_cfg(client.me.id, emojis=emojis)
    await message.reply_text(
        t("**✅ Default emojis saved :** {sel}", sel=" ".join(show(e) for e in emojis))
    )

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
