import logging
import asyncio
from datetime import datetime, timedelta, time, timezone
from aiogram import types, Dispatcher
from aiogram.types import ChatType, ContentType
from zoneinfo import ZoneInfo  
from config import NOTIFICATION_GROUP_ID
from database import db

logger = logging.getLogger(__name__)

bot = None  

def set_bot(b):
    """Установка экземпляра бота."""
    global bot
    bot = b

# === Вспомогательные функции ===

def is_working_hours(now=None):
    """Проверяет, является ли указанное время рабочим."""
    try:
        moscow_tz = ZoneInfo('Europe/Moscow')
        now = now or datetime.now(moscow_tz)
        weekday = now.weekday()  # 0 - Понедельник, 6 - Воскресенье
        current_time = now.time()

        if weekday < 5:  # Будни
            start_time = time(7, 0)
            end_time = time(23, 0)
        else:  # Выходные
            start_time = time(10, 0)
            end_time = time(19, 0)

        return start_time <= current_time < end_time
    except Exception as e:
        logger.error(f"Ошибка в функции is_working_hours: {e}")
        return False

def get_next_working_period_start(now=None):
    
    try:
        moscow_tz = ZoneInfo('Europe/Moscow')
        now = now or datetime.now(moscow_tz)
        current_date = now.date()

        days_ahead = 0
        while True:
            next_date = current_date + timedelta(days=days_ahead)
            next_weekday = next_date.weekday()
            if next_weekday < 5:
                start_time = time(7, 0)
            else:
                start_time = time(10, 0)
            next_start_datetime = datetime.combine(next_date, start_time, tzinfo=moscow_tz)
            if next_start_datetime > now:
                return next_start_datetime
            days_ahead += 1
    except Exception as e:
        logger.error(f"Ошибка в функции get_next_working_period_start: {e}")
        return now or datetime.now()

def get_working_minutes_between(start_dt, end_dt):
    """Вычисляет количество рабочих минут между двумя датами."""
    try:
        total_minutes = 0
        current_dt = start_dt
        moscow_tz = ZoneInfo('Europe/Moscow')

        while current_dt < end_dt:
            weekday = current_dt.weekday()
            if weekday < 5:
                start_time = time(7, 0)
                end_time = time(23, 0)
            else:
                start_time = time(10, 0)
                end_time = time(19, 0)

            working_start = datetime.combine(current_dt.date(), start_time, tzinfo=moscow_tz)
            working_end = datetime.combine(current_dt.date(), end_time, tzinfo=moscow_tz)

            if current_dt < working_start:
                current_dt = working_start

            if current_dt >= working_end:
                current_dt = datetime.combine(current_dt.date() + timedelta(days=1), time(0, 0), tzinfo=moscow_tz)
                continue

            interval_end = min(end_dt, working_end)
            minutes = (interval_end - current_dt).total_seconds() / 60
            total_minutes += minutes
            current_dt = interval_end

        return total_minutes
    except Exception as e:
        logger.error(f"Ошибка в функции get_working_minutes_between: {e}")
        return 0

async def manage_user_role(message, role_to_add=None, role_to_remove=None):
    """Добавление или удаление ролей пользователей."""
    try:
        user_id = message.from_user.id
        role = await db.get_user_role(user_id)
        if role != 'admin':
            await message.reply("У вас нет прав для выполнения этой команды.")
            return

        args = message.get_args()
        if not args:
            await message.reply("Пожалуйста, укажите @username или user_id пользователя.")
            return

        if args.isdigit():
            target_user_id = int(args)
            target_username = None
        else:
            target_username = args.strip('@')
            target_user_id = await get_user_id_by_username(target_username)
        if not target_user_id:
            await message.reply("Пользователь не найден.")
            return

        if role_to_add:
            await db.add_staff(target_user_id, target_username, role_to_add)
            await message.reply(f"Пользователь с ID {target_user_id} добавлен с ролью {role_to_add}.")
        elif role_to_remove:
            await db.remove_staff(target_user_id)
            await message.reply(f"Пользователь с ID {target_user_id} удален из таблицы staff.")
    except Exception as e:
        logger.error(f"Ошибка в функции manage_user_role: {e}")
        await message.reply("Произошла ошибка при управлении ролями.")

async def get_user_id_by_username(username):
    """Получение ID пользователя по username."""
    try:
        async with db.pool.acquire() as connection:
            result = await connection.fetchrow("""SELECT user_id FROM staff WHERE username = $1""", username)
            return result['user_id'] if result else None
    except Exception as e:
        logger.error(f"Ошибка в функции get_user_id_by_username: {e}")
        return None

