import telebot
from telebot import types
import os
import time
from config import *
from database import *

# ============================================
#           BOT INITIALIZATION
# ============================================
bot = telebot.TeleBot(BOT_TOKEN)
init_db()

print("=" * 50)
print("🤖 Bot is starting...")
print("=" * 50)


# ============================================
#           HELPER FUNCTIONS
# ============================================
def main_menu_keyboard():
    """Main menu ke buttons create karta hai"""
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=2
    )
    btn1 = types.KeyboardButton("🛒 Buy ID")
    btn2 = types.KeyboardButton("💰 Check Balance")
    btn3 = types.KeyboardButton("💳 Add Balance")
    btn4 = types.KeyboardButton("📞 Contact Admin")
    btn5 = types.KeyboardButton("📜 My Orders")
    btn6 = types.KeyboardButton("📦 Stock Status")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup


def buy_id_keyboard():
    """Buy ID ke price options inline buttons"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(
        "📧 1 Gmail + Pass — ₹20", 
        callback_data="buy_20"
    )
    btn2 = types.InlineKeyboardButton(
        "📧 3 Gmail + Pass — ₹58", 
        callback_data="buy_58"
    )
    btn3 = types.InlineKeyboardButton(
        "📧 5 Gmail + Pass — ₹90", 
        callback_data="buy_90"
    )
    btn_back = types.InlineKeyboardButton(
        "🔙 Back to Menu", 
        callback_data="back_menu"
    )
    markup.add(btn1, btn2, btn3, btn_back)
    return markup


def confirm_purchase_keyboard(price, count):
    """Purchase confirm karne ka button"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton(
        "✅ Confirm Purchase", 
        callback_data=f"confirm_{price}_{count}"
    )
    btn_no = types.InlineKeyboardButton(
        "❌ Cancel", 
        callback_data="cancel_purchase"
    )
    markup.add(btn_yes, btn_no)
    return markup


def admin_payment_keyboard(payment_id, user_id):
    """Admin ke liye approve/reject buttons"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_approve = types.InlineKeyboardButton(
        "✅ Approve", 
        callback_data=f"approve_{payment_id}_{user_id}"
    )
    btn_reject = types.InlineKeyboardButton(
        "❌ Reject", 
        callback_data=f"reject_{payment_id}_{user_id}"
    )
    markup.add(btn_approve, btn_reject)
    return markup


# ============================================
#           /start COMMAND
# ============================================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # User register karo
    register_user(user_id, username, first_name)

    welcome_text = f"""
🎉 **Welcome {first_name}!** 🎉

━━━━━━━━━━━━━━━━━━━━━
🤖 **Gmail ID Shop Bot**
━━━━━━━━━━━━━━━━━━━━━

📧 Yahan se aap Gmail IDs kharid sakte ho!

💰 **Price List:**
├ 1 Gmail + Pass = ₹20
├ 3 Gmail + Pass = ₹58
└ 5 Gmail + Pass = ₹90

🔽 Neeche menu se option choose karo:
"""
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


# ============================================
#           CHECK BALANCE
# ============================================
@bot.message_handler(
    func=lambda msg: msg.text == "💰 Check Balance"
)
def check_balance(message):
    user_id = message.from_user.id
    balance = get_balance(user_id)

    balance_text = f"""
💰 **Your Balance**
━━━━━━━━━━━━━━━━━━━━━
👤 User: {message.from_user.first_name}
🆔 ID: `{user_id}`
💵 Balance: **₹{balance:.2f}**
━━━━━━━━━━━━━━━━━━━━━

💳 Balance add karne ke liye 
"Add Balance" button dabao!
"""
    bot.send_message(
        message.chat.id, 
        balance_text, 
        parse_mode="Markdown"
    )


# ============================================
#           ADD BALANCE (QR Code Send)
# ============================================
@bot.message_handler(
    func=lambda msg: msg.text == "💳 Add Balance"
)
def add_balance_handler(message):
    user_id = message.from_user.id

    add_text = f"""
💳 **Add Balance**
━━━━━━━━━━━━━━━━━━━━━

📱 **Steps to Add Balance:**

1️⃣ Neeche diye QR Code ko scan karo
2️⃣ Payment karo (any UPI app se)
3️⃣ Payment hone ke baad amount type karo
   Example: `/paid 100`
4️⃣ Admin verify karke balance add karega

