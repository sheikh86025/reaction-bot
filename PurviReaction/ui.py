# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder)

# 🚀 This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️

# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardButton as Button

from PurviReaction import app
from PurviReaction import database as db
from PurviReaction.utils import get_tr

START_PHOTO = "https://files.catbox.moe/8vbfvp.jpg"
CLONE_PHOTO = "https://files.catbox.moe/rdfi4z.jpg"

HELP_READ = """**• ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ғᴏʀ ᴍᴏʀᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ.  

♦ ɪғ ʏᴏᴜ'ʀᴇ ғᴀᴄɪɴɢ ᴀɴʏ ᴘʀᴏʙʟᴇᴍ ʏᴏᴜ ᴄᴀɴ ᴀsᴋ ɪɴ [sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ](https://t.me/offerkingdom).

» ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : /**
"""

TOOLS_DATA_READ = """**<u>❖ ᴄᴏᴍᴍᴀɴᴅs ғᴏʀ ʀᴇᴀᴄᴛɪᴏɴ :</u>

• /start sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ !
──────────────
• /stats - ɢᴇᴛ ʙᴏᴛ sᴛᴀᴛs, ᴜᴘᴛɪᴍᴇ ᴀɴᴅ ᴘɪɴɢ
──────────────
• /reaction on|off - ᴛᴜʀɴ ʀᴇᴀᴄᴛɪᴏɴs ᴏɴ/ᴏғғ ɪɴ ᴀɴʏ ᴄʜᴀᴛ (ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ᴀᴅᴍɪɴs + ʙᴏᴛ ᴏᴡɴᴇʀ)
──────────────
• /broadcast ᴛᴇxᴛ - sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴄʜᴀᴛs ᴀɴᴅ ᴜsᴇʀs, ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ /broadcast ᴛᴏ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴀs ɪᴛ ɪs (ʙᴏᴛ ᴏᴡɴᴇʀ ᴏɴʟʏ)
──────────────
✦ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : [ᴏғғᴇʀ ᴋɪɴɢᴅᴏᴍ](t.me/offerkingdom)**
"""

ALPHA_READ = """**<u>❖ ᴄᴏᴍᴍᴀɴᴅs ғᴏʀ ᴄʟᴏɴᴇ ғᴇᴀᴛᴜʀᴇs :</u>

• /clone [ ʙᴏᴛ ᴛᴏᴋᴇɴ ] - ᴍᴀᴋᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ.
──────────────
• /cloned - sᴇᴇ ᴄʟᴏɴᴇᴅ ʙᴏᴛs ᴏɴʟʏ ᴏᴡɴᴇʀ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.
──────────────
• /totalbots - ɢᴇᴛ ᴛᴏᴛᴀʟ ᴄʟᴏɴᴇᴅ ʙᴏᴛs ᴄᴏᴜɴᴛ.
──────────────
• /delclone - ʀᴇᴍᴏᴠᴇ ʏᴏᴜʀ ʙᴏᴛ ᴄʟᴏɴᴇ.
──────────────
• /delallclone - ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴄʟᴏɴᴇᴅ ʙᴏᴛs ᴏɴʟʏ ᴏᴡɴᴇʀ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.
──────────────
✦ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : [ᴏғғᴇʀ ᴋɪɴɢᴅᴏᴍ](t.me/offerkingdom)**
"""


def start_caption(user):
    return (
        f"**✦ ʜᴇʏ {user.mention}!**\n**✦ ɪ'ᴍ ʏᴏᴜʀ ᴀᴜᴛᴏ ʀᴇᴀᴄᴛɪᴏɴ ʙᴏᴛ !!**\n\n"
        "**• ɪ'ᴍ ʀᴇᴀᴄᴛ ᴛᴏ ᴇᴠᴇʀʏ ᴍᴇssᴀɢᴇ ɪɴ ɢʀᴏᴜᴘs, ᴄʜᴀɴɴᴇʟs & ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛs ᴡɪᴛʜ ᴀ ʀᴀɴᴅᴏᴍ ᴇᴍᴏᴊɪ..!!**\n\n"
        "**✦ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : [ᴏғғᴇʀ ᴋɪɴɢᴅᴏᴍ](t.me/offerkingdom)**"
    )


def clone_start_caption(user):
    return (
        f"**✦ ʜᴇʏ {user.mention}!!**\n**◆ ɪ'ᴍ ʏᴏᴜʀ ᴄʟᴏɴᴇᴅ ᴀᴜᴛᴏ ʀᴇᴀᴄᴛɪᴏɴ ʙᴏᴛ !!**\n\n"
        "**• ɪ'ᴍ ʀᴇᴀᴄᴛ ᴛᴏ ᴇᴠᴇʀʏ ᴍᴇssᴀɢᴇ ɪɴ ɢʀᴏᴜᴘs, ᴄʜᴀɴɴᴇʟs & ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛs ᴡɪᴛʜ ᴀ ʀᴀɴᴅᴏᴍ ᴇᴍᴏᴊɪ..!!**\n\n"
        f"**◆ ɢᴏ & ᴄʟᴏɴᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ :\n     @{app.me.username}**"
    )