# === Обработчики команд ===

async def start_handler(message: types.Message):
    """Обработчик команды /start."""
    try:
        user_id = message.from_user.id
        logger.info(f"Получена команда /start от пользователя {user_id}")

        if message.chat.type == ChatType.PRIVATE or message.chat.id == NOTIFICATION_GROUP_ID:
            role = await db.get_user_role(user_id)
            response = {
                'support': "Привет! Вы зарегистрированы как сотрудник техподдержки.",
                'admin': "Привет! Вы зарегистрированы как администратор.",
                'sales': "Привет! Вы зарегистрированы как продажник."
            }.get(role, "Здравствуйте! Вы не зарегистрированы в системе.")
            await message.reply(response)
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")

async def add_staff_handler(message: types.Message):
    await manage_user_role(message, role_to_add='support')

async def remove_staff_handler(message: types.Message):
    await manage_user_role(message, role_to_remove='support')

async def add_admin_handler(message: types.Message):
    await manage_user_role(message, role_to_add='admin')

async def remove_admin_handler(message: types.Message):
    await manage_user_role(message, role_to_remove='admin')

async def add_sales_handler(message: types.Message):
    await manage_user_role(message, role_to_add='sales')

async def remove_sales_handler(message: types.Message):
    await manage_user_role(message, role_to_remove='sales')

async def check_roles_handler(message: types.Message):
    """Обработчик команды /check_roles."""
    try:
        user_id = message.from_user.id
        role = await db.get_user_role(user_id)
        if role:
            await message.reply(f"Ваша роль: {role}")
        else:
            await message.reply("Вы не зарегистрированы в системе.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /check_roles: {e}")
        await message.reply("Произошла ошибка при проверке ролей.")

async def close_task_handler(message: types.Message):
    """Обработчик команды /close."""
    try:
        user_id = message.from_user.id
        role = await db.get_user_role(user_id)

        if role not in ['support', 'admin']:
            await message.reply("У вас нет прав для выполнения этой команды.")
            return

        args = message.get_args()
        if not args:
            await message.reply("Пожалуйста, укажите название чата для закрытия задачи.")
            return

        chat_title = args.strip('"')
        task = await db.get_open_task_by_chat_title(chat_title)

        if task:
            await db.close_task(task['id'], user_id)
            await bot.send_message(
                NOTIFICATION_GROUP_ID,
                f"✅ Задача для чата \"{chat_title}\" успешно закрыта."
            )
            # Удалено двойное логирование о закрытии задачи
        else:
            await message.reply(f"⚠️ Задача для чата \"{chat_title}\" не найдена или уже закрыта.")
            logger.warning(f"Попытка закрыть несуществующую или уже закрытую задачу \"{chat_title}\" пользователем {user_id}.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /close: {e}")
        await message.reply("Произошла ошибка при закрытии задачи.")

# === Обработчик сообщений ===

async def message_handler(message: types.Message):
    """Обработчик текстовых сообщений."""
    try:
        chat = message.chat
        user_id = message.from_user.id

        # Игнорируем сообщения в группе уведомлений, кроме команд
        if chat.id == NOTIFICATION_GROUP_ID and not message.text.startswith('/'):
            return

        role = await db.get_user_role(user_id)

        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return

#        if message.content_type != ContentType.TEXT:
#           return

        # Если сообщение от support или admin, закрываем задачу, если она есть
        if role in ['support', 'admin']:
            task = await db.get_open_task_by_chat_id(chat.id)
            if task:
                await db.increment_support_activity(user_id, message.from_user.username)
                await db.close_task(task['id'], user_id)
                # Удалено двойное логирование о закрытии задачи
        elif role == 'sales':
            return  # Игнорируем сообщения от продажников
        else:
            # Сообщение от клиента
            task = await db.get_open_task_by_chat_id(chat.id)
            if not task:
                await db.create_task(chat.id, chat.title or chat.username or chat.first_name)
                # Удалено двойное логирование о создании задачи
                asyncio.create_task(schedule_notifications(chat.id))
    except Exception as e:
        logger.error(f"Ошибка в обработчике сообщений: {e}")

# === Расписание уведомлений о KPI ===

