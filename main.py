import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from dotenv import load_dotenv

from database import Database
from keyboards import *
from states import Registration, ExchangeOffer, AddAd, Broadcast, BlockUser
from texts import TEXTS
from keep_alive import keep_alive
from admin import setup_admin_handlers

import sys
import os

# Debug uchun environment variable'larni tekshirish
print("🔍 Checking environment variables...")
print(f"BOT_TOKEN exists: {'Yes' if os.getenv('BOT_TOKEN') else 'No'}")
print(f"ADMIN_IDS: {os.getenv('ADMIN_IDS')}")
print(f"PYTHON_VERSION: {os.getenv('PYTHON_VERSION')}")
print(f"DATABASE_NAME: {os.getenv('DATABASE_NAME')}")
sys.stdout.flush()  # Loglarni darhol chiqarish

load_dotenv()

# Logging sozlamalari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot sozlamalari
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))
DATABASE_NAME = os.getenv('DATABASE_NAME', 'phone_sales.db')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database(DATABASE_NAME)

# Admin handlerni ulash
setup_admin_handlers(dp, bot, db, ADMIN_IDS)

# ADMIN_IDS ni xavfsiz o'qish
ADMIN_IDS = []
admin_ids_str = os.getenv('ADMIN_IDS')
if admin_ids_str:
    try:
        # Vergul bilan ajratilgan ID larni o'qish
        for id_str in admin_ids_str.split(','):
            id_str = id_str.strip()
            if id_str:
                ADMIN_IDS.append(int(id_str))
        print(f"✅ Loaded ADMIN_IDS: {ADMIN_IDS}")
    except ValueError as e:
        print(f"❌ Error parsing ADMIN_IDS: {e}")
        print(f"   Raw value: '{admin_ids_str}'")
else:
    print("⚠️ ADMIN_IDS environment variable not set!")

# Bot tokenini tekshirish
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ BOT_TOKEN environment variable not set!")
    sys.exit(1)
else:
    print(f"✅ BOT_TOKEN loaded (length: {len(BOT_TOKEN)})")

# Admin xabar yuborish
async def notify_admin(message: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message)
        except:
            pass

# Foydalanuvchini tekshirish
async def check_user(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer(TEXTS['uz']['not_registered'])
        return None
    if user['is_blocked'] == 1:
        await message.answer("🚫 Siz bloklangansiz / Вы заблокированы")
        return None
    return user

# Start komandasi
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    logger.info(f"User {user_id} started the bot")
    
    # Avvalgi stateni tozalash
    await state.clear()
    
    # Admin uchun alohida
    if user_id in ADMIN_IDS:
        if user:
            lang = user['language']
            await message.answer(
                "👨‍💼 Admin panelga xush kelibsiz!",
                reply_markup=get_admin_keyboard(lang)
            )
        else:
            await message.answer(TEXTS['uz']['welcome'])
            await message.answer(TEXTS['uz']['choose_lang'], reply_markup=get_language_keyboard())
            await state.set_state(Registration.language)
        return
    
    # Oddiy foydalanuvchi uchun
    await notify_admin(f"🆕 Yangi foydalanuvchi botni ishga tushirdi!\nID: {user_id}\nUsername: @{message.from_user.username}")
    
    if user:
        # Ro'yxatdan o'tgan foydalanuvchi
        lang = user['language']
        await message.answer(
            TEXTS[lang]['welcome'] + "\n\n" + TEXTS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang)
        )
    else:
        # Ro'yxatdan o'tmagan foydalanuvchi
        await message.answer(TEXTS['uz']['welcome'])
        await message.answer(TEXTS['uz']['choose_lang'], reply_markup=get_language_keyboard())
        await state.set_state(Registration.language)

