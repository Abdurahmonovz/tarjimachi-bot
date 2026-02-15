import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from googletrans import Translator
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Logging sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot tokenini environment dan olish
API_TOKEN = os.getenv('BOT_TOKEN')

if not API_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# Bot obyektlari
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
translator = Translator()

# Foydalanuvchilar tarixi
user_history = {}


# Tugmalar yaratish
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbekcha ➡ 🇷🇺 Ruscha")],
            [KeyboardButton(text="🇷🇺 Ruscha ➡ 🇺🇿 O'zbekcha")],
            [KeyboardButton(text="🇺🇸 English ➡ 🇺🇿 O'zbekcha")],
            [KeyboardButton(text="🇺🇿 O'zbekcha ➡ 🇺🇸 English")],
            [KeyboardButton(text="🇬🇧 English ➡ 🇷🇺 Russian")],
            [KeyboardButton(text="🇷🇺 Russian ➡ 🇬🇧 English")],
            [KeyboardButton(text="📋 So'nggi tarjimalar"), KeyboardButton(text="⚙️ Sozlamalar")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Tarjima qilish uchun tilni tanlang..."
    )
    return keyboard


def get_back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Asosiy menyuga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_language_buttons():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿➡🇷🇺", callback_data="uz_ru"),
        InlineKeyboardButton(text="🇷🇺➡🇺🇿", callback_data="ru_uz"),
        InlineKeyboardButton(text="🇺🇸➡🇺🇿", callback_data="en_uz")
    )
    builder.row(
        InlineKeyboardButton(text="🇺🇿➡🇺🇸", callback_data="uz_en"),
        InlineKeyboardButton(text="🇬🇧➡🇷🇺", callback_data="en_ru"),
        InlineKeyboardButton(text="🇷🇺➡🇬🇧", callback_data="ru_en")
    )
    return builder.as_markup()


# Start komandasi
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = """
    🌍 *Tarjima Botiga Xush Kelibsiz!*

    *Mening xususiyatlarim:*
    ✅ 6 xil til juftligida tarjima
    ✅ Tezkor va aniq tarjima
    ✅ Zamonlarga mos grammatika
    ✅ Tarjima tarixini saqlash

    *Foydalanish uchun:*
    1. Quyidagi tugmalardan til juftligini tanlang
    2. Tarjima qilmoqchi bo'lgan matningizni yuboring
    3. Natijani darhol oling!

    📝 *Mavjud tillar:*
    • O'zbekcha ⇄ Ruscha
    • O'zbekcha ⇄ Inglizcha
    • Inglizcha ⇄ Ruscha
    """

    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


# Asosiy menyu tugmalarini qayta ishlash
@dp.message(lambda message: message.text in [
    "🇺🇿 O'zbekcha ➡ 🇷🇺 Ruscha",
    "🇷🇺 Ruscha ➡ 🇺🇿 O'zbekcha",
    "🇺🇸 English ➡ 🇺🇿 O'zbekcha",
    "🇺🇿 O'zbekcha ➡ 🇺🇸 English",
    "🇬🇧 English ➡ 🇷🇺 Russian",
    "🇷🇺 Russian ➡ 🇬🇧 English"
])
async def handle_translation_mode(message: types.Message):
    user_id = message.from_user.id

    # Tanlangan til juftligini aniqlash
    mode_map = {
        "🇺🇿 O'zbekcha ➡ 🇷🇺 Ruscha": ("uz", "ru"),
        "🇷🇺 Ruscha ➡ 🇺🇿 O'zbekcha": ("ru", "uz"),
        "🇺🇸 English ➡ 🇺🇿 O'zbekcha": ("en", "uz"),
        "🇺🇿 O'zbekcha ➡ 🇺🇸 English": ("uz", "en"),
        "🇬🇧 English ➡ 🇷🇺 Russian": ("en", "ru"),
        "🇷🇺 Russian ➡ 🇬🇧 English": ("ru", "en")
    }

    mode = mode_map[message.text]
    user_history[user_id] = {"mode": mode, "history": []}

    mode_names = {
        "uz_ru": "O'zbekcha ➡ Ruscha",
        "ru_uz": "Ruscha ➡ O'zbekcha",
        "en_uz": "Inglizcha ➡ O'zbekcha",
        "uz_en": "O'zbekcha ➡ Inglizcha",
        "en_ru": "Inglizcha ➡ Ruscha",
        "ru_en": "Ruscha ➡ Inglizcha"
    }

    mode_key = f"{mode[0]}_{mode[1]}"
    mode_text = mode_names.get(mode_key, "Tanlangan til")

    await message.answer(
        f"✅ *{mode_text}* rejimi tanlandi!\n\n"
        f"Endi tarjima qilmoqchi bo'lgan matningizni yuboring:",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard()
    )


# Orqaga qaytish
@dp.message(lambda message: message.text == "🔙 Asosiy menyuga qaytish")
async def back_to_main(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=get_main_keyboard())


