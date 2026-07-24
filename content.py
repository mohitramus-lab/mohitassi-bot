# ─────────────────────────────────────────────────────────────
#  content.py  –  "The Viral Finance Content Agent"
#
#  A built-in marketing expert for the stock / financial markets
#  niche. It thinks like a top social-media growth strategist who
#  studies what goes viral on Instagram, YouTube Shorts, TikTok,
#  X (Twitter) and Facebook — and turns that into ready-to-shoot
#  daily content ideas for trading, investing and "make money"
#  content.
#
#  Commands (owner / team only):
#     /idea            – one full viral content idea right now
#     /ideas           – today's batch of daily content ideas
#     /hook  <topic>   – a scroll-stopping hook (optional topic)
#     /calendar        – a 7-day content plan
#     /contenthelp     – how the agent works
#
#  It also auto-delivers a fresh batch to the owner every morning
#  (see send_daily_ideas + the run_daily job wired in bot.py).
# ─────────────────────────────────────────────────────────────

import random
from datetime import datetime, time, timedelta

import pytz
from telegram import Update
from telegram.ext import ContextTypes

from config import TIMEZONE, OWNER_ID
from utils import is_team_member

# When the daily batch is auto-sent (local hour, 24h). Edit freely.
DAILY_HOUR = 8
DAILY_MIN = 30


def _tz():
    try:
        return pytz.timezone(TIMEZONE)
    except Exception:
        return pytz.utc


# ─────────────────────────────────────────────────────────────
#  THE MARKETING BRAIN
#  These libraries are the "expert knowledge". Each piece is
#  written to be genuinely scroll-stopping in the finance niche.
#  (No markdown metachars like * _ ` [ ] inside strings so the
#   Telegram Markdown parser never breaks.)
# ─────────────────────────────────────────────────────────────

# Themes rotate day-by-day so the well never runs dry.
THEMES = [
    "Beginner mistakes that quietly kill accounts",
    "The psychology of why traders lose",
    "Turning a small account into a big one (realistically)",
    "Reading the market like a pro",
    "Passive income and long-term investing",
    "Risk management nobody teaches you",
    "Crypto vs stocks — the honest breakdown",
    "Options explained without the jargon",
    "Daily market recap done in 30 seconds",
    "Money habits of people who actually get rich",
    "Chart patterns that repeat forever",
    "Earnings season survival guide",
]

# Hooks = the first 1.5 seconds. This is 80% of the battle.
HOOKS = [
    "I lost my first 1,000 dollars trading so you don't have to.",
    "Nobody talks about this, but it's why 90% of traders fail.",
    "If you have 100 dollars, watch this before you invest a single cent.",
    "The market just did something it only does before a big move.",
    "This one chart pattern printed money 3 times this month.",
    "Rich people don't save money. They do THIS instead.",
    "I asked a fund manager one question. His answer changed how I trade.",
    "Stop buying stocks at the wrong time. Here's the fix.",
    "You're not bad at trading. You're just breaking these 3 rules.",
    "The fastest way to blow up your account, ranked.",
    "Everyone's buying this stock. Here's why I'm not.",
    "This is what 10,000 dollars in the S&P looks like after 10 years.",
    "Day trading looks easy on TikTok. Here's the part they cut out.",
    "The 1% invest while you're scrolling. Let's fix that in 60 seconds.",
    "I backtested this strategy 500 times. The result surprised me.",
    "Your broker doesn't want you to know this order type.",
    "Three words that saved my portfolio in the last crash.",
    "How much you'd have if you invested 10 dollars a day since 2015.",
    "The market is fear and greed. Here's how to trade both.",
    "I turned my biggest loss into my best lesson. Steal it.",
]

# Formats = the container the idea lives in.
FORMATS = [
    ("Reel / Short (15-30s)", "Fast cuts, big on-screen text, one single idea, loop the ending back to the hook."),
    ("Carousel (6-8 slides)", "Slide 1 = the hook. Middle slides = one point each. Last slide = CTA + save prompt."),
    ("X / Twitter thread", "Hook tweet, then 5-7 punchy tweets, screenshots of charts, end with a bold takeaway."),
    ("YouTube Short", "Vertical, subtitle everything, deliver value in under 40 seconds, tease a longer video."),
    ("Talking-head Reel", "You on camera + b-roll of charts. Authority builds trust and trust builds a following."),
    ("Green-screen react", "Green-screen over a headline / chart and react with your hot take."),
    ("Text-on-screen story", "No face needed. Screen-record a chart, narrate the story of the trade."),
]

