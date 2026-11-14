# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton as B
from pyrogram.types import InlineKeyboardMarkup as M

from PurviReaction import database as db
from PurviReaction.emojis import ALLOWED, extract, show
from PurviReaction.rules import CHANCES, DELAYS, MODES, TYPES, cycle
from PurviReaction.utils import (
    GROUPS, can_manage, get_tr, resolve_target, title_of,
)

CHATS = filters.private | filters.group | filters.channel
MODE_LABEL = {"random": "Random 🎲", "fixed": "Fixed 📌", "sequence": "Sequence 🔁"}
TYPE_LABEL = {
    "text": "Text", "photo": "Photo", "video": "Video", "sticker": "Sticker",
    "voice": "Voice/Audio", "doc": "Files", "anim": "GIF", "other": "Other",
}
PAGE, PER_ROW = 42, 7


def emoji_line(emojis, limit=24):
    return " ".join(show(e) for e in emojis[:limit]) + (" …" if len(emojis) > limit else "")


def delay_label(cfg):
    if not cfg["dmax"]:
        return "Off"
    return f"{cfg['dmin']:g}-{cfg['dmax']:g}s"


# ---------------------------------------------------------------- panels
async def main_panel(client, chat):
    t = await get_tr(client)
    cfg = await db.get_cfg(client.me.id, chat.id)
    cid = chat.id
    types_on = sum(1 for k in TYPES if cfg["types"].get(k, True))
    text = t(
        "**⚙️ Reaction Settings**\n"
        "**Chat :** `{title}`\n\n"
        "• **Reactions :** {state}\n"
        "• **Mode :** {mode}\n"
        "• **Chance :** {chance}%\n"
        "• **Delay :** {delay}\n"
        "• **Emojis :** {emojis}\n"
        "• **Message types :** {types}/8 on\n"
        "• **Keywords :** {kw}\n"
        "• **Ignored users :** {ign}\n"
        "• **Ignore admins :** {ia}",
        title=title_of(chat),
        state=t.v("ON ✅" if cfg["enabled"] else "OFF ❌"),
        mode=t.v(MODE_LABEL[cfg["mode"]]),
        chance=cfg["chance"],
        delay=t.v(delay_label(cfg)),
        emojis=t.v(f"{len(cfg['emojis'])} selected") if cfg["emojis"] else t.v("Default"),
        types=types_on,
        kw=len(cfg["keywords"]),
        ign=len(cfg["ignored"]),
        ia=t.v("ON" if cfg["ignore_admins"] else "OFF"),
    )
    rows = [
        [B(t.v("Reactions : ON ✅" if cfg["enabled"] else "Reactions : OFF ❌"), callback_data=f"ST:t:{cid}")],
        [B(t.v("Mode : " + MODE_LABEL[cfg["mode"]]), callback_data=f"ST:m:{cid}")],
        [
            B(t.v(f"Chance : {cfg['chance']}%"), callback_data=f"ST:c:{cid}"),
            B(t.v("Delay : " + delay_label(cfg)), callback_data=f"ST:d:{cid}"),
        ],
        [
            B(t.v("😀 Emojis"), callback_data=f"ST:e:{cid}"),
            B(t.v("🎯 Filters"), callback_data=f"ST:f:{cid}"),
        ],
    ]
    if chat.type in GROUPS:
        rows.append([B(t.v("Ignore admins : " + ("ON" if cfg["ignore_admins"] else "OFF")), callback_data=f"ST:ia:{cid}")])
    rows.append([B(t.v("Close"), callback_data=f"ST:x:{cid}")])
    return text, M(rows)


