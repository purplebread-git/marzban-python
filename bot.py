
import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
    async with session.get('')


TOKEN = "kXuAQERwXyFuOA"
MARZBAN_API_URL = ""
MARZBAN_API_TOKEN = ".._-Gn-2cxL8GekfoKsg"
YMONEY_WALLET = "YOUR_YUMONEY_WALLET"
PRICE = 300  # Стоимость подписки в рублях

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

users = {}  # Временное хранилище пользователей

async def create_marzban_user(user_id):
    """Создает пользователя в Marzban"""
    expire_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
    data = {
        "username": f"user_{user_id}",
        "expire": expire_date,
        "data_limit": None
    }
    headers = {"Authorization": f"Bearer {MARZBAN_API_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{MARZBAN_API_URL}/clients", json=data, headers=headers) as resp:
            return await resp.json()

async def generate_payment_link(user_id):
    """Генерация ссылки на оплату через ЮMoney"""
    return f"https://yoomoney.ru/quickpay/confirm.xml?receiver={YMONEY_WALLET}&sum={PRICE}&label={user_id}&quickpay-form=shop"

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")]
    ])
    await message.answer("Привет! Здесь ты можешь оформить подписку на наш VPN.", reply_markup=keyboard)



@dp.message(Command("create"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    marzban_user = await create_marzban_user(user_id)




@dp.callback_query(lambda c: c.data == "buy_subscription")
async def buy_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    payment_link = await generate_payment_link(user_id)
    await callback_query.message.answer(f"Оплати подписку по ссылке: {payment_link}\n\nПосле оплаты напиши /check")
    users[user_id] = "pending"
    await callback_query.answer()

@dp.message(Command("check"))
async def check_payment(message: types.Message):
    user_id = message.from_user.id
    if users.get(user_id) == "pending":
        users[user_id] = "active"
        marzban_user = await create_marzban_user(user_id)
        config = marzban_user.get("config", "Не удалось получить конфиг")
        await message.answer(f"Оплата подтверждена! Вот твой конфиг: \n```{config}```", parse_mode="Markdown")
    else:
        await message.answer("Ты еще не оплатил подписку.")

async def send_reminders():
    """Отправляет напоминания о продлении подписки"""
    for user_id, status in users.items():
        if status == "active":
            await bot.send_message(user_id, "Твоя подписка скоро заканчивается! Продли её командой /check")

scheduler.add_job(send_reminders, "interval", days=1)

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
