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
🔥 All features working properly
"""

HELP_MSG = """
🛠 **Help - Available Commands**
/start - Show bot status
/about - About this bot
/help - Help menu
/osint - Open OSINT Menu
"""

ABOUT_MSG = """
💀 **Sevr0c–Moros AI**
👑 Made by: @iamorosss & @sevr0c
⚠️ Educational purpose only
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


session_messages = {}  # Chat memory


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

    await update.message.reply_photo(
        photo=PHOTO_PATH,
        caption=CAPTION,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


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


async def osint_cmd(update, ctx):
    uid = update.message.from_user.id
    if not await is_joined_all(uid, ctx):
        await send_force_join(update, ctx)
        return

    kb = [
        [InlineKeyboardButton("📱 Phone Lookup", callback_data="osint_phone")],
        [InlineKeyboardButton("🔙 Back", callback_data="osint_back")]
    ]
    await update.message.reply_text("🕵️ Select OSINT Service:", reply_markup=InlineKeyboardMarkup(kb))


# ========== CALLBACK HANDLER ========== #
async def callback_handler(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    add_user(uid)

    if q.data == "check_join":
        if not await is_joined_all(uid, ctx):
            await q.answer("❌ Not joined all!", show_alert=True)
            return
        await q.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("🟢 JOINED ✔", callback_data="none")]])
        )
        await ctx.bot.send_message(uid, "🎉 Verified! Now you can use the bot.")
        return

    if q.data == "osint_phone":
        ctx.user_data['mode'] = "phone"
        await ctx.bot.send_message(uid, "📱 Send phone number to lookup:")
        return

    if q.data == "osint_back":
        ctx.user_data['mode'] = None
        await ctx.bot.send_message(uid, "🔙 Back.")
        return


# ========== AI SYSTEM WITH MEMORY ========== #
async def ai_response(uid, text):
    if uid not in session_messages:
        session_messages[uid] = []

    session_messages[uid].append({"role": "user", "content": text})

    try:
        out = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=session_messages[uid]
        )
        reply = out.choices[0].message.content
        session_messages[uid].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        return f"⚠️ AI Error: `{e}`"


# ========== MAIN MESSAGE HANDLER ========== #
async def handle_msg(update, ctx):
    uid = update.message.from_user.id
    text = update.message.text
    add_user(uid)

    if not await is_joined_all(uid, ctx):
        await send_force_join(update, ctx)
        return

    if ctx.user_data.get('mode') == "phone":
        await update.message.reply_text(f"📞 OSINT Enabled — Coming soon 🔍\nYou entered: `{text}`")
        ctx.user_data['mode'] = None
        return

    await update.message.reply_text("💬 Thinking...")
    reply = await ai_response(uid, text)
    await update.message.reply_text(reply)


# ========== RUN ========== #
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("about", about_cmd))
app.add_handler(CommandHandler("osint", osint_cmd))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.TEXT, handle_msg))

app.run_polling()