# Tarjima qilish funksiyasi
async def translate_text(text, src, dest):
    try:
        # Google Translate API orqali tarjima
        translated = GoogleTranslator(source=src, target=dest).translate(text)
        return translated
    except Exception as e:
        logger.error(f"Translation error: {e}")
        try:
            # Zahirada saqlangan tarjima
            result = translator.translate(text, src=src, dest=dest)
            return result.text
        except Exception as e2:
            logger.error(f"Backup translation error: {e2}")
            return "❌ Tarjima qilishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."


# Matn tarjimasi
@dp.message()
async def handle_translation(message: types.Message):
    user_id = message.from_user.id

    # Agar foydalanuvchi tarixi bo'lmasa
    if user_id not in user_history:
        await message.answer("Iltimos, avval tarjima rejimini tanlang!", reply_markup=get_main_keyboard())
        return

    # Agar orqaga qaytish bo'lsa
    if message.text == "🔙 Asosiy menyuga qaytish":
        return

    # Agar sozlamalar yoki tarix bo'lsa
    if message.text == "📋 So'nggi tarjimalar":
        history = user_history.get(user_id, {}).get("history", [])
        if history:
            history_text = "📜 *So'nggi 5 ta tarjima:*\n\n"
            for i, item in enumerate(history[-5:], 1):
                history_text += f"{i}. *Asl:* {item['original'][:50]}...\n"
                history_text += f"   *Tarjima:* {item['translated'][:50]}...\n\n"
        else:
            history_text = "📭 Tarjima tarixi bo'sh"
        await message.answer(history_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
        return

    if message.text == "⚙️ Sozlamalar":
        settings_text = """
        ⚙️ *Sozlamalar*

        *Hozirgi rejim:* {}

        *Qo'shimcha imkoniyatlar (tez orada):*
        ✅ Avto-tarjima rejimi
        ✅ Matnni ovozga aylantirish
        ✅ Lug'at qo'shish
        ✅ Shaxsiy sozlamalar

        Iltimos, sabr qiling, tez orada yangilanishlar kutilmoqda!
        """
        current_mode = user_history.get(user_id, {}).get("mode", ["", ""])
        mode_text = f"{current_mode[0]} ➡ {current_mode[1]}" if current_mode else "Tanlanmagan"
        await message.answer(settings_text.format(mode_text), parse_mode="Markdown")
        return

    # Oddiy matnni tarjima qilish
    mode = user_history[user_id]["mode"]
    src_lang, dest_lang = mode

    # Matnni tekshirish
    if len(message.text.strip()) == 0:
        await message.answer("Iltimos, tarjima qilish uchun matn kiriting!")
        return

    if len(message.text) > 4000:
        await message.answer("❌ Matn juda uzun! Iltimos, 4000 belgidan oshmasligiga e'tibor bering.")
        return

    # "Tarjima qilinmoqda..." xabarni yuborish
    processing_msg = await message.answer("🔄 Tarjima qilinmoqda...")

    # Tarjima qilish
    try:
        translated_text = await translate_text(message.text, src_lang, dest_lang)

        # Tarixga qo'shish
        if user_id in user_history:
            user_history[user_id]["history"].append({
                "original": message.text,
                "translated": translated_text,
                "mode": f"{src_lang}_{dest_lang}"
            })
            # Tarixni cheklash (oxirgi 50 ta)
            if len(user_history[user_id]["history"]) > 50:
                user_history[user_id]["history"] = user_history[user_id]["history"][-50:]

        # Natijani chiroyli formatda ko'rsatish
        result_text = f"""
📝 *Asl matn ({src_lang.upper()}):*
`{message.text}`

✅ *Tarjima ({dest_lang.upper()}):*
`{translated_text}`

🔄 *Til juftligi:* {src_lang.upper()} ➡ {dest_lang.upper()}

📎 *Foydali:* Matnni tanlab, nusxa olishingiz mumkin.
        """

        # Inline tugmalar
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Boshqa tilga tarjima", callback_data="change_mode"),
                InlineKeyboardButton(text="📋 Tarix", callback_data="show_history")
            ]
        ])

        # Xabarni o'chirish va yangi xabar yuborish
        await bot.delete_message(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
        await message.answer(result_text, parse_mode="Markdown", reply_markup=inline_keyboard)

    except Exception as e:
        logger.error(f"Error in translation: {e}")
        await bot.delete_message(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
        await message.answer("❌ Tarjima qilishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


# Inline tugmalar uchun handler
@dp.callback_query()
async def handle_inline_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if callback_query.data == "change_mode":
        await callback_query.message.answer(
            "Yangi tarjima rejimini tanlang:",
            reply_markup=get_main_keyboard()
        )
    elif callback_query.data == "show_history":
        history = user_history.get(user_id, {}).get("history", [])
        if history:
            history_text = "📜 *So'nggi 5 ta tarjima:*\n\n"
            for i, item in enumerate(history[-5:], 1):
                history_text += f"{i}. *Asl:* {item['original'][:30]}...\n"
                history_text += f"   *Tarjima:* {item['translated'][:30]}...\n\n"
        else:
            history_text = "📭 Tarjima tarixi bo'sh"

        await callback_query.message.answer(history_text, parse_mode="Markdown")

    await callback_query.answer()


# Botni ishga tushirish
async def main():
    logger.info("Bot ishga tushmoqda...")
    logger.info(f"Bot token: {API_TOKEN[:10]}... (yashirin)")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")