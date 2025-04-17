import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Logging konfiguratsiyasi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Ma'lumotlar bazasini yaratish
def setup_database():
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        landmark TEXT,
        additional_info TEXT,
        rating REAL DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

# Bot holatlari
MENU, ADD_NAME, ADD_ADDRESS, ADD_LANDMARK, ADD_INFO, RATE, DELETE_CONFIRM = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ishga tushganda birinchi xabar"""
    keyboard = [
        [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
        [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
        [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
        [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Assalomu alaykum! Restoran ma'lumotlari botiga xush kelibsiz. "
        "Nima qilishni xohlaysiz?",
        reply_markup=reply_markup
    )
    return MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asosiy menyu funksiyalari"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'add':
        await query.message.reply_text("Restoran nomini kiriting:")
        return ADD_NAME
    elif query.data == 'view':
        await show_restaurants(update, context)
        return MENU
    elif query.data == 'delete':
        await delete_restaurant_prompt(update, context)
        return DELETE_CONFIRM
    elif query.data == 'recommend':
        await recommend_restaurant(update, context)
        return MENU
    else:
        return MENU

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restoran nomini saqlash"""
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Restoran manzilini kiriting:")
    return ADD_ADDRESS

async def add_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restoran manzilini saqlash"""
    context.user_data['address'] = update.message.text
    await update.message.reply_text("Restoran mo'ljalini kiriting (yoki 'yo'q' deb yozing):")
    return ADD_LANDMARK

async def add_landmark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restoran mo'ljalini saqlash"""
    text = update.message.text
    if text.lower() != "yo'q":
        context.user_data['landmark'] = text
    else:
        context.user_data['landmark'] = ""
    
    await update.message.reply_text("Qo'shimcha ma'lumotlarni kiriting (yoki 'yo'q' deb yozing):")
    return ADD_INFO

