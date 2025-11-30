import os
import json
os.system("pip install openai==1.30.0 python-telegram-bot==20.3 requests")

from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

# ================= BOT CONFIG ================= #
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=OPENAI_KEY)

OWNER_IDS = [8180209483, 7926496057]

PHOTO_PATH = "https://i.postimg.cc/76L59xVj/03cf19b6-e979-4d2f-9d6f-3ba2469e60c2.jpg"

CHANNELS = [
    (-1002090323246, "⚡", "https://t.me/CodeTweakz"),
    (-1002145075313, "🔥", "https://t.me/Scripts0x"),
    (-1003279886990, "💎", "https://t.me/techmoros"),
    (-1002733321153, "🚀", "https://t.me/MethRoot"),
]

CAPTION = """
💀 **Sevr0c–Moros AI ⚡**
Join all channels first to use the bot.
"""

STATUS_MSG = """
💀 **Sevr0c–Moros AI Status**
━━━━━━━━━━━━━━━━━━
⚡ Bot is LIVE
🟢 No maintenance
🔥 Everything working perfectly
"""

HELP_MSG = """
🛠 **Commands**
/start - Bot status
/help - Commands menu
/about - About bot
/osint - OSINT menu
/broadcast - OWNER only (Reply to a message)
"""

ABOUT_MSG = """
💀 **Sevr0c–Moros AI**
Creators:
👑 @iamorosss
⚡ @sevr0c
⚠️ Education purpose only
"""

DB_FILE = "users.json"

def load_users():
    if not os.path.exists(DB_FILE): return []
    return json.load(open(DB_FILE, "r"))

def save_users(u): json.dump(u, open(DB_FILE, "w"))

def add_user(uid):
    u = load_users()
    if uid not in u:
        u.append(uid)
        save_users(u)


session_messages = {}  # Chat memory (AI)


# ========== FORCE JOIN CHECK ========== #
async def is_joined_all(uid, ctx):
    for cid, _, _ in CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(cid, uid)
            if m.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


async def send_force_join(update, ctx):
    kb = [
        [
            InlineKeyboardButton(f"{CHANNELS[0][1]} Join", url=CHANNELS[0][2]),
            InlineKeyboardButton(f"{CHANNELS[1][1]} Join", url=CHANNELS[1][2])
        ],
        [
            InlineKeyboardButton(f"{CHANNELS[2][1]} Join", url=CHANNELS[2][2]),
            InlineKeyboardButton(f"{CHANNELS[3][1]} Join", url=CHANNELS[3][2])
        ],
        [InlineKeyboardButton("⭕ JOINED ❌", callback_data="check_join")]
    ]

    await update.message.reply_photo(PHOTO_PATH, CAPTION,
        InlineKeyboardMarkup(kb), parse_mode="Markdown")


# ========== COMMANDS ========== #
async def start_cmd(update: Update, ctx):
    uid = update.message.from_user.id
    add_user(uid)
    session_messages[uid] = []

    if not await is_joined_all(uid, ctx):
        await send_force_join(update, ctx)
        return

    await update.message.reply_text(STATUS_MSG, parse_mode="Markdown")


async def help_cmd(update, ctx):
    await update.message.reply_text(HELP_MSG, parse_mode="Markdown")


async def about_cmd(update, ctx):
    await update.message.reply_text(ABOUT_MSG, parse_mode="Markdown")


# ========== OSINT ========== #
async def osint_cmd(update, ctx):
    uid = update.message.from_user.id
    if not await is_joined_all(uid, ctx):
        await send_force_join(update, ctx)
        return

    kb = [
        [InlineKeyboardButton("📱 Phone Lookup", callback_data="osint_phone")],
        [InlineKeyboardButton("🔙 Back", callback_data="osint_back")]
    ]
    await update.message.reply_text("🕵️ Select OSINT:", reply_markup=InlineKeyboardMarkup(kb))


# ========== CALLBACK HANDLER ========== #
async def callback_handler(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    add_user(uid)

    if q.data == "check_join":
        if not await is_joined_all(uid, ctx):
            await q.answer("❌ Join all channels!", show_alert=True)
            return
        await q.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("🟢 JOINED ✔", callback_data="none")]])
        )
        await ctx.bot.send_message(uid, "🎉 Verified! Enjoy bot.")
        return

    if q.data == "osint_phone":
        ctx.user_data['mode'] = "phone"
        await ctx.bot.send_message(uid, "📞 Send phone number:")
        return

    if q.data == "osint_back":
        ctx.user_data['mode'] = None
        await ctx.bot.send_message(uid, "🔙 Back to menu.")
        return


# ========== AI WITH MEMORY ========== #
async def ai_response(uid, text):
    if uid not in session_messages:
        session_messages[uid] = []

    session_messages[uid].append({"role": "user", "content": text})

    out = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=session_messages[uid]
    )

    reply = out.choices[0].message.content
    session_messages[uid].append({"role": "assistant", "content": reply})
    return reply


# ========== BROADCAST (UPGRADED) ========== #
async def broadcast_cmd(update, ctx):
    uid = update.message.from_user.id

    if uid not in OWNER_IDS:
        await update.message.reply_text("❌ Only Owner can use this.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("📢 Reply to a message and send /broadcast")
        return

    msg = update.message.reply_to_message
    users = load_users()
    sent = 0

    for u in users:
        try:
            await ctx.bot.copy_message(
                chat_id=u,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(f"📡 Broadcast sent to {sent} users ✔")


# ========== MAIN TEXT HANDLER ========== #
async def handle_msg(update, ctx):
    uid = update.message.from_user.id
    text = update.message.text
    add_user(uid)

    if not await is_joined_all(uid, ctx):
        await send_force_join(update, ctx)
        return

    if ctx.user_data.get('mode') == "phone":
        await update.message.reply_text(f"📞 Saved! Lookup soon: `{text}`")
        ctx.user_data['mode'] = None
        return

    await update.message.reply_text("💬 Thinking...")
    reply = await ai_response(uid, text)
    await update.message.reply_text(reply)


# ========== RUN BOT ========== #
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("about", about_cmd))
app.add_handler(CommandHandler("osint", osint_cmd))
app.add_handler(CommandHandler("broadcast", broadcast_cmd))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

app.run_polling()