# Til tanlash (ro'yxatdan o'tish uchun)
@dp.message(Registration.language)
async def process_language(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        lang = 'uz' if message.text == "🇺🇿 O'zbekcha" else 'ru'
        db.update_user_language(message.from_user.id, lang)
        await message.answer(
            "✅ Til o'zgartirildi!",
            reply_markup=get_admin_keyboard(lang)
        )
        await state.clear()
        return
    
    lang = 'uz' if message.text == "🇺🇿 O'zbekcha" else 'ru'
    await state.update_data(language=lang)
    await state.set_state(Registration.name)
    await message.answer(
        TEXTS[lang]['ask_name'],
        reply_markup=ReplyKeyboardRemove()
    )

# Ism qabul qilish
@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await state.clear()
        return
    
    if len(message.text) > 100:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        await message.answer("❌ Ism juda uzun! Qayta kiriting:")
        return
    
    await state.update_data(name=message.text)
    data = await state.get_data()
    lang = data.get('language', 'uz')
    await state.set_state(Registration.phone)
    await message.answer(
        TEXTS[lang]['ask_phone'],
        reply_markup=get_phone_keyboard(lang)
    )

# Telefon raqam qabul qilish
@dp.message(Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await state.clear()
        return
    
    if message.contact:
        phone = message.contact.phone_number
        await state.update_data(phone=phone)
        data = await state.get_data()
        lang = data.get('language', 'uz')
        await state.set_state(Registration.location)
        await message.answer(
            TEXTS[lang]['ask_location'],
            reply_markup=get_location_keyboard(lang)
        )
    else:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        await message.answer(
            "❌ Iltimos, telefon raqamni tugma orqali yuboring!",
            reply_markup=get_phone_keyboard(lang)
        )

# Lokatsiya qabul qilish
@dp.message(Registration.location)
async def process_location(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await state.clear()
        return
    
    if message.location:
        location = f"{message.location.latitude}, {message.location.longitude}"
        await state.update_data(location=location)
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Animatsiya
        animation_msg = await message.answer(TEXTS[lang]['checking'].format(""))
        await asyncio.sleep(0.3)
        await animation_msg.edit_text(TEXTS[lang]['checking'].format("."))
        await asyncio.sleep(0.3)
        await animation_msg.edit_text(TEXTS[lang]['checking'].format(".."))
        await asyncio.sleep(0.3)
        await animation_msg.edit_text(TEXTS[lang]['checking'].format("..."))
        await asyncio.sleep(0.3)
        
        # Ma'lumotlarni saqlash
        user_id = message.from_user.id
        success = db.add_user(
            user_id=user_id,
            full_name=data['name'],
            phone=data['phone'],
            location=location,
            language=lang
        )
        
        if success:
            await animation_msg.edit_text(TEXTS[lang]['registered'])
            await asyncio.sleep(1)
            await message.answer(
                TEXTS[lang]['main_menu'],
                reply_markup=get_main_keyboard(lang)
            )
            
            # Adminga xabar
            await notify_admin(
                f"✅ Yangi foydalanuvchi ro'yxatdan o'tdi!\n"
                f"ID: {user_id}\n"
                f"Ism: {data['name']}\n"
                f"Tel: {data['phone']}\n"
                f"Til: {lang}"
            )
        else:
            await message.answer(TEXTS[lang]['error'])
        
        await state.clear()
    else:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        await message.answer(
            TEXTS[lang]['ask_location'],
            reply_markup=get_location_keyboard(lang)
        )

# Uyali Aloqa bo'limi
@dp.message(lambda message: message.text in ["📱 Uyali Aloqa", "📱 Мобильная связь"])
async def mobile_section(message: types.Message, state: FSMContext):
    user = await check_user(message)
    if not user:
        return
    
    lang = user['language']
    await message.answer(
        TEXTS[lang]['choose_brand'],
        reply_markup=get_brands_keyboard(lang)
    )

# Brend tanlanganda (Uyali Aloqa uchun)
@dp.message(lambda message: message.text in (PHONE_BRANDS['uz'] + PHONE_BRANDS['ru']))
async def show_brand_ads(message: types.Message, state: FSMContext):
    user = await check_user(message)
    if not user:
        return
    
    lang = user['language']
    brand_text = message.text
    
    from keyboards import BRAND_NAMES
    if brand_text in BRAND_NAMES:
        brand = BRAND_NAMES[brand_text]
    else:
        brand = brand_text.replace("📱 ", "")
    
    ads = db.get_ads_by_brand(brand)
    
    if not ads:
        await message.answer(TEXTS[lang]['no_ads'])
        return
    
    for ad in ads:
        ad_id = ad[0]
        brand = ad[1]
        model = ad[2]
        price = ad[3]
        desc = ad[4]
        photo_id = ad[5]
        seller = ad[6]
        phone = ad[7]
        location = ad[8]
        created = ad[9]
        
        caption = (
            f"📱 <b>{brand} {model}</b>\n\n"
            f"💰 Narx: <b>{price:,.0f} so'm</b>\n"
            f"📝 {desc}\n\n"
            f"👤 Sotuvchi: {seller}\n"
            f"📍 {location}\n"
            f"📅 {created}"
        )
        
        # Sevimlilar va Orqaga tugmalari
        builder = InlineKeyboardBuilder()
        
        # Sevimlilar uchun yurakcha
        is_fav = db.is_favorite(message.from_user.id, ad_id)
        fav_text = "❤️" if is_fav else "🤍"
        
        if lang == 'uz':
            builder.row(
                InlineKeyboardButton(text=fav_text, callback_data=f"fav_{ad_id}"),
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_brands")
            )
        else:
            builder.row(
                InlineKeyboardButton(text=fav_text, callback_data=f"fav_{ad_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_brands")
            )
        
        if photo_id:
            await message.answer_photo(
                photo=photo_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer(
                caption,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )

# Sevimlilarga qo'shish/olib tashlash
@dp.callback_query(lambda c: c.data and c.data.startswith('fav_'))
async def process_favorite(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Iltimos avval ro'yxatdan o'ting!")
        return
    
    ad_id = int(callback.data.split('_')[1])
    lang = user['language']
    
    if db.is_favorite(callback.from_user.id, ad_id):
        db.remove_from_favorites(callback.from_user.id, ad_id)
        await callback.answer("❌ Sevimlilardan olib tashlandi")
        new_fav_text = "🤍"
    else:
        db.add_to_favorites(callback.from_user.id, ad_id)
        await callback.answer("❤️ Sevimlilarga qo'shildi")
        new_fav_text = "❤️"
    
    # Keyboardni yangilash
    try:
        builder = InlineKeyboardBuilder()
        if lang == 'uz':
            builder.row(
                InlineKeyboardButton(text=new_fav_text, callback_data=f"fav_{ad_id}"),
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_brands")
            )
        else:
            builder.row(
                InlineKeyboardButton(text=new_fav_text, callback_data=f"fav_{ad_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_brands")
            )
        
        await callback.message.edit_reply_markup(
            reply_markup=builder.as_markup()
        )
    except:
        pass

# Orqaga (callback uchun)
@dp.callback_query(lambda c: c.data == "back_to_brands")
async def back_to_brands(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    
    lang = user['language']
    await callback.message.delete()
    await callback.message.answer(
        TEXTS[lang]['choose_brand'],
        reply_markup=get_brands_keyboard(lang)
    )

# Sevimlilar bo'limi
@dp.message(lambda message: message.text in ["❤️ Sevimlilar", "❤️ Избранное"])
async def show_favorites(message: types.Message, state: FSMContext):
    user = await check_user(message)
    if not user:
        return
    
    lang = user['language']
    user_id = message.from_user.id
    
    # Sevimlilarni olish
    favorites = db.get_user_favorites(user_id)
    
    if not favorites:
        if lang == 'uz':
            await message.answer(
                "📭 <b>Sevimlilar bo'limi bo'sh</b>\n\n"
                "Elonlarni ko'rib, yurakcha ❤️ bosib sevimlilarga qo'shishingiz mumkin.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "📭 <b>Раздел избранного пуст</b>\n\n"
                "Вы можете просматривать объявления и добавлять их в избранное, нажимая на сердечко ❤️.",
                parse_mode="HTML"
            )
        return
    
    if lang == 'uz':
        await message.answer(f"❤️ <b>Sevimlilar</b> ({len(favorites)} ta):", parse_mode="HTML")
    else:
        await message.answer(f"❤️ <b>Избранное</b> ({len(favorites)} шт.):", parse_mode="HTML")
    
    for ad in favorites:
        ad_id = ad[0]
        brand = ad[1]
        model = ad[2]
        price = ad[3]
        desc = ad[4]
        photo_id = ad[5]
        seller = ad[6]
        phone = ad[7]
        location = ad[8]
        created = ad[9]
        
        caption = (
            f"📱 <b>{brand} {model}</b>\n\n"
            f"💰 Narx: <b>{price:,.0f} so'm</b>\n"
            f"📝 {desc}\n\n"
            f"👤 Sotuvchi: {seller}\n"
            f"📍 {location}\n"
            f"📅 {created}"
        )
        
        # Sevimlilardan olib tashlash tugmasi
        builder = InlineKeyboardBuilder()
        if lang == 'uz':
            builder.row(
                InlineKeyboardButton(text="❌ Sevimlilardan olib tashlash", callback_data=f"remove_fav_{ad_id}"),
            )
        else:
            builder.row(
                InlineKeyboardButton(text="❌ Удалить из избранного", callback_data=f"remove_fav_{ad_id}"),
            )
        
        if photo_id:
            await message.answer_photo(
                photo=photo_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer(
                caption,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )

# Sevimlilardan olib tashlash
@dp.callback_query(lambda c: c.data and c.data.startswith('remove_fav_'))
async def remove_favorite(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Iltimos avval ro'yxatdan o'ting!")
        return
    
    try:
        ad_id = int(callback.data.split('_')[2])
    except:
        await callback.answer("❌ Xatolik yuz berdi")
        return
    
    lang = user['language']
    
    db.remove_from_favorites(callback.from_user.id, ad_id)
    
    if lang == 'uz':
        await callback.answer("✅ Sevimlilardan olib tashlandi")
    else:
        await callback.answer("✅ Удалено из избранного")
    
    try:
        await callback.message.delete()
    except:
        pass

# AYIRBOSHLASH BO'LIMI
@dp.message(lambda message: message.text in ["🔄 Ayirboshlash", "🔄 Обмен"])
async def exchange_start(message: types.Message, state: FSMContext):
    """Ayirboshlash bo'limi"""
    user = await check_user(message)
    if not user:
        return
    
    lang = user['language']
    
    # State ni tozalaymiz
    await state.clear()
    
    if lang == 'uz':
        text = (
            "🔄 <b>Ayirboshlash</b>\n\n"
            "Telefoningiz haqida ma'lumot yozing va suratini yuboring.\n\n"
            "Misol: iPhone 13 Pro, 256GB, 9/10, Apple Watch ga almashtiraman"
        )
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📤 Ma'lumot yuborish")],
                [KeyboardButton(text="🔙 Orqaga"), KeyboardButton(text="🏠 Asosiy menyu")]
            ],
            resize_keyboard=True
        )
    else:
        text = (
            "🔄 <b>Обмен</b>\n\n"
            "Напишите информацию о вашем телефоне и отправьте фото.\n\n"
            "Пример: iPhone 13 Pro, 256GB, 9/10, меняю на Apple Watch"
        )
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📤 Отправить информацию")],
                [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 Главное меню")]
            ],
            resize_keyboard=True
        )
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    await state.update_data(step="exchange_main")
    logger.info(f"User {message.from_user.id} - Exchange main menu")

# BARCHA XABARLAR UCHUN UMUMIY HANDLER
@dp.message()
async def handle_all_messages(message: types.Message, state: FSMContext):
    """Barcha xabarlarni ushlash va state bo'yicha yo'naltirish"""
    user = db.get_user(message.from_user.id)
    if not user:
        await cmd_start(message, state)
        return
    
    lang = user['language']
    data = await state.get_data()
    current_step = data.get('step')
    
    logger.info(f"User {message.from_user.id} - Step: {current_step}, Message: {message.text}")
    
    # --- ASOSIY MENYU TUGMALARI ---
    
    # Uyali Aloqa
    if message.text in ["📱 Uyali Aloqa", "📱 Мобильная связь"]:
        await mobile_section(message, state)
        return
    
    # Sevimlilar
    if message.text in ["❤️ Sevimlilar", "❤️ Избранное"]:
        await show_favorites(message, state)
        return
    
    # Ayirboshlash (allaqachon handler bor)
    if message.text in ["🔄 Ayirboshlash", "🔄 Обмен"]:
        return  # Yuqoridagi handler ishlaydi
    
    # Qo'llab-quvvatlash
    if message.text in ["📞 Qo'llab-quvvatlash", "📞 Поддержка"]:
        if lang == 'uz':
            await message.answer("📞 Qo'llab-quvvatlash: +998880445550")
        else:
            await message.answer("📞 Поддержка: +998880445550")
        return
    
    # Sotuvchi bilan aloqa
    if message.text in ["👤 Sotuvchi bilan aloqa", "👤 Связаться с продавцом"]:
        if lang == 'uz':
            await message.answer("👤 Sotuvchi bilan aloqa: +998880445550")
        else:
            await message.answer("👤 Связаться с продавцом: +998880445550")
        return
    
    # Tilni o'zgartirish
    if message.text in ["🌐 Tilni o'zgartirish", "🌐 Изменить язык"]:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "🌐 Tilni tanlang / Выберите язык:",
            reply_markup=keyboard
        )
        await state.set_state("changing_language")
        return
    
    # Tilni o'zgartirish jarayoni
    if await state.get_state() == "changing_language":
        if message.text == "🇺🇿 O'zbekcha":
            new_lang = 'uz'
        elif message.text == "🇷🇺 Русский":
            new_lang = 'ru'
        else:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await message.answer(
                "❌ Iltimos, tilni tanlang!\n❌ Пожалуйста, выберите язык!",
                reply_markup=keyboard
            )
            return
        
        # Tilni yangilash
        db.update_user_language(message.from_user.id, new_lang)
        
        if new_lang == 'uz':
            await message.answer(
                "✅ Til muvaffaqiyatli o'zgartirildi!",
                reply_markup=get_main_keyboard(new_lang)
            )
        else:
            await message.answer(
                "✅ Язык успешно изменен!",
                reply_markup=get_main_keyboard(new_lang)
            )
        
        await state.clear()
        return
    
    # Orqaga qaytish
    if message.text in ["🔙 Orqaga", "🔙 Назад"]:
        await state.clear()
        await message.answer(
            TEXTS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang)
        )
        return
    
    # Asosiy menyu
    if message.text in ["🏠 Asosiy menyu", "🏠 Главное меню"]:
        await state.clear()
        await message.answer(
            TEXTS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang)
        )
        return
    
    # --- AYIRBOSHLASH BO'LIMI STEPLARI ---
    
    # Exchange main menu
    if current_step == "exchange_main":
        if message.text in ["📤 Ma'lumot yuborish", "📤 Отправить информацию"]:
            if lang == 'uz':
                await message.answer(
                    "📝 <b>Ma'lumot yozing</b>\n\n"
                    "Telefoningiz haqida ma'lumot yozing:",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
                        resize_keyboard=True
                    )
                )
            else:
                await message.answer(
                    "📝 <b>Напишите информацию</b>\n\n"
                    "Напишите информацию о вашем телефоне:",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="🔙 Назад")]],
                        resize_keyboard=True
                    )
                )
            await state.update_data(step="waiting_info")
            return
    
    # Ma'lumot kutish
    elif current_step == "waiting_info":
        if message.text in ["🔙 Orqaga", "🔙 Назад"]:
            await exchange_start(message, state)
            return
        
        # Ma'lumotni saqlash
        await state.update_data(info=message.text)
        await state.update_data(step="waiting_photo")
        
        if lang == 'uz':
            await message.answer(
                "📸 <b>Surat yuboring</b>\n\n"
                "Telefoningizning suratini yuboring:",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
                    resize_keyboard=True
                )
            )
        else:
            await message.answer(
                "📸 <b>Отправьте фото</b>\n\n"
                "Отправьте фото вашего телефона:",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔙 Назад")]],
                    resize_keyboard=True
                )
            )
        return
    
    # Surat kutish
    elif current_step == "waiting_photo":
        if message.text in ["🔙 Orqaga", "🔙 Назад"]:
            await exchange_start(message, state)
            return
        
        # Agar surat bo'lsa
        if message.photo:
            info_text = data.get('info', '')
            photo_id = message.photo[-1].file_id
            
            # Taklifni saqlash
            offer_id = db.add_exchange_offer_simple(
                user_id=message.from_user.id,
                user_phone=user['phone'],
                user_name=user['full_name'],
                offer_text=info_text,
                photos=photo_id
            )
            
            if offer_id:
                if lang == 'uz':
                    await message.answer(
                        f"✅ <b>Taklifingiz qabul qilindi!</b>\n\n"
                        f"Admin tez orada ko'rib chiqadi.",
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard(lang)
                    )
                else:
                    await message.answer(
                        f"✅ <b>Ваше предложение принято!</b>\n\n"
                        f"Администратор скоро рассмотрит.",
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard(lang)
                    )
                
                # Adminga xabar
                for admin_id in ADMIN_IDS:
                    try:
                        admin_text = (
                            f"🔄 <b>Yangi ayirboshlash taklifi</b>\n\n"
                            f"👤 {user['full_name']}\n"
                            f"📞 {user['phone']}\n"
                            f"🆔 <code>{message.from_user.id}</code>\n\n"
                            f"📝 {info_text}"
                        )
                        await bot.send_photo(admin_id, photo=photo_id, caption=admin_text, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"Error sending to admin: {e}")
            else:
                if lang == 'uz':
                    await message.answer("❌ Xatolik yuz berdi")
                else:
                    await message.answer("❌ Ошибка")
            
            await state.clear()
            return
        
        # Agar surat bo'lmasa
        else:
            if lang == 'uz':
                await message.answer("❌ Iltimos, surat yuboring!")
            else:
                await message.answer("❌ Пожалуйста, отправьте фото!")
            return

