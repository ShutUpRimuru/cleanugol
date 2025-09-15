import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = '8446416030:AAH4fFbpC644n4I9-mT4PofWEpTIbiuAxJg'
ADMIN_CHAT_ID = '-1002929602692'

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

BTN_SERVICES = '✨ Услуги и цены'
BTN_CALC = '🧮 Рассчитать стоимость'
BTN_LEAD = '📞 Оставить заявку'
BTN_ABOUT = '❓ О нас'
BTN_BACK = '⬅️ Назад'
BTN_MENU = '⬅️ В меню'
BTN_CANCEL = '✖ Отмена'
BTN_CONTACT = 'Отправить контакт'

SERVICES_TEXT = (
    "Наши услуги и стартовые цены:\n\n"
    "🌱 <b>Поддерживающая уборка</b> — от 2 500 ₽\n"
    "✨ <b>Генеральная уборка</b> — от 6 000 ₽\n"
    "🛠️ <b>Уборка после ремонта</b> — от 9 000 ₽\n\n"
    "Точная стоимость зависит от площади — можно рассчитать прямо здесь."
)

ABOUT_TEXT = (
    "«Чистый Угол» — сервис эко‑уборки квартир и офисов.\n\n"
    "✅ Эко‑средства: безопасны для детей и питомцев.\n"
    "✅ Проверенные клинеры: обучение и стандарты качества.\n"
    "✅ Гарантия: недочёты устраним бесплатно."
)

def kb_main() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=BTN_SERVICES), types.KeyboardButton(text=BTN_CALC)],
            [types.KeyboardButton(text=BTN_LEAD), types.KeyboardButton(text=BTN_ABOUT)]
        ],
        resize_keyboard=True
    )

def kb_type() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text='Поддерживающая'),
             types.KeyboardButton(text='Генеральная'),
             types.KeyboardButton(text='После ремонта')],
            [types.KeyboardButton(text=BTN_MENU), types.KeyboardButton(text=BTN_CANCEL)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def kb_area() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=BTN_BACK), types.KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True
    )

def kb_phone() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=BTN_CONTACT, request_contact=True)],
            [types.KeyboardButton(text=BTN_BACK), types.KeyboardButton(text=BTN_CANCEL)]
        ],
        resize_keyboard=True
    )

class Calc(StatesGroup):
    type = State()
    area = State()
    phone = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
        "Я — бот‑помощник сервиса эко‑уборки «Чистый Угол».\n\n"
        "🌿 Используем гипоаллергенные средства.\n"
        "🧹 Наводим чистоту, пока вы отдыхаете.\n\n"
        "Выберите действие в меню ниже."
    )
    await message.answer(text, reply_markup=kb_main())

@dp.message(F.text == BTN_SERVICES)
async def services(message: types.Message):
    await message.answer(SERVICES_TEXT, reply_markup=kb_main())

@dp.message(F.text == BTN_ABOUT)
async def about(message: types.Message):
    await message.answer(ABOUT_TEXT, reply_markup=kb_main())

@dp.message(F.text == BTN_LEAD)
async def quick_lead(message: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=BTN_CONTACT, request_contact=True)],
            [types.KeyboardButton(text=BTN_MENU)]
        ],
        resize_keyboard=True
    )
    await message.answer("Нажмите кнопку ниже, чтобы поделиться номером телефона.", reply_markup=kb)

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    phone = message.contact.phone_number
    await message.answer(f"Спасибо, ваш номер {phone} получен — скоро свяжемся!", reply_markup=kb_main())
    user = message.from_user
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"‼️ Быстрая заявка\nТелефон: {phone}\nПользователь: {user.full_name} @{user.username or '—'} (id {user.id})"
    )

@dp.message(F.text == BTN_MENU)
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню.", reply_markup=kb_main())

@dp.message(F.text == BTN_CANCEL)
async def cancel_flow(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено. Вы в главном меню.", reply_markup=kb_main())

@dp.message(F.text == BTN_CALC)
async def start_calc(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Calc.type)
    await message.answer("Какой тип уборки вас интересует?", reply_markup=kb_type())

@dp.message(StateFilter(Calc.type), F.text.in_({'Поддерживающая', 'Генеральная', 'После ремонта'}))
async def set_type(message: types.Message, state: FSMContext):
    await state.update_data(order_type=message.text)
    await state.set_state(Calc.area)
    await message.answer("Укажите площадь в м² (только число от 10 до 1000).", reply_markup=kb_area())

@dp.message(StateFilter(Calc.type), F.text == BTN_MENU)
async def type_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню.", reply_markup=kb_main())

@dp.message(StateFilter(Calc.type))
async def type_fallback(message: types.Message):
    await message.answer(
        "Пожалуйста, выберите вариант из клавиатуры: Поддерживающая / Генеральная / После ремонта.",
        reply_markup=kb_type()
    )

@dp.message(StateFilter(Calc.area), F.text == BTN_BACK)
async def area_back(message: types.Message, state: FSMContext):
    await state.set_state(Calc.type)
    await message.answer("Вернулись к выбору типа уборки.", reply_markup=kb_type())

@dp.message(StateFilter(Calc.area))
async def set_area(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(',', '.')
    if not re.fullmatch(r'(?:\d{2,4})(?:\.\d)?', text):
        await message.answer("Введите число от 10 до 1000 (без единиц измерения).", reply_markup=kb_area())
        return
    await state.update_data(area=text)
    await state.set_state(Calc.phone)
    await message.answer("Оставьте номер телефона или нажмите «Отправить контакт».", reply_markup=kb_phone())

@dp.message(StateFilter(Calc.phone), F.text == BTN_BACK)
async def phone_back(message: types.Message, state: FSMContext):
    await state.set_state(Calc.area)
    await message.answer("Введите площадь в м².", reply_markup=kb_area())

def normalize_phone(p: str) -> str | None:
    digits = re.sub(r'\D+', '', p)
    if 10 <= len(digits) <= 15:
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        if not digits.startswith('+'):
            digits = '+' + digits
        return digits
    return None

@dp.message(StateFilter(Calc.phone), F.contact)
async def phone_contact(message: types.Message, state: FSMContext):
    phone = normalize_phone(message.contact.phone_number) or message.contact.phone_number
    await finalize_order(message, state, phone)

@dp.message(StateFilter(Calc.phone))
async def phone_text(message: types.Message, state: FSMContext):
    phone = normalize_phone(message.text.strip())
    if not phone:
        await message.answer(
            "Введите телефон в формате +7XXXXXXXXXX или отправьте контакт кнопкой ниже.",
            reply_markup=kb_phone()
        )
        return
    await finalize_order(message, state, phone)

async def finalize_order(message: types.Message, state: FSMContext, phone: str):
    data = await state.get_data()
    order_type = data.get('order_type', '—')
    area = data.get('area', '—')
    await message.answer(
        f"Спасибо! Ваша заявка принята.\n\n"
        f"Тип: {order_type}\nПлощадь: {area} м²\nТелефон: {phone}\n\n"
        f"Менеджер скоро свяжется с вами.",
        reply_markup=kb_main()
    )
    user = message.from_user
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"‼️ Новая заявка\nТип: {order_type}\nПлощадь: {area} м²\nТелефон: {phone}\n"
        f"Пользователь: {user.full_name} @{user.username or '—'} (id {user.id})"
    )
    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