async def schedule_notifications(chat_id):
    """Расписание уведомлений и автоматическое закрытие задач."""
    try:
        notification_times = [15, 10, 5]  # Минуты до истечения SLA
        notification_sent = set()

        while True:
            task = await db.get_open_task_by_chat_id(chat_id)
            if not task or task['is_closed']:
                return

            moscow_tz = ZoneInfo('Europe/Moscow')
            created_at_utc = task['created_at'].replace(tzinfo=timezone.utc)
            created_at = created_at_utc.astimezone(moscow_tz)
            now = datetime.now(moscow_tz)

            if not is_working_hours(now):
                next_working_time = get_next_working_period_start(now)
                sleep_duration = (next_working_time - now).total_seconds()
                await asyncio.sleep(sleep_duration)
                continue

            working_minutes_elapsed = get_working_minutes_between(created_at, now)
            time_remaining = 60 - int(working_minutes_elapsed)

            if time_remaining in notification_times and time_remaining not in notification_sent:
                message_text = (
                    f"🔴 !!!ВНИМАНИЕ!!! До истечения SLA по задаче в чате \"{task['chat_title']}\" осталось {time_remaining} минут.\n"
                    f"Для закрытия задачи введите /close \"{task['chat_title']}\""
                )
                await bot.send_message(NOTIFICATION_GROUP_ID, message_text)
                notification_sent.add(time_remaining)

            if time_remaining <= 0:
                await db.mark_task_overdue(task['id'])
                await db.close_task(task['id'], None)
                await bot.send_message(
                    NOTIFICATION_GROUP_ID,
                    f"🔴 !!!ВНИМАНИЕ!!! SLA по задаче \"{task['chat_title']}\" просрочен!\nЗадача закрыта!"
                )
                logger.info(f"Задача {task['id']} автоматически закрыта и отмечена как просроченная.")
                return

            await asyncio.sleep(30)
    except Exception as e:
        logger.error(f"Ошибка в функции schedule_notifications: {e}")

# === Функция для отправки еженедельного отчета ===

async def send_weekly_report():
    """Формирует и отправляет еженедельный отчет."""
    try:
        logger.info("Формируем еженедельный отчет.")

        moscow_tz = ZoneInfo('Europe/Moscow')
        now = datetime.now(moscow_tz)
        last_week = now - timedelta(days=7)

        support_activity = await db.get_support_activity_last_week()
        sla_violations = await db.get_sla_violations_last_week()

        total_responses = sum(row['responses'] for row in support_activity)

        activity_report = "Статистика активности сотрудников техподдержки:\n"
        if total_responses > 0:
            for row in support_activity:
                username = row['username'] or "Неизвестный"
                responses = row['responses']
                percentage = (responses / total_responses * 100)
                activity_report += f"{username}: {responses} ответов ({percentage:.2f}%)\n"
        else:
            activity_report += "Нет активности за прошедшую неделю.\n"

        sla_report = f"Количество нарушений SLA: {len(sla_violations)}\n"
        if sla_violations:
            sla_report += "Детализация нарушений:\n"
            for row in sla_violations:
                chat_title = row['chat_title'] or "Неизвестный чат"
                violation_time = row['closed_at'] or row['created_at']
                violation_time = violation_time.replace(tzinfo=timezone.utc).astimezone(moscow_tz)
                violation_time_str = violation_time.strftime("%Y-%m-%d %H:%M:%S")
                sla_report += f"- Чат: \"{chat_title}\", Дата и время просрочки: {violation_time_str}\n"
        else:
            sla_report += "Нарушений SLA за неделю не обнаружено.\n"

        weekly_report = f"📝 Еженедельный отчет за неделю до {now.strftime('%d.%m.%Y')}:\n\n"
        weekly_report += activity_report + "\n" + sla_report

        await bot.send_message(NOTIFICATION_GROUP_ID, weekly_report)
        logger.info("Еженедельный отчет отправлен.")
    except Exception as e:
        logger.error(f"Ошибка в функции send_weekly_report: {e}")

# === Регистрация обработчиков ===

def register_handlers(dp: Dispatcher):
    try:
        dp.register_message_handler(start_handler, commands=['start'])
        dp.register_message_handler(add_staff_handler, commands=['add_staff'])
        dp.register_message_handler(remove_staff_handler, commands=['remove_staff'])
        dp.register_message_handler(add_admin_handler, commands=['add_admin'])
        dp.register_message_handler(remove_admin_handler, commands=['remove_admin'])
        dp.register_message_handler(add_sales_handler, commands=['add_sales'])
        dp.register_message_handler(remove_sales_handler, commands=['remove_sales'])
        dp.register_message_handler(check_roles_handler, commands=['check_roles'])
        dp.register_message_handler(close_task_handler, commands=['close'])
        dp.register_message_handler(message_handler, content_types=ContentType.TEXT)
        logger.info("Обработчики успешно зарегистрированы.")
    except Exception as e:
        logger.error(f"Ошибка при регистрации обработчиков: {e}")