⚠️ **Note:** 
• Sirf UPI se payment karo
• Screenshot Admin ko bhejo
• Fake payment pe ban hoga!

━━━━━━━━━━━━━━━━━━━━━
"""
    bot.send_message(
        message.chat.id, 
        add_text, 
        parse_mode="Markdown"
    )

    # QR Code image send karo
    if os.path.exists(QR_CODE_PATH):
        with open(QR_CODE_PATH, 'rb') as qr_photo:
            bot.send_photo(
                message.chat.id, 
                qr_photo, 
                caption=(
                    "⬆️ **Ye QR Code scan karke payment karo**\n\n"
                    "Payment ke baad type karo:\n"
                    "`/paid <amount>`\n\n"
                    "Example: `/paid 100`"
                ),
                parse_mode="Markdown"
            )
    else:
        bot.send_message(
            message.chat.id,
            (
                "⚠️ QR Code available nahi hai!\n"
                f"Admin se contact karo: @{ADMIN_USERNAME}"
            )
        )


# ============================================
#      /paid COMMAND - Payment Request
# ============================================
@bot.message_handler(commands=['paid'])
def paid_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    first_name = message.from_user.first_name or "N/A"

    try:
        amount = float(message.text.split()[1])
        if amount <= 0:
            bot.send_message(
                message.chat.id, 
                "❌ Invalid amount! Positive number dalo."
            )
            return
    except (IndexError, ValueError):
        bot.send_message(
            message.chat.id, 
            "❌ Sahi format use karo!\n"
            "Example: `/paid 100`",
            parse_mode="Markdown"
        )
        return

    # Payment request create karo
    payment_id = create_payment_request(user_id, amount)

    # User ko confirm karo
    bot.send_message(
        message.chat.id,
        f"""
✅ **Payment Request Submitted!**
━━━━━━━━━━━━━━━━━━━━━
🆔 Request ID: #{payment_id}
💵 Amount: ₹{amount:.2f}
📊 Status: ⏳ Pending
━━━━━━━━━━━━━━━━━━━━━

⏳ Admin verify karega, thoda wait karo!
✅ Approve hone pe balance auto add hoga.
"""  ,
        parse_mode="Markdown"
    )

    # Admin ko notification bhejo
    admin_text = f"""
