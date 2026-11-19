# Reaction bot (lite)

Reacts to every message in your groups and channels. One file (`main.py`), very small.

## Variables
| Name | Needed | What |
|---|---|---|
| `BOT_TOKEN` | yes | main bot token |
| `OWNER_ID` | yes | your Telegram user id |
| `EXTRA_BOT_TOKENS` | no | more bots, comma separated. Every bot adds ONE different emoji per message |
| `MONGO_URL` | no | remembers settings after restart |
| `EMOJIS` | no | default emojis, e.g. `🔥 ❤️ 👍` |
| `PRIVATE_MODE` | no | `true` (default): bot leaves chats where anyone but you added it |

## Owner commands (send in the bot's DM)
- `/emoji` - **tap to choose** emojis (✔ = selected, then Done)
- `/setemoji 🔥 ❤️ 👍` (type them) / `/resetemoji` / `/emojis`
- `/chance 50` - react on 50% of messages
- `/delay 1 5` - wait 1-5 seconds first (`/delay 0` = off)
- `/off` / `/on` - inside a group, or in DM: `/off chat_id`, `/off @username`, `/off <post link>`
- send a **post link** (`t.me/channel/123`) - every bot reacts on that post. Add emojis next to the link to choose them.

Add every bot to your group, and as admin to your channel.

## Only the owner can use it
Only `OWNER_ID` can run commands or change emojis. Anyone else who messages the bot gets one line saying it is private, and the bot leaves any chat that someone else adds it to.

## Deploy (Railway)
Keep `main.py`, `Dockerfile`, `railway.json`, `requirements.txt` in the **root** of the repo (delete the old project files). `railway.json` already sets the start command.