async def emoji_panel(client, chat, page=0):
    t = await get_tr(client)
    cfg = await db.get_cfg(client.me.id, chat.id)
    cid = chat.id
    pages = (len(ALLOWED) + PAGE - 1) // PAGE
    page = max(0, min(page, pages - 1))
    chosen = cfg["emojis"]
    items = list(enumerate(ALLOWED))[page * PAGE:(page + 1) * PAGE]
    rows = []
    for i in range(0, len(items), PER_ROW):
        rows.append([
            B(show(e) + ("✔" if e in chosen else ""), callback_data=f"ST:et:{cid}:{idx}:{page}")
            for idx, e in items[i:i + PER_ROW]
        ])
    nav = []
    if page > 0:
        nav.append(B("⬅️", callback_data=f"ST:ep:{cid}:{page - 1}"))
    nav.append(B(f"{page + 1}/{pages}", callback_data=f"ST:noop:{cid}"))
    if page < pages - 1:
        nav.append(B("➡️", callback_data=f"ST:ep:{cid}:{page + 1}"))
    rows.append(nav)
    rows.append([
        B(t.v("Select all"), callback_data=f"ST:ea:{cid}:{page}"),
        B(t.v("Use default"), callback_data=f"ST:er:{cid}:{page}"),
    ])
    rows.append([B(t.v("⬅️ Back"), callback_data=f"ST:b:{cid}")])
    text = t(
        "**😀 Choose reaction emojis**\n\n"
        "• Tap an emoji to select / unselect it.\n"
        "• Nothing selected = default emojis are used.\n"
        "• Mode **Fixed** uses the first selected emoji, **Sequence** goes one by one.\n\n"
        "**Selected ({n}) :** {sel}",
        n=len(chosen),
        sel=emoji_line(chosen) if chosen else t.v("none (default)"),
    )
    return text, M(rows)


async def filter_panel(client, chat):
    t = await get_tr(client)
    cfg = await db.get_cfg(client.me.id, chat.id)
    cid = chat.id
    btns = [
        B(t.v(("✅ " if cfg["types"].get(k, True) else "❌ ") + TYPE_LABEL[k]), callback_data=f"ST:ft:{cid}:{k}")
        for k in TYPES
    ]
    rows = [btns[i:i + 2] for i in range(0, len(btns), 2)]
    rows.append([B(t.v("⬅️ Back"), callback_data=f"ST:b:{cid}")])
    text = t(
        "**🎯 Message filters**\n\n"
        "• ✅ = I react to this type, ❌ = I skip it.\n"
        "• Keywords : `/addkeyword word` (react only on messages with these words)\n"
        "• Currently **{n}** keyword(s).",
        n=len(cfg["keywords"]),
    )
    return text, M(rows)


async def render(client, query, view="main", page=0):
    chat = query.message.chat
    if view == "emoji":
        text, markup = await emoji_panel(client, chat, page)
    elif view == "filter":
        text, markup = await filter_panel(client, chat)
    else:
        text, markup = await main_panel(client, chat)
    try:
        await query.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except MessageNotModified:
        pass


