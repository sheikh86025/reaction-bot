"""Lightweight reaction bot (single file).

Required variables : BOT_TOKEN, OWNER_ID
Optional variables : EXTRA_BOT_TOKENS (more bots = more reactions per message),
                     EMOJIS, MONGO_URL, DB_NAME, PRIVATE_MODE, API_ID, API_HASH
"""
import asyncio
import logging
import os
import random
import re
import time

try:  # faster event loop = less CPU
    import uvloop

    uvloop.install()
except Exception:
    pass

LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)

from pyrogram import Client, enums, errors, filters, idle  # noqa: E402
from pyrogram.handlers import CallbackQueryHandler, ChatMemberUpdatedHandler, MessageHandler  # noqa: E402
from pyrogram.types import InlineKeyboardButton as Btn  # noqa: E402
from pyrogram.types import InlineKeyboardMarkup as Markup  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("reactbot")

# ----------------------------------------------------------------- settings
API_ID = int(os.getenv("API_ID", "6435225"))
API_HASH = os.getenv("API_HASH", "4e984ea35f854762dcde906dce426c2d")
OWNER_ID = int(os.getenv("OWNER_ID") or 0)
TOKENS = [
    t for t in f"{os.getenv('BOT_TOKEN', '')} {os.getenv('EXTRA_BOT_TOKENS', '')}"
    .replace(",", " ").split() if ":" in t
]
MONGO_URL = os.getenv("MONGO_URL")
PRIVATE_MODE = os.getenv("PRIVATE_MODE", "true").strip().lower() in ("1", "true", "yes", "on")

if not OWNER_ID or not TOKENS:
    raise SystemExit("Set BOT_TOKEN and OWNER_ID in the variables.")

# --------------------------------------------------------------- emoji list
VS16 = "\ufe0f"
# every reaction emoji Telegram lets a bot use
ALLOWED = [
    "👍", "👎", "❤", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬", "😢",
    "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳",
    "❤‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌", "🏆", "💔", "🤨", "😐", "🍓",
    "🍾", "💋", "🖕", "😈", "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈",
    "😇", "😨", "🤝", "✍", "🤗", "🫡", "🎅", "🎄", "☃", "💅", "🤪", "🗿",
    "🆒", "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎", "👾", "🤷‍♂", "🤷", "🤷‍♀",
    "😡",
]
ALT = {  # same emoji with the "emoji style" selector, tried if the plain one is refused
    "❤": "❤" + VS16, "✍": "✍" + VS16, "☃": "☃" + VS16, "⚡": "⚡" + VS16,
    "🕊": "🕊" + VS16, "❤‍🔥": "❤" + VS16 + "‍🔥",
    "🤷‍♂": "🤷‍♂" + VS16, "🤷‍♀": "🤷‍♀" + VS16,
}
POSITIVE = [
    "👍", "❤", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "🙏", "👌",
    "😍", "💯", "🤣", "⚡", "🏆", "💘", "😘", "😎", "🤗", "🆒",
]
_BY_LEN = sorted(ALLOWED, key=len, reverse=True)


def extract(text):
    """Allowed emojis found in a text (order kept, no duplicates)."""
    s, out, i = (text or "").replace(VS16, ""), [], 0
    while i < len(s):
        for e in _BY_LEN:
            if s.startswith(e, i):
                if e not in out:
                    out.append(e)
                i += len(e)
                break
        else:
            i += 1
    return out


def show(emojis):
    return " ".join(ALT.get(e, e) for e in emojis)


DEFAULT_POOL = extract(os.getenv("EMOJIS", "")) or list(POSITIVE)
pool = list(DEFAULT_POOL)
off = set()          # chats where reactions are switched off
chance = 100         # % of messages that get a reaction
dmin = dmax = 0      # random delay (seconds) before reacting
CLIENTS = []         # running bots
_TASKS = set()

# ------------------------------------------- optional MongoDB (only to remember settings)
_col = None


def _collection():
    global _col
    if _col is None and MONGO_URL:
        from pymongo import MongoClient

        _col = MongoClient(MONGO_URL, serverSelectionTimeoutMS=8000)[
            os.getenv("DB_NAME", "reactbot")
        ]["settings"]
    return _col


def _load():
    try:
        col = _collection()
        return col.find_one({"_id": "emojis"}) if col is not None else None
    except Exception as e:
        LOG.warning("MongoDB read failed: %s", e)


def _save():
    try:
        col = _collection()
        if col is None:
            return False
        data = {"list": pool, "off": sorted(off), "chance": chance, "dmin": dmin, "dmax": dmax}
        col.update_one({"_id": "emojis"}, {"$set": data}, upsert=True)
        return True
    except Exception as e:
        LOG.warning("MongoDB write failed: %s", e)
        return False


