# Telegram Refreshment Rotation Bot (RefBot)

A Telegram bot that automates the management of weekly refreshment duties for standing meetings.

## Features

- 🔄 Automated rotation management for weekly duties
- 📱 Direct message notifications via Telegram
- ✅ Confirmation/decline system with 24-hour response window
- 🔀 Smart fallback logic for declined assignments
- 👮 Admin controls for manual overrides
- 📊 Status tracking and reporting

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (obtain from [@BotFather](https://t.me/botfather))
- macOS, Linux, or Windows environment

### Installation

1. **Clone or create the project structure:**
```bash
# Run the setup script to create project structure
bash setup.sh
cd refbot
```

2. **Set up Python virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install python-telegram-bot==21.3 APScheduler==3.10.4 python-dotenv==1.0.0 pytz
```

4. **Configure the bot:**

Create `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_