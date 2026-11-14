# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

"""Telegram's standard reaction emojis + helpers (no Telegram imports here)."""

VS16 = "\ufe0f"

# Full list of reactions a bot may use (Bot API "ReactionTypeEmoji")
ALLOWED = [
    "👍", "👎", "❤", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬", "😢",
    "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳",
    "❤‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌", "🏆", "💔", "🤨", "😐", "🍓",
    "🍾", "💋", "🖕", "😈", "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈",
    "😇", "😨", "🤝", "✍", "🤗", "🫡", "🎅", "🎄", "☃", "💅", "🤪", "🗿",
    "🆒", "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎", "👾", "🤷‍♂", "🤷", "🤷‍♀",
    "😡",
]
ALLOWED_SET = set(ALLOWED)
_BY_LEN = sorted(ALLOWED, key=len, reverse=True)

# Some emojis may need the "emoji style" selector when sent / shown
ALT = {
    "❤": "❤" + VS16,
    "✍": "✍" + VS16,
    "☃": "☃" + VS16,
    "⚡": "⚡" + VS16,
    "🕊": "🕊" + VS16,
    "❤‍🔥": "❤" + VS16 + "‍🔥",
    "🤷‍♂": "🤷‍♂" + VS16,
    "🤷‍♀": "🤷‍♀" + VS16,
}


def norm(text):
    return text.replace(VS16, "")


def show(emoji):
    """Colourful form for buttons/messages."""
    return ALT.get(emoji, emoji)


def variants(emoji):
    """Forms to try (in order) when sending a reaction."""
    return [emoji] + ([ALT[emoji]] if emoji in ALT else [])


def extract(text):
    """Pick every allowed reaction emoji out of free text, keep order, no dupes."""
    s, out, i = norm(text or ""), [], 0
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


def default_pool(reactions):
    """Owner's config.REACTIONS, cleaned (invalid emojis dropped)."""
    pool = [e for e in dict.fromkeys(norm(x) for x in reactions) if e in ALLOWED_SET]
    return pool or ALLOWED[:12]

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
