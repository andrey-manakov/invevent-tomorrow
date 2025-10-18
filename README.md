# InvEvent Telegram Bot

InvEvent is a minimalistic Telegram bot that helps friends coordinate plans for tomorrow. Users can create quick one-time plans, share them with friends, and join each other's events through deep links. Friendships are created automatically whenever someone opens a shared event link.

## Features

- Button-driven wizard for creating plans scheduled for tomorrow.
- Share-to-add friendship flow using one-time deep links.
- View, edit, delete, and share your own plans.
- Browse friends' plans and join them with a single tap.
- Automatic plan expiry once the scheduled time has passed.
- SQLite storage with automatic schema initialization.

## Requirements

- Python 3.10+
- Telegram bot token (from [@BotFather](https://t.me/BotFather))

## Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd invevent-tomorrow
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   Copy the example environment file and fill in your values.
   ```bash
   cp .env.example .env
   ```

   | Variable | Description |
   |----------|-------------|
   | `BOT_TOKEN` | Telegram bot token from BotFather |
   | `BOT_USERNAME` | Public username of your bot (without `@`) |
   | `DB_PATH` | Path to the SQLite database file |
   | `SHARE_TOKEN_TTL_HOURS` | Lifetime of share links (default `48`) |

5. **Run the bot**
   ```bash
   python -m invEvent.bot
   ```

The database schema is created automatically on the first run.

## Deployment on RUVDS (Linux VPS)

1. SSH into your VPS and install system dependencies:
   ```bash
   sudo apt update
   sudo apt install python3 python3-venv python3-pip
   ```

2. Clone the project and set up the environment (use the same steps as above).

3. Create a systemd service unit `/etc/systemd/system/invevent.service`:
   ```ini
   [Unit]
   Description=InvEvent Telegram Bot
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/opt/invevent
   EnvironmentFile=/opt/invevent/.env
   ExecStart=/opt/invevent/.venv/bin/python -m invEvent.bot
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

4. Reload systemd and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable invevent.service
   sudo systemctl start invevent.service
   sudo systemctl status invevent.service
   ```

Logs are available through `journalctl -u invevent.service`.

## Project Structure

```
invEvent/
  bot.py           # Main entry point and bot handlers
  config.py        # Environment configuration loader
  db.py            # SQLite access helpers and migrations
  models.py        # Dataclasses for core entities
  keyboards.py     # Inline keyboard builders
  views.py         # Formatting helpers for plan cards
  services/
      users.py     # User registration and friendship helpers
      plans.py     # Plan CRUD and querying logic
      sharing.py   # Share token generation and redemption
      timeutil.py  # Time helpers
```

## Development Tips

- Use `python -m invEvent.bot` during development; the bot uses long polling.
- Telebot's built-in logging can be enabled by setting the `TELEBOT_LOG_LEVEL` environment variable.
- SQLite database files can be inspected with `sqlite3 <DB_PATH>`. The schema is maintained automatically.

## License

This project is provided as-is for the InvEvent concept demonstration.