🔔 **NEW PAYMENT REQUEST!**
━━━━━━━━━━━━━━━━━━━━━
🆔 Payment ID: #{payment_id}
👤 User: {first_name} (@{username})
🔢 User ID: `{user_id}`
💵 Amount: ₹{amount:.2f}
⏰ Time: {time.strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━
"""
    bot.send_message(
        ADMIN_ID,
        admin_text,
        parse_mode="Markdown",
        reply_markup=admin_payment_keyboard(
            payment_id, user_id
        )
    )


# ============================================
#           BUY ID
# ============================================
@bot.message_handler(
    func=lambda msg: msg.text == "🛒 Buy ID"
)
def buy_id_handler(message):
    user_id = message.from_user.id
    balance = get_balance(user_id)
    stock = get_stock_count()

    buy_text = f"""
🛒 **Buy Gmail ID**
━━━━━━━━━━━━━━━━━━━━━
💵 Your Balance: **₹{balance:.2f}**
📦 Available Stock: **{stock} Gmail IDs**
━━━━━━━━━━━━━━━━━━━━━

📋 **Price List:**
┌─────────────────────────┐
│ 📧 1 Gmail + Pass = ₹20  │
│ 📧 3 Gmail + Pass = ₹58  │
│ 📧 5 Gmail + Pass = ₹90  │
└─────────────────────────┘

⬇️ Neeche se choose karo:
"""
    bot.send_message(
        message.chat.id, 
        buy_text, 
        parse_mode="Markdown",
        reply_markup=buy_id_keyboard()
    )


# ============================================
#     CALLBACK HANDLER (Inline Buttons)
# ============================================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    # ---- BUY OPTIONS ----
    if data == "buy_20":
        handle_buy_selection(call, 20, 1)

    elif data == "buy_58":
        handle_buy_selection(call, 58, 3)

    elif data == "buy_90":
        handle_buy_selection(call, 90, 5)

    # ---- CONFIRM PURCHASE ----
    elif data.startswith("confirm_"):
        parts = data.split("_")
        price = int(parts[1])
        count = int(parts[2])
        process_purchase(call, price, count)

    # ---- CANCEL PURCHASE ----
    elif data == "cancel_purchase":
        bot.edit_message_text(
            "❌ Purchase cancelled!",
            call.message.chat.id,
            call.message.message_id
        )

    # ---- BACK TO MENU ----
    elif data == "back_menu":
        bot.edit_message_text(
            "🔙 Main menu pe jao - neeche buttons use karo!",
            call.message.chat.id,
            call.message.message_id
        )

    # ---- ADMIN: APPROVE PAYMENT ----
    elif data.startswith("approve_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(
                call.id, "❌ Only Admin!"
            )
            return
        parts = data.split("_")
        payment_id = int(parts[1])
        target_user_id = int(parts[2])
        handle_approve(call, payment_id, target_user_id)

    # ---- ADMIN: REJECT PAYMENT ----
    elif data.startswith("reject_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(
                call.id, "❌ Only Admin!"
            )
            return
        parts = data.split("_")
        payment_id = int(parts[1])
        target_user_id = int(parts[2])
        handle_reject(call, payment_id, target_user_id)

    bot.answer_callback_query(call.id)


def handle_buy_selection(call, price, count):
    """Buy option select hone pe confirm puchta hai"""
    user_id = call.from_user.id
    balance = get_balance(user_id)
    stock = get_stock_count()

    if balance < price:
        bot.edit_message_text(
            f"""
❌ **Insufficient Balance!**
━━━━━━━━━━━━━━━━━━━━━
💵 Your Balance: ₹{balance:.2f}
💰 Required: ₹{price}
📉 Short: ₹{price - balance:.2f}
━━━━━━━━━━━━━━━━━━━━━

💳 Pehle "Add Balance" karke balance add karo!
""",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        return

    if stock < count:
        bot.edit_message_text(
            f"""
❌ **Stock Not Available!**
━━━━━━━━━━━━━━━━━━━━━
📦 Available: {stock} Gmail IDs
📋 Required: {count} Gmail IDs
━━━━━━━━━━━━━━━━━━━━━

⏳ Thoda wait karo, Admin stock add karega!
Contact: @{ADMIN_USERNAME}
""",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        return

    # Confirm button dikhao
    bot.edit_message_text(
        f"""
🛒 **Confirm Purchase?**
━━━━━━━━━━━━━━━━━━━━━
📧 Gmail IDs: {count}
💰 Price: ₹{price}
💵 Your Balance: ₹{balance:.2f}
💵 After Purchase: ₹{balance - price:.2f}
━━━━━━━━━━━━━━━━━━━━━

⚠️ Confirm karne ke baad refund nahi hoga!
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=confirm_purchase_keyboard(price, count)
    )


