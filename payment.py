from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_conn
from config import OWNER_ID, TEAM_IDS
from utils import is_team_member, fmt_dt


async def register_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/token <reference_number>`\nExample: `/token TKN-2024-001`", parse_mode="Markdown")
        return

    token = " ".join(context.args)
    conn = get_conn()
    existing = conn.execute("SELECT * FROM payments WHERE token=?", (token,)).fetchone()
    if existing:
        await update.message.reply_text(f"⚠️ Token `{token}` already exists with status: *{existing['status']}*", parse_mode="Markdown")
        conn.close()
        return
    conn.execute("INSERT INTO payments (token, status) VALUES (?,?)", (token, "pending"))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ *Payment Token Registered*\n\n"
        f"📌 Token: `{token}`\n"
        f"📊 Status: ⏳ Pending\n\n"
        f"_Share your bot link with the party. They should send a photo of the payment proof._",
        parse_mode="Markdown"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    caption = update.message.caption or ""

    # Save photo to pending payment if token mentioned in caption
    conn = get_conn()
    matched_token = None
    if caption:
        payments = conn.execute("SELECT * FROM payments WHERE status='pending'").fetchall()
        for p in payments:
            if p['token'].lower() in caption.lower():
                matched_token = p['token']
                break

    photo_id = update.message.photo[-1].file_id

    # Update DB if token matched
    if matched_token:
        conn.execute(
            "UPDATE payments SET from_id=?, from_name=?, photo_id=?, updated_at=CURRENT_TIMESTAMP WHERE token=?",
            (sender.id, sender.full_name, photo_id, matched_token)
        )
        conn.commit()

    conn.close()

    # Notify all team members
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"pay_confirm_{matched_token or 'unknown'}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"pay_reject_{matched_token or 'unknown'}")
        ]
    ])

    notify_text = (
        f"📸 *Payment Photo Received!*\n"
        f"━━━━━━━━━━━━━\n"
        f"👤 From: *{sender.full_name}* (ID: `{sender.id}`)\n"
        f"📝 Caption: {caption or 'None'}\n"
        f"🔑 Token Detected: `{matched_token or 'None – add manually'}`\n\n"
        f"Use buttons below or:\n"
        f"`/confirm <token>` / `/reject <token>`"
    )

    for tid in TEAM_IDS:
        try:
            await context.bot.forward_message(chat_id=tid, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
            await context.bot.send_message(chat_id=tid, text=notify_text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            pass

    await update.message.reply_text(
        "✅ *Photo received!*\nYour payment proof has been sent for verification. Please wait for confirmation.",
        parse_mode="Markdown"
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # pay_confirm_TOKEN or pay_reject_TOKEN

    parts = data.split("_", 2)
    action = parts[1]
    token  = parts[2] if len(parts) > 2 else "unknown"

    conn = get_conn()
    conn.execute(
        "UPDATE payments SET status=?, updated_at=CURRENT_TIMESTAMP WHERE token=?",
        (action + "ed", token)
    )
    conn.commit()
    conn.close()

    emoji = "✅" if action == "confirm" else "❌"
    await query.edit_message_text(
        f"{emoji} Payment `{token}` has been *{'confirmed' if action == 'confirm' else 'rejected'}*.",
        parse_mode="Markdown"
    )


async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/confirm <token>`", parse_mode="Markdown")
        return
    token = " ".join(context.args)
    conn = get_conn()
    conn.execute("UPDATE payments SET status='confirmed', updated_at=CURRENT_TIMESTAMP WHERE token=?", (token,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Payment `{token}` *confirmed!*", parse_mode="Markdown")


async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/reject <token>`", parse_mode="Markdown")
        return
    token = " ".join(context.args)
    conn = get_conn()
    conn.execute("UPDATE payments SET status='rejected', updated_at=CURRENT_TIMESTAMP WHERE token=?", (token,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"❌ Payment `{token}` *rejected.*", parse_mode="Markdown")


async def list_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    filter_status = context.args[0] if context.args else None
    conn = get_conn()
    if filter_status:
        rows = conn.execute("SELECT * FROM payments WHERE status=? ORDER BY created_at DESC LIMIT 20", (filter_status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM payments ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No payments found.")
        return

    text = f"💰 *Payments* {f'({filter_status})' if filter_status else '(last 20)'}:\n━━━━━━━━━━━━━\n"
    for r in rows:
        emoji = {"pending": "⏳", "confirmed": "✅", "rejected": "❌"}.get(r['status'], "❓")
        text += f"{emoji} `{r['token']}` — *{r['status']}*"
        if r['from_name']:
            text += f" | 👤 {r['from_name']}"
        text += f"\n"
    await update.message.reply_text(text, parse_mode="Markdown")