# ------------------------------------------------------------- callbacks
@Client.on_callback_query(filters.regex(r"^ST:"), group=-1)
async def settings_cb(client, query):
    parts = query.data.split(":")
    action = parts[1]
    t = await get_tr(client)
    msg = query.message
    try:
        cid = int(parts[2])
    except (IndexError, ValueError):
        return await query.answer()
    if not msg or msg.chat.id != cid:
        return await query.answer(t.v("This panel is not for this chat."), show_alert=True)
    if not await can_manage(client, msg.chat, query.from_user):
        return await query.answer(t.v("Only admins can change settings."), show_alert=True)
    if action == "noop":
        return await query.answer()
    if action == "x":
        await query.answer()
        return await msg.delete()

    bot_id = client.me.id
    cfg = await db.get_cfg(bot_id, cid)
    view, page = "main", 0

    if action == "t":
        cfg["enabled"] = not cfg["enabled"]
    elif action == "m":
        cfg["mode"] = cycle(MODES, cfg["mode"])
    elif action == "c":
        cfg["chance"] = cycle(CHANCES, cfg["chance"])
    elif action == "d":
        dmin, dmax = cycle(DELAYS, (cfg["dmin"], cfg["dmax"]))
        cfg["dmin"], cfg["dmax"] = dmin, dmax
    elif action == "ia":
        cfg["ignore_admins"] = not cfg["ignore_admins"]
    elif action in ("e", "ep", "et", "ea", "er"):
        view = "emoji"
        page = int(parts[-1]) if action != "e" and parts[-1].lstrip("-").isdigit() else 0
        if action == "et":
            e = ALLOWED[int(parts[3])]
            if e in cfg["emojis"]:
                cfg["emojis"].remove(e)
            else:
                cfg["emojis"].append(e)
        elif action == "ea":
            cfg["emojis"] = list(ALLOWED)
        elif action == "er":
            cfg["emojis"] = []
    elif action in ("f", "ft"):
        view = "filter"
        if action == "ft" and parts[3] in cfg["types"]:
            cfg["types"][parts[3]] = not cfg["types"][parts[3]]
    # "b" (back) just shows the main panel

    if action not in ("e", "ep", "f", "b"):
        await db.save_cfg(bot_id, cid)
    await query.answer()
    await render(client, query, view, page)


# -------------------------------------------------------------- commands
async def ctx(client, message):
    t = await get_tr(client)
    if not await can_manage(client, message.chat, message.from_user, message.sender_chat):
        await message.reply_text(t("**You are not authorized to use this.**"))
        return None, None
    return t, await db.get_cfg(client.me.id, message.chat.id)


def arg_text(message):
    parts = (message.text or "").split(None, 1)
    return parts[1].strip() if len(parts) > 1 else ""


@Client.on_message(filters.command("settings") & CHATS)
async def settings_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    text, markup = await main_panel(client, message.chat)
    await message.reply_text(text, reply_markup=markup, disable_web_page_preview=True)


@Client.on_message(filters.command("emojis") & CHATS)
async def emojis_cmd(client, message):
    t = await get_tr(client)
    cfg = await db.get_cfg(client.me.id, message.chat.id)
    await message.reply_text(
        t("**Allowed reaction emojis :**\n\n{all}\n\n**Selected :** {sel}\n\n"
          "Use `/setreactions 🔥 ❤️ 🤣` or `/settings`",
          all=emoji_line(ALLOWED, 100),
          sel=emoji_line(cfg["emojis"]) if cfg["emojis"] else t.v("default"))
    )


@Client.on_message(filters.command("setreactions") & CHATS)
async def setreactions_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    emojis = extract(arg_text(message))
    if not emojis:
        return await message.reply_text(
            t("**Send the emojis after the command.**\n\n**Example :** `/setreactions 🔥 ❤️ 🤣`\n"
              "**All allowed emojis :** `/emojis`")
        )
    cfg["emojis"] = emojis
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(
        t("**✅ Saved {n} emoji(s) :** {sel}", n=len(emojis), sel=emoji_line(emojis))
    )


@Client.on_message(filters.command("resetreactions") & CHATS)
async def resetreactions_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    cfg["emojis"] = []
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(t("**✅ Emojis reset. Default emojis will be used.**"))


@Client.on_message(filters.command("setmode") & CHATS)
async def setmode_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    mode = message.command[1].lower() if len(message.command) > 1 else ""
    if mode not in MODES:
        return await message.reply_text(
            t("**Use :** `/setmode random` | `/setmode fixed` | `/setmode sequence`")
        )
    cfg["mode"] = mode
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(t("**✅ Mode set to {m}.**", m=t.v(MODE_LABEL[mode])))


@Client.on_message(filters.command("setchance") & CHATS)
async def setchance_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    try:
        value = int(message.command[1])
        assert 1 <= value <= 100
    except Exception:
        return await message.reply_text(t("**Use :** `/setchance 50` (1 to 100)"))
    cfg["chance"] = value
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(t("**✅ I will react to {v}% of the messages.**", v=value))


