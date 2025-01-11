import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Загрузка зашифрованных данных и ключа шифрования
ENCRYPTED_TOKEN = os.getenv('ENCRYPTED_TOKEN')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Загрузка пароля базы данных напрямую
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Загрузка остальных переменных окружения
DB_USER = os.getenv('DB_USER')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
NOTIFICATION_GROUP_ID = int(os.getenv('NOTIFICATION_GROUP_ID'))
TIMEZONE = os.getenv('TIMEZONE')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  

# Проверка наличия ключа шифрования
if not ENCRYPTION_KEY:
    raise ValueError("Ключ шифрования (ENCRYPTION_KEY) отсутствует в файле .env!")

# Конвертация ключа шифрования из строки в байты
ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

# Функция расшифровки данных
def decrypt_data(encrypted_data):
    """Расшифровка данных с использованием ключа."""
    try:
        f = Fernet(ENCRYPTION_KEY)
        decrypted_data = f.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"Ошибка расшифровки данных: {e}")

# Расшифровка токена бота
if not ENCRYPTED_TOKEN:
    raise ValueError("Зашифрованный токен (ENCRYPTED_TOKEN) отсутствует в файле .env!")
BOT_TOKEN = decrypt_data(ENCRYPTED_TOKEN)

# Проверка наличия остальных обязательных переменных
required_env_vars = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,  # Добавлено
    "DB_NAME": DB_NAME,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "NOTIFICATION_GROUP_ID": NOTIFICATION_GROUP_ID,
    "TIMEZONE": TIMEZONE,
}
missing_vars = [key for key, value in required_env_vars.items() if not value]

if missing_vars:
    raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
