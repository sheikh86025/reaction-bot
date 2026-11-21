"""Lightweight reaction bot (single file).

Required variables : BOT_TOKEN, OWNER_ID
Optional variables : EXTRA_BOT_TOKENS (more bots = more reactions per message),
                     EMOJIS, ALLOWED_USERS, MONGO_URL, DB_NAME, PRIVATE_MODE, API_ID, API_HASH
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
ENV_ALLOWED = {int(x) for x in os.getenv("ALLOWED_USERS", "").replace(",", " ").split() if x.lstrip("-").isdigit()}

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
chat_emojis = {}     # chat id -> that chat's own emoji list
co_owners = set(ENV_ALLOWED)  # extra users who may use the bot (the owner is always allowed)
stats = {"total": 0, "bots": {}, "chats": {}, "titles": {}}
STARTED = time.time()
dirty = False        # stats changed since the last save
GAP = 1.1            # seconds between posts when reacting on many posts


def is_admin_id(uid):
    return uid == OWNER_ID or uid in co_owners


async def _admin_filter(_, __, update):
    user = getattr(update, "from_user", None)
    return bool(user and is_admin_id(user.id))


ADMIN = filters.create(_admin_filter)   # owner + co-owners
OWNER = filters.user(OWNER_ID)          # owner only


def bump(bot, chat, title=None):
    """Count one reaction (saved every few minutes)."""
    global dirty
    c, b = str(chat), str(bot.idx)
    stats["total"] += 1
    stats["bots"][b] = stats["bots"].get(b, 0) + 1
    stats["chats"][c] = stats["chats"].get(c, 0) + 1
    if title:
        stats["titles"][c] = str(title)[:40]
    if len(stats["chats"]) > 1500:
        for key in sorted(stats["chats"], key=stats["chats"].get)[:200]:
            stats["chats"].pop(key, None)
            stats["titles"].pop(key, None)
    dirty = True

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


def snapshot():
    """Copy of everything we remember (taken on the main thread, so saving is safe)."""
    return {
        "list": list(pool), "off": sorted(off), "chance": chance, "dmin": dmin, "dmax": dmax,
        "chat_emojis": {str(k): list(v) for k, v in chat_emojis.items()},
        "co_owners": sorted(co_owners - ENV_ALLOWED),
        "stats": {"total": stats["total"], "bots": dict(stats["bots"]),
                  "chats": dict(stats["chats"]), "titles": dict(stats["titles"])},
    }


def _save(data=None):
    try:
        col = _collection()
        if col is None:
            return False
        col.update_one({"_id": "emojis"}, {"$set": data or snapshot()}, upsert=True)
        return True
    except Exception as e:
        LOG.warning("MongoDB write failed: %s", e)
        return False


def apply(doc):
    global pool, off, chance, dmin, dmax, chat_emojis, co_owners
    pool = [e for e in doc.get("list", []) if e in ALLOWED] or pool
    off = set(doc.get("off", []))
    chance = int(doc.get("chance", 100))
    dmin, dmax = doc.get("dmin", 0), doc.get("dmax", 0)
    chat_emojis = {int(k): v for k, v in (doc.get("chat_emojis") or {}).items()
                   if [e for e in v if e in ALLOWED]}
    co_owners = set(ENV_ALLOWED) | set(doc.get("co_owners", []))
    st = doc.get("stats") or {}
    stats["total"] = int(st.get("total", 0))
    for key in ("bots", "chats", "titles"):
        stats[key] = dict(st.get(key) or {})


async def persist():
    return await asyncio.to_thread(_save, snapshot()) if MONGO_URL else False


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
    order = list(source or chat_emojis.get(chat_id) or pool)
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


class NoReaction(Exception):
    """The chat refused every emoji (message shown to the owner)."""

    def __init__(self, text, hard=True):
        super().__init__(text)
        self.hard = hard   # False = only this post refused (e.g. a service message)


_ALLOWED = {}  # chat -> (time, None = anything / [] = reactions off / [emojis])


def cached(chat):
    hit = _ALLOWED.get(chat)
    return (True, hit[1]) if hit and time.time() - hit[0] < 600 else (False, None)


async def allowed_reactions(client, chat):
    """Emojis the chat allows: None = anything (or unknown), [] = reactions are off."""
    known, res = cached(chat)
    if known:
        return res
    try:
        ar = (await client.get_chat(chat)).available_reactions
    except Exception:
        return None
    if ar is None:
        res = []
    elif getattr(ar, "all_are_enabled", False):
        res = None
    else:
        res = [e.replace(VS16, "") for e in (getattr(r, "emoji", None) for r in ar.reactions or []) if e]
    if len(_ALLOWED) > 500:
        _ALLOWED.clear()
    _ALLOWED[chat] = (time.time(), res)
    return res


def fit(allowed, idx, bots, source=None):
    """Our emojis that the chat allows, rotated per bot (max 3)."""
    ours = list(dict.fromkeys(e for e in list(source or pool) + POSITIVE if e in allowed))
    if not ours:
        return []
    k = idx % len(ours)
    return (ours[k:] + ours[:k])[:3]


async def do_react(client, message, emojis):
    tried = set()
    for attempt in range(2):  # 2nd round uses the emojis the chat really allows
        for emoji in emojis:
            tried.add(emoji)
            try:
                if await send(message, emoji):
                    return bump(client, message.chat.id, message.chat.title)
            except errors.FloodWait as e:
                if e.value <= 30:
                    await asyncio.sleep(e.value)
                    try:
                        if await send(message, emoji):
                            bump(client, message.chat.id, message.chat.title)
                    except Exception:
                        pass
                return
            except Exception as e:  # deleted message, no rights, ...
                LOG.debug("react failed: %s", e)
                return
        allowed = await allowed_reactions(client, message.chat.id) if attempt == 0 else None
        emojis = [e for e in fit(allowed, client.idx, len(TOKENS), chat_emojis.get(message.chat.id))
                  if e not in tried] if allowed else []
        if not emojis:
            return


async def react_later(client, message, emojis):
    await asyncio.sleep(random.uniform(dmin, max(dmin, dmax)))
    await do_react(client, message, emojis)


async def on_message(client, message):
    chat = message.chat.id
    if chat in off:
        return
    known, allowed = cached(chat)
    if known and allowed == []:  # reactions are switched off in this chat
        return
    emojis = pick(chat, message.id, client.idx, len(TOKENS))
    if not emojis:
        return
    if known and allowed:
        emojis = [e for e in emojis if e in allowed] or fit(allowed, client.idx, len(TOKENS), chat_emojis.get(chat))
    if dmax > 0:  # wait in the background so the bot can keep reading new messages
        task = asyncio.create_task(react_later(client, message, emojis))
        _TASKS.add(task)
        task.add_done_callback(_TASKS.discard)
    else:
        await do_react(client, message, emojis)


async def guard(client, update):
    """Private mode: if someone else adds the bot to a chat, leave it."""
    new, old = update.new_chat_member, update.old_chat_member
    if not new or new.user.id != client.me.id or update.chat.type == enums.ChatType.PRIVATE:
        return
    if new.status in IN_CHAT and not (old and old.status in IN_CHAT):
        adder = update.from_user
        if adder and not is_admin_id(adder.id):
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
        f"**Chance :** {chance}%  •  **Delay :** {delay_text()}\n"
        f"**Chats off :** {len(off)}  •  **Chats with own emojis :** {len(chat_emojis)}\n\n"
        "**Emojis**\n"
        "`/emoji` - tap to choose (all chats)\n"
        "`/setemoji 🔥 ❤️ 👍` - or type them  •  `/resetemoji`\n"
        "`/chatemoji` - own emojis for ONE chat (in the chat, or DM: `/chatemoji @name`)\n"
        "`/chatemojis` - chats that have own emojis  •  `/emojis` - all allowed\n\n"
        "**Control**\n"
        "`/chance 50`  •  `/delay 1 5`  •  `/off` `/on` (in a chat, or DM + id/@name/link)\n"
        "`/stats` - reactions done\n\n"
        "**Posts**\n"
        "Send a post link - all bots react on it\n"
        "`/last post_link 10` - react on that post and the 9 before it\n"
        "`/remove post_link 10` - remove the bots' reactions from them\n\n"
        "**Co-owners** (owner only): `/allow user_id` • `/disallow user_id` • `/allowed`"
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


def get_list(scope):
    return pool if scope == "g" else (chat_emojis.get(scope) or pool)


def set_list(scope, emojis):
    """scope 'g' = every chat, a chat id = that chat only (None = back to the main list)."""
    global pool
    if scope == "g":
        pool = emojis
    elif emojis is None:
        chat_emojis.pop(scope, None)
    else:
        chat_emojis[scope] = emojis


def emoji_markup(page=0, scope="g"):
    pages = (len(ALLOWED) + PAGE - 1) // PAGE
    page = max(0, min(page, pages - 1))
    chosen = set(get_list(scope))
    items = list(enumerate(ALLOWED))[page * PAGE:(page + 1) * PAGE]
    rows = [
        [Btn(ALT.get(e, e) + ("✔" if e in chosen else ""), callback_data=f"EM:{scope}:t:{i}:{page}")
         for i, e in items[k:k + ROW]]
        for k in range(0, len(items), ROW)
    ]
    nav = [Btn("⬅️", callback_data=f"EM:{scope}:p:{page - 1}")] if page > 0 else []
    nav.append(Btn(f"{page + 1}/{pages}", callback_data=f"EM:{scope}:n"))
    if page < pages - 1:
        nav.append(Btn("➡️", callback_data=f"EM:{scope}:p:{page + 1}"))
    rows.append(nav)
    rows.append([Btn("✨ Positive set", callback_data=f"EM:{scope}:a:{page}"),
                 Btn("↩️ Default" if scope == "g" else "↩️ Main list", callback_data=f"EM:{scope}:r:{page}")])
    rows.append([Btn("✅ Done", callback_data=f"EM:{scope}:d")])
    return Markup(rows)


def emoji_text(scope="g"):
    cur = get_list(scope)
    where = "**all chats**" if scope == "g" else f"chat `{scope}`" + ("" if scope in chat_emojis else " (now uses the main list)")
    return (
        f"**😀 Choose reaction emojis for** {where}\n\n"
        "Tap an emoji to select / unselect it. ✔ = selected.\n"
        f"**Selected ({len(cur)}) :** {show(cur)}\n\nTap **Done** to save."
    )


async def cmd_panel(client, message):
    await message.reply_text(emoji_text(), reply_markup=emoji_markup(0))


async def cb_emoji(client, query):
    parts = query.data.split(":")
    scope = "g" if parts[1] == "g" else int(parts[1])
    act, page = parts[2], 0
    if act == "n":
        return await query.answer()
    if act == "d":
        note = "" if await persist() else "\n\n⚠️ Not saved permanently (set `MONGO_URL`)."
        cur = get_list(scope)
        await query.message.edit_text(f"✅ **Saved {len(cur)} emoji(s) :** {show(cur)}{note}")
        return await query.answer()
    if act == "t":
        e, page = ALLOWED[int(parts[3])], int(parts[4])
        cur = list(get_list(scope))
        if e in cur:
            if len(cur) == 1:
                return await query.answer("Keep at least one emoji.", show_alert=True)
            cur.remove(e)
        else:
            cur.append(e)
        set_list(scope, cur)
    elif act == "p":
        page = int(parts[3])
    elif act == "a":
        set_list(scope, list(POSITIVE)); page = int(parts[3])
    elif act == "r":
        set_list(scope, list(DEFAULT_POOL) if scope == "g" else None); page = int(parts[3])
    await query.answer()
    try:
        await query.message.edit_text(emoji_text(scope), reply_markup=emoji_markup(page, scope))
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


async def put(client, chat, msg_id, emoji):
    """One reaction on a post. True = done, False = Telegram refused this emoji."""
    for form in (emoji, ALT.get(emoji)):
        if not form:
            continue
        for attempt in range(2):
            try:
                await client.send_reaction(chat_id=chat, message_id=msg_id, emoji=form)
                return True
            except INVALID:
                break
            except errors.FloodWait as e:
                if attempt or e.value > 30:
                    raise
                await asyncio.sleep(e.value)
    return False


async def react_link(client, chat, msg_id, emojis, source=None):
    for emoji in emojis:
        if await put(client, chat, msg_id, emoji):
            bump(client, chat)
            return emoji
    allowed = await allowed_reactions(client, chat)  # ask the chat what it allows
    if allowed == []:
        raise NoReaction("reactions are turned off in that chat")
    if allowed:
        for emoji in fit(allowed, client.idx, len(TOKENS), source):
            if emoji not in emojis and await put(client, chat, msg_id, emoji):
                bump(client, chat)
                return emoji
        raise NoReaction("that chat allows only " + show(allowed[:10]))
    raise NoReaction("Telegram refused these emojis", hard=False)


async def cmd_link(client, message):
    links = parse_links(message.text)
    if not links:
        return
    custom = extract(LINK_RE.sub(" ", message.text))  # emojis written next to the link
    lines, hard = [], False
    for chat, msg_id in links:
        ok, errs = 0, []
        own = custom or chat_emojis.get(await chat_key(client, chat)) or None
        for bot in CLIENTS:
            emojis = pick(chat, msg_id, bot.idx, len(TOKENS), force=True, source=own)
            try:
                await react_link(bot, chat, msg_id, emojis, own)
                ok += 1
            except Exception as e:
                errs.append(f"Bot {bot.idx + 1}: {e if isinstance(e, NoReaction) else type(e).__name__}")
                hard = hard or not isinstance(e, NoReaction)
        lines.append(f"{'✅' if ok else '❌'} `{chat}/{msg_id}` → {ok}/{len(CLIENTS)} bots")
        lines += [f"   ⚠️ {x}" for x in errs[:3]]
    if hard:
        lines.append("\nBots must be members/admins of that chat. For private channel links the bot must have seen a message there since the last restart.")
    await message.reply_text("\n".join(lines))


_IDS = {}


async def chat_key(client, ref):
    """Numeric chat id for a link's chat (only looked up when chats have own emojis)."""
    if isinstance(ref, int) or not chat_emojis:
        return ref
    if ref not in _IDS:
        try:
            _IDS[ref] = (await client.get_chat(ref)).id
        except Exception:
            _IDS[ref] = ref
    return _IDS[ref]


