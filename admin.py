import logging
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards import get_admin_keyboard, get_brands_keyboard, BRAND_NAMES
from states import AddAd, Broadcast, BlockUser
from texts import TEXTS

logger = logging.getLogger(__name__)

def setup_admin_handlers(dp, bot, db, ADMIN_IDS):
    
    # Admin panelga kirish
    @dp.message(Command("admin"))
    async def admin_panel(message: types.Message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        user = db.get_user(message.from_user.id)
        lang = user['language'] if user else 'uz'
        
        await message.answer(
            "👨‍💼 Admin panel",
            reply_markup=get_admin_keyboard(lang)
        )

    # Foydalanuvchilar ro'yxati
    @dp.message(lambda message: message.text == "👥 Foydalanuvchilar")
    async def show_users(message: types.Message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        users = db.get_all_users()
        text = "👥 Foydalanuvchilar:\n\n"
        
        for user in users:
            text += f"ID: {user[0]}\nIsm: {user[1]}\nTel: {user[2]}\nTil: {user[4]}\nBlok: {'✅' if user[6] else '❌'}\n\n"
        
        await message.answer(text)

    # Bloklash/Blokdan ochish
    @dp.message(lambda message: message.text == "🔨 Bloklash/Blokdan ochish")
    async def block_user_start(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        await message.answer("📝 Foydalanuvchi ID sini yuboring:")
        await state.set_state(BlockUser.user_id)

    @dp.message(BlockUser.user_id)
    async def block_user_process(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        try:
            user_id = int(message.text)
            user = db.get_user(user_id)
            
            if user:
                if user['is_blocked'] == 0:
                    db.block_user(user_id)
                    await message.answer(f"✅ Foydalanuvchi {user_id} bloklandi!")
                    try:
                        await bot.send_message(user_id, "🚫 Siz admin tomonidan bloklandingiz!")
                    except:
                        pass
                else:
                    db.unblock_user(user_id)
                    await message.answer(f"✅ Foydalanuvchi {user_id} blokdan ochildi!")
                    try:
                        await bot.send_message(user_id, "✅ Siz blokdan ochildingiz!")
                    except:
                        pass
            else:
                await message.answer("❌ Bunday foydalanuvchi topilmadi!")
        except:
            await message.answer("❌ Noto'g'ri ID format!")
        
        await state.clear()

    # Ayirboshlash takliflari uchun inline keyboard
    def get_exchange_offer_keyboard(offer_id: int, lang: str = 'uz'):
        builder = InlineKeyboardBuilder()
        
        if lang == 'uz':
            builder.row(
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_offer_{offer_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_offer_{offer_id}")
            )
            builder.row(
                InlineKeyboardButton(text="💬 Xabar yozish", callback_data=f"message_user_{offer_id}")
            )
        else:
            builder.row(
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_offer_{offer_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_offer_{offer_id}")
            )
            builder.row(
                InlineKeyboardButton(text="💬 Написать", callback_data=f"message_user_{offer_id}")
            )
        
        return builder.as_markup()

      # Ayirboshlash takliflari (barchasi)
    @dp.message(lambda message: message.text == "🔄 Ayirboshlash takliflari")
    async def show_all_exchange_offers(message: types.Message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        user = db.get_user(message.from_user.id)
        lang = user['language'] if user else 'uz'
        
        offers = db.get_all_exchange_offers()
        
        if not offers:
            await message.answer("📭 Takliflar yo'q")
            return
        
        await message.answer(f"🔄 {len(offers)} ta taklif:")
        
        for offer in offers:
            offer_id = offer[0]
            user_id = offer[1]
            user_phone = offer[2]
            user_name = offer[3]
            wanted_brand = offer[4]
            wanted_model = offer[5]
            offer_brand = offer[6]
            offer_model = offer[7]
            offer_description = offer[8]
            status = offer[9]
            created_at = offer[10]
            
            status_text = "⏳ Kutilmoqda" if status == 'pending' else "✅ Qabul qilingan" if status == 'accepted' else "❌ Rad etilgan"
            
            text = (
                f"🔄 <b>Taklif #{offer_id}</b>\n"
                f"📊 {status_text}\n"
                f"📅 {created_at}\n\n"
                f"👤 {user_name}\n"
                f"📞 {user_phone}\n"
                f"🆔 <code>{user_id}</code>\n\n"
                f"🟢 <b>Kerak:</b> {wanted_brand} - {wanted_model}\n"
                f"🔵 <b>Taklif:</b> {offer_brand} - {offer_model}\n\n"
                f"📝 {offer_description}"
            )
            
            # Statusga qarab tugmalar
            builder = InlineKeyboardBuilder()
            if status == 'pending':
                builder.row(
                    InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_offer_{offer_id}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_offer_{offer_id}")
                )
                builder.row(
                    InlineKeyboardButton(text="💬 Xabar yozish", callback_data=f"message_user_{offer_id}")
                )
            else:
                builder.row(
                    InlineKeyboardButton(text="💬 Xabar yozish", callback_data=f"message_user_{offer_id}")
                )
            
            await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

    # Taklifni qabul qilish
    @dp.callback_query(lambda c: c.data and c.data.startswith('accept_offer_'))
    async def accept_offer(callback: types.CallbackQuery):
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ Ruxsat yo'q")
            return
        
        offer_id = int(callback.data.split('_')[2])
        db.update_exchange_offer_status(offer_id, 'accepted')
        
        # Taklif egasiga xabar
        offer = None
        offers = db.get_pending_exchange_offers()
        for o in offers:
            if o[0] == offer_id:
                offer = o
                break
        
        if offer:
            try:
                user_id = offer[1]
                user = db.get_user(user_id)
                if user:
                    lang = user['language']
                    text_uz = "✅ Sizning ayirboshlash taklifingiz qabul qilindi! Tez orada admin siz bilan bog'lanadi."
                    text_ru = "✅ Ваше предложение обмена принято! Скоро администратор свяжется с вами."
                    await bot.send_message(user_id, text_uz if lang == 'uz' else text_ru)
            except:
                pass
        
        await callback.answer("✅ Taklif qabul qilindi")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("✅ Taklif qabul qilindi")

    # Taklifni rad etish
    @dp.callback_query(lambda c: c.data and c.data.startswith('reject_offer_'))
    async def reject_offer(callback: types.CallbackQuery):
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ Ruxsat yo'q")
            return
        
        offer_id = int(callback.data.split('_')[2])
        db.update_exchange_offer_status(offer_id, 'rejected')
        
        # Taklif egasiga xabar
        offer = None
        offers = db.get_pending_exchange_offers()
        for o in offers:
            if o[0] == offer_id:
                offer = o
                break
        
        if offer:
            try:
                user_id = offer[1]
                user = db.get_user(user_id)
                if user:
                    lang = user['language']
                    text_uz = "❌ Sizning ayirboshlash taklifingiz rad etildi."
                    text_ru = "❌ Ваше предложение обмена отклонено."
                    await bot.send_message(user_id, text_uz if lang == 'uz' else text_ru)
            except:
                pass
        
        await callback.answer("❌ Taklif rad etildi")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("❌ Taklif rad etildi")

    # Foydalanuvchiga xabar yozish
    @dp.callback_query(lambda c: c.data and c.data.startswith('message_user_'))
    async def message_user(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ Ruxsat yo'q")
            return
        
        offer_id = int(callback.data.split('_')[2])
        
        # Taklif ma'lumotlarini olish
        offer = None
        offers = db.get_pending_exchange_offers()
        for o in offers:
            if o[0] == offer_id:
                offer = o
                break
        
        if offer:
            user_id = offer[1]
            await state.update_data(reply_user_id=user_id, offer_id=offer_id)
            await callback.message.answer("💬 Foydalanuvchiga yuboriladigan xabarni yozing:")
            await state.set_state("waiting_admin_reply")
        else:
            await callback.answer("❌ Taklif topilmadi")
        
        await callback.answer()

    # Admin javobini qabul qilish
    @dp.message(lambda message: message.text, F.state == "waiting_admin_reply")
    async def process_admin_reply(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        data = await state.get_data()
        user_id = data.get('reply_user_id')
        offer_id = data.get('offer_id')
        
        if user_id:
            try:
                user = db.get_user(user_id)
                if user:
                    lang = user['language']
                    header_uz = f"💬 Admin sizga taklif #{offer_id} bo'yicha xabar yubordi:\n\n"
                    header_ru = f"💬 Администратор отправил вам сообщение по предложению #{offer_id}:\n\n"
                    
                    await bot.send_message(
                        user_id,
                        (header_uz if lang == 'uz' else header_ru) + message.text
                    )
                    await message.answer("✅ Xabar yuborildi!")
                else:
                    await message.answer("❌ Foydalanuvchi topilmadi")
            except Exception as e:
                await message.answer(f"❌ Xatolik: {e}")
        
        await state.clear()
        
        user = db.get_user(message.from_user.id)
        lang = user['language'] if user else 'uz'
        await message.answer(
            "Admin panel",
            reply_markup=get_admin_keyboard(lang)
        )

    # Elon qo'shish
    @dp.message(lambda message: message.text == "📝 Elon qo'shish")
    async def add_ad_start(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        await message.answer("📱 Brendni tanlang:", reply_markup=get_brands_keyboard('uz'))
        await state.set_state(AddAd.brand)

    @dp.message(AddAd.brand)
    async def add_ad_brand(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        if message.text in ["🔙 Orqaga", "🔙 Назад"]:
            user = db.get_user(message.from_user.id)
            lang = user['language'] if user else 'uz'
            await state.clear()
            await message.answer(
                "Admin panel",
                reply_markup=get_admin_keyboard(lang)
            )
            return
        
        from keyboards import BRAND_NAMES
        if message.text in BRAND_NAMES:
            brand = BRAND_NAMES[message.text]
            await state.update_data(brand=brand)
            await message.answer("📱 Modelni kiriting:", reply_markup=ReplyKeyboardRemove())
            await state.set_state(AddAd.model)
        else:
            await message.answer("❌ Iltimos, brendni tanlang!")

    @dp.message(AddAd.model)
    async def add_ad_model(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        await state.update_data(model=message.text)
        await message.answer("💰 Narxni kiriting (so'm):")
        await state.set_state(AddAd.price)

    @dp.message(AddAd.price)
    async def add_ad_price(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        try:
            price = float(message.text.replace(" ", ""))
            await state.update_data(price=price)
            await message.answer("📝 Tavsif kiriting:")
            await state.set_state(AddAd.description)
        except:
            await message.answer("❌ Noto'g'ri narx! Qayta kiriting:")

    @dp.message(AddAd.description)
    async def add_ad_description(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        await state.update_data(description=message.text)
        await message.answer("📸 Rasm yuboring (yoki /skip ni bosing)")
        await state.set_state(AddAd.photo)

    @dp.message(AddAd.photo, F.photo)
    async def add_ad_photo(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        photo_id = message.photo[-1].file_id
        data = await state.get_data()
        
        # Sotuvchi raqami - +998880445550
        seller_phone = "+998880445550"
        
        ad_id = db.add_ad(
            brand=data['brand'],
            model=data['model'],
            price=data['price'],
            description=data['description'],
            photo_id=photo_id,
            seller_name=message.from_user.full_name,
            seller_phone=seller_phone,  # Doimiy raqam
            seller_location="Admin"
        )
        
        if ad_id:
            await message.answer("✅ Elon qo'shildi!")
            
            # Barcha foydalanuvchilarga xabar
            users = db.get_all_users()
            for user in users:
                try:
                    if user[6] == 0:  # is_blocked
                        lang = user[4]
                        if lang == 'uz':
                            text = (
                                f"🆕 <b>Yangi elon!</b>\n\n"
                                f"📱 {data['brand']} {data['model']}\n"
                                f"💰 {data['price']:,.0f} so'm\n\n"
                                f"📝 {data['description']}\n\n"
                                f"📞 Qo'ng'iroq qilish: {seller_phone}"
                            )
                        else:
                            text = (
                                f"🆕 <b>Новое объявление!</b>\n\n"
                                f"📱 {data['brand']} {data['model']}\n"
                                f"💰 {data['price']:,.0f} сум\n\n"
                                f"📝 {data['description']}\n\n"
                                f"📞 Позвонить: {seller_phone}"
                            )
                        
                        if photo_id:
                            await bot.send_photo(
                                user[0],
                                photo=photo_id,
                                caption=text,
                                parse_mode="HTML"
                            )
                        else:
                            await bot.send_message(
                                user[0],
                                text,
                                parse_mode="HTML"
                            )
                except:
                    pass
        else:
            await message.answer("❌ Xatolik yuz berdi")
        
        await state.clear()
        user = db.get_user(message.from_user.id)
        lang = user['language'] if user else 'uz'
        await message.answer(
            "Admin panel",
            reply_markup=get_admin_keyboard(lang)
        )

    @dp.message(AddAd.photo, Command("skip"))
    async def skip_photo(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        data = await state.get_data()
        
        # Sotuvchi raqami - +998880445550
        seller_phone = "+998880445550"
        
        ad_id = db.add_ad(
            brand=data['brand'],
            model=data['model'],
            price=data['price'],
            description=data['description'],
            photo_id=None,
            seller_name=message.from_user.full_name,
            seller_phone=seller_phone,  # Doimiy raqam
            seller_location="Admin"
        )
        
        if ad_id:
            await message.answer("✅ Elon qo'shildi!")
            
            # Barcha foydalanuvchilarga xabar
            users = db.get_all_users()
            for user in users:
                try:
                    if user[6] == 0:  # is_blocked
                        lang = user[4]
                        if lang == 'uz':
                            text = (
                                f"🆕 <b>Yangi elon!</b>\n\n"
                                f"📱 {data['brand']} {data['model']}\n"
                                f"💰 {data['price']:,.0f} so'm\n\n"
                                f"📝 {data['description']}\n\n"
                                f"📞 Qo'ng'iroq qilish: {seller_phone}"
                            )
                        else:
                            text = (
                                f"🆕 <b>Новое объявление!</b>\n\n"
                                f"📱 {data['brand']} {data['model']}\n"
                                f"💰 {data['price']:,.0f} сум\n\n"
                                f"📝 {data['description']}\n\n"
                                f"📞 Позвонить: {seller_phone}"
                            )
                        
                        await bot.send_message(
                            user[0],
                            text,
                            parse_mode="HTML"
                        )
                except:
                    pass
        else:
            await message.answer("❌ Xatolik yuz berdi")
        
        await state.clear()
        user = db.get_user(message.from_user.id)
        lang = user['language'] if user else 'uz'
        await message.answer(
            "Admin panel",
            reply_markup=get_admin_keyboard(lang)
        )

    # Elonlarni ko'rish va o'chirish
    @dp.message(lambda message: message.text == "📋 Elonlarni boshqarish")
    async def manage_ads(message: types.Message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        user = db.get_user(message.from_user.id)
        lang = user['language'] if user else 'uz'
        
        ads = db.get_all_ads_admin()
        
        if not ads:
            await message.answer("📭 Elonlar yo'q")
            return
        
        await message.answer(f"📋 {len(ads)} ta elon:")
        
        for ad in ads:
            ad_id = ad[0]
            brand = ad[1]
            model = ad[2]
            price = ad[3]
            desc = ad[4]
            photo_id = ad[5]
            is_active = ad[10]
            
            status = "✅ Faol" if is_active == 1 else "❌ Sotilgan"
            
            text = (
                f"📱 <b>ID: {ad_id}</b>\n"
                f"{brand} {model}\n"
                f"💰 {price:,.0f} so'm\n"
                f"📝 {desc[:50]}...\n"
                f"📊 {status}"
            )
            
            # O'chirish tugmasi
            builder = InlineKeyboardBuilder()
            if is_active == 1:
                builder.row(
                    InlineKeyboardButton(text="❌ Sotilgan deb belgilash", callback_data=f"delete_ad_{ad_id}")
                )
            
            if photo_id:
                await message.answer_photo(
                    photo=photo_id,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
            else:
                await message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )

    # Elonni o'chirish (sotilgan deb belgilash)
    @dp.callback_query(lambda c: c.data and c.data.startswith('delete_ad_'))
    async def delete_ad(callback: types.CallbackQuery):
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ Ruxsat yo'q")
            return
        
        ad_id = int(callback.data.split('_')[2])
        
        success = db.delete_ad(ad_id)
        
        if success:
            await callback.answer("✅ Elon sotilgan deb belgilandi")
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n❌ SOTILGAN",
                reply_markup=None
            )
        else:
            await callback.answer("❌ Xatolik yuz berdi")

    # Statistika
    @dp.message(lambda message: message.text == "📊 Statistika")
    async def show_stats(message: types.Message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        stats = db.get_stats()
        text = (
            f"📊 Statistika:\n\n"
            f"👥 Foydalanuvchilar: {stats['users']}\n"
            f"📝 Elonlar: {stats['ads']}\n"
            f"🔄 Kutilayotgan takliflar: {stats['pending_offers']}"
        )
        await message.answer(text)

    # Broadcast xabar yuborish
    @dp.message(lambda message: message.text == "📢 Xabar yuborish")
    async def broadcast_start(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        await message.answer("📝 Xabarni yozing (yoki /cancel):")
        await state.set_state(Broadcast.message)

    @dp.message(Broadcast.message)
    async def broadcast_message(message: types.Message, state: FSMContext):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        if message.text == "/cancel":
            await state.clear()
            user = db.get_user(message.from_user.id)
            lang = user['language'] if user else 'uz'
            await message.answer(
                "Bekor qilindi",
                reply_markup=get_admin_keyboard(lang)
            )
            return
        
        users = db.get_all_users()
        sent = 0
        failed = 0
        blocked = 0
        
        status_msg = await message.answer("⏳ Xabar yuborilmoqda...")
        
        for i, user in enumerate(users):
            try:
                if user[6] == 0:  # is_blocked
                    await bot.send_message(user[0], message.text)
                    sent += 1
                else:
                    blocked += 1
                
                if i % 10 == 0:
                    await status_msg.edit_text(f"⏳ Yuborilmoqda: {sent} ta")
            except:
                failed += 1
        
        await status_msg.edit_text(
            f"✅ Xabar yuborildi!\n\n"
            f"Yuborildi: {sent}\n"
            f"Bloklangan: {blocked}\n"
            f"Xatolik: {failed}"
        )
        
        await state.clear()

    # Admin asosiy menyuga qaytish
    @dp.message(lambda message: message.text == "🏠 Asosiy menyu")
    async def admin_main_menu(message: types.Message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        user = db.get_user(message.from_user.id)
        lang = user['language'] if user else 'uz'
        await message.answer(
            "Admin panel",
            reply_markup=get_admin_keyboard(lang)
        )