import os
import qrcode
import json
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔑 CONFIG
API_ID = 30442407
API_HASH = "27740c262c0c93fb897c789dc2a7326e"
BOT_TOKEN = "8684248491:AAEM2oSOyilVxagWyUjI71_svP6rX_jEjIE"
ADMIN_ID = 6759880165

app = Client("pro_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DB_FILE = "data.json"

# ---------------- DB ----------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {"upi": "amitupadhyay07@axl"}
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

db = load_db()
users = {}

# ---------------- PRICES ----------------
PRICES = {
    "drip": {"1":100,"3":200,"7":350,"15":700,"30":950},
    "hg": {"10":340,"20":600,"30":850},
    "prime": {"1":90,"3":180,"7":320,"10":370},
    "pato": {"3":290,"7":440,"15":750,"30":1000}
}

# ---------------- START MENU ----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Shop Now", callback_data="shop")]
    ])

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🔥 Welcome to Bittu Gaming Store Bot\n 🔥 ─── WHY CHOOSE US ───🔥\n\n🔑 Genuine Premium Keys\n⚡ Instant Auto Delivery\n🛡️ Secure UPI Payments\n💎 Unbeatable Prices\n👊 Real 24/7 Support\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Let's get you a key!", reply_markup=main_menu())

# ---------------- SHOP ----------------
@app.on_callback_query(filters.regex("shop"))
async def shop(client, query):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Drip Client", callback_data="buy_drip")],
        [InlineKeyboardButton("🎮 HG Cheats", callback_data="buy_hg")],
        [InlineKeyboardButton("🎮 Prime Hook", callback_data="buy_prime")],
        [InlineKeyboardButton("🎮 Pato Team", callback_data="buy_pato")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ])
    await query.message.edit("🎮 Select Product:", reply_markup=kb)

# ---------------- BACK ----------------
@app.on_callback_query(filters.regex("back_main"))
async def back_main(client, query):
    await query.message.edit("🔥 Welcome to Gaming Store Bot", reply_markup=main_menu())

# ---------------- SELECT DAYS ----------------
@app.on_callback_query(filters.regex("buy_"))
async def select_days(client, query):
    product = query.data.replace("buy_", "")
    users[query.from_user.id] = {"product": product}

    buttons = []
    for d, price in PRICES[product].items():
        buttons.append([InlineKeyboardButton(f"{d} Days - ₹{price}", callback_data=f"plan_{product}_{d}")])

    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="shop")])

    await query.message.edit(
        f"📅 Select Plan for {product.upper()}:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- BUY ----------------
@app.on_callback_query(filters.regex("plan_"))
async def buy(client, query):
    user_id = query.from_user.id
    _, product, days = query.data.split("_")
    amount = PRICES[product][days]
    upi = db["upi"]

    upi_link = f"upi://pay?pa={upi}&pn=Shop&am={amount}&cu=INR"

    qr = qrcode.make(upi_link)
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    users[user_id] = {"product": product, "days": days}

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I HAVE PAID", callback_data="paid")]
    ])

    await query.message.delete()

    await app.send_photo(
        user_id,
        photo=bio,
        caption=f"""
🎮 Product: {product.upper()}
📅 Plan: {days} Days

💳 UPI: {upi}
💰 Amount: ₹{amount}

👉 QR scan karke payment karo
""",
        reply_markup=kb
    )

# ---------------- PAID ----------------
@app.on_callback_query(filters.regex("paid"))
async def paid(client, query):
    user_id = query.from_user.id

    if user_id not in users:
        return

    users[user_id]["waiting_name"] = True

    await query.message.reply("📝 Send your UPI name:")

# ---------------- GIVE KEY (IMPORTANT - PEHLE) ----------------
@app.on_message(filters.command("givekey"))
async def give_key(client, message):
    try:
        if message.from_user.id != ADMIN_ID:
            return

        parts = message.text.split(maxsplit=2)

        if len(parts) < 3:
            return await message.reply("Usage:\n/givekey user_id KEY")

        user_id = int(parts[1])
        key = parts[2]

        await app.send_message(
            user_id,
            f"✅ Payment Successful!\n\n🔑 Your Key:\n{key}"
        )

        await message.reply("✅ Key Sent")

        users.pop(user_id, None)

    except Exception as e:
        await message.reply(f"Error: {e}")

# ---------------- GET NAME ----------------
@app.on_message(filters.text & ~filters.command(["givekey","setupi","start"]))
async def get_name(client, message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in users:
        return

    if not users[user_id].get("waiting_name"):
        return

    if len(text) < 3:
        return

    users[user_id]["waiting_name"] = False

    data = users[user_id]

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ])

    await app.send_message(
        ADMIN_ID,
        f"""💰 Payment Request

👤 User: {user_id}
🎮 Product: {data['product']}
📅 Days: {data['days']}
📝 Name: {text}""",
        reply_markup=kb
    )

    await message.reply("⏳ Waiting for approval...")

# ---------------- APPROVE ----------------
@app.on_callback_query(filters.regex("approve_"))
async def approve(client, query):
    if query.from_user.id != ADMIN_ID:
        return

    user_id = int(query.data.split("_")[1])

    await query.message.edit(
        f"""✅ Approved

👤 User ID: `{user_id}`

👉 Send:
/givekey {user_id} YOUR-KEY"""
    )

# ---------------- REJECT ----------------
@app.on_callback_query(filters.regex("reject_"))
async def reject(client, query):
    if query.from_user.id != ADMIN_ID:
        return

    user_id = int(query.data.split("_")[1])

    await app.send_message(user_id, "❌ Payment Rejected")
    await query.message.edit("❌ Rejected")

    users.pop(user_id, None)

@app.on_message(filters.command("broadcast"))
async def broadcast(client, message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.split(maxsplit=1)[1]

    sent = 0

    for uid in list(users.keys()):
        try:
            await app.send_message(uid, f"📢 {text}")
            sent += 1
        except:
            pass

    await message.reply(f"✅ Sent: {sent}")
    
# ---------------- SET UPI ----------------
@app.on_message(filters.command("setupi"))
async def set_upi(client, message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        new_upi = message.text.split()[1]
        db["upi"] = new_upi
        save_db(db)
        await message.reply(f"✅ UPI Updated: {new_upi}")
    except:
        await message.reply("Usage: /setupi yourupi@upi")

app.run()
