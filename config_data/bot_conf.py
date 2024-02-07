import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import pytz

BASE_DIR = Path(__file__).resolve().parent.parent


"""
format = "%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"
"""

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default_formatter': {
            # 'format': "%(asctime)s - [%(levelname)8s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
            'format': "%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s"
        },
    },

    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
        },
        'rotating_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "bot"}.log',
            'backupCount': 2,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },

        'errors_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "errors_bot"}.log',
            'backupCount': 2,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },
    },
    'loggers': {
        'bot_logger': {
            'handlers': ['stream_handler', 'rotating_file_handler'],
            'level': 'DEBUG',
            'propagate': True
        },
        'errors_logger': {
            'handlers': ['stream_handler', 'errors_file_handler'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


@dataclass
class PostgresConfig:
    database: str  # Название базы данных
    db_host: str  # URL-адрес базы данных
    db_port: str  # URL-адрес базы данных
    db_user: str  # Username пользователя базы данных
    db_password: str  # Пароль к базе данных


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    API_HASH: str
    API_ID: str
    base_dir = BASE_DIR
    GROUP_ID: str
    TIMEZONE: pytz.timezone


@dataclass
class Logic:
    pass


@dataclass
class Config:
    tg_bot: TgBot
    logic: Logic
    db: PostgresConfig


def load_config(path=None) -> Config:
    return Config(tg_bot=TgBot(token=os.getenv('BOT_TOKEN'),
                               API_HASH=os.getenv('API_HASH'),
                               API_ID=os.getenv('API_ID'),
                               GROUP_ID=os.getenv('GROUP_ID'),
                               TIMEZONE=pytz.timezone(os.getenv('TIMEZONE')),
                               ),
                  db=PostgresConfig(
                      database=os.getenv('POSTGRES_DB'),
                      db_host=os.getenv('DB_HOST'),
                      db_port=os.getenv('DB_PORT'),
                      db_user=os.getenv('POSTGRES_USER'),
                      db_password=os.getenv('POSTGRES_PASSWORD'),
                  ),
                  logic=Logic(),
                  )


load_dotenv()

conf = load_config()
print(conf)
tz = conf.tg_bot.TIMEZONE
db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"



def get_my_loggers():
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger('bot_logger'), logging.getLogger('errors_logger')
