# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from pyrogram import Client
from PurviReaction import ui


@Client.on_callback_query()
async def callbacks(client, query):
    data = query.data

    if data == "CLOSE":
        return await query.message.delete()

    page = await ui.page_for(client, query.from_user, data)
    if page:
        text, markup = page
        await query.message.edit_text(
            text, reply_markup=markup, disable_web_page_preview=True
        )

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
