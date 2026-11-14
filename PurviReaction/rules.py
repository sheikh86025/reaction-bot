# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

"""Reaction rules that don't need Telegram (easy to test)."""
import random

MODES = ["random", "fixed", "sequence"]
CHANCES = [100, 75, 50, 25, 10]
DELAYS = [(0, 0), (1, 3), (3, 5), (5, 10)]
TYPES = ["text", "photo", "video", "sticker", "voice", "doc", "anim", "other"]

_seq = {}


def msg_kind(m):
    """text / photo / video / sticker / voice / doc / anim / other"""
    if getattr(m, "animation", None):
        return "anim"
    if getattr(m, "sticker", None):
        return "sticker"
    if getattr(m, "photo", None):
        return "photo"
    if getattr(m, "video", None) or getattr(m, "video_note", None):
        return "video"
    if getattr(m, "voice", None) or getattr(m, "audio", None):
        return "voice"
    if getattr(m, "document", None):
        return "doc"
    if getattr(m, "text", None):
        return "text"
    return "other"


def keyword_match(text, keywords):
    if not keywords:
        return True
    low = (text or "").lower()
    return any(k in low for k in keywords)


def chance_ok(chance, rnd=random.random):
    return chance >= 100 or rnd() * 100 < chance


def next_counter(key):
    n = _seq.get(key, 0)
    _seq[key] = n + 1
    return n


def choose(pool, mode, counter):
    if mode == "fixed":
        return pool[0]
    if mode == "sequence":
        return pool[counter % len(pool)]
    return random.choice(pool)


def delay_value(dmin, dmax):
    if not dmax or dmax <= 0:
        return 0
    return random.uniform(dmin, max(dmin, dmax))


def cycle(options, current):
    """Next item after `current` (wraps; unknown -> first)."""
    try:
        return options[(options.index(current) + 1) % len(options)]
    except ValueError:
        return options[0]

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