async def cmd_chatemoji(client, message):
    """Own emojis for one chat. In the chat: /chatemoji [emojis|reset]. In DM: /chatemoji target [emojis|reset]."""
    args = (message.text or "").split(None, 2)
    if message.chat.type == enums.ChatType.PRIVATE:
        if len(args) < 2:
            return await message.reply_text(
                "Use : `/chatemoji @channel` (tap) or `/chatemoji chat_id 🔥 ❤️` or `/chatemoji post_link reset`")
        try:
            chat = await resolve_chat(client, args[1])
        except Exception:
            return await message.reply_text("Chat not found. Use a chat id, @username or a post link.")
        rest = args[2] if len(args) > 2 else ""
    else:
        chat, rest = message.chat.id, " ".join(args[1:])
    if rest.strip().lower() == "reset":
        chat_emojis.pop(chat, None)
        await persist()
        return await message.reply_text(f"✅ Chat `{chat}` uses the main emoji list again.")
    emojis = extract(rest)
    if emojis:
        chat_emojis[chat] = emojis
        note = "" if await persist() else "\n\n⚠️ Not saved permanently (set `MONGO_URL`)."
        return await message.reply_text(f"✅ **Chat** `{chat}` **:** {show(emojis)}{note}")
    if rest.strip():
        return await message.reply_text("No allowed emoji found. Example : `/chatemoji 🔥 ❤️ 👍`")
    await message.reply_text(emoji_text(chat), reply_markup=emoji_markup(0, chat))


