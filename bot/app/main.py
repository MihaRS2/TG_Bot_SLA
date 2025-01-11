import asyncio
import logging
from aiogram import Bot, Dispatcher, executor
from config import BOT_TOKEN
from database import db
from handlers import register_handlers, send_weekly_report, set_bot
import aioschedule


logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def scheduler():
    """Настройка задач планировщика."""
    logger.info("Запуск планировщика.")
    # Еженедельный отчет каждое воскресенье в 20:00 по московскому времени
    aioschedule.every().sunday.at("20:00").do(send_weekly_report)

    while True:
        try:
            await aioschedule.run_pending()
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
        await asyncio.sleep(60)

async def on_startup(dp):
    """Действия при запуске бота."""
    logger.info("Инициализация бота...")
    try:
        await db.connect()
        logger.info("Успешное подключение к базе данных.")
        asyncio.create_task(scheduler())
        logger.info("Планировщик успешно запущен.")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        raise

async def on_shutdown(dp):
    """Действия при остановке бота."""
    logger.info("Выключение бота...")
    try:
        await db.close()
        logger.info("Соединение с базой данных успешно закрыто.")
    except Exception as e:
        logger.error(f"Ошибка при завершении работы бота: {e}")

def main():
    """Главная точка входа для запуска бота."""
    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(bot)

        # Передаем экземпляр бота в handlers.py
        set_bot(bot)

        # Регистрация обработчиков
        register_handlers(dp)

        # Запуск бота
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
    except Exception as e:
        logger.critical(f"Фатальная ошибка в главной функции: {e}")
        raise

if __name__ == '__main__':
    main()

