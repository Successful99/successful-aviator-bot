# SUCCESSFUL AVIATOR BOT

A Telegram bot that provides sample payout calculations, lets users manually record multipliers, reports descriptive statistics, and sends opt-in scheduled reminders. It does **not** predict crash points.

## Local test

1. Install Python 3.10 or newer.
2. Run `pip install -r requirements.txt`.
3. Set the `BOT_TOKEN` environment variable to the token from Telegram's official @BotFather.
4. Run `python bot.py`.
5. Open your bot in Telegram and send `/start`.

Do not put your token in source code or commit it to a public repository.

## Deploy 24/7 on Render

1. Upload these files to a private GitHub repository.
2. In Render, create a **Background Worker** from that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Add environment variables in Render's dashboard:
   - `BOT_TOKEN` = your private BotFather token
   - `BROADCAST_HOURS` = `6` (optional; default is 6)
6. Deploy and inspect logs. Keep the worker on an always-on plan if continuous operation is required.
7. Open the bot in Telegram, send `/start`, then `/subscribe`.

## Important persistence note

The bot uses SQLite. On hosting providers where worker filesystems are ephemeral, the database may be lost during redeploy/restart. Attach a persistent disk and set `DB_PATH` to a path on that disk, or replace SQLite with a managed PostgreSQL database before relying on long-term history.

## Commands

- `/start`
- `/help`
- `/guide`
- `/record 1.42`
- `/stats`
- `/subscribe`
- `/unsubscribe`

All scheduled messages are opt-in. Historical records do not predict future results.
