# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

"""Small-caps <-> normal text switch (no Telegram imports here)."""
import re

_MAP = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ",
    "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
    "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "ꜱ", "t": "ᴛ", "u": "ᴜ",
    "v": "ᴠ", "w": "ᴡ", "y": "ʏ", "z": "ᴢ",
}
_TO_SC = str.maketrans(_MAP)
_TO_NORMAL = str.maketrans({v: k for k, v in _MAP.items()})

# things that must never be converted: `code`, <tags>, {placeholders},
# (links), urls, @usernames, /commands
_PROTECT = re.compile(
    r"(`[^`]*`|<[^>]+>|\{[^}]*\}|\([^)\s]*[/:][^)\s]*\)|https?://\S+|@\w+|(?<![\w/])/\w+)"
)


def smallcaps(text):
    parts = _PROTECT.split(text)
    return "".join(p if i % 2 else p.lower().translate(_TO_SC) for i, p in enumerate(parts))


def from_smallcaps(text):
    return text.translate(_TO_NORMAL)


class Tr:
    """t("text {x}", x=1) -> text in the bot's chosen style."""

    def __init__(self, small_caps=True):
        self.sc = small_caps

    def __call__(self, text, **kw):
        if self.sc:
            text = smallcaps(text)
        return text.format(**kw) if kw else text

    def v(self, text):
        """Convert a short value/label."""
        return smallcaps(text) if self.sc else text

    def fix(self, text):
        """Text that is already written in small caps (old UI strings)."""
        return text if self.sc else from_smallcaps(text)

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
