# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

import asyncio
import time

from pyrogram import Client, filters
from pyrogram.enums import ChatType

import config
from PurviReaction import LOGGER, app
from PurviReaction import database as db
from PurviReaction.modules import clone as clonemod
from PurviReaction.utils import chunk_lines, get_tr

DAY = 86400


def time_left(expires_at):
    if not expires_at:
        return "Lifetime ♾️"
    left = int(expires_at - time.time())
    if left <= 0:
        return "Expired ❌"
    days, rest = divmod(left, DAY)
    hours = rest // 3600
    return f"{days}d {hours}h" if days else f"{hours}h {(rest % 3600) // 60}m"


async def _notify(user_id, text):
    try:
        await app.send_message(user_id, text)
    except Exception:
        pass


async def check_expiry():
    now = int(time.time())
    for c in await db.get_clones():
        exp = c.get("expires_at")
        if not exp or c.get("expired"):
            continue
        name = f"@{c['username']}" if c.get("username") else c["bot_id"]
        if exp <= now:
            await clonemod.stop_clone(c["bot_id"])
            await db.update_clone(c["bot_id"], expired=True)
            await _notify(
                c["user_id"],
                f"⌛ **Your clone {name} has expired and was stopped.**\n"
                "Contact @TheSigmaCoder to renew it.",
            )
            await _notify(config.OWNER_ID, f"⌛ Clone {name} expired (owner `{c['user_id']}`).")
        elif exp - now < DAY and not c.get("warned"):
            await db.update_clone(c["bot_id"], warned=True)
            await _notify(
                c["user_id"],
                f"⚠️ **Your clone {name} expires in less than 24 hours.**\n"
                "Contact @TheSigmaCoder to renew it.",
            )


async def expiry_loop():
    while True:
        try:
            await check_expiry()
        except Exception:
            LOGGER.exception("Clone expiry check failed.")
        await asyncio.sleep(600)


@Client.on_message(filters.command("premium") & filters.private)
async def premium_cmd(client, message):
    t = await get_tr(client)
    if not (message.from_user and message.from_user.id == config.OWNER_ID):
        return await message.reply_text(t("**You are not authorized to use this.**"))
    if len(message.command) < 3:
        return await message.reply_text(
            t("**Use :** `/premium bot_id_or_@username 30` or `/premium bot_id_or_@username lifetime`")
        )
    clone = await db.find_clone(message.command[1])
    if not clone:
        return await message.reply_text(t("**Clone not found.**"))

    arg, now = message.command[2].lower(), int(time.time())
    if arg == "lifetime":
        fields = {"expires_at": None, "expired": False, "warned": False}
    else:
        try:
            days = int(arg)
            assert days > 0
        except Exception:
            return await message.reply_text(t("**Days must be a number like** `30` **or** `lifetime`"))
        current = clone.get("expires_at")
        base = current if (current and current > now and not clone.get("expired")) else now
        fields = {"expires_at": base + days * DAY, "expired": False, "warned": False}
    await db.update_clone(clone["bot_id"], **fields)

    note = ""
    if clone["bot_id"] not in clonemod.RUNNING:
        try:
            await clonemod.start_clone(clone["token"])
        except Exception as e:
            note = t("\n⚠️ **Could not start the bot :** `{e}`", e=str(e)[:150])
    left = time_left(fields["expires_at"])
    await message.reply_text(
        t("**✅ Updated** @{u} **→** {left}", u=clone.get("username") or clone["bot_id"], left=left) + note
    )
    await _notify(clone["user_id"], f"✅ **Your clone is active now.** Validity : {left}")


@Client.on_message(filters.command("myclone") & filters.private)
async def myclone_cmd(client, message):
    t = await get_tr(client)
    if message.chat.type != ChatType.PRIVATE or not message.from_user:
        return await message.reply_text(t("**Use this command in bot DM.**"))
    mine = await db.get_clones_by_owner(message.from_user.id)
    if not mine:
        return await message.reply_text(t("**You have no clone yet. Use** `/clone bot_token`"))
    rows = []
    for c in mine:
        status = "Expired ❌" if c.get("expired") else (
            "Running ✅" if c["bot_id"] in clonemod.RUNNING else "Stopped ⚠️")
        rows.append(
            t("• @{u}\n   **Status :** {s}\n   **Validity :** {v}\n",
              u=c.get("username") or c["bot_id"], s=t.v(status), v=t.v(time_left(c.get("expires_at"))))
        )
    await message.reply_text("".join(rows))


@Client.on_message(filters.command("expiring") & filters.private)
async def expiring_cmd(client, message):
    t = await get_tr(client)
    if not (message.from_user and message.from_user.id == config.OWNER_ID):
        return await message.reply_text(t("**You are not authorized to use this.**"))
    rows = [
        f"• {'@' + c['username'] if c.get('username') else c['bot_id']} : "
        f"{'Expired ❌' if c.get('expired') else time_left(c.get('expires_at'))}"
        for c in sorted(await db.get_clones(), key=lambda c: c.get("expires_at") or 1 << 60)
    ]
    if not rows:
        return await message.reply_text(t("**No clones.**"))
    for text in chunk_lines(t("**Clone validity :**\n\n"), rows):
        await message.reply_text(text)

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
