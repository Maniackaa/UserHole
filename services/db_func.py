import asyncio
import datetime
from typing import Optional

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from config_data.bot_conf import get_my_loggers, tz
from database.db import User, engine, BotSettings, Task

logger, err_log = get_my_loggers()
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def check_user(tg_id: int | str) -> User:
    """Возвращает найденного пользователя по tg_id"""
    logger.debug(f'Ищем юзера {tg_id}')
    tg_id = int(tg_id)
    async with async_session() as session:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar()
        logger.debug(f'Пользователь:{user}')
        return user


async def get_or_create_user(user, refferal=None) -> Optional[User]:
    """Из юзера ТГ создает User"""
    try:
        old_user = await check_user(user.id)
        if old_user:
            logger.debug(f'Пользователь {old_user} есть в базе')
            return old_user
        # Создание нового пользователя
        logger.debug('Добавляем пользователя')
        async with async_session() as session:
            new_user = User(tg_id=user.id,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            username=user.username,
                            created_at=datetime.datetime.now(tz=tz),
                            )
            session.add(new_user)
            await session.commit()
            logger.debug(f'Пользователь создан: {new_user}')
        return new_user
    except Exception as err:
        err_log.error('Пользователь не создан', exc_info=True)


async def read_bot_settings(name: str) -> str:
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False)
    async with async_session() as session:
        q = select(BotSettings).where(BotSettings.name == name).limit(1)
        result = await session.execute(q)
        readed_setting: BotSettings = result.scalars().one_or_none()
    return readed_setting.value


async def read_all_bot_settings():
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False)
    async with async_session() as session:
        q = select(BotSettings)
        result = await session.execute(q)
        readed_setting: BotSettings = result.scalars().all()
    # print(readed_setting)
    return readed_setting


async def set_botsettings_value(name, value):
    try:
        async_session = async_sessionmaker(engine)
        async with async_session() as session:
            query = select(BotSettings).where(BotSettings.name == name).limit(1)
            result = await session.execute(query)
            setting: BotSettings = result.scalar()
            if setting:
                setting.value = value
            await session.commit()
    except Exception as err:
        err_log.error(f'Ошибка set_botsettings_value. name: {name}, value: {value}')
        raise err


async def user_finished(user_id: int):
    """Установка статуса finished"""
    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar()
        if user:
            user.status = 'finished'
            user.status_updated_at = datetime.datetime.now(tz=tz)
        await session.commit()


async def user_dead(user_id: int):
    """Установка статуса dead"""
    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar()
        if user:
            user.status = 'dead'
            user.status_updated_at = datetime.datetime.now(tz=tz)
        await session.commit()


async def get_task_from_id(task_id: int) -> Task:
    """Возвращает Task по id"""
    async with async_session() as session:
        stmt = select(Task).where(Task.id == task_id)
        result = await session.execute(stmt)
        task = result.scalar()
        # logger.debug(f'Task:{task}')
        return task


async def set_task_complete(task_id: int) -> Task:
    """Возвращает Task по id"""
    async with async_session() as session:
        stmt = select(Task).where(Task.id == task_id)
        result = await session.execute(stmt)
        task = result.scalar()
        task.status = 'complete'
        await session.commit()
        logger.debug(f'Task complete:{task}')
        return task


async def create_hole_step(user_id: int, step: int, task_start_time: datetime.datetime) -> Task:
    """Возвращает Task по id"""
    async with async_session() as session:
        hole_step = Task(user_id=user_id, step=step, task_start_time=task_start_time)
        session.add(hole_step)
        await session.commit()
        logger.debug(f'Создана Task:{hole_step}')
        return hole_step


async def get_alive_users() -> list[User]:
    async with async_session() as session:
        stmt = select(User).where(User.status == 'alive')
        result = await session.execute(stmt)
        users = result.scalars()
        return users


async def get_created_tasks() -> list[Task]:
    """Возвращает Task по id"""
    async with async_session() as session:
        stmt = select(Task).where(Task.status == 'created')
        result = await session.execute(stmt)
        tasks = result.scalars().all()
        logger.debug(f'Найдены таски:{tasks}')
        return tasks


async def main():
    x = await get_created_tasks()
    print(x)


if __name__ == '__main__':
    asyncio.run(main())