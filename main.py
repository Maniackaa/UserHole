import asyncio
import datetime

from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, BadRequest
from pyrogram.types import Message

from config_data.bot_conf import get_my_loggers, conf, tz
from services.db_func import check_user, get_or_create_user, user_finished, user_dead

logger, err_log = get_my_loggers()


async def send_message(client, chat_id, text):
    """Отправка сообщения"""
    try:
        await client.send_message(chat_id=chat_id, text=text)
    except FloodWait as e:
        logger.warning(e)
        await asyncio.sleep(e.value + 5)
        await send_message(client, chat_id, text)

    except BadRequest as err:
        logger.warning(err)
        await user_dead(chat_id)
        raise err

    except Exception as err:
        logger.error(err)
        raise err


async def worker(client: Client, message: Message):
    """Воронка для нового пользователя"""
    try:
        logger.debug(f'Начало воронки')
        # await asyncio.sleep(6 * 60)
        await asyncio.sleep(3)

        # Этап 1.
        user = await get_or_create_user(message.from_user)
        status = user.status
        if status in ('dead', 'finished'):
            return
        text = 'Текст 1'
        await send_message(client, message.chat.id, text)
        logger.debug(f'Текст 1 отправлен для {user}')
        # await asyncio.sleep(39 * 60)
        await asyncio.sleep(10)

        # Этап 2.
        user = await get_or_create_user(message.from_user)
        status = user.status
        if status in ('dead', 'finished'):
            logger.debug(f'Прерываем этап 2. Статус {status}')
            return
        text = 'Текст 2'
        await send_message(client, message.chat.id, text)
        logger.debug(f'Текст 2 отправлен для {user}')
        start_time = datetime.datetime.now(tz=tz)

        # Ждем этап 3
        while True:
            delta = datetime.datetime.now(tz=tz) - start_time
            # if delta > datetime.timedelta(days=2, hours=2):
            if delta > datetime.timedelta(seconds=10):
                logger.debug('Время вышло')
                break
            await asyncio.sleep(1)

        # Эьап 3
        # Если статус finished значит точка отсчета -  смена статуса
        text = 'Текст 3'
        user = await get_or_create_user(message.from_user)
        status = user.status
        if status == 'dead':
            logger.debug('Статус dead')
            return
        if status == 'alive':
            await send_message(client, message.chat.id, text)
            logger.debug(f'Текст 3 отправлен для {user}')
            # Установка статуса finished
            await user_finished(user.id)
            return
        elif status == 'finished':
            logger.debug('Этап 3. Статус finished')
            start_time = user.status_updated_at
            while True:
                delta = datetime.datetime.now(tz=tz) - start_time
                # if delta > datetime.timedelta(days=2, hours=2):
                if delta > datetime.timedelta(seconds=10):
                    await send_message(client, message.chat.id, text)
                    logger.debug(f'Текст 3 отправлен для {user}')
                    break

    except Exception as err:
        logger.error(f'Воронка прекращена из-за: {err}')


async def pyrobot():
    client = Client(name="my_account", api_hash=conf.tg_bot.API_HASH, api_id=conf.tg_bot.API_ID, workers=200)

    @client.on_message(filters.outgoing & filters.private)
    async def last_filter(client: Client, message: Message):
        """Проверка исходящих сообщений. Если есть ключевые слова, то ставим статус finished юзеру"""
        keywords = ['прекрасно', 'или', 'ожидать']
        send_user_tg = message.chat.id
        send_user = await check_user(send_user_tg)
        if send_user:
            for keyword in keywords:
                if keyword in message.text.lower():
                    await user_finished(send_user.id)
                    logger.debug(f'Статус пользователя {send_user} изменен на finished')
                    break

    @client.on_message(filters=filters.private)
    async def incoming_message_hole_check(client: Client, message: Message):
        is_old_user = await check_user(message.from_user.id)
        if is_old_user:
            logger.debug('Старый пользователь')
            return
        asyncio.create_task(worker(client, message))
        logger.debug('Воронка создана')

    await client.start()
    try:
        await idle()
    finally:
        await client.stop()

if __name__ == '__main__':
    asyncio.run(pyrobot())