async def cmd_chatemojis(client, message):
    if not chat_emojis:
        return await message.reply_text("No chat has its own emojis. Set one with /chatemoji")
    rows = [f"`{c}` : {show(e[:8])}" + (" …" if len(e) > 8 else "") for c, e in chat_emojis.items()]
    await message.reply_text("**Chats with own emojis :**\n\n" + "\n".join(rows[:60]))


async def cmd_allow(client, message):
    """Co-owners can use the bot (owner only)."""
    cmd = message.command[0]
    if cmd == "allowed":
        ids = [OWNER_ID] + sorted(co_owners)
        return await message.reply_text("**Allowed users :**\n" + "\n".join(f"• `{u}`" + (" (owner)" if u == OWNER_ID else "") for u in ids))
    try:
        uid = int(message.command[1])
    except Exception:
        return await message.reply_text(f"Use : `/{cmd} user_id`")
    if uid == OWNER_ID:
        return await message.reply_text("That is the owner already.")
    if cmd == "allow":
        co_owners.add(uid)
    elif uid in ENV_ALLOWED:
        return await message.reply_text("That id is in the `ALLOWED_USERS` variable. Remove it there.")
    else:
        co_owners.discard(uid)
    await persist()
    await message.reply_text(f"✅ `{uid}` {'can use the bot now' if cmd == 'allow' else 'removed'}.")


