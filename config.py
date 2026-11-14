# =======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 🚀

# This source code is under MIT License 📜 Unauthorized forking, importing, or using this code without giving proper credit will result in legal action ⚠️
 
# 📩 DM for permission : @TheSigmaCoder
# =======================================================

from os import getenv
from dotenv import load_dotenv

load_dotenv()

API_ID = int(getenv("API_ID", "6435225"))
API_HASH = getenv("API_HASH", "4e984ea35f854762dcde906dce426c2d")
BOT_TOKEN = getenv("BOT_TOKEN", None)
MONGO_URL = getenv("MONGO_URL", None)

DB_NAME = getenv("DB_NAME", "purvi")
OWNER_ID = int(getenv("OWNER_ID", "0"))
if not OWNER_ID:
    raise SystemExit("OWNER_ID is not set. Add your Telegram user id in the variables.")
UPDATE_CHNL = "offerkingdom"

# Private bot: only OWNER_ID (+ ALLOWED_USERS) can use it, only approved chats get reactions
PRIVATE_MODE = getenv("PRIVATE_MODE", "true").strip().lower() in ("1", "true", "yes", "on")
ALLOWED_USERS = [
    int(x) for x in getenv("ALLOWED_USERS", "").replace(",", " ").split() if x.lstrip("-").isdigit()
]

# Days a cloned bot stays active (0 = lifetime). Owner can extend with /premium
CLONE_DAYS = int(getenv("CLONE_DAYS", "0"))

REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "🙏", "👌",
    "😍", "💯", "🤣", "⚡", "🏆", "💘", "😘", "😎", "🤗", "🆒",
]

# ======================================================
# ©️ 2025-26 All Rights Reserved by Purvi Bots (Im-Notcoder) 😎

# 🧑‍💻 Developer : t.me/TheSigmaCoder
# 🔗 Source link : GitHub.com/Im-Notcoder/Purvi-Reaction
# 📢 Telegram channel : t.me/Purvi_Bots
# =======================================================