def process_purchase(call, price, count):
    """Purchase process karta hai - gmail bhejta hai"""
    user_id = call.from_user.id
    balance = get_balance(user_id)

    # Double check balance
    if balance < price:
        bot.edit_message_text(
            "❌ Insufficient balance!",
            call.message.chat.id,
            call.message.message_id
        )
        return

    # Available gmails fetch karo
    gmails = get_available_gmails(count)

    if len(gmails) < count:
        bot.edit_message_text(
            "❌ Sorry! Stock khatam ho gaya!",
            call.message.chat.id,
            call.message.message_id
        )
        return

    # Balance deduct karo
    deduct_balance(user_id, price)

    # Gmail details format karo
    gmail_text = ""
    for i, gmail in enumerate(gmails, 1):
        mark_gmail_sold(gmail['id'], user_id)
        gmail_text += (
            f"┌ **{i}.**\n"
            f"│ 📧 Email: `{gmail['email']}`\n"
            f"│ 🔑 Pass:  `{gmail['password']}`\n"
            f"└────────────────\n"
        )

    # Purchase history save karo
    add_purchase_history(user_id, price, count)

    # Success message
    new_balance = get_balance(user_id)
    bot.edit_message_text(
        f"""
✅ **Purchase Successful!** 🎉
━━━━━━━━━━━━━━━━━━━━━
📧 Gmail IDs: {count}
💰 Paid: ₹{price}
💵 Remaining Balance: ₹{new_balance:.2f}
━━━━━━━━━━━━━━━━━━━━━

📋 **Your Gmail IDs:**
━━━━━━━━━━━━━━━━━━━━━
{gmail_text}
━━━━━━━━━━━━━━━━━━━━━

⚠️ Ye message save kar lo!
📌 Tip: Click karke copy kar sakte ho!
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

    # Admin ko notify karo
    bot.send_message(
        ADMIN_ID,
        f"""
🛒 **NEW PURCHASE!**
━━━━━━━━━━━━━━━━━━━━━
👤 User: {call.from_user.first_name}
🆔 ID: {user_id}
📧 Gmail IDs: {count}
💰 Amount: ₹{price}
━━━━━━━━━━━━━━━━━━━━━
""",
        parse_mode="Markdown"
    )


def handle_approve(call, payment_id, target_user_id):
    """Admin payment approve karta hai"""
    result_user_id, result = approve_payment(payment_id)

    if result_user_id is None:
        bot.edit_message_text(
            f"❌ Error: {result}",
            call.message.chat.id,
            call.message.message_id
        )
        return

    amount = result
    new_balance = get_balance(target_user_id)

    # Admin ko update karo
    bot.edit_message_text(
        call.message.text + 
        f"\n\n✅ **APPROVED!**\n"
        f"₹{amount} added to user {target_user_id}\n"
        f"New Balance: ₹{new_balance:.2f}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

    # User ko notify karo
    bot.send_message(
        target_user_id,
        f"""
✅ **Payment Approved!** 🎉
━━━━━━━━━━━━━━━━━━━━━
🆔 Payment ID: #{payment_id}
💵 Amount Added: ₹{amount:.2f}
💰 New Balance: ₹{new_balance:.2f}
━━━━━━━━━━━━━━━━━━━━━

Ab aap "Buy ID" se Gmail kharid sakte ho! 🛒
""",
        parse_mode="Markdown"
    )


def handle_reject(call, payment_id, target_user_id):
    """Admin payment reject karta hai"""
    result_user_id, result = reject_payment(payment_id)

    if result_user_id is None:
        bot.edit_message_text(
            f"❌ Error: {result}",
            call.message.chat.id,
            call.message.message_id
        )
        return

    # Admin ko update karo
    bot.edit_message_text(
        call.message.text + "\n\n❌ **REJECTED!**",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

    # User ko notify karo
    bot.send_message(
        target_user_id,
        f"""
❌ **Payment Rejected!**
━━━━━━━━━━━━━━━━━━━━━
🆔 Payment ID: #{payment_id}
📊 Status: Rejected
━━━━━━━━━━━━━━━━━━━━━

⚠️ Agar aapne sach mein payment kiya hai 
to Admin se contact karo: @{ADMIN_USERNAME}
""",
        parse_mode="Markdown"
    )


# ============================================
#           CONTACT ADMIN
# ============================================
@bot.message_handler(
    func=lambda msg: msg.text == "📞 Contact Admin"
)
def contact_admin(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        "💬 Chat with Admin", 
        url=f"https://t.me/{ADMIN_USERNAME}"
    )
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        f"""
📞 **Contact Admin**
━━━━━━━━━━━━━━━━━━━━━
👤 Admin: @{ADMIN_USERNAME}

📋 **Admin se contact karo agar:**
• Payment issue ho
• Gmail kaam na kare
• Koi complaint ho
• Bulk order karna ho
━━━━━━━━━━━━━━━━━━━━━
""",
        parse_mode="Markdown",
        reply_markup=markup
    )


# ============================================
#           MY ORDERS
# ============================================
@bot.message_handler(
    func=lambda msg: msg.text == "📜 My Orders"
)
def my_orders(message):
    user_id = message.from_user.id
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM purchase_history 
        WHERE user_id = ? 
        ORDER BY purchase_date DESC LIMIT 10
    ''', (user_id,))
    orders = c.fetchall()
    conn.close()

    if not orders:
        bot.send_message(
            message.chat.id,
            "📜 Aapne abhi tak koi purchase nahi ki!"
        )
        return

    orders_text = "📜 **Your Recent Orders**\n"
    orders_text += "━━━━━━━━━━━━━━━━━━━━━\n"

    for order in orders:
        orders_text += (
            f"🛒 {order['gmail_count']} Gmail IDs "
            f"— ₹{order['amount']:.0f} "
            f"— {order['purchase_date']}\n"
        )

    orders_text += "━━━━━━━━━━━━━━━━━━━━━"

    bot.send_message(
        message.chat.id, 
        orders_text, 
        parse_mode="Markdown"
    )


# ============================================
#           STOCK STATUS
# ============================================
@bot.message_handler(
    func=lambda msg: msg.text == "📦 Stock Status"
)
def stock_status(message):
    stock = get_stock_count()
    status_emoji = "🟢" if stock >= 10 else (
        "🟡" if stock >= 5 else "🔴"
    )

    bot.send_message(
        message.chat.id,
        f"""
📦 **Stock Status**
━━━━━━━━━━━━━━━━━━━━━
{status_emoji} Available Gmail IDs: **{stock}**
━━━━━━━━━━━━━━━━━━━━━

🟢 = Stock Available (10+)
🟡 = Low Stock (5-9)
🔴 = Very Low Stock (0-4)
""",
        parse_mode="Markdown"
    )


# ============================================
#        ADMIN COMMANDS
# ============================================

# --- Add Gmail to Stock ---
@bot.message_handler(commands=['addgmail'])
def add_gmail_command(message):
    """Admin command: /addgmail email@gmail.com password123"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(
            message.chat.id, 
            "❌ Only Admin can use this!"
        )
        return

    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(
                message.chat.id,
                "❌ Format: `/addgmail email password`",
                parse_mode="Markdown"
            )
            return

        email = parts[1]
        password = parts[2]
        add_gmail_to_stock(email, password)

        stock = get_stock_count()
        bot.send_message(
            message.chat.id,
            f"""
✅ **Gmail Added to Stock!**
━━━━━━━━━━━━━━━━━━━━━
📧 Email: `{email}`
🔑 Pass: `{password}`
📦 Total Stock: {stock}
━━━━━━━━━━━━━━━━━━━━━
""",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"❌ Error: {str(e)}"
        )


