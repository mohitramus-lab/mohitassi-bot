# 🤖 All-in-One Telegram Manager Bot

A powerful Telegram bot for managing payments, auto-replies, contacts, scheduled messages, and chat organisation.

---

## 🚀 Quick Setup (5 Steps)

### Step 1 – Get Your Bot Token
1. Open Telegram and message `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy your **bot token**

### Step 2 – Get Your Telegram ID
1. Message `@userinfobot` on Telegram
2. Copy your numeric **user ID**

### Step 3 – Edit config.py
```python
BOT_TOKEN = "paste_your_token_here"
OWNER_ID  = 123456789       # your numeric ID
TIMEZONE  = "Asia/Karachi"  # your timezone
```

### Step 4 – Install & Run Locally
```bash
pip install -r requirements.txt
python bot.py
```

### Step 5 – Deploy to Cloud (24/7)

**Option A: Railway.app (Free)**
1. Create account at railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Push your bot folder to GitHub first
4. Set env variable: `BOT_TOKEN=your_token`

**Option B: VPS (DigitalOcean / Hostinger)**
```bash
# Upload files to server
scp -r telegram_bot/ user@your_server_ip:~/

# On server:
sudo apt install python3 python3-pip -y
pip3 install -r requirements.txt

# Run as background service
nohup python3 bot.py &

# OR use screen:
screen -S bot
python3 bot.py
# Ctrl+A then D to detach
```

**Option C: Docker**
```bash
docker build -t mybot .
docker run -d --restart always --name mybot mybot
```

---

## 📋 Full Command Reference

### 💰 Payment Management
| Command | Description |
|---------|-------------|
| `/token TKN-001` | Register payment token |
| `/confirm TKN-001` | Confirm payment received |
| `/reject TKN-001` | Reject payment |
| `/payments` | List all payments |
| `/payments pending` | Filter by status |

### 🤖 Auto-Reply
| Command | Description |
|---------|-------------|
| `/addreply hello \| Hi! How can I help?` | Add keyword auto-reply |
| `/addreply rate \| Our rate is X \| exact` | Exact match |
| `/listreplies` | View all auto-replies |
| `/delreply 3` | Delete reply ID 3 |
| `/autoreplyon` | Enable auto-reply |
| `/autoreplyoff` | Disable auto-reply |

### 👥 Contacts & Broadcast
| Command | Description |
|---------|-------------|
| `/addcontact Ali \| @ali123 \| client` | Add contact |
| `/contacts` | List all contacts |
| `/contacts client` | Filter by label |
| `/contact ali` | Search contact |
| `/broadcast client \| New offer!` | Message all clients |
| `/delcontact 5` | Delete contact ID 5 |

### ⏰ Scheduler
| Command | Description |
|---------|-------------|
| `/schedule 123 \| 2024-12-25 09:00 \| Merry Christmas!` | Schedule message |
| `/schedule 123 \| 2024-12-01 08:00 \| Good morning! \| daily` | Daily repeat |
| `/schedules` | View pending schedules |
| `/cancelschedule 3` | Cancel schedule ID 3 |

### 🗂 Chat Organiser
| Command | Description |
|---------|-------------|
| `/tag here \| VIP Client` | Tag current chat |
| `/tag -1001234 \| Supplier` | Tag by chat ID |
| `/chats` | View all tagged chats |
| `/chats VIP` | Filter by tag |
| `/note Payment Record \| Ali paid 50k` | Save a note |
| `/notes` | View all notes |
| `/pin Important Info \| Bank details here` | Pin a note |
| `/delnote 4` | Delete note ID 4 |

### 📈 Content Agent (Viral Finance Ideas)
Your in-house marketing strategist for the stock-market / trading / "make money"
niche. It studies what goes viral on Instagram, YouTube Shorts, TikTok and X and
turns it into ready-to-shoot daily content ideas (hook + format + angle + CTA +
hashtags). It also auto-DMs the owner a fresh batch every morning.

| Command | Description |
|---------|-------------|
| `/ideas` | Today's curated batch of viral content ideas |
| `/idea` | One fresh idea now (add a topic, e.g. `/idea options`) |
| `/hook` | Scroll-stopping opening lines (add a topic) |
| `/calendar` | A 7-day content plan |
| `/contenthelp` | How the content agent works |

> Auto-delivery time and posting-window tips live in `content.py`
> (`DAILY_HOUR` / `DAILY_MIN`). Edit them to fit your audience.

### 👑 Team Management
| Command | Description |
|---------|-------------|
| `/addteam 987654321 Sarah` | Add team member |
| `/removeteam 987654321` | Remove team member |
| `/team` | List team members |
| `/stats` | Bot statistics |

---

## 💡 Tips

- **Payment Workflow**: Register token → Share bot with party → Party sends photo with token in caption → You get notified → Confirm/Reject
- **Auto-Reply**: Set keywords like "price", "rate", "hello" to respond automatically when you're busy
- **Broadcast**: Add all clients with label "client" and broadcast offers in one command
- **Timezone**: Set your timezone in config.py for correct scheduled times

---

## 🔒 Security
- Only Owner and Team members can use commands
- Customers/parties can only send payment photos and receive auto-replies
- All data stored locally in SQLite database (bot_data.db)