# Qo'llab-quvvatlash (qo'shimcha)
@dp.message(lambda message: message.text in ["📞 Qo'llab-quvvatlash", "📞 Поддержка"])
async def support_handler(message: types.Message, state: FSMContext):
    user = await check_user(message)
    if not user:
        return
    lang = user['language']
    if lang == 'uz':
        await message.answer("📞 Qo'llab-quvvatlash: +998880445550")
    else:
        await message.answer("📞 Поддержка: +998880445550")

# Sotuvchi bilan aloqa (qo'shimcha)
@dp.message(lambda message: message.text in ["👤 Sotuvchi bilan aloqa", "👤 Связаться с продавцом"])
async def seller_handler(message: types.Message, state: FSMContext):
    user = await check_user(message)
    if not user:
        return
    lang = user['language']
    if lang == 'uz':
        await message.answer("👤 Sotuvchi bilan aloqa: +998880445550")
    else:
        await message.answer("👤 Связаться с продавцом: +998880445550")

async def main():
    logger.info("🚀 Bot started")
    await notify_admin("🚀 Bot ishga tushdi!")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Polling error: {e}")
        await asyncio.sleep(5)
        # Qayta urinish
        await main()

if __name__ == '__main__':
    # Keep alive serverini ishga tushirish
    from keep_alive import start_keep_alive
    start_keep_alive()
    
    # Botni ishga tushirish
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            time.sleep(10)  # 10 soniya kutib qayta ishga tushirish