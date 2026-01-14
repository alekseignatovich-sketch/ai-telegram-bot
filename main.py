import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Загрузка переменных окружения ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AVATAR_URL = os.getenv("AVATAR_URL", "https://github.com/alekseignatovich-sketch/ai-telegram-bot/blob/513f6ac6c0e072b4ced65c5ebdaabc202c139619/kitten.gif")  # белый милый котёнок

# Проверка обязательных токенов
if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("❌ Отсутствуют TELEGRAM_TOKEN или GROQ_API_KEY в переменных окружения!")

# --- Инициализация Groq-клиента ---
client = Groq(api_key=GROQ_API_KEY)

# --- Хранилище языков пользователей (в памяти; для продакшена можно добавить Redis/SQLite) ---
user_language = {}

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Привет! Я — ваш AI-помощник с милым котёнком!\n\n"
        "Пожалуйста, выберите язык:\n"
        "/ru — Русский\n"
        "/en — English\n"
        "/es — Español"
    )
    await update.message.reply_photo(photo=AVATAR_URL, caption=welcome_text)

# --- Установка языка ---
async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str, lang_name: str):
    user_id = update.effective_user.id
    user_language[user_id] = lang_code
    await update.message.reply_photo(
        photo=AVATAR_URL,
        caption=f"✅ Выбран язык: {lang_name}"
    )

async def cmd_ru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_lang(update, context, "ru", "Русский")

async def cmd_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_lang(update, context, "en", "English")

async def cmd_es(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_lang(update, context, "es", "Español")

# --- Системные промпты по языкам ---
def get_system_prompt(lang_code: str) -> str:
    prompts = {
        "ru": "Ты дружелюбный, умный и полезный помощник. Отвечай кратко, чётко и с эмодзи. Ты — милый котёнок 🐾.",
        "en": "You are a friendly, smart, and helpful assistant. Respond briefly, clearly, and with emojis. You are a cute kitten 🐾.",
        "es": "Eres un asistente amable, inteligente y útil. Responde brevemente, claramente y con emojis. Eres un gatito adorable 🐾."
    }
    return prompts.get(lang_code, prompts["en"])

# --- Обработка текстовых сообщений ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_language:
        await update.message.reply_text("Пожалуйста, сначала выберите язык: /ru, /en или /es")
        return

    user_msg = update.message.text
    lang = user_language[user_id]
    system_prompt = get_system_prompt(lang)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            temperature=0.7,
            timeout=30
        )
        ai_response = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Ошибка Groq: {e}")
        ai_response = "😿 Извините, сейчас не могу ответить. Попробуйте позже."

    await update.message.reply_photo(photo=AVATAR_URL, caption=ai_response)

# --- Основная функция запуска ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ru", cmd_ru))
    app.add_handler(CommandHandler("en", cmd_en))
    app.add_handler(CommandHandler("es", cmd_es))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("✅ Бот запущен и ожидает сообщения...")
    app.run_polling()

# --- Точка входа ---
if __name__ == "__main__":
    main()