# --- Bulk Add Gmail ---
@bot.message_handler(commands=['bulkadd'])
def bulk_add_command(message):
    """
    Admin command - multiple gmails add:
    /bulkadd
    email1@gmail.com:password1
    email2@gmail.com:password2
    email3@gmail.com:password3
    """
    if message.from_user.id != ADMIN_ID:
        return

    try:
        lines = message.text.strip().split('\n')[1:]
        if not lines:
            bot.send_message(
                message.chat.id,
                "❌ Format:\n"
                "`/bulkadd\n"
                "email1:pass1\n"
                "email2:pass2`",
                parse_mode="Markdown"
            )
            return

        count = 0
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                email = parts[0].strip()
                password = parts[1].strip()
                add_gmail_to_stock(email, password)
                count += 1

        stock = get_stock_count()
        bot.send_message(
            message.chat.id,
            f"""
✅ **Bulk Gmail Added!**
━━━━━━━━━━━━━━━━━━━━━
📧 Added: {count} Gmail IDs
📦 Total Stock: {stock}
━━━━━━━━━━━━━━━━━━━━━
""",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"❌ Error: {str(e)}"
        )


# --- Admin: Manual Add Balance ---
@bot.message_handler(commands=['addbal'])
def admin_add_balance(message):
    """/addbal user_id amount"""
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split()
        target_user_id = int(parts[1])
        amount = float(parts[2])

        add_balance(target_user_id, amount)
        new_bal = get_balance(target_user_id)

        bot.send_message(
            message.chat.id,
            f"""
✅ **Balance Added!**
━━━━━━━━━━━━━━━━━━━━━
👤 User ID: {target_user_id}
💵 Added: ₹{amount:.2f}
💰 New Balance: ₹{new_bal:.2f}
━━━━━━━━━━━━━━━━━━━━━
""",
            parse_mode="Markdown"
        )

        # User ko notify karo
        bot.send_message(
            target_user_id,
            f"""
✅ **Balance Added by Admin!**
💵 Amount: ₹{amount:.2f}
💰 New Balance: ₹{new_bal:.2f}
""",
            parse_mode="Markdown"
        )
    except (IndexError, ValueError):
        bot.send_message(
            message.chat.id,
            "❌ Format: `/addbal user_id amount`",
            parse_mode="Markdown"
        )


# --- Admin: View All Users ---
@bot.message_handler(commands=['users'])
def admin_view_users(message):
    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()
    if not users:
        bot.send_message(message.chat.id, "No users found!")
        return

    text = "👥 **All Users**\n━━━━━━━━━━━━━━━━\n"
    for user in users:
        text += (
            f"👤 {user['first_name']} "
            f"| ID: `{user['user_id']}` "
            f"| ₹{user['balance']:.2f}\n"
        )

    bot.send_message(
        message.chat.id, text, parse_mode="Markdown"
    )


