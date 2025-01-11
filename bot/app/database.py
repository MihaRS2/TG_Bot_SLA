import asyncpg
import logging
import datetime
from config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Подключение к базе данных."""
        logger.debug("Подключение к базе данных...")
        try:
            self.pool = await asyncpg.create_pool(
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                host=DB_HOST,
                port=DB_PORT
            )
            await self.create_tables()
            logger.info("Подключение к базе данных установлено.")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise e

    async def close(self):
        """Закрытие подключения к базе данных."""
        logger.debug("Закрытие подключения к базе данных...")
        if self.pool:
            await self.pool.close()
            logger.info("Подключение к базе данных закрыто.")

    async def create_tables(self):
        """Создание таблиц при необходимости."""
        logger.debug("Создание таблиц, если они не существуют...")
        try:
            async with self.pool.acquire() as connection:
                # Создание таблицы staff
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS staff (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT UNIQUE NOT NULL,
                        username TEXT,
                        role TEXT CHECK (role IN ('support', 'admin', 'sales')) NOT NULL
                    );
                """)
                # Создание таблицы tasks
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        chat_title TEXT,
                        created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                        is_overdue BOOLEAN DEFAULT FALSE,
                        is_closed BOOLEAN DEFAULT FALSE,
                        closed_at TIMESTAMP WITHOUT TIME ZONE,
                        closed_by BIGINT
                    );
                """)
                # Создание таблицы support_activity
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS support_activity (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL UNIQUE,
                        username TEXT,
                        responses INT DEFAULT 0,
                        last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                    );
                """)
            logger.info("Таблицы готовы.")
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            raise e

    # === Методы для управления сотрудниками ===

    async def add_staff(self, user_id, username, role):
        """Добавление или обновление сотрудника."""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO staff (user_id, username, role)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username, role = EXCLUDED.role
                """, user_id, username, role)
                logger.info(f"Добавлен или обновлен пользователь {user_id} с ролью {role}.")
        except Exception as e:
            logger.error(f"Ошибка при добавлении/обновлении пользователя {user_id}: {e}")

    async def remove_staff(self, user_id):
        """Удаление сотрудника."""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    DELETE FROM staff WHERE user_id = $1
                """, user_id)
                logger.info(f"Пользователь {user_id} удален из таблицы staff.")
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")

    async def get_user_role(self, user_id):
        """Получение роли пользователя."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetchrow("""
                    SELECT role FROM staff WHERE user_id = $1
                """, user_id)
                return result['role'] if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении роли пользователя {user_id}: {e}")
            return None

    async def get_all_staff(self):
        """Получение списка всех сотрудников."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetch("""
                    SELECT user_id, username, role FROM staff
                """)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении списка сотрудников: {e}")
            return []

    # === Методы для управления задачами ===

    async def create_task(self, chat_id, chat_title):
        """Создание задачи."""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO tasks (chat_id, chat_title, created_at)
                    VALUES ($1, $2, $3)
                """, chat_id, chat_title, datetime.datetime.utcnow())
                logger.info(f"Создана задача для чата {chat_id} ({chat_title}).")
        except Exception as e:
            logger.error(f"Ошибка при создании задачи для чата {chat_id}: {e}")

    async def get_open_task_by_chat_id(self, chat_id):
        """Получение открытой задачи по ID чата."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetchrow("""
                    SELECT * FROM tasks WHERE chat_id = $1 AND is_closed = FALSE
                """, chat_id)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении задачи для чата {chat_id}: {e}")
            return None

    async def get_open_task_by_chat_title(self, chat_title):
        """Получение открытой задачи по названию чата."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetchrow("""
                    SELECT * FROM tasks WHERE chat_title = $1 AND is_closed = FALSE
                """, chat_title)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении задачи для чата {chat_title}: {e}")
            return None

    async def get_task_by_id(self, task_id):
        """Получение задачи по ID."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetchrow("""
                    SELECT * FROM tasks WHERE id = $1
                """, task_id)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении задачи с ID {task_id}: {e}")
            return None

    async def close_task(self, task_id, closed_by):
        """Закрытие задачи."""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    UPDATE tasks
                    SET is_closed = TRUE, closed_at = $1, closed_by = $2
                    WHERE id = $3
                """, datetime.datetime.utcnow(), closed_by, task_id)
                logger.info(f"Задача {task_id} закрыта пользователем {closed_by}.")
        except Exception as e:
            logger.error(f"Ошибка при закрытии задачи {task_id}: {e}")

    async def mark_task_overdue(self, task_id):
        """Отметка задачи как просроченной."""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    UPDATE tasks SET is_overdue = TRUE WHERE id = $1
                """, task_id)
                logger.info(f"Задача {task_id} отмечена как просроченная.")
        except Exception as e:
            logger.error(f"Ошибка при отметке задачи {task_id} как просроченной: {e}")

    async def get_overdue_tasks(self):
        """Получение всех просроченных задач."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetch("""
                    SELECT * FROM tasks WHERE is_overdue = TRUE AND is_closed = FALSE
                """)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении просроченных задач: {e}")
            return []

    async def get_open_tasks(self):
        """Получение всех открытых задач."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetch("""
                    SELECT * FROM tasks WHERE is_closed = FALSE
                """)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении открытых задач: {e}")
            return []

    async def cleanup_old_tasks(self):
        """Очистка старых задач, закрытых более двух недель назад."""
        try:
            two_weeks_ago = datetime.datetime.utcnow() - datetime.timedelta(weeks=2)
            async with self.pool.acquire() as connection:
                deleted_records = await connection.execute("""
                    DELETE FROM tasks
                    WHERE is_closed = TRUE AND closed_at < $1
                """, two_weeks_ago)
                logger.info(f"Очистка старых задач выполнена. Удалено записей: {deleted_records}.")
        except Exception as e:
            logger.error(f"Ошибка при очистке старых задач: {e}")

    # === Методы для управления активностью поддержки ===

    async def increment_support_activity(self, user_id, username):
        """Увеличение активности сотрудника техподдержки."""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO support_activity (user_id, username, responses, last_updated)
                    VALUES ($1, $2, 1, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        responses = support_activity.responses + 1,
                        username = EXCLUDED.username,
                        last_updated = NOW()
                """, user_id, username)
                logger.debug(f"Активность пользователя {user_id} обновлена.")
        except Exception as e:
            logger.error(f"Ошибка при обновлении активности пользователя {user_id}: {e}")

    # === Методы для отчетов ===

    async def get_support_activity_last_week(self):
        """Получение активности сотрудников техподдержки за последнюю неделю."""
        try:
            last_week = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            async with self.pool.acquire() as connection:
                result = await connection.fetch("""
                    SELECT sa.username, sa.responses
                    FROM support_activity sa
                    JOIN staff s ON sa.user_id = s.user_id
                    WHERE s.role = 'support' AND sa.last_updated >= $1
                    ORDER BY sa.responses DESC
                """, last_week)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении активности за последнюю неделю: {e}")
            return []

    async def get_sla_violations_last_week(self):
        """Получение просроченных задач за последнюю неделю."""
        try:
            last_week = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            async with self.pool.acquire() as connection:
                result = await connection.fetch("""
                    SELECT chat_title, created_at, closed_at
                    FROM tasks
                    WHERE is_overdue = TRUE AND created_at >= $1
                    ORDER BY closed_at
                """, last_week)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении просроченных задач: {e}")
            return []

    async def get_tasks_closed_between(self, start_date, end_date):
        """Получение задач, закрытых в указанный период."""
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetch("""
                    SELECT * FROM tasks
                    WHERE is_closed = TRUE AND closed_at BETWEEN $1 AND $2
                """, start_date, end_date)
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении задач, закрытых в период с {start_date} по {end_date}: {e}")
            return []

    db = None  # Инициализация переменной для экземпляра базы данных


# Создание глобального экземпляра базы данных
db = Database()
