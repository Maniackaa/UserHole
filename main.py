import asyncio
import datetime

from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, BadRequest
from pyrogram.types import Message

from config_data.bot_conf import get_my_loggers, conf, tz
from services.db_func import check_user, get_or_create_user, user_finished, user_dead, get_task_from_id, \
    create_hole_step, set_task_complete, get_alive_users, get_created_tasks

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

msg1 = 'Текст 1'
msg2 = 'Текст 2'
msg3 = 'Текст 3'
trigger = False


async def hole_step_1(client: Client, task_id: int):
    """Первый этап"""
    task = await get_task_from_id(task_id)
    while task.status == 'created' and task.user.status == 'alive':
        now = datetime.datetime.now(tz=tz)
        task = await get_task_from_id(task_id)
        if now >= task.task_start_time:
            # Выполняем этап 1
            await send_message(client, task.user.tg_id, text=msg1)
            await set_task_complete(task_id)
            # Создаем этап 2
            step2 = await create_hole_step(
                user_id=task.user_id, step=2,
                # task_start_time=datetime.datetime.now(tz=tz) + datetime.timedelta(minutes=39)
                task_start_time=datetime.datetime.now(tz=tz) + datetime.timedelta(seconds=10)
            )
            asyncio.create_task(hole_step_2(client, step2.id))
        await asyncio.sleep(5)
        task = await get_task_from_id(task_id)


async def hole_step_2(client: Client, task_id: int):
    """Второй этап"""
    task = await get_task_from_id(task_id)
    while task.status == 'created' and task.user.status == 'alive':
        now = datetime.datetime.now(tz=tz)
        task = await get_task_from_id(task_id)
        if now >= task.task_start_time:
            # Выполняем этап 2
            if trigger is False:
                await send_message(client, task.user.tg_id, text=msg2)
                await set_task_complete(task_id)
                # Создаем этап 3
                step3 = await create_hole_step(
                    user_id=task.user_id, step=3,
                    # task_start_time=datetime.datetime.now(tz=tz) + datetime.timedelta(days=1, hours=2)
                    task_start_time=datetime.datetime.now(tz=tz) + datetime.timedelta(seconds=10)
                )
                asyncio.create_task(hole_step_3(client, step3.id))
            else:
                # если
                pass
        await asyncio.sleep(5)
        task = await get_task_from_id(task_id)


async def hole_step_3(client: Client, task_id: int):
    """Третий этап"""
    task = await get_task_from_id(task_id)
    while task.status == 'created'  and task.user.status == 'alive':
        now = datetime.datetime.now(tz=tz)
        task = await get_task_from_id(task_id)
        if now >= task.task_start_time:
            # Выполняем этап 3
            await send_message(client, task.user.tg_id, text=msg3)
            await set_task_complete(task_id)
        await asyncio.sleep(5)
        task = await get_task_from_id(task_id)


async def trigger_search(client):
    """Проверка триггера"""
    while True:
        # Я понял так: если нашли триггер - сообщение 2 отменится.
        # Если пользователь на этапе 1 и ждет этап 2, то делаем ему этап 3 через 1 day 2 hours
        users = await get_alive_users()
        for user in users:
            for task in user.tasks:
                if task.step == 1 and task.status == 'created':
                    step3 = await create_hole_step(
                        user_id=task.user_id, step=3,
                        task_start_time=datetime.datetime.now(tz=tz) + datetime.timedelta(days=1, hours=2)
                    )
                    asyncio.create_task(hole_step_3(client, step3.id))

        await asyncio.sleep(1)


async def start_tasks(client):
    """Запускает таски при переазапуске"""
    logger.debug('Запуск незавершенных задач')
    tasks = await get_created_tasks()
    logger.debug(f'Задач: {len(tasks)}')
    for task in tasks:
        print(task.id, task.step)
        if task.step == 1:
            asyncio.create_task(hole_step_1(client, task.id))
        elif task.step == 2:
            asyncio.create_task(hole_step_2(client, task.id))
        elif task.step == 3:
            asyncio.create_task(hole_step_3(client, task.id))


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

    @client.on_message(filters.private & ~filters.bot)
    async def incoming_message_hole_check(client: Client, message: Message):
        is_old_user = await check_user(message.from_user.id)
        if is_old_user:
            logger.debug('Старый пользователь')
            return
        # Создание 1 этапа
        user = await get_or_create_user(message.from_user)
        task = await create_hole_step(user_id=user.id, step=1,
                                      # task_start_time=datetime.datetime.now(tz=tz) + datetime.timedelta(minutes=6)
                                      task_start_time=datetime.datetime.now(tz=tz) + datetime.timedelta(seconds=10)
                                      )
        asyncio.create_task(hole_step_1(client=client, task_id=task.id))
        logger.debug('Воронка создана')

    await client.start()
    try:
        await start_tasks(client)
        await idle()
    finally:
        await client.stop()

if __name__ == '__main__':
    asyncio.run(pyrobot())
