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
| `ALLOWED_USERS` | no | co-owner user ids, comma separated |
| `PRIVATE_MODE` | no | `true` (default): bot leaves chats where anyone but you added it |

## Commands (send in the bot's DM; the owner and co-owners can use them)
**Emojis**
- `/emoji` - tap to choose emojis for all chats (✔ = selected, then Done)
- `/setemoji 🔥 ❤️ 👍` (type them) / `/resetemoji` / `/emojis` (all allowed)
- `/chatemoji` - own emojis for ONE chat. In the chat: `/chatemoji` (tap) or `/chatemoji 🔥 ❤️` or `/chatemoji reset`. In DM: `/chatemoji @channel`, `/chatemoji chat_id 🔥 ❤️`, `/chatemoji post_link reset`
- `/chatemojis` - chats that have their own emojis

**Control**
- `/chance 50` - react on 50% of messages
- `/delay 1 5` - wait 1-5 seconds first (`/delay 0` = off)
- `/off` / `/on` - inside a group, or in DM: `/off chat_id`, `/off @username`, `/off <post link>`
- `/stats` - reactions done, per bot, top chats

**Posts**
- send a **post link** (`t.me/channel/123`) - every bot reacts on that post. Add emojis next to the link to choose them.
- `/last <link of the newest post> 10` - react on that post and the 9 before it (max 50)
- `/remove <post link> 10` - remove the bots' reactions from those posts (default 1)

**Co-owners** (owner only): `/allow user_id`, `/disallow user_id`, `/allowed`. You can also set the `ALLOWED_USERS` variable.

Telegram does not let bots read a channel's history, so `/last` needs the link of the newest post and counts backwards from it.

## Only the owner can use it
Only `OWNER_ID` and the co-owners can run commands or change emojis. Anyone else who messages the bot gets one line saying it is private, and the bot leaves any chat that someone else (not owner/co-owner) adds it to.

## Deploy (Railway)
Keep `main.py`, `Dockerfile`, `railway.json`, `requirements.txt` in the **root** of the repo (delete the old project files). `railway.json` already sets the start command.