@Client.on_message(filters.command("setdelay") & CHATS)
async def setdelay_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    try:
        nums = [float(x) for x in message.command[1:3]]
        assert nums and all(0 <= n <= 60 for n in nums)
    except Exception:
        return await message.reply_text(
            t("**Use :** `/setdelay 2 5` (random 2 to 5 sec) or `/setdelay 0` (off)\nMax 60 seconds.")
        )
    dmin, dmax = (0, 0) if nums[0] == 0 and len(nums) == 1 else (nums[0], nums[-1])
    if len(nums) == 1 and nums[0] > 0:
        dmin = dmax = nums[0]
    cfg["dmin"], cfg["dmax"] = min(dmin, dmax), max(dmin, dmax)
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(t("**✅ Delay : {d}**", d=t.v(delay_label(cfg))))


@Client.on_message(filters.command("addkeyword") & CHATS)
async def addkeyword_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    words = [w.strip().lower() for w in arg_text(message).split(",") if w.strip()]
    if not words:
        return await message.reply_text(t("**Use :** `/addkeyword hello, good morning`"))
    for w in words:
        if w[:40] not in cfg["keywords"] and len(cfg["keywords"]) < 50:
            cfg["keywords"].append(w[:40])
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(
        t("**✅ Now reacting only on messages with :** `{k}`", k=", ".join(cfg["keywords"]))
    )


@Client.on_message(filters.command("delkeyword") & CHATS)
async def delkeyword_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    words = {w.strip().lower() for w in arg_text(message).split(",") if w.strip()}
    cfg["keywords"] = [k for k in cfg["keywords"] if k not in words]
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(t("**✅ Removed. Keywords left : {n}**", n=len(cfg["keywords"])))


@Client.on_message(filters.command("clearkeywords") & CHATS)
async def clearkeywords_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    cfg["keywords"] = []
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(t("**✅ Keywords cleared. I react to every message again.**"))


@Client.on_message(filters.command("keywords") & CHATS)
async def keywords_cmd(client, message):
    t = await get_tr(client)
    cfg = await db.get_cfg(client.me.id, message.chat.id)
    if not cfg["keywords"]:
        return await message.reply_text(t("**No keywords set. I react to every message.**"))
    await message.reply_text(t("**Keywords :** `{k}`", k=", ".join(cfg["keywords"])))


@Client.on_message(filters.command(["ignore", "unignore"]) & CHATS)
async def ignore_cmd(client, message):
    t, cfg = await ctx(client, message)
    if cfg is None:
        return
    if message.chat.type not in GROUPS:
        return await message.reply_text(t("**This command only works in groups.**"))
    target = await resolve_target(client, message)
    if not target:
        return await message.reply_text(
            t("**Reply to a user or send** `/ignore user_id` **(use** `/unignore` **to undo).**")
        )
    uid, label = target
    if message.command[0].lower() == "ignore":
        if uid not in cfg["ignored"] and len(cfg["ignored"]) < 200:
            cfg["ignored"].append(uid)
        text = t("**✅ I will not react to** {u}", u=label)
    else:
        if uid in cfg["ignored"]:
            cfg["ignored"].remove(uid)
        text = t("**✅ I will react to** {u} **again.**", u=label)
    await db.save_cfg(client.me.id, message.chat.id)
    await message.reply_text(text)


@Client.on_message(filters.command("ignorelist") & CHATS)
async def ignorelist_cmd(client, message):
    t = await get_tr(client)
    cfg = await db.get_cfg(client.me.id, message.chat.id)
    if not cfg["ignored"]:
        return await message.reply_text(t("**No ignored users.**"))
    await message.reply_text(
        t("**Ignored users :**\n{ids}", ids="\n".join(f"• `{u}`" for u in cfg["ignored"]))
    )

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
