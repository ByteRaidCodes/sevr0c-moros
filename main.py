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
    (-1002090323246, "⚡", "https://t.me/+2CuRAk4cJVUzMDY9"),
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
/broadcast - OWNER only (Reply to msg)
/forget - Clear saved memory
"""

ABOUT_MSG = """
💀 **Sevr0c–Moros AI**
Creators:
👑 @iamorosss
⚡ @sevr0c
⚠️ Education purpose only
"""

# ================= USER & MEMORY DB ================= #
USERS_DB = "users.json"
MEMORY_DB = "memory.json"

def load_db(file):
    if not os.path.exists(file): return {}
    try: return json.load(open(file, "r"))
    except: return {}

def save_db(file, data):
    json.dump(data, open(file, "w"))

def add_user(uid):
    users = load_db(USERS_DB)
    if isinstance(users, dict): users = []  # FIX
    if uid not in users:
        users.append(uid)
        save_db(USERS_DB, users)

def get_memory(uid):
    mem = load_db(MEMORY_DB)
    return mem.get(str(uid), {})

def save_memory(uid, key, value):
    mem = load_db(MEMORY_DB)
    if str(uid) not in mem:
        mem[str(uid)] = {}
    mem[str(uid)][key] = value
    save_db(MEMORY_DB, mem)

# Save user info from chat
def extract_memory(uid, text):
    text = text.lower()

    if "my name is" in text:
        name = text.split("my name is")[1].strip().split(" ")[0]
        save_memory(uid, "name", name.capitalize())

    if "i like" in text:
        interest = text.split("i like")[1].strip().split(".")[0]
        save_memory(uid, "interest", interest)

session_messages = {}

# ========== FORCE JOIN CHECK ========== #
async def is_joined_all(uid, ctx):
    for cid, _, _ in CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(cid, uid)
            if m.status in ["left", "kicked"]: return False
        except: return False
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
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ========== COMMANDS ========== #
async def start_cmd(update: Update, ctx):
    uid = update.message.from_user.id
    add_user(uid)
    session_messages[uid] = []
    await update.message.reply_text(STATUS_MSG, parse_mode="Markdown")

async def help_cmd(update, ctx):
    await update.message.reply_text(HELP_MSG, parse_mode="Markdown")

async def about_cmd(update, ctx):
    await update.message.reply_text(ABOUT_MSG, parse_mode="Markdown")

async def forget_cmd(update, ctx):
    uid = update.message.from_user.id
    mem = load_db(MEMORY_DB)
    if str(uid) in mem:
        del mem[str(uid)]
        save_db(MEMORY_DB, mem)
    await update.message.reply_text("🧹 Memory wiped successfully!")

async def stats_cmd(update, ctx):
    users = load_db(USERS_DB)
    if isinstance(users, dict): users = []
    count = len(users)
    await update.message.reply_text(f"📊 Total Users: **{count}**", parse_mode="Markdown")

async def osint_cmd(update, ctx):
    uid = update.message.from_user.id
    kb = [[InlineKeyboardButton("📱 Phone Lookup (Soon)", callback_data="osint_soon")]]
    await update.message.reply_text("🕵 OSINT Tools:", reply_markup=InlineKeyboardMarkup(kb))

# ========== CALLBACK ========== #
async def callback_handler(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "check_join":
        if not await is_joined_all(uid, ctx):
            await q.answer("❌ Still not joined!", show_alert=True)
            return
        await q.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("🟢 JOINED ✔", callback_data="none")]])
        )
        await ctx.bot.send_message(uid, "🎉 Verified!")
        return

    await ctx.bot.send_message(uid, "🛠️ Coming soon…")

# ========== AI WITH MEMORY ========== #
async def ai_response(uid, text):
    extract_memory(uid, text)

    memory = get_memory(uid)
    memory_context = "\n".join([f"{k}: {v}" for k,v in memory.items()])

    messages = [
        {"role": "system", "content": f"You remember:\n{memory_context}\nBe friendly."}
    ] + session_messages.get(uid, []) + [
        {"role": "user", "content": text}
    ]

    out = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = out.choices[0].message.content
    session_messages.setdefault(uid, []).append({"role": "assistant", "content": reply})
    return reply

# ========== BROADCAST ========== #
async def broadcast_cmd(update, ctx):
    uid = update.message.from_user.id
    if uid not in OWNER_IDS:
        await update.message.reply_text("❌ Owner only")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply a message and send /broadcast")
        return
    
    msg = update.message.reply_to_message
    users = load_db(USERS_DB)
    sent = 0

    for u in users:
        try:
            await ctx.bot.copy_message(chat_id=u, from_chat_id=msg.chat_id, message_id=msg.message_id)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"📡 Broadcast sent to {sent} users ✔")

# ========== MAIN MESSAGE ========== #
async def handle_msg(update, ctx):
    uid = update.message.from_user.id
    text = update.message.text
    add_user(uid)

    await update.message.reply_text("🤖 Thinking...")
    reply = await ai_response(uid, text)
    await update.message.reply_text(reply)

# ================= RUN ================= #
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_cmd))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("stats", stats_cmd))
app.add_handler(CommandHandler("about", about_cmd))
app.add_handler(CommandHandler("forget", forget_cmd))
app.add_handler(CommandHandler("osint", osint_cmd))
app.add_handler(CommandHandler("broadcast", broadcast_cmd))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))

app.run_polling()


