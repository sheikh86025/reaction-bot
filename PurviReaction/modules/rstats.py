# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from pyrogram import Client, filters

from PurviReaction import database as db
from PurviReaction.utils import get_tr, is_bot_owner


@Client.on_message(filters.command("rstats"))
async def rstats_cmd(client, message):
    t = await get_tr(client)
    bot_id = client.me.id
    here = await db.chat_reactions(bot_id, message.chat.id)
    total = await db.total_reactions(bot_id)
    await message.reply_text(
        t("**📈 Reaction stats**\n\n• **This chat :** {here}\n• **All chats :** {total}", here=here, total=total)
    )


@Client.on_message(filters.command("topchats") & filters.private)
async def topchats_cmd(client, message):
    t = await get_tr(client)
    user = message.from_user
    if not (user and await is_bot_owner(client.me.id, user.id)):
        return await message.reply_text(t("**You are not authorized to use this.**"))
    rows = await db.top_chats(client.me.id, 10)
    if not rows:
        return await message.reply_text(t("**No reactions counted yet.**"))
    def clean(x):
        return "".join(c for c in str(x) if c not in "*_`[]<>~|")

    lines = [
        f"{i}. {clean(r.get('title') or r['chat_id'])} : {r['count']}"
        for i, r in enumerate(rows, 1)
    ]
    await message.reply_text(t("**🏆 Top chats by reactions**\n\n") + "\n".join(lines))

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
