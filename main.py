"""Main bot file."""

import asyncio
import json
import logging
import os
import random

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply, \
    KeyboardButton, InlineKeyboardButton, Message, CallbackQuery
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
EXPLORERS_FILE = 'explorers.json'

# Bot token
TOKEN = os.environ.get('BOT_TOKEN')

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Global variables
explorers = None
user_states = {}

user_router = Router()


def load_explorers() -> dict:
    """
    This function load explorers.json file.

    Returns:
        dict: json data
    """
    try:
        with open(EXPLORERS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


async def send_photo_safe(
        chat_id: int,
        image_path: str,
        caption: str = None,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None = None,
) -> bool | None:
    """
    Helper function to send photos safely.

    Args:
        chat_id: chat id
        image_path: path to image file
        caption: caption
        reply_markup: keyboard markup

    Returns:
        bool: True - success
    """
    try:
        await bot.send_photo(
            chat_id,
            FSInputFile(image_path),
            caption=caption,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        print(f"Error sending image {image_path}: {e}")
        if caption:
            await bot.send_message(chat_id, caption, reply_markup=reply_markup)


def create_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Helper function to create reply keyboard.

    Returns:
        ReplyKeyboardMarkup: keyboard markup
    """
    buttons_map = [
        [KeyboardButton(text="📚 Список мореплавателей"), KeyboardButton(text="❓ Проверь себя"), ],
        [KeyboardButton(text="🏠 Главное меню")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons_map, resize_keyboard=True, )
    return keyboard


def create_main_keyboard() -> InlineKeyboardMarkup:
    """
    Create main keyboard.

    Returns:
        InlineKeyboardMarkup: inline keyboard markup
    """
    buttons_map = [
        [
            InlineKeyboardButton(text="📚 Список мореплавателей", callback_data="show_list", ),
            InlineKeyboardButton(text="❓ Проверь себя", callback_data="quiz"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_map)
    return keyboard


def create_explorer_keyboard(explorer_id: str) -> InlineKeyboardMarkup:
    """
    This function create explorer keyboard.

    Args:
        explorer_id: explorer id

    Returns:
        InlineKeyboardMarkup: inline keyboard markup
    """
    buttons_map = [
        [
            InlineKeyboardButton(text="🗺 Маршрут", callback_data=f"route_{explorer_id}", ),
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_map)
    return keyboard


def create_keyboard() -> InlineKeyboardMarkup:
    """
    This function create back to menu keyboard.

    Returns:
        InlineKeyboardMarkup: inline keyboard markup
    """
    buttons_map = [
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu"), ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_map)
    return keyboard


# ============================================= COMMAND HANDLERS =======================================================

@user_router.message(Command('start'))
async def handle_start(message: Message) -> None:
    """
    This function is called when a user send start command.

    Args:
        message: message object

    Returns:
        None: None
    """
    chat_id = message.chat.id
    user_states[chat_id] = "1"
    welcome_text = """
🌊 Добро пожаловать в мир великих мореплавателей!

🚢 Выберите действие:

📚 Список мореплавателей - изучите великих первооткрывателей
❓ Проверь себя - проверьте свои знания
"""
    await message.answer(welcome_text, reply_markup=create_main_keyboard())
    await message.answer("Выберите действие:", reply_markup=create_reply_keyboard())


# ============================================= MESSAGE HANDLERS =======================================================

@user_router.message(F.text)
async def handle_text(message: Message) -> None:
    """
    This function is called when a user send text message.

    Args:
        message: message object

    Returns:
        None: None
    """
    if message.text == "📚 Список мореплавателей":
        await show_explorers_list(message)
    elif message.text == "❓ Проверь себя":
        await start_quiz(message)
    elif message.text == "🏠 Главное меню":
        await show_main_menu(message)


# ============================================= CALLBACK HANDLERS ======================================================

@user_router.callback_query()
async def handle_callback(callback_query: CallbackQuery) -> None:
    """
    This function is called when a user send callback query.

    Args:
        callback_query: callback query object

    Returns:
        None: None
    """
    chat_id = callback_query.message.chat.id
    match callback_query.data:
        case "show_list":
            await show_explorers_list(callback_query.message)
        case "quiz":
            await start_quiz(callback_query.message)
        case data if data.startswith("select_"):
            explorer_id = callback_query.data.split("_")[1]
            user_states[chat_id] = explorer_id
            await show_explorer_info(callback_query.message)
        case data if data.startswith("route_"):
            explorer_id = callback_query.data.split("_")[1]
            user_states[chat_id] = explorer_id
            await show_route(callback_query.message)
        case data if data.startswith("main_menu"):
            await show_main_menu(callback_query.message)
        case data if data.startswith("quiz"):
            await handle_quiz_answer(callback_query)

    try:
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=None
        )
    except:
        pass


async def show_main_menu(message: Message) -> None:
    """
    This function is called when a user send main menu command.

    Args:
        message: message object

    Returns:
        None: None
    """
    welcome_text = """
🌊 Главное меню

🚢 Выберите действие:

📚 Список мореплавателей - изучите великих первооткрывателей
❓ Проверь себя - проверьте свои знания
"""
    await bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_keyboard()
    )
    await bot.send_message(
        message.chat.id,
        "Выберите действие:",
        reply_markup=create_reply_keyboard()
    )


async def show_explorers_list(message: Message) -> None:
    """
    This function is called when a user send explorers list command.

    Args:
        message: message object

    Returns:
        None: None
    """
    buttons_map = [
        [InlineKeyboardButton(text=f"{ex_obj['name']} ({ex_obj['years']})", callback_data=f"select_{ex_id}"), ]
        for ex_id, ex_obj in explorers.items()
    ]
    buttons_map.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_map)
    await bot.send_message(
        message.chat.id,
        "📚 Выберите мореплавателя:",
        reply_markup=keyboard
    )


async def show_explorer_info(message: Message) -> None:
    """
    This function is called when a user send explorer info command.

    Args:
        message: message object

    Returns:
        None: None
    """
    explorer_id = user_states.get(message.chat.id, "1")
    explorer = explorers[explorer_id]
    caption = f"""
📚 {explorer['name']}
Годы жизни: {explorer['years']}
{explorer['bio']}
"""
    await send_photo_safe(message.chat.id, explorer['image'], caption, create_explorer_keyboard(explorer_id))


async def show_route(message: Message) -> None:
    """
    This function is called when a user send route command.

    Args:
        message: message object

    Returns:
        None: None
    """
    explorer_id = user_states.get(message.chat.id, "1")
    explorer = explorers[explorer_id]
    if explorer['route'] != "нет":
        await send_photo_safe(message.chat.id, explorer['route'], "Маршрут", create_keyboard())
    else:
        await bot.send_message(message.chat.id, "Маршрут не доступен.", reply_markup=create_keyboard())


async def start_quiz(message: Message) -> None:
    """
    This function is called when a user send start quiz command.

    Args:
        message: message object

    Returns:
        None: None
    """
    explorer_id = random.choice(list(explorers.keys()))
    explorer = explorers[explorer_id]
    caption = f"❓ О каком мореплавателе идет речь?\n\n{explorer['bio']}"
    await send_photo_safe(message.chat.id, explorer['image'], caption)

    options = [explorer]
    while len(options) < 3:
        option = random.choice(list(explorers.values()))
        if option not in options:
            options.append(option)

    random.shuffle(options)

    buttons_map = [
        [InlineKeyboardButton(text=option['name'], callback_data=f"quiz_{option['name'] == explorer['name']}"), ]
        for option in options
    ]
    buttons_map.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_map)

    await bot.send_message(
        message.chat.id,
        "Выберите правильный ответ:",
        reply_markup=keyboard
    )


async def handle_quiz_answer(callback_query: CallbackQuery) -> None:
    """
    This function is called when a user send quiz command.

    Args:
        callback_query: callback query

    Returns:
        None: None
    """
    is_correct = callback_query.data.split("_")[1] == "True"
    text = "✅ Правильно! Молодец!" if is_correct else "❌ Неправильно! Попробуй еще раз!"

    buttons_map = [
        [
            InlineKeyboardButton(text="🔄 Ещё вопрос", callback_data="quiz"),
            InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_map)
    await bot.send_message(
        callback_query.message.chat.id,
        text,
        reply_markup=keyboard
    )


async def main() -> None:
    """
    This function is called on run the bot.

    Returns:
        None: None
    """
    # Подключение роутеров
    dp.include_router(user_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    explorers = load_explorers()
    asyncio.run(main())