# --- Admin: View Pending Payments ---
@bot.message_handler(commands=['pending'])
def admin_pending_payments(message):
    if message.from_user.id != ADMIN_ID:
        return

    payments = get_pending_payments()
    if not payments:
        bot.send_message(
            message.chat.id, 
            "✅ No pending payments!"
        )
        return

    for p in payments:
        bot.send_message(
            message.chat.id,
            f"""
⏳ **Pending Payment**
━━━━━━━━━━━━━━━━━━━━━
🆔 Payment ID: #{p['id']}
👤 User: {p['first_name']} (@{p['username']})
💵 Amount: ₹{p['amount']:.2f}
⏰ Time: {p['created_at']}
━━━━━━━━━━━━━━━━━━━━━
""",
            parse_mode="Markdown",
            reply_markup=admin_payment_keyboard(
                p['id'], p['user_id']
            )
        )


# --- Admin: View Stock ---
@bot.message_handler(commands=['stock'])
def admin_stock(message):
    if message.from_user.id != ADMIN_ID:
        return

    stock = get_stock_count()
    bot.send_message(
        message.chat.id,
        f"📦 Available Stock: **{stock}** Gmail IDs",
        parse_mode="Markdown"
    )


# --- Admin: Broadcast Message ---
@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    """/broadcast Your message here"""
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace('/broadcast ', '', 1)
    if text == '/broadcast':
        bot.send_message(
            message.chat.id,
            "❌ Format: `/broadcast Your message`",
            parse_mode="Markdown"
        )
        return

    users = get_all_users()
    sent = 0
    failed = 0

    for user in users:
        try:
            bot.send_message(
                user['user_id'],
                f"📢 **Admin Broadcast:**\n\n{text}",
                parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            failed += 1

    bot.send_message(
        message.chat.id,
        f"📢 Broadcast sent!\n"
        f"✅ Sent: {sent}\n❌ Failed: {failed}"
    )


# --- Admin Help ---
@bot.message_handler(commands=['adminhelp'])
def admin_help(message):
    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(
        message.chat.id,
        """
🔧 **Admin Commands**
━━━━━━━━━━━━━━━━━━━━━

📧 **Gmail Management:**
`/addgmail email pass` - Add 1 gmail
`/bulkadd` - Add multiple gmails
`/stock` - Check stock

💰 **Balance Management:**
`/addbal user_id amount` - Add balance
`/pending` - View pending payments

👥 **User Management:**
`/users` - View all users

📢 **Other:**
`/broadcast message` - Send to all users
`/adminhelp` - Show this help

━━━━━━━━━━━━━━━━━━━━━
""",
        parse_mode="Markdown"
    )


# ============================================
#           HELP COMMAND
# ============================================
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        f"""
❓ **Help & Guide**
━━━━━━━━━━━━━━━━━━━━━

📋 **How to Buy Gmail IDs:**

1️⃣ **Add Balance:**
   • "💳 Add Balance" button dabao
   • QR Code scan karke payment karo
   • `/paid <amount>` type karo
   • Admin approve karega

2️⃣ **Buy Gmail:**
   • "🛒 Buy ID" button dabao
   • Plan choose karo (₹20/₹58/₹90)
   • Confirm karo
   • Gmail + Password mil jayega!

3️⃣ **Check Balance:**
   • "💰 Check Balance" button dabao

━━━━━━━━━━━━━━━━━━━━━
💰 **Price List:**
├ 1 Gmail = ₹20
├ 3 Gmail = ₹58
└ 5 Gmail = ₹90

📞 Problem? Contact: @{ADMIN_USERNAME}
━━━━━━━━━━━━━━━━━━━━━
""",
        parse_mode="Markdown"
    )


# ============================================
#        UNKNOWN MESSAGE HANDLER
# ============================================
@bot.message_handler(func=lambda msg: True)
def unknown_message(message):
    bot.send_message(
        message.chat.id,
        "❓ Ye command samajh nahi aaya!\n"
        "Neeche menu ke buttons use karo 👇",
        reply_markup=main_menu_keyboard()
    )


# ============================================
#              START BOT
# ============================================
if __name__ == "__main__":
    print("✅ Bot is running!")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print("=" * 50)

    # Bot start karo (infinite polling)
    bot.infinity_polling(
        timeout=60, 
        long_polling_timeout=60
    )