# What's new

**Emoji choice** – `/settings` > 😀 Emojis (tap to select), or `/setreactions 🔥 ❤️ 🤣`. `/emojis` lists all allowed ones.
**Per chat** – mode (random/fixed/sequence), chance %, delay, message-type filters, keywords, ignore list / ignore admins, on/off for groups, channels and DMs.
**Owner** – `/setstart`, `/setphoto`, `/resetstart`, `/style`, `/defaultreactions`, `/ban` `/unban` `/banlist`, `/gban` `/ungban` `/gbanlist` (main owner), `/topchats`, `/premium`, `/expiring`.
**Users** – `/rstats`, `/myclone`.
**Clones** – set `CLONE_DAYS` (0 = lifetime). Expired clones stop automatically; renew with `/premium @bot 30` or `/premium @bot lifetime`.

Each clone has its own settings (emojis, style, start text, bans, stats).

## Private mode (default ON)
- Only `OWNER_ID` (and `ALLOWED_USERS`) can use the bot. Everyone else is ignored.
- Bot reacts only in **approved chats**. If you add it to a chat it is approved automatically; if anyone else adds it, it leaves.
- Already added chats: send `/approveall` in the bot's DM once. Others: `/approve` in the chat, `/unapprove`, `/approved`.
- Cloning and the "must join channel" check are off in private mode.
- Set `PRIVATE_MODE=false` to make it public again.
- Default emoji list is now positive only.
