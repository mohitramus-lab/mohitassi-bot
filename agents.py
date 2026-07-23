from telegram import Update
from telegram.ext import ContextTypes
from database import get_conn
from utils import is_team_member, owner_only


@owner_only
async def add_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: `/addagent <name> | <telegram_id> | <specialty>`\n"
            "Example: `/addagent Sara | 987654321 | payments`\n"
            "Specialty is optional (default: general).",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    parts = [p.strip() for p in full.split("|")]
    name      = parts[0] if len(parts) > 0 and parts[0] else "Unknown"
    id_raw    = parts[1] if len(parts) > 1 else ""
    specialty = parts[2] if len(parts) > 2 and parts[2] else "general"

    tg_id = None
    if id_raw:
        if not id_raw.lstrip("@").isdigit():
            await update.message.reply_text("❌ Telegram ID must be numeric.")
            return
        tg_id = int(id_raw.lstrip("@"))

    conn = get_conn()
    conn.execute(
        "INSERT INTO agents (name, telegram_id, specialty, added_by) VALUES (?,?,?,?)",
        (name, tg_id, specialty, update.effective_user.id)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Agent registered!\n"
        f"🎧 *{name}*\n"
        f"🆔 `{tg_id if tg_id else 'N/A'}`\n"
        f"🏷 Specialty: `{specialty}`\n"
        f"🟢 Status: available",
        parse_mode="Markdown"
    )


@owner_only
async def remove_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/delagent <id>`", parse_mode="Markdown")
        return
    conn = get_conn()
    conn.execute("DELETE FROM agents WHERE id=?", (context.args[0],))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Agent `{context.args[0]}` removed.", parse_mode="Markdown")


async def get_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/agent <name or specialty>`", parse_mode="Markdown")
        return
    query = "%" + " ".join(context.args) + "%"
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM agents WHERE name LIKE ? OR specialty LIKE ?", (query, query)
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No agent found.")
        return
    text = "🔍 *Agent Search:*\n━━━━━━━━━━━━━\n"
    for r in rows:
        status = "🟢 available" if r['available'] else "🔴 offline"
        text += f"*[{r['id']}]* 🎧 *{r['name']}* — {status}\n"
        if r['telegram_id']:
            text += f"   🆔 `{r['telegram_id']}`\n"
        text += f"   🏷 {r['specialty']}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def list_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    conn = get_conn()
    rows = conn.execute("SELECT * FROM agents ORDER BY available DESC, name").fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No agents yet. Use `/addagent` to register one.", parse_mode="Markdown")
        return

    online = sum(1 for r in rows if r['available'])
    text = f"🎧 *Support Agents* ({online}/{len(rows)} online):\n━━━━━━━━━━━━━\n"
    for r in rows:
        dot = "🟢" if r['available'] else "🔴"
        text += f"{dot} [{r['id']}] *{r['name']}* — `{r['specialty']}`"
        if r['telegram_id']:
            text += f"  (`{r['telegram_id']}`)"
        text += "\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def _set_availability(update: Update, context: ContextTypes.DEFAULT_TYPE, available: int):
    if not await is_team_member(update):
        return
    if not context.args:
        cmd = "agenton" if available else "agentoff"
        await update.message.reply_text(f"Usage: `/{cmd} <id>`", parse_mode="Markdown")
        return
    conn = get_conn()
    cur = conn.execute("UPDATE agents SET available=? WHERE id=?", (available, context.args[0]))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    if not changed:
        await update.message.reply_text(f"❌ No agent with ID `{context.args[0]}`.", parse_mode="Markdown")
        return
    state = "🟢 available" if available else "🔴 offline"
    await update.message.reply_text(f"✅ Agent `{context.args[0]}` is now {state}.", parse_mode="Markdown")


async def agent_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _set_availability(update, context, 1)


async def agent_offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _set_availability(update, context, 0)