def clone_info_caption():
    return (
        "**✦ ᴡᴀɴᴛ ʏᴏᴜʀ ᴏᴡɴ ʀᴇᴀᴄᴛɪᴏɴ ʙᴏᴛ ?**\n\n"
        "**• ɢᴏ ᴛᴏ ᴛʜᴇ ᴍᴀɪɴ ʙᴏᴛ & sᴇɴᴅ /clone ᴡɪᴛʜ ʏᴏᴜʀ ʙᴏᴛ ᴛᴏᴋᴇɴ.**\n\n"
        f"**◆ ᴍᴀɪɴ ʙᴏᴛ : @{app.me.username}**"
    )


def clone_info_buttons():
    return InlineKeyboardMarkup([
        [Button("ᴄʟᴏɴᴇ ʙᴏᴛ", url=f"https://t.me/{app.me.username}")]
    ])


def add_button(client):
    return [
        [
            Button(
                "✙ ᴀᴅᴅ ᴍᴇ ɪɴ ɢʀᴏᴜᴘ ✙",
                url=f"http://t.me/{client.me.username}?startgroup=true"
            )
        ],
        [
            Button(
                "✙ ᴀᴅᴅ ᴍᴇ ɪɴ ᴄʜᴀɴɴᴇʟ ✙",
                url=f"https://t.me/{client.me.username}?startchannel=new&admin=post_messages+invite_users"
            )
        ]
    ]


def start_buttons(client):
    return InlineKeyboardMarkup(
        add_button(client) + [
            [
                Button("sᴜᴘᴘᴏʀᴛ", url="https://t.me/offerkingdom"),
                Button("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/offerkingdom"),
            ],
            [Button("⌯ ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs ⌯", callback_data="HELP")],
        ]
    )


def clone_start_buttons(client):
    return InlineKeyboardMarkup(add_button(client))


def help_buttons():
    return InlineKeyboardMarkup([
        [
            Button("ᴄʟᴏɴᴇ", callback_data="ALPHA_CMD"),
            Button("ʀᴇᴀᴄᴛɪᴏɴ", callback_data="TOOLS_DATA"),
        ],
        [
            Button("sᴇᴛᴛɪɴɢs", callback_data="SET_HELP"),
            Button("ᴏᴡɴᴇʀ ᴛᴏᴏʟs", callback_data="OWN_HELP"),
        ],
        [Button("ʙᴀᴄᴋ", callback_data="BACK")],
    ])


def back_buttons():
    return InlineKeyboardMarkup([[
        Button("ʙᴀᴄᴋ", callback_data="ALPHA_BACK"),
        Button("ᴄʟᴏsᴇ", callback_data="CLOSE"),
    ]])

async def start_text(client, user):
    """Start caption (custom text from the bot owner, or the default one)."""
    cfg = await db.get_bot_cfg(client.me.id)
    custom = cfg.get("start_text")
    if custom:
        return (
            custom.replace("{mention}", user.mention)
            .replace("{name}", user.first_name or "")
            .replace("{bot}", f"@{client.me.username}")
        )
    is_main = client.me.id == app.me.id
    text = start_caption(user) if is_main else clone_start_caption(user)
    return text if cfg.get("style", "sc") == "sc" else (await get_tr(client)).fix(text)


async def start_photo(client):
    cfg = await db.get_bot_cfg(client.me.id)
    return cfg.get("start_photo") or (START_PHOTO if client.me.id == app.me.id else CLONE_PHOTO)


SET_HELP = """**<u>❖ Settings commands (group/channel admins) :</u>**
• `/settings` - open the settings panel
• `/setreactions 🔥 ❤️ 🤣` - choose your emojis
• `/emojis` - list of allowed emojis
• `/setmode random` | `fixed` | `sequence`
• `/setchance 50` - react on 50% of messages
• `/setdelay 2 5` - random delay (seconds)
• `/addkeyword hello` - react only on keywords
• `/ignore` (reply) - ignore a user, `/unignore`
• `/rstats` - reaction count
──────────────
✦ Powered by : [Offer Kingdom](t.me/offerkingdom)"""

OWN_HELP = """**<u>❖ Bot owner tools :</u>**
• `/setstart text` - custom start text ({mention} {name} {bot})
• `/setphoto` - reply to a photo
• `/resetstart` - back to default
• `/style` - small caps / normal text
• `/defaultreactions 🔥 ❤️` - default emojis
• `/ban` `/unban` `/banlist` - bot level
• `/topchats` - top chats by reactions
• `/myclone` - your clone validity
• `/approve` `/unapprove` `/approved` `/approveall` - private mode chats
──────────────
✦ Powered by : [Offer Kingdom](t.me/offerkingdom)"""


async def page_for(client, user, data):
    """(text, buttons) for a help-menu callback, or None."""
    t = await get_tr(client)
    if data in ("HELP", "ALPHA_BACK"):
        return t.fix(HELP_READ), help_buttons()
    if data == "BACK":
        return await start_text(client, user), start_buttons(client)
    if data == "TOOLS_DATA":
        return t.fix(TOOLS_DATA_READ), back_buttons()
    if data == "ALPHA_CMD":
        return t.fix(ALPHA_READ), back_buttons()
    if data == "SET_HELP":
        return t(SET_HELP), back_buttons()
    if data == "OWN_HELP":
        return t(OWN_HELP), back_buttons()
    return None

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎
# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