async def add_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Qo'shimcha ma'lumotlarni saqlash va restoranni bazaga qo'shish"""
    text = update.message.text
    if text.lower() != "yo'q":
        context.user_data['additional_info'] = text
    else:
        context.user_data['additional_info'] = ""
    
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO restaurants (name, address, landmark, additional_info)
    VALUES (?, ?, ?, ?)
    ''', (
        context.user_data['name'],
        context.user_data['address'],
        context.user_data['landmark'],
        context.user_data['additional_info']
    ))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"Restoran '{context.user_data['name']}' muvaffaqiyatli qo'shildi!")
    
    # Asosiy menyuni qayta ko'rsatish
    keyboard = [
        [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
        [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
        [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
        [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
    return MENU

async def show_restaurants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha restoranlarni ko'rsatish"""
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM restaurants')
    restaurants = cursor.fetchall()
    conn.close()
    
    if not restaurants:
        if update.callback_query:
            await update.callback_query.message.reply_text("Hozircha restoranlar yo'q.")
        else:
            await update.message.reply_text("Hozircha restoranlar yo'q.")
    else:
        for rest in restaurants:
            rest_id, name, address, landmark, additional_info, rating = rest
            
            info_text = f"🏢 *{name}*\n"
            info_text += f"📍 Manzil: {address}\n"
            
            if landmark:
                info_text += f"🔍 Mo'ljal: {landmark}\n"
            
            if additional_info:
                info_text += f"ℹ️ Qo'shimcha: {additional_info}\n"
            
            if rating > 0:
                info_text += f"⭐ Reyting: {rating}/5\n"
            
            keyboard = [
                [InlineKeyboardButton("Baholash", callback_data=f'rate_{rest_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.message.reply_text(info_text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text(info_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Asosiy menyuni qayta ko'rsatish
    keyboard = [
        [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
        [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
        [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
        [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)

async def rate_restaurant_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restorani baholash uchun so'rov"""
    query = update.callback_query
    await query.answer()
    
    rest_id = int(query.data.split('_')[1])
    context.user_data['rating_restaurant_id'] = rest_id
    
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM restaurants WHERE id = ?', (rest_id,))
    rest_name = cursor.fetchone()[0]
    conn.close()
    
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data=f'star_1'),
            InlineKeyboardButton("2", callback_data=f'star_2'),
            InlineKeyboardButton("3", callback_data=f'star_3'),
            InlineKeyboardButton("4", callback_data=f'star_4'),
            InlineKeyboardButton("5", callback_data=f'star_5')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(f"{rest_name} restoraniga 1 dan 5 gacha baho bering:", reply_markup=reply_markup)
    return RATE

async def save_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restorani baholash"""
    query = update.callback_query
    await query.answer()
    
    rating = int(query.data.split('_')[1])
    rest_id = context.user_data['rating_restaurant_id']
    
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE restaurants SET rating = ? WHERE id = ?', (rating, rest_id))
    conn.commit()
    
    cursor.execute('SELECT name FROM restaurants WHERE id = ?', (rest_id,))
    rest_name = cursor.fetchone()[0]
    conn.close()
    
    await query.message.reply_text(f"{rest_name} restoraniga {rating}/5 baho berdingiz.")
    
    # Asosiy menyuni qayta ko'rsatish
    keyboard = [
        [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
        [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
        [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
        [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
    return MENU

async def delete_restaurant_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restorani o'chirish uchun ro'yxatni ko'rsatish"""
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM restaurants')
    restaurants = cursor.fetchall()
    conn.close()
    
    if not restaurants:
        if update.callback_query:
            await update.callback_query.message.reply_text("O'chirish uchun restoranlar yo'q.")
        else:
            await update.message.reply_text("O'chirish uchun restoranlar yo'q.")
        
        # Asosiy menyuni qayta ko'rsatish
        keyboard = [
            [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
            [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
            [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
            [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
        return MENU
    
    keyboard = []
    for rest_id, name in restaurants:
        keyboard.append([InlineKeyboardButton(name, callback_data=f'del_{rest_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text("O'chirish uchun restoranni tanlang:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("O'chirish uchun restoranni tanlang:", reply_markup=reply_markup)
    return DELETE_CONFIRM

async def delete_restaurant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restorani o'chirish"""
    query = update.callback_query
    await query.answer()
    
    rest_id = int(query.data.split('_')[1])
    
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM restaurants WHERE id = ?', (rest_id,))
    rest_name = cursor.fetchone()[0]
    
    cursor.execute('DELETE FROM restaurants WHERE id = ?', (rest_id,))
    conn.commit()
    conn.close()
    
    await query.message.reply_text(f"Restoran '{rest_name}' o'chirildi.")
    
    # Asosiy menyuni qayta ko'rsatish
    keyboard = [
        [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
        [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
        [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
        [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
    return MENU

async def recommend_restaurant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Eng yuqori reytingli restoranlarni tavsiya qilish"""
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM restaurants ORDER BY rating DESC LIMIT 3')
    restaurants = cursor.fetchall()
    conn.close()
    
    if not restaurants:
        if update.callback_query:
            await update.callback_query.message.reply_text("Hozircha tavsiya qilish uchun restoranlar yo'q.")
        else:
            await update.message.reply_text("Hozircha tavsiya qilish uchun restoranlar yo'q.")
    else:
        await (update.callback_query.message if update.callback_query else update.message).reply_text("⭐ Eng yaxshi restoranlar ⭐")
        
        for rest in restaurants:
            rest_id, name, address, landmark, additional_info, rating = rest
            
            info_text = f"🏢 *{name}*\n"
            info_text += f"📍 Manzil: {address}\n"
            
            if landmark:
                info_text += f"🔍 Mo'ljal: {landmark}\n"
            
            if additional_info:
                info_text += f"ℹ️ Qo'shimcha: {additional_info}\n"
            
            if rating > 0:
                info_text += f"⭐ Reyting: {rating}/5\n"
            
            if update.callback_query:
                await update.callback_query.message.reply_text(info_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(info_text, parse_mode='Markdown')
    
    # Asosiy menyuni qayta ko'rsatish
    keyboard = [
        [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
        [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
        [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
        [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Amalni bekor qilish"""
    await update.message.reply_text("Amal bekor qilindi.")
    
    # Asosiy menyuni qayta ko'rsatish
    keyboard = [
        [InlineKeyboardButton("Restoran qo'shish", callback_data='add')],
        [InlineKeyboardButton("Restoranlarni ko'rish", callback_data='view')],
        [InlineKeyboardButton("Restorani o'chirish", callback_data='delete')],
        [InlineKeyboardButton("Restoran tavsiya qilish", callback_data='recommend')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Nima qilishni xohlaysiz?", reply_markup=reply_markup)
    return MENU

async def main():
    # Ma'lumotlar bazasini sozlash
    setup_database()
    
    # Bot tokeni
    token = os.getenv("BOT_TOKEN", "7713917511:AAHFWbUngqXdCMPr8aC6kc1K2fmAMFvdv6M")
    
    # Bot yaratish
    application = ApplicationBuilder().token(token).build()
    
    # Avval webhook ni o'chirish
    await application.bot.delete_webhook(drop_pending_updates=True)
    
    # Suhbat modelini yaratish
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [CallbackQueryHandler(menu_handler)],
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_address)],
            ADD_LANDMARK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_landmark)],
            ADD_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_info)],
            RATE: [CallbackQueryHandler(save_rating, pattern=r'^star_')],
            DELETE_CONFIRM: [CallbackQueryHandler(delete_restaurant, pattern=r'^del_')]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True
    )
    
    # Rate qilish uchun handler
    application.add_handler(CallbackQueryHandler(rate_restaurant_prompt, pattern=r'^rate_'))
    
    # Suhbat modelini qo'shish
    application.add_handler(conv_handler)

    )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
