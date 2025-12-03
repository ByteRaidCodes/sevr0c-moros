import os
import json
os.system("pip install openai==1.30.0 python-telegram-bot==20.3 requests")

from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
import datetime

# ================= BOT CONFIG ================= #
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=OPENAI_KEY)

OWNER_IDS = [8180209483, 7926496057]

start_time = datetime.datetime.now()

PHOTO_PATH = "https://i.postimg.cc/76L59xVj/03cf19b6-e979-4d2f-9d6f-3ba2469e60c2.jpg"

CHANNELS = [
    (-1002090323246, "⚡", "https://t.me/CodeTweakz"),
    (-1002145075313, "🔥", "https://t.me/Scripts0x"),
    (-1003279886990, "💎", "https://t.me/techmoros"),
    (-1002733321153, "🚀", "https://t.me/MethRoot"),
]

CAPTION = "💀 **Sevr0c–Moros AI ⚡**\nJoin all channels first to use the bot."

STATUS_MSG = "💀 Bot is LIVE and working fine!"

HELP_MSG = """
🛠 **Commands**
/start - Bot status
/help - Commands menu
/about - About bot
/osint - OSINT menu
/stats - Bot analytics
/forget - Clear memory
/broadcast - Owner only
"""

ABOUT_MSG = """
💀 Sevr0c–Moros AI
👑 @iamorosss & ⚡ @sevr0c
⚠️ Educational Purpose Only
"""

# ================= USER & MEMORY DB ================= #
USERS_DB = "users.json"
MEMORY_DB = "memory.json"
MESSAGES_DB = "messages.json"

def load_list(file):
    if not os.path.exists(file): return []
    return json.load(open(file, "r"))

def save_list(file, data): json.dump(data, open(file, "w"))

def load_dict(file):
    if not os.path.exists(file): return {}
    return json.load(open(file, "r"))

def save_dict(file, data): json.dump(data, open(file, "w"))

def add_user(uid):
    users = load_list(USERS_DB)
    if uid not in users:
        users.append(uid)
        save_list(USERS_DB, users)

def update_message_count(uid):
    msg_db = load_dict(MESSAGES_DB)
    msg_db[str(uid)] = msg_db.get(str(uid), 0) + 1
    save_dict(MESSAGES_DB, msg_db)

def get_memory(uid):
    mem = load_dict(MEMORY_DB)
    return mem.get(str(uid), {})

def save_memory(uid, key, value):
    mem = load_dict(MEMORY_DB)
    if str(uid) not in mem:
        mem[str(uid)] = {}
    mem[str(uid)][key] = value
    save_dict(MEMORY_DB, mem)

def extract_memory(uid, text):
    text = text.lower()
    if "my name is" in text:
        save_memory(uid, "name", text.split("my name is")[1].split()[0].capitalize())
    if "i like" in text:
        save_memory(uid, "interest", text.split("i like")[1].split(".")[0].strip())

session_messages = {}

# ================= FORCE JOIN ================= #
async def is_joined_all(uid, ctx):
    for cid, _, _ in CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(cid, uid)
            if m.status in ["left", "kicked"]:
                return False
        except: return False
    return True

# ================= /stats COMMAND ================= #
async def stats_cmd(update, ctx):
    uid = update.message.from_user.id
    if uid not in OWNER_IDS:
        await update.message.reply_text("❌ Only Owner can use this command")
        return

    users = load_list(USERS_DB)
    mem = load_dict(MEMORY_DB)
    msg_count = sum(load_dict(MESSAGES_DB).values())

    uptime = datetime.datetime.now() - start_time

    stats = f"""
📊 **Sevr0c–Moros AI Stats**
━━━━━━━━━━━━━━━━━━
👤 Total Users: {len(users)}
🧠 Memory Users: {len(mem)}
💬 Messages: {msg_count}
⏱️ Uptime: {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m
━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(stats, parse_mode="Markdown")

# ================= AI ================= #
async def ai_response(uid, text):
    extract_memory(uid, text)
    update_message_count(uid)

    mem = get_memory(uid)
    memory_context = "\n".join([f"{k}: {v}" for k,v in mem.items()])

    messages = [{"role": "system", "content": f"User memory:\n{memory_context}"}]
    messages += session_messages.get(uid, [])
    messages.append({"role": "user", "content": text})

    out = client.chat.completions.create(model="gpt-4o-mini", messages=messages)

    reply = out.choices[0].message.content
    session_messages.setdefault(uid, []).append({"role": "assistant", "content": reply})
    return reply

# ================= MAIN MSG HANDLER ================= #
async def handle_msg(update, ctx):
    uid = update.message.from_user.id
    text = update.message.text
    add_user(uid)

    await update.message.reply_text("⚙️ Thinking…")
    reply = await ai_response(uid, text)
    await update.message.reply_text(reply)

# ================= RUN BOT ================= #
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_cmd := lambda u,c: handle_msg(u,c)))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("about", about_cmd))
app.add_handler(CommandHandler("osint", osint_cmd := lambda u,c: u.message.reply_text("osint soon")))
app.add_handler(CommandHandler("forget", forget_cmd := lambda u,c: u.message.reply_text("cleared")))
app.add_handler(CommandHandler("broadcast", broadcast_cmd := lambda u,c: None))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CallbackQueryHandler(callback_handler := lambda u,c: None))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
app.run_polling()
