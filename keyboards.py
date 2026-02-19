from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Telefon modellari
PHONE_BRANDS = {
    'uz': [
        "📱 Apple", "📱 Samsung", "📱 Huawei", "📱 Oppo",
        "📱 Redmi", "📱 Vivo", "📱 Sony", "📱 Infinix",
        "📱 Tecno", "📱 Oneplus", "📱 Google Pixel",
        "📱 Nokia", "📱 Boshqa Model"
    ],
    'ru': [
        "📱 Apple", "📱 Samsung", "📱 Huawei", "📱 Oppo",
        "📱 Redmi", "📱 Vivo", "📱 Sony", "📱 Infinix",
        "📱 Tecno", "📱 Oneplus", "📱 Google Pixel",
        "📱 Nokia", "📱 Другая Модель"
    ]
}

# BREENDLARNI TO'G'RI NOMLARI (iconsiz)
BRAND_NAMES = {
    "📱 Apple": "Apple",
    "📱 Samsung": "Samsung",
    "📱 Huawei": "Huawei",
    "📱 Oppo": "Oppo",
    "📱 Redmi": "Redmi",
    "📱 Vivo": "Vivo",
    "📱 Sony": "Sony",
    "📱 Infinix": "Infinix",
    "📱 Tecno": "Tecno",
    "📱 Oneplus": "Oneplus",
    "📱 Google Pixel": "Google Pixel",
    "📱 Nokia": "Nokia",
    "📱 Boshqa Model": "Boshqa Model",
    "📱 Другая Модель": "Boshqa Model"
}

# Til tanlash keyboard
def get_language_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇷🇺 Русский")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# Telefon raqam keyboard
def get_phone_keyboard(lang='uz'):
    texts = {
        'uz': "📱 Telefon raqamni yuborish",
        'ru': "📱 Отправить номер телефона"
    }
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts[lang], request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# Lokatsiya keyboard
def get_location_keyboard(lang='uz'):
    texts = {
        'uz': "📍 Joylashuvni yuborish",
        'ru': "📍 Отправить местоположение"
    }
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts[lang], request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# Asosiy menyu keyboard (foydalanuvchi uchun)
def get_main_keyboard(lang='uz'):
    if lang == 'uz':
        texts = {
            'mobile': "📱 Uyali Aloqa",
            'favorites': "❤️ Sevimlilar",
            'exchange': "🔄 Ayirboshlash",
            'support': "📞 Qo'llab-quvvatlash",
            'seller': "👤 Sotuvchi bilan aloqa",
            'change_lang': "🌐 Tilni o'zgartirish"
        }
    else:
        texts = {
            'mobile': "📱 Мобильная связь",
            'favorites': "❤️ Избранное",
            'exchange': "🔄 Обмен",
            'support': "📞 Поддержка",
            'seller': "👤 Связаться с продавцом",
            'change_lang': "🌐 Изменить язык"
        }
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts['mobile'])],
            [KeyboardButton(text=texts['favorites']), KeyboardButton(text=texts['exchange'])],
            [KeyboardButton(text=texts['support']), KeyboardButton(text=texts['seller'])],
            [KeyboardButton(text=texts['change_lang'])]
        ],
        resize_keyboard=True
    )
    return keyboard

# Admin menyu keyboard (yangilangan)
def get_admin_keyboard(lang='uz'):
    if lang == 'uz':
        texts = {
            'users': "👥 Foydalanuvchilar",
            'block': "🔨 Bloklash/Blokdan ochish",
            'exchange': "🔄 Ayirboshlash takliflari",
            'add_ad': "📝 Elon qo'shish",
            'manage_ads': "📋 Elonlarni boshqarish",  # Yangi tugma
            'stats': "📊 Statistika",
            'broadcast': "📢 Xabar yuborish",
            'main': "🏠 Asosiy menyu"
        }
    else:
        texts = {
            'users': "👥 Пользователи",
            'block': "🔨 Блокировка/Разблокировка",
            'exchange': "🔄 Предложения обмена",
            'add_ad': "📝 Добавить объявление",
            'manage_ads': "📋 Управление объявлениями",  # Yangi tugma
            'stats': "📊 Статистика",
            'broadcast': "📢 Отправить сообщение",
            'main': "🏠 Главное меню"
        }
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts['users']), KeyboardButton(text=texts['block'])],
            [KeyboardButton(text=texts['exchange']), KeyboardButton(text=texts['add_ad'])],
            [KeyboardButton(text=texts['manage_ads']), KeyboardButton(text=texts['stats'])],  # Yangi qator
            [KeyboardButton(text=texts['broadcast'])],
            [KeyboardButton(text=texts['main'])]
        ],
        resize_keyboard=True
    )
    return keyboard

# Telefon brendlari keyboard (Uyali Aloqa uchun)
def get_brands_keyboard(lang='uz'):
    brands = PHONE_BRANDS[lang]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=brand)] for brand in brands] + 
                [[KeyboardButton(text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад")]],
        resize_keyboard=True
    )
    return keyboard

# Ayirboshlash uchun keyboard (TAYYOR tugmasi bilan)
def get_exchange_brands_keyboard(lang='uz'):
    brands = PHONE_BRANDS[lang]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=brand)] for brand in brands] + 
                [[KeyboardButton(text="✅ Tayyor" if lang == 'uz' else "✅ Готово")],
                 [KeyboardButton(text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад")]],
        resize_keyboard=True
    )
    return keyboard

# Elon uchun inline keyboard
def get_ad_inline_keyboard(ad_id, user_id, lang='uz', db=None):
    builder = InlineKeyboardBuilder()
    
    is_fav = False
    if db:
        is_fav = db.is_favorite(user_id, ad_id)
    
    fav_text = "❤️" if is_fav else "🤍"
    
    if lang == 'uz':
        builder.row(
            InlineKeyboardButton(text=fav_text, callback_data=f"fav_{ad_id}"),
            InlineKeyboardButton(text="📞 Qo'ng'iroq", callback_data=f"call_{ad_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_brands")
        )
    else:
        builder.row(
            InlineKeyboardButton(text=fav_text, callback_data=f"fav_{ad_id}"),
            InlineKeyboardButton(text="📞 Позвонить", callback_data=f"call_{ad_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_brands")
        )
    
    return builder.as_markup()