def _clean(x):
    return "".join(c for c in str(x) if c not in "*_`[]<>~|")


async def cmd_stats(client, message):
    up = int(time.time() - STARTED)
    bots = " • ".join(f"Bot {int(k) + 1}: {v}" for k, v in sorted(stats["bots"].items(), key=lambda kv: int(kv[0])))
    top = sorted(stats["chats"].items(), key=lambda kv: -kv[1])[:5]
    rows = [f"{i}. {_clean(stats['titles'].get(c, c))} : {n}" for i, (c, n) in enumerate(top, 1)]
    await message.reply_text(
        "📊 **Stats**\n\n"
        f"**Reactions :** {stats['total']}\n"
        f"**Bots running :** {len(CLIENTS)}/{len(TOKENS)}" + (f"\n{bots}" if bots else "") + "\n"
        f"**Chats counted :** {len(stats['chats'])}\n"
        f"**Running for :** {up // 86400}d {up % 86400 // 3600}h {up % 3600 // 60}m"
        + ("\n\n**Top chats**\n" + "\n".join(rows) if rows else "")
    )


SKIP = tuple(getattr(errors, n) for n in ("MessageIdInvalid", "MessageNotFound") if hasattr(errors, n))


async def range_bot(bot, chat, start, count, remove, source):
    """One bot: react on (or remove its reaction from) posts start, start-1, ..."""
    done = skipped = 0
    err = None
    for k in range(count):
        mid = start - k
        if mid < 1:
            break
        try:
            if remove:
                await bot.send_reaction(chat_id=chat, message_id=mid)
            else:
                await react_link(bot, chat, mid, pick(chat, mid, bot.idx, len(TOKENS), force=True, source=source), source)
            done += 1
        except SKIP:  # deleted post
            skipped += 1
        except NoReaction as e:
            if e.hard:
                err = str(e)
                break
            skipped += 1
        except Exception as e:
            err = type(e).__name__
            break
        if k < count - 1:
            await asyncio.sleep(GAP)
    return done, skipped, err


