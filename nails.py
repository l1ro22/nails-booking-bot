import asyncio
from datetime import datetime       
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
if not TOKEN or not ADMIN_ID:
    raise ValueError("Проверьте BOT_TOKEN и ADMIN_ID в файле .env")
ADMIN_ID = int(ADMIN_ID)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

SERVICES = {
    "corbez": ("Коррекция без дизайна", 1600),
    "cors": ("Коррекция с дизайном", 1700),
    "narashivaniemin": ("Наращивание с минимальным дизайном", 2000),
    'narashivaniemax': ("Наращивание от 3 и дизайн", 2200),
    "extra": ("Экстра-наращивание от 5 до 7", 2600),

}


# Шаги анкеты
class Booking(StatesGroup):
    time = State()
    name = State()
    phone = State()

    
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Записаться")],
        [KeyboardButton(text="Услуги и цены"), KeyboardButton(text="Контакты")],
    ],
    resize_keyboard=True,
)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def services_keyboard():
    buttons = []
    for key, (name, price) in SERVICES.items():
        buttons.append(
            [InlineKeyboardButton(text=f"{name} — {price} ₽", callback_data=f"service:{key}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! 💅\n"
        "Я помогу записаться на маникюр. Выберите пункт меню:",
        reply_markup=main_menu,
    )


@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Запись отменена.", reply_markup=main_menu)


@dp.message(Command("id"))
async def get_id(message: Message):
    await message.answer(f"Ваш ID: {message.chat.id}")


@dp.message(F.text == "Записаться")
async def book(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите услугу:", reply_markup=services_keyboard())


@dp.callback_query(F.data.startswith("service:"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    name, price = SERVICES[key]
    await state.update_data(service=f"{name} — {price} ₽")
    await callback.message.answer(
        f"Вы выбрали: {name} — {price} ₽\n\n"
        "Когда вам удобно прийти? Напишите день и время, например: «пятница после 18:00».\n"
        "Отменить запись: /cancel"
    )
    await state.set_state(Booking.time)
    await callback.answer()


@dp.message(Booking.time, F.text)
async def get_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer("Как вас зовут?")
    await state.set_state(Booking.name)


@dp.message(Booking.name, F.text)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Оставьте номер телефона: нажмите кнопку ниже или введите вручную.",
        reply_markup=phone_keyboard,
    )
    await state.set_state(Booking.phone)


@dp.message(Booking.phone)
async def get_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        digits = "".join(char for char in message.text if char.isdigit())
        if len(digits) == 11 and digits[0] in "78":
            phone = "+7" + digits[1:]
        else:
            await message.answer(
                "Похоже, это не номер телефона 🤔\n"
                "Введите номер в формате +7 999 123-45-67 или нажмите кнопку ниже."
            )
            return
    else:
        await message.answer("Пожалуйста, отправьте номер телефона.")
        return

    data = await state.get_data()
    await state.clear()

    data = await state.get_data()
    await state.clear()

    user = message.from_user
    username = f"@{user.username}" if user.username else "нет username"

    
    created = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    
    
    await bot.send_message(
        ADMIN_ID,
        "🔔 Новая заявка!\n\n"
        f"Создана: {created}\n"
        f"Услуга: {data['service']}\n"
        f"Удобное время: {data['time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {phone}\n"
        f"Telegram: {username}",
    )
    await message.answer(
        "Спасибо! Заявка принята ✅\nМастер скоро свяжется с вами, чтобы подтвердить время.",
        reply_markup=main_menu,
    )


@dp.message(F.text == "Услуги и цены")
async def services(message: Message):
    response = "Наши услуги:\n"
    for name, price in SERVICES.values():
        response += f"- {name}: {price} ₽\n"
    await message.answer(response)


@dp.message(F.text == "Контакты")
async def contacts(message: Message):
    await message.answer("Мастер: @ksxzxss\nАдрес:26 линия 35/2 2 подъезд 3 этаж\nтгк с работами:@nogtyzz")


@dp.message()
async def unknown(message: Message):
    await message.answer("Я вас не понял 🙈 Воспользуйтесь кнопками меню.")


async def main():
    await dp.start_polling(bot)


asyncio.run(main()) 