def apply(doc):
    global pool, off, chance, dmin, dmax
    pool = [e for e in doc.get("list", []) if e in ALLOWED] or pool
    off = set(doc.get("off", []))
    chance = int(doc.get("chance", 100))
    dmin, dmax = doc.get("dmin", 0), doc.get("dmax", 0)


async def persist():
    return await asyncio.to_thread(_save) if MONGO_URL else False


# ------------------------------------------------------------------ reacting
INVALID = getattr(errors, "ReactionInvalid", ())
IN_CHAT = (enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR,
           enums.ChatMemberStatus.OWNER)


def pick(chat_id, msg_id, idx, bots, n_tries=3, force=False, source=None):
    """Emojis this bot may use for a message ([] = skip this message).

    All bots seed a random generator with the message, so they agree on whether the
    message is picked (chance %) and shuffle the list the same way. Bot number `idx`
    then takes the idx-th emoji, so every bot shows a DIFFERENT emoji on one message.
    """
    rnd = random.Random(f"{chat_id}:{msg_id}")
    if not force and chance < 100 and rnd.random() * 100 >= chance:
        return []
    order = list(source or pool)
    rnd.shuffle(order)
    out = []
    for k in range(n_tries):
        e = order[(idx + k * bots) % len(order)]
        if e not in out:
            out.append(e)
    return out


async def send(message, emoji):
    for form in (emoji, ALT.get(emoji)):
        if not form:
            continue
        try:
            await message.react(form)
            return True
        except INVALID:
            continue
    return False


async def do_react(message, emojis):
    for emoji in emojis:
        try:
            if await send(message, emoji):
                return
        except errors.FloodWait as e:
            if e.value <= 30:
                await asyncio.sleep(e.value)
                try:
                    await send(message, emoji)
                except Exception:
                    pass
            return
        except Exception as e:  # deleted message, no rights, ...
            LOG.debug("react failed: %s", e)
            return


async def react_later(message, emojis):
    await asyncio.sleep(random.uniform(dmin, max(dmin, dmax)))
    await do_react(message, emojis)


async def on_message(client, message):
    if message.chat.id in off:
        return
    emojis = pick(message.chat.id, message.id, client.idx, len(TOKENS))
    if not emojis:
        return
    if dmax > 0:  # wait in the background so the bot can keep reading new messages
        task = asyncio.create_task(react_later(message, emojis))
        _TASKS.add(task)
        task.add_done_callback(_TASKS.discard)
    else:
        await do_react(message, emojis)


async def guard(client, update):
    """Private mode: if someone else adds the bot to a chat, leave it."""
    new, old = update.new_chat_member, update.old_chat_member
    if not new or new.user.id != client.me.id or update.chat.type == enums.ChatType.PRIVATE:
        return
    if new.status in IN_CHAT and not (old and old.status in IN_CHAT):
        adder = update.from_user
        if adder and adder.id != OWNER_ID:
            try:
                await client.leave_chat(update.chat.id)
            except Exception:
                pass


# ------------------------------------------------------------- owner commands
LINK_RE = re.compile(r"(?:https?://)?t\.me/(?:c/(\d+)|([A-Za-z][A-Za-z0-9_]{3,}))((?:/\d+)+)", re.I)


def parse_links(text):
    """[(chat, message_id)] for every post link (t.me/name/12 or t.me/c/123/12)."""
    out = []
    for m in LINK_RE.finditer(text or ""):
        cid, user, path = m.groups()
        item = (int("-100" + cid) if cid else user, int(path.split("/")[-1]))
        if item not in out:
            out.append(item)
    return out[:10]


def delay_text():
    return f"{dmin:g}-{dmax:g}s" if dmax else "Off"


def info():
    return (
        "🤖 **Reaction bot**\n\n"
        f"**Emojis ({len(pool)}) :** {show(pool)}\n"
        f"**Bots reacting :** {len(TOKENS)} (each bot adds 1 reaction per message)\n"
        f"**Chance :** {chance}%\n"
        f"**Delay :** {delay_text()}\n"
        f"**Chats switched off :** {len(off)}\n\n"
        "`/emoji` - **tap to choose** your emojis\n"
        "`/setemoji 🔥 ❤️ 👍 🎉` - or type them\n"
        "`/resetemoji` - back to default\n"
        "`/emojis` - all emojis Telegram allows\n"
        "`/chance 50` - react on 50% of the messages\n"
        "`/delay 1 5` - wait 1 to 5 seconds first (`/delay 0` = off)\n"
        "`/off` and `/on` - inside a group, or in DM: `/off chat_id` | `/off @username` | `/off post_link`\n\n"
        "📎 **Send me a post link** (t.me/channel/123) and all bots react on that post."
    )