async def range_work(client, status, chat, start, count, remove, custom):
    try:
        source = custom or chat_emojis.get(await chat_key(client, chat)) or None
        res = await asyncio.gather(*(range_bot(b, chat, start, count, remove, source) for b in CLIENTS))
        lines = [f"{'🧹 Removed' if remove else '✅ Reacted'} on `{chat}` posts {start} → {max(start - count + 1, 1)}\n"]
        for bot, (done, skipped, err) in zip(CLIENTS, res):
            lines.append(f"Bot {bot.idx + 1}: {done} done" + (f", {skipped} skipped" if skipped else "") + (f"\n   ⚠️ {err}" if err else ""))
        if any(err and err not in ("FloodWait",) and not err.startswith(("reactions", "that chat")) for _, _, err in res):
            lines.append("\nBots must be members/admins of that chat.")
        await status.edit_text("\n".join(lines))
    except Exception as e:
        await status.edit_text(f"❌ {type(e).__name__}")


async def cmd_range(client, message):
    """/last post_link [N]  - react on that post and the N-1 before it.  /remove post_link [N] - take the reactions back."""
    remove = message.command[0] == "remove"
    links = parse_links(message.text)
    if not links:
        return await message.reply_text(
            f"Use : `/{message.command[0]} https://t.me/channel/123 10`\n"
            "Send the link of the **newest** post, then how many posts (max 50).")
    nums = [int(x) for x in message.command[1:] if x.isdigit()]
    count = max(1, min(nums[0] if nums else (1 if remove else 10), 50))
    chat, start = links[0]
    custom = [] if remove else extract(LINK_RE.sub(" ", message.text))
    status = await message.reply_text(f"⏳ {'Removing' if remove else 'Reacting on'} {count} post(s)...")
    task = asyncio.create_task(range_work(client, status, chat, start, count, remove, custom))
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)


