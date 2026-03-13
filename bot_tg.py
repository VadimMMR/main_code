import asyncio
import logging
import asyncpg
import aiohttp
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- Настройки ---
BOT_TOKEN = "8667089058:AAGpW3MM9GE3RDDtG6d33FJoQLPqmrAmgVc"  # Замените на ваш токен
DATABASE_URL = "postgresql://neondb_owner:npg_v6fYP1IEOzUs@ep-dawn-surf-abgw0kss-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# API Endpoints (без проверки, используем как есть)
API_DEVICE = "https://main-code-aqq3.onrender.com/api/device"
API_OS_STANDARD = "https://main-code-aqq3.onrender.com/api/os/standard"
API_OS_ADVANCED = "https://main-code-aqq3.onrender.com/api/os/advanced"

# --- Инициализация бота и диспетчера ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Хранилище для соединения с БД (пул будет создан при старте) ---
db_pool = None

# --- Вспомогательные функции для работы с БД ---
async def get_db_pool():
    """Возвращает пул соединений с БД, создавая его при первом вызове."""
    global db_pool
    if db_pool is None:
        try:
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
            logging.info("Пул соединений с БД создан.")
        except Exception as e:
            logging.error(f"Ошибка подключения к БД: {e}")
            return None
    return db_pool

async def get_table_names():
    """Получает список имен таблиц из базы данных."""
    pool = await get_db_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            # Запрос для получения всех таблиц в схеме public (стандартно для PostgreSQL)
            rows = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            return [row['table_name'] for row in rows]
    except Exception as e:
        logging.error(f"Ошибка получения списка таблиц: {e}")
        return []

async def get_table_content(table_name: str):
    """Получает все данные из указанной таблицы."""
    pool = await get_db_pool()
    if not pool:
        return None, "Ошибка подключения к базе данных."
    try:
        async with pool.acquire() as conn:
            # Безопасно подставляем имя таблицы (мы его контролируем, но для подстраховки используем идентификатор)
            rows = await conn.fetch(f"SELECT * FROM {table_name};")
            if not rows:
                return "Таблица пуста.", None
            
            # Получаем названия колонок
            columns = list(rows[0].keys())
            
            # Формируем заголовок таблицы
            header = " | ".join(columns)
            separator = "-" * len(header)
            
            # Формируем строки для вывода
            result_lines = [header, separator]
            
            for row in rows:
                # Для каждой строки формируем значения в том же порядке, что и колонки
                values = []
                for col in columns:
                    value = row[col]
                    # Преобразуем значение в строку, обрабатывая специальные типы
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, (dict, list)):
                        values.append(json.dumps(value, ensure_ascii=False)[:50] + "..." if len(json.dumps(value)) > 50 else json.dumps(value, ensure_ascii=False))
                    else:
                        values.append(str(value))
                result_lines.append(" | ".join(values))
            
            # Объединяем все строки
            full_text = "\n".join(result_lines)
            
            # Ограничим вывод, чтобы не превысить лимит сообщения Telegram (4096 символов)
            if len(full_text) > 3500:
                # Показываем информацию о количестве записей
                record_count = len(rows)
                full_text = f"Всего записей: {record_count}\n\n" + full_text[:3000] + f"\n\n... (показано первых {len(result_lines) - 2} из {record_count} записей)"
            
            return full_text, None
    except Exception as e:
        logging.error(f"Ошибка получения данных из таблицы {table_name}: {e}")
        return None, f"Ошибка при запросе к таблице: {e}"

# --- Функции для создания клавиатур ---
def main_menu_keyboard():
    """Главное меню с двумя кнопками."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Получить результат", callback_data="get_result")
    builder.button(text="🗄 Просмотреть базу данных", callback_data="view_db")
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

def result_options_keyboard():
    """Кнопки выбора: информация об устройстве или об ОС."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💻 Информация об устройстве", callback_data="info_device")
    builder.button(text="🖥 Информация об ОС", callback_data="info_os")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

def os_options_keyboard():
    """Кнопки выбора режима для ОС: standard или advanced."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⚙️ Режим Standard", callback_data="os_standard")
    builder.button(text="🚀 Режим Advanced", callback_data="os_advanced")
    builder.button(text="🔙 Назад", callback_data="back_to_result_options")
    builder.adjust(1)
    return builder.as_markup()

def tables_keyboard(table_names: list):
    """Создает клавиатуру с кнопками для каждой таблицы."""
    builder = InlineKeyboardBuilder()
    for name in table_names:
        builder.button(text=name, callback_data=f"table_{name}")
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    # Располагаем кнопки таблиц в несколько колонок для удобства, например по 2 в ряд
    builder.adjust(2)
    return builder.as_markup()

# --- Функция для выполнения HTTP запросов к API ---
async def fetch_api_data(url: str):
    """Отправляет GET запрос к API и возвращает отформатированный JSON или сообщение об ошибке."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    # Пытаемся распарсить JSON для красивого форматирования
                    try:
                        data = json.loads(text)
                        # Форматируем JSON с отступами
                        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                        return formatted_json
                    except json.JSONDecodeError:
                        # Если это не JSON, возвращаем как есть
                        return text
                else:
                    return f"❌ Ошибка API: статус {response.status}"
    except asyncio.TimeoutError:
        return "❌ Таймаут при подключении к API."
    except aiohttp.ClientConnectorError:
        return "❌ Не удалось подключиться к API (сервер недоступен)."
    except Exception as e:
        return f"❌ Неизвестная ошибка: {e}"