async def cmd_info(client, message):
    if message.command[0] == "emojis":
        return await message.reply_text(f"**Allowed emojis :**\n\n{show(ALLOWED)}")
    await message.reply_text(info())


async def cmd_set(client, message):
    global pool
    parts = (message.text or "").split(None, 1)
    emojis = extract(parts[1]) if len(parts) > 1 else []
    if not emojis and len(parts) > 1:
        return await message.reply_text(
            "No allowed emoji found.\n**Example :** `/setemoji 🔥 ❤️ 👍 🎉`\n"
            "Or tap them : /emoji"
        )
    if not emojis:
        return await cmd_panel(client, message)
    pool = emojis
    note = "" if await persist() else "\n\n⚠️ Not saved permanently (set `MONGO_URL` to keep it after restart)."
    await message.reply_text(f"✅ **Saved {len(emojis)} emoji(s) :** {show(emojis)}{note}")


async def cmd_reset(client, message):
    global pool
    pool = list(DEFAULT_POOL)
    await persist()
    await message.reply_text(f"✅ **Default emojis :** {show(pool)}")


async def cmd_chance(client, message):
    global chance
    try:
        value = int(message.command[1])
        assert 1 <= value <= 100
    except Exception:
        return await message.reply_text("Use : `/chance 50` (1 to 100)")
    chance = value
    await persist()
    await message.reply_text(f"✅ **Chance :** {chance}% of the messages")


async def cmd_delay(client, message):
    global dmin, dmax
    try:
        nums = [float(x) for x in message.command[1:3]]
        assert nums and all(0 <= n <= 60 for n in nums)
    except Exception:
        return await message.reply_text("Use : `/delay 1 5` (1 to 5 sec) or `/delay 3` or `/delay 0` (off). Max 60.")
    dmin, dmax = min(nums), max(nums)
    await persist()
    await message.reply_text(f"✅ **Delay :** {delay_text()}")


PAGE, ROW = 42, 7


def emoji_markup(page=0):
    pages = (len(ALLOWED) + PAGE - 1) // PAGE
    page = max(0, min(page, pages - 1))
    chosen = set(pool)
    items = list(enumerate(ALLOWED))[page * PAGE:(page + 1) * PAGE]
    rows = [
        [Btn(ALT.get(e, e) + ("✔" if e in chosen else ""), callback_data=f"EM:t:{i}:{page}")
         for i, e in items[k:k + ROW]]
        for k in range(0, len(items), ROW)
    ]
    nav = [Btn("⬅️", callback_data=f"EM:p:{page - 1}")] if page > 0 else []
    nav.append(Btn(f"{page + 1}/{pages}", callback_data="EM:n"))
    if page < pages - 1:
        nav.append(Btn("➡️", callback_data=f"EM:p:{page + 1}"))
    rows.append(nav)
    rows.append([Btn("✨ Positive set", callback_data=f"EM:a:{page}"),
                 Btn("↩️ Default", callback_data=f"EM:r:{page}")])
    rows.append([Btn("✅ Done", callback_data="EM:d")])
    return Markup(rows)


def emoji_text():
    return (
        "**😀 Choose reaction emojis**\n\n"
        "Tap an emoji to select / unselect it. ✔ = selected.\n"
        f"**Selected ({len(pool)}) :** {show(pool)}\n\nTap **Done** to save."
    )


async def cmd_panel(client, message):
    await message.reply_text(emoji_text(), reply_markup=emoji_markup(0))


async def cb_emoji(client, query):
    global pool
    parts = query.data.split(":")
    act, page = parts[1], 0
    if act == "n":
        return await query.answer()
    if act == "d":
        note = "" if await persist() else "\n\n⚠️ Not saved permanently (set `MONGO_URL`)."
        await query.message.edit_text(f"✅ **Saved {len(pool)} emoji(s) :** {show(pool)}{note}")
        return await query.answer()
    if act == "t":
        e, page = ALLOWED[int(parts[2])], int(parts[3])
        if e in pool:
            if len(pool) == 1:
                return await query.answer("Keep at least one emoji.", show_alert=True)
            pool = [x for x in pool if x != e]
        else:
            pool = pool + [e]
    elif act == "p":
        page = int(parts[2])
    elif act == "a":
        pool, page = list(POSITIVE), int(parts[2])
    elif act == "r":
        pool, page = list(DEFAULT_POOL), int(parts[2])
    await query.answer()
    try:
        await query.message.edit_text(emoji_text(), reply_markup=emoji_markup(page))
    except errors.MessageNotModified:
        pass


_NOTICED = {}


async def private_notice(client, message):
    """Strangers get one short line (max once an hour each), nothing else."""
    now, uid = time.time(), message.from_user.id if message.from_user else 0
    if now - _NOTICED.get(uid, 0) < 3600:
        return
    if len(_NOTICED) > 1000:
        _NOTICED.clear()
    _NOTICED[uid] = now
    await message.reply_text("🔒 This is a private bot. Only the owner can use it.")


async def resolve_chat(client, arg):
    links = parse_links(arg)
    if links:
        arg = links[0][0]
    if isinstance(arg, int) or str(arg).lstrip("-").isdigit():
        return int(arg)
    return (await client.get_chat(str(arg).lstrip("@"))).id


async def cmd_onoff(client, message):
    turn_on = message.command[0] == "on"
    if len(message.command) > 1:
        try:
            chat_id = await resolve_chat(client, message.command[1])
        except Exception:
            return await message.reply_text("Chat not found. Use a chat id, @username or a post link.")
    elif message.chat.type != enums.ChatType.PRIVATE:
        chat_id = message.chat.id
    else:
        return await message.reply_text("Use `/off` inside a group, or `/off chat_id` | `/off @username` | `/off post_link` here.")
    (off.discard if turn_on else off.add)(chat_id)
    await persist()
    await message.reply_text(f"✅ **Reactions {'ON' if turn_on else 'OFF'} for** `{chat_id}`")


async def react_link(client, chat, msg_id, emojis):
    """Put one reaction on a post (needs the bot to be inside that chat)."""
    for emoji in emojis:
        for form in (emoji, ALT.get(emoji)):
            if not form:
                continue
            for attempt in range(2):
                try:
                    await client.send_reaction(chat_id=chat, message_id=msg_id, emoji=form)
                    return emoji
                except INVALID:
                    break
                except errors.FloodWait as e:
                    if attempt or e.value > 30:
                        raise
                    await asyncio.sleep(e.value)
    raise ValueError("ReactionInvalid")


async def cmd_link(client, message):
    links = parse_links(message.text)
    if not links:
        return
    custom = extract(LINK_RE.sub(" ", message.text))  # emojis written next to the link
    lines = []
    for chat, msg_id in links:
        ok, errs = 0, []
        for bot in CLIENTS:
            emojis = pick(chat, msg_id, bot.idx, len(TOKENS), force=True, source=custom)
            try:
                await react_link(bot, chat, msg_id, emojis)
                ok += 1
            except Exception as e:
                errs.append(f"Bot {bot.idx + 1}: {type(e).__name__}")
        lines.append(f"{'✅' if ok else '❌'} `{chat}/{msg_id}` → {ok}/{len(CLIENTS)} bots")
        lines += [f"   ⚠️ {x}" for x in errs[:3]]
    if any(line.startswith("   ⚠️") for line in lines):
        lines.append("\nBots must be members/admins of that chat. For private channel links the bot must have seen a message there since the last restart.")
    await message.reply_text("\n".join(lines))


# ------------------------------------------------------------------- startup
def attach(client, idx):
    client.idx = idx
    client.add_handler(MessageHandler(on_message, (filters.group | filters.channel) & ~filters.service))
    if PRIVATE_MODE:
        client.add_handler(ChatMemberUpdatedHandler(guard))
    if idx == 0:
        me = filters.user(OWNER_ID)
        dm = filters.private & me
        add = client.add_handler
        add(MessageHandler(cmd_info, filters.command(["start", "help", "emojis"]) & dm))
        add(MessageHandler(cmd_set, filters.command("setemoji") & dm))
        add(MessageHandler(cmd_panel, filters.command("emoji") & dm))
        add(CallbackQueryHandler(cb_emoji, filters.regex(r"^EM:") & me))
        add(MessageHandler(private_notice, filters.private & ~me))
        add(MessageHandler(cmd_reset, filters.command("resetemoji") & dm))
        add(MessageHandler(cmd_chance, filters.command("chance") & dm))
        add(MessageHandler(cmd_delay, filters.command("delay") & dm))
        add(MessageHandler(cmd_onoff, filters.command(["on", "off"]) & (filters.private | filters.group) & me))
        add(MessageHandler(cmd_link, dm & filters.text & ~filters.regex(r"^/")))


async def main():
    saved = await asyncio.to_thread(_load) if MONGO_URL else None
    if saved:
        apply(saved)
    for i, token in enumerate(TOKENS):
        client = Client(f"bot{i}", api_id=API_ID, api_hash=API_HASH, bot_token=token,
                        in_memory=True, workers=2)
        attach(client, i)
        try:
            await client.start()
            CLIENTS.append(client)
        except Exception as e:
            LOG.error("Bot %d could not start: %s", i + 1, e)
    if not CLIENTS:
        raise SystemExit("No bot could start. Check BOT_TOKEN.")
    print(f"Running with {len(CLIENTS)} bot(s), {len(pool)} emojis.", flush=True)
    await idle()
    for client in CLIENTS:
        await client.stop()


if __name__ == "__main__":
    LOOP.run_until_complete(main())