async def stats_loop():
    global dirty
    while True:
        await asyncio.sleep(300)
        if dirty and MONGO_URL:
            dirty = False
            await persist()


# ------------------------------------------------------------------- startup
def attach(client, idx):
    client.idx = idx
    client.add_handler(MessageHandler(on_message, (filters.group | filters.channel) & ~filters.service))
    if PRIVATE_MODE:
        client.add_handler(ChatMemberUpdatedHandler(guard))
    if idx == 0:
        dm = filters.private & ADMIN
        add = client.add_handler
        add(MessageHandler(cmd_info, filters.command(["start", "help", "emojis"]) & dm))
        add(MessageHandler(cmd_set, filters.command("setemoji") & dm))
        add(MessageHandler(cmd_panel, filters.command("emoji") & dm))
        add(CallbackQueryHandler(cb_emoji, filters.regex(r"^EM:") & ADMIN))
        add(MessageHandler(private_notice, filters.private & ~ADMIN))
        add(MessageHandler(cmd_reset, filters.command("resetemoji") & dm))
        add(MessageHandler(cmd_chance, filters.command("chance") & dm))
        add(MessageHandler(cmd_delay, filters.command("delay") & dm))
        add(MessageHandler(cmd_onoff, filters.command(["on", "off"]) & (filters.private | filters.group) & ADMIN))
        add(MessageHandler(cmd_chatemoji, filters.command("chatemoji") & (filters.private | filters.group) & ADMIN))
        add(MessageHandler(cmd_chatemojis, filters.command("chatemojis") & dm))
        add(MessageHandler(cmd_stats, filters.command("stats") & dm))
        add(MessageHandler(cmd_range, filters.command(["last", "remove"]) & dm))
        add(MessageHandler(cmd_allow, filters.command(["allow", "disallow", "allowed"]) & filters.private & OWNER))
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
    saver = asyncio.create_task(stats_loop())
    await idle()
    saver.cancel()
    if dirty:
        await persist()
    for client in CLIENTS:
        await client.stop()


if __name__ == "__main__":
    LOOP.run_until_complete(main())
