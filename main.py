import os
import json
os.system("pip install openai==1.30.0 python-telegram-bot==20.3 requests")

from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

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
/osint - OSINT menu (coming)
/broadcast - OWNER only (Reply to msg)
/forget - Clear your memory
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
    """Robust loader: returns correct type even if file corrupted."""
    if not os.path.exists(file):
        # default empty structures
        return {} if file == MEMORY_DB else []
    try:
        data = json.load(open(file, "r"))
    except Exception:
        return {} if file == MEMORY_DB else []
    # type safety
    if file == MEMORY_DB:
        return data if isinstance(data, dict) else {}
    else:
        return data if isinstance(data, list) else []


def save_db(file, data):
    json.dump(data, open(file, "w"))


def add_user(uid: int):
    users = load_db(USERS_DB)
    if uid not in users:
        users.append(uid)
        save_db(USERS_DB, users)


def get_memory(uid: int):
    mem = load_db(MEMORY_DB)
    return mem.get(str(uid), {})


def save_memory(uid: int, key: str, value: str):
    mem = load_db(MEMORY_DB)
    if str(uid) not in mem:
        mem[str(uid)] = {}
    mem[str(uid)][key] = value
    save_db(MEMORY_DB, mem)


def extract_memory(uid: int, text: str):
    text_low = text.lower()

    if "my name is" in text_low:
        name_part = text_low.split("my name is", 1)[1].strip()
        name = name_part.split()[0]
        save_memory(uid, "name", name.capitalize())

    if "i like" in text_low:
        like_part = text_low.split("i like", 1)[1]
        interest = like_part.split(".")[0].strip()
        save_memory(uid, "interest", interest)

    if "i am" in text_low and "years old" in text_low:
        age_part = text_low.split("i am", 1)[1].split("years old", 1)[0].strip()
        save_memory(uid, "age", age_part)


# in-RAM chat history
session_messages: dict[int, list[dict]] = {}

# ================= FORCE JOIN CHECK ================= #
async def is_joined_all(uid, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    for cid, _, _ in CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(cid, uid)
            if m.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True


async def send_force_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [
            InlineKeyboardButton("⚡ Join", url=CHANNELS[0][2]),
            InlineKeyboardButton("🔥 Join", url=CHANNELS[1][2]),
        ],
        [
            InlineKeyboardButton("💎 Join", url=CHANNELS[2][2]),
            InlineKeyboardButton("🚀 Join", url=CHANNELS[3][2]),
        ],
        [InlineKeyboardButton("⭕ JOINED ❌", callback_data="check_join")],
    ]
    await update.message.reply_photo(
        photo=PHOTO_PATH,
        caption=CAPTION,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )


# ================= COMMANDS ================= #
async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    add_user(uid)
    session_messages[uid] = []

    # force join before using
    if not await is_joined_all(uid, ctx):
        await send_force_join(update, ctx)
        return

    await update.message.reply_text(STATUS_MSG, parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_MSG, parse_mode="Markdown")


async def about_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_MSG, parse_mode="Markdown")


async def forget_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    mem = load_db(MEMORY_DB)
    if str(uid) in mem:
        del mem[str(uid)]
        save_db(MEMORY_DB, mem)
    await update.message.reply_text("🧹 Memory cleared!")


async def osint_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # placeholder menu, you can upgrade later
    kb = [
        [InlineKeyboardButton("📱 Phone Lookup (soon)", callback_data="osint_phone")],
        [InlineKeyboardButton("🔙 Back", callback_data="osint_back")],
    ]
    await update.message.reply_text(
        "🕵 OSINT Menu (coming soon):", reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= CALLBACK HANDLER ================= #
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    add_user(uid)

    if q.data == "check_join":
        if not await is_joined_all(uid, ctx):
            await q.answer("❌ Join all channels first!", show_alert=True)
            return

        await q.edit_message_reply_markup(
            InlineKeyboardMarkup(
                [[InlineKeyboardButton("🟢 JOINED ✔", callback_data="none")]]
            )
        )
        await ctx.bot.send_message(uid, "🎉 Verified! You can now use the bot.")
        return

    # other buttons (osint, etc.) for now
    if q.data == "osint_phone":
        await ctx.bot.send_message(uid, "📱 Phone OSINT coming soon…")
    elif q.data == "osint_back":
        await ctx.bot.send_message(uid, "🔙 Back.")


# ================= AI WITH MEMORY ================= #
async def ai_response(uid: int, text: str) -> str:
    extract_memory(uid, text)
    memory = get_memory(uid)
    memory_context = "\n".join(f"{k}: {v}" for k, v in memory.items())

    session_messages.setdefault(uid, [])

    messages = [
        {
            "role": "system",
            "content": (
                f"User memory:\n{memory_context}\n"
                "Behave like a smart, friendly hacker assistant."
            ),
        },
        *session_messages[uid],
        {"role": "user", "content": text},
    ]

    out = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    reply = out.choices[0].message.content
    session_messages[uid].append({"role": "assistant", "content": reply})
    return reply


# ================= BROADCAST ================= #
async def broadcast_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user

