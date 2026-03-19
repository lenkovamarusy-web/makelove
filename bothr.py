import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# -------- Состояния --------
class Form(StatesGroup):
    category = State()
    text = State()
    anonymous = State()

# -------- Клавиатуры --------
menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💌 Благодарность", callback_data="thanks")],
    [InlineKeyboardButton(text="📰 Новость", callback_data="news")],
    [InlineKeyboardButton(text="💡 Идея", callback_data="idea")]
])

anon_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Анонимно", callback_data="anon_yes")],
    [InlineKeyboardButton(text="С именем", callback_data="anon_no")]
])

# -------- Старт --------
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("Что хочешь отправить?", reply_markup=menu)

# -------- Категория --------
@dp.callback_query(F.data.in_(["thanks", "news", "idea"]))
async def category(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data)
    await callback.message.answer("Напиши текст (до 500 символов):")
    await state.set_state(Form.text)

# -------- Текст --------
@dp.message(Form.text)
async def get_text(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("Слишком длинно (макс 500 символов)")
        return

    await state.update_data(text=message.text)
    await message.answer("Как опубликовать?", reply_markup=anon_kb)
    await state.set_state(Form.anonymous)

# -------- Анонимность и сохранение --------
@dp.callback_query(Form.anonymous, F.data.in_(["anon_yes", "anon_no"]))
async def anon(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    category_map = {
        "thanks": "💌 Благодарность",
        "news": "📰 Новость",
        "idea": "💡 Идея"
    }

    is_anon = callback.data == "anon_yes"
    author = "Анонимно" if is_anon else callback.from_user.full_name

    text = f"{category_map[data['category']]}\n{data['text']}\n— {author}\n{'='*40}\n"

    # Отправляем только админу
    await bot.send_message(ADMIN_ID, f"Новое сообщение:\n\n{text}")
    await callback.message.answer("Отправлено и сохранено ✅")
    await state.clear()

# -------- Тестовое напоминание --------
async def weekly_reminder_loop():
    while True:
        now = datetime.utcnow() + timedelta(hours=1)

        next_run = now.replace(hour=16, minute=35, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        print(f"Ждем {wait_seconds} секунд...")

        await asyncio.sleep(wait_seconds)

        await bot.send_message(
            CHANNEL_ID,
            text="Напоминание: напишите, пожалуйста, когда планируете работать удалённо на следующую неделю."
        )

        await asyncio.sleep(60)
# -------- Запуск --------
async def main():
    # Запускаем цикл с напоминаниями
    asyncio.create_task(weekly_reminder_loop())
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