# Angles = the actual content spine. {theme} gets filled in.
ANGLES = [
    "Break down '{theme}' using a real recent example from this week's market.",
    "List the top 3 things about '{theme}' that beginners get wrong.",
    "Tell a personal story tied to '{theme}' — a win or a painful loss.",
    "Do a myth vs reality on '{theme}'. Bust one popular piece of bad advice.",
    "Show a before/after: a portfolio that ignores '{theme}' vs one that respects it.",
    "React to a trending finance headline through the lens of '{theme}'.",
    "Give a 5-step framework the viewer can screenshot for '{theme}'.",
    "Compare two tickers / assets to illustrate '{theme}' visually.",
    "Answer the most-asked DM you get about '{theme}'.",
    "Explain '{theme}' like the viewer is 12 — simple wins the algorithm.",
]

# CTAs = what you want them to do (drives the algorithm).
CTAS = [
    "Follow for a market recap every single day.",
    "Save this so you don't forget it when the market moves.",
    "Comment your ticker and I'll give you my honest take.",
    "Share this with the friend who keeps buying at the top.",
    "Follow — part 2 tomorrow goes even deeper.",
    "Drop a chart emoji if you want the full strategy breakdown.",
    "Which side are you on? Tell me in the comments.",
]

# Hashtag sets per platform vibe.
HASHTAGS = [
    "#stockmarket #investing #trading #finance #stocks",
    "#daytrading #stockmarket #wallstreet #investing101 #moneytips",
    "#personalfinance #investing #financialfreedom #passiveincome #wealth",
    "#crypto #stocks #trading #markets #investingtips",
    "#optionstrading #stockmarket #tradingview #charting #fintok",
]

# Best posting windows (general guidance — test for your audience).
POST_TIMES = [
    "Pre-market: 6:30-8:30am (people checking before the open)",
    "Lunch scroll: 12-1pm",
    "Post-close: 4-6pm (recap window converts best)",
    "Evening: 7-9pm (longest watch time)",
]


def _rng_for_today():
    """Deterministic per-day randomness: the same day always yields
    the same batch, but each new day rotates fresh ideas."""
    today = datetime.now(_tz()).date()
    return random.Random(today.toordinal())


def _build_idea(rng, theme=None):
    theme = theme or rng.choice(THEMES)
    hook = rng.choice(HOOKS)
    fmt_name, fmt_tip = rng.choice(FORMATS)
    angle = rng.choice(ANGLES).format(theme=theme)
    cta = rng.choice(CTAS)
    tags = rng.choice(HASHTAGS)
    return {
        "theme": theme,
        "hook": hook,
        "format": fmt_name,
        "format_tip": fmt_tip,
        "angle": angle,
        "cta": cta,
        "tags": tags,
    }


def _format_idea(idea, index=None):
    head = f"💡 *Content Idea {index}*" if index else "💡 *Content Idea*"
    return (
        f"{head}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"🎬 *Format:* {idea['format']}\n"
        f"🪝 *Hook (first 2 sec):*\n_{idea['hook']}_\n\n"
        f"🎯 *The angle:*\n{idea['angle']}\n\n"
        f"📌 *Make it work:* {idea['format_tip']}\n"
        f"📣 *CTA:* {idea['cta']}\n"
        f"🏷 {idea['tags']}"
    )


# ─────────────────────────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────────────────────────

async def content_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/idea — one fresh viral idea on demand (freshly random)."""
    if not await is_team_member(update):
        return
    rng = random.Random()  # on-demand = truly fresh each call
    topic = " ".join(context.args).strip() if context.args else None
    theme = topic if topic else None
    idea = _build_idea(rng, theme=theme)
    await update.message.reply_text(_format_idea(idea), parse_mode="Markdown")


async def daily_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ideas — today's curated batch (stable for the whole day)."""
    if not await is_team_member(update):
        return
    await update.message.reply_text(_daily_batch_text(), parse_mode="Markdown")


def _daily_batch_text(n=5):
    rng = _rng_for_today()
    theme_of_day = rng.choice(THEMES)
    today = datetime.now(_tz()).strftime("%A, %d %B %Y")

    header = (
        "📈 *DAILY VIRAL CONTENT — FINANCE & TRADING*\n"
        f"🗓 {today}\n"
        f"🔥 *Theme of the day:* {theme_of_day}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # Build n distinct ideas, biased toward today's theme.
    ideas = []
    used_hooks = set()
    attempts = 0
    while len(ideas) < n and attempts < 50:
        attempts += 1
        theme = theme_of_day if len(ideas) % 2 == 0 else rng.choice(THEMES)
        idea = _build_idea(rng, theme=theme)
        if idea["hook"] in used_hooks:
            continue
        used_hooks.add(idea["hook"])
        ideas.append(idea)

    body = "\n\n".join(_format_idea(idea, i + 1) for i, idea in enumerate(ideas))

    footer = (
        "\n\n━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ *Best times to post today:*\n• " + "\n• ".join(POST_TIMES) + "\n\n"
        "🧠 *Pro tip:* Post the recap-style idea within 30 min of the close — "
        "timely market content rides the algorithm hardest.\n"
        "Type /idea for a fresh one anytime, or /calendar for a 7-day plan."
    )
    return header + body + footer


async def viral_hook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/hook <topic> — just a scroll-stopping opening line."""
    if not await is_team_member(update):
        return
    rng = random.Random()
    hooks = rng.sample(HOOKS, k=min(3, len(HOOKS)))
    topic = " ".join(context.args).strip() if context.args else None
    intro = f"🪝 *Hooks for:* {topic}\n\n" if topic else "🪝 *Scroll-stopping hooks:*\n\n"
    text = intro + "\n\n".join(f"{i+1}. _{h}_" for i, h in enumerate(hooks))
    await update.message.reply_text(text, parse_mode="Markdown")


async def content_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/calendar — a 7-day content plan (one theme per day)."""
    if not await is_team_member(update):
        return
    rng = _rng_for_today()
    tz = _tz()
    start = datetime.now(tz)
    themes = rng.sample(THEMES, k=min(7, len(THEMES)))
    lines = ["🗓 *YOUR 7-DAY CONTENT PLAN*", "━━━━━━━━━━━━━━━━━━━"]
    for i, theme in enumerate(themes):
        day = (start + timedelta(days=i)).strftime("%a %d %b")
        fmt_name, _ = rng.choice(FORMATS)
        lines.append(f"*{day}* — {fmt_name}\n   → {theme}")
    lines.append("\nType /ideas for today's full ready-to-shoot batch.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def content_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/contenthelp — explain the agent."""
    if not await is_team_member(update):
        return
    await update.message.reply_text(
        "🤖 *Viral Finance Content Agent*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "I'm your in-house marketing strategist for stock-market, trading and "
        "money content. I turn what goes viral across Instagram, YouTube Shorts, "
        "TikTok and X into ready-to-shoot ideas.\n\n"
        "*Commands:*\n"
        "  `/ideas` – today's batch of viral content ideas\n"
        "  `/idea` – one fresh idea now (add a topic, e.g. `/idea options`)\n"
        "  `/hook` – scroll-stopping opening lines (add a topic)\n"
        "  `/calendar` – a 7-day content plan\n"
        "  `/contenthelp` – this message\n\n"
        f"📬 I also DM you a fresh batch automatically every day at "
        f"{DAILY_HOUR:02d}:{DAILY_MIN:02d} ({TIMEZONE}).",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────────────────────
#  DAILY AUTO-DELIVERY (wired via job_queue.run_daily in bot.py)
# ─────────────────────────────────────────────────────────────

async def send_daily_ideas(context: ContextTypes.DEFAULT_TYPE):
    """Push the daily batch to the owner automatically."""
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=_daily_batch_text(),
            parse_mode="Markdown",
        )
    except Exception:
        # Never let a delivery error crash the job queue.
        pass


def daily_time():
    """The local time-of-day to fire send_daily_ideas."""
    return time(hour=DAILY_HOUR, minute=DAILY_MIN, tzinfo=_tz())