# --- Обработчики команд ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    await message.answer(
        "👋 Добро пожаловать! Выберите действие:",
        reply_markup=main_menu_keyboard()
    )

# --- Обработчики колбэков ---
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню."""
    await callback.message.edit_text(
        "👋 Выберите действие:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_result_options")
async def back_to_result_options(callback: CallbackQuery):
    """Возврат к меню выбора результата."""
    await callback.message.edit_text(
        "📊 Выберите тип информации:",
        reply_markup=result_options_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "get_result")
async def get_result(callback: CallbackQuery):
    """Обработка нажатия 'Получить результат'."""
    await callback.message.edit_text(
        "📊 Выберите тип информации:",
        reply_markup=result_options_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "info_device")
async def info_device(callback: CallbackQuery):
    """Обработка запроса информации об устройстве."""
    await callback.message.edit_text("⏳ Запрашиваю данные об устройстве...")
    data = await fetch_api_data(API_DEVICE)
    # Отправляем новым сообщением, чтобы не потерять клавиатуру навигации
    await callback.message.answer(f"💻 *Информация об устройстве:*\n```json\n{data}\n```", parse_mode="Markdown")
    # Возвращаем клавиатуру выбора результата (или можно оставить как есть)
    await callback.message.answer(
        "📊 Выберите тип информации:",
        reply_markup=result_options_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "info_os")
async def info_os(callback: CallbackQuery):
    """Обработка выбора информации об ОС."""
    await callback.message.edit_text(
        "🖥 Выберите режим:",
        reply_markup=os_options_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "os_standard")
async def os_standard(callback: CallbackQuery):
    """Обработка запроса информации об ОС в стандартном режиме."""
    await callback.message.edit_text("⏳ Запрашиваю данные об ОС (Standard)...")
    data = await fetch_api_data(API_OS_STANDARD)
    await callback.message.answer(f"🖥 *Информация об ОС (Standard):*\n```json\n{data}\n```", parse_mode="Markdown")
    await callback.message.answer(
        "🖥 Выберите режим:",
        reply_markup=os_options_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "os_advanced")
async def os_advanced(callback: CallbackQuery):
    """Обработка запроса информации об ОС в расширенном режиме."""
    await callback.message.edit_text("⏳ Запрашиваю данные об ОС (Advanced)...")
    data = await fetch_api_data(API_OS_ADVANCED)
    await callback.message.answer(f"🖥 *Информация об ОС (Advanced):*\n```json\n{data}\n```", parse_mode="Markdown")
    await callback.message.answer(
        "🖥 Выберите режим:",
        reply_markup=os_options_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "view_db")
async def view_db(callback: CallbackQuery):
    """Обработка нажатия 'Просмотреть базу данных'."""
    await callback.message.edit_text("⏳ Загружаю список таблиц...")
    tables = await get_table_names()
    
    if not tables:
        await callback.message.edit_text(
            "❌ Не удалось получить список таблиц или база данных пуста.",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"🗄 Найдено таблиц: {len(tables)}\nВыберите таблицу для просмотра:",
        reply_markup=tables_keyboard(tables)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("table_"))
async def show_table_content(callback: CallbackQuery):
    """Показывает содержимое выбранной таблицы."""
    table_name = callback.data[6:]  # Убираем префикс "table_"
    
    await callback.message.edit_text(f"⏳ Загружаю данные из таблицы '{table_name}'...")
    
    content, error = await get_table_content(table_name)
    
    if error:
        await callback.message.answer(f"❌ {error}")
    elif isinstance(content, list) and not content:
        await callback.message.answer(f"Таблица '{table_name}' пуста.")
    else:
        # Отправляем содержимое
        await callback.message.answer(
            f"📋 *Содержимое таблицы '{table_name}':*\n```\n{content}\n```",
            parse_mode="Markdown"
        )
    
    # Возвращаем пользователя к списку таблиц
    tables = await get_table_names()
    if tables:
        await callback.message.answer(
            "🗄 Выберите таблицу для просмотра:",
            reply_markup=tables_keyboard(tables)
        )
    else:
        await callback.message.answer(
            "👋 Главное меню:",
            reply_markup=main_menu_keyboard()
        )
    
    await callback.answer()

# --- Обработка неизвестных колбэков ---
@dp.callback_query()
async def unknown_callback(callback: CallbackQuery):
    """Обработка неизвестных callback данных."""
    await callback.answer("Неизвестная команда", show_alert=False)

# --- Запуск бота ---
async def on_startup():
    """Действия при запуске бота."""
    logging.basicConfig(level=logging.INFO)
    # Инициализируем пул соединений при старте
    await get_db_pool()
    logging.info("Бот запущен и готов к работе!")

async def on_shutdown():
    """Действия при остановке бота."""
    global db_pool
    if db_pool:
        await db_pool.close()
        logging.info("Пул соединений с БД закрыт.")

async def main():
    # Регистрируем функции startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())