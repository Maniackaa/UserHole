import asyncio
import datetime
import json
import sys
import uuid

from time import time
from typing import List

from sqlalchemy import create_engine, ForeignKey, Date, String, DateTime, \
    Float, UniqueConstraint, Integer, MetaData, BigInteger, ARRAY, Table, Column, select, JSON, BLOB, delete
from sqlalchemy.dialects.mysql import TEXT
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, relationship, Session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils.functions import database_exists, create_database

from config_data.bot_conf import get_my_loggers, conf, db_url

logger, err_log = get_my_loggers()
metadata = MetaData()

sync_engine = create_engine(db_url, echo=False)
engine = create_async_engine(f"postgresql+asyncpg://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}", echo=False)

# Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    tg_id = mapped_column(BigInteger(), unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='alive')
    status_updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    tasks: Mapped[list['Task']] = relationship(back_populates='user', lazy='subquery')

    def __repr__(self):
        return f'{self.id}. {self.tg_id} {self.username or "-"}'

    def set(self, key, value):
        _session = Session()
        try:
            with _session:
                order = _session.query(User).filter(User.id == self.id).one_or_none()
                setattr(order, key, value)
                _session.commit()
                logger.debug(f'Изменено значение {key} на {value}')
        except Exception as err:
            err_log.error(f'Ошибка изменения {key} на {value}')
            raise err


class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship("User", back_populates="tasks", lazy='subquery')
    step: Mapped[int] = mapped_column(Integer())
    task_start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='created')


class BotSettings(Base):
    __tablename__ = 'bot_settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(50), nullable=True, default='')
    description: Mapped[str] = mapped_column(String(255),
                                             nullable=True,
                                             default='')

    @classmethod
    def get_item(cls, name):
        _session = Session()
        try:
            with _session:
                setting = _session.query(cls).filter(cls.name == name).one_or_none()
                if setting:
                    return setting.value
        except Exception as err:
            err_log.error(f'err')
            raise err


if not database_exists(db_url):
    create_database(db_url)
Base.metadata.create_all(sync_engine)



if __name__ == '__main__':

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()


    async def test_user(async_session: async_sessionmaker[AsyncSession]) -> None:
        async with async_session() as session:
            stmt = select(User).where(User.id == 585896156)
            result = await session.execute(stmt)
            print(result.scalar())



    # if __name__ == '__main__':
    #     if sys.version_info[:2] == (3, 7):
    #         asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    #     loop = asyncio.get_event_loop()
    #     try:
    #         async_session = async_sessionmaker(engine, expire_on_commit=False)
    #         loop.run_until_complete(init_models())
    #         loop.run_until_complete(test_user(async_session))
    #         loop.run_until_complete(asyncio.sleep(2.0))
    #     finally:
    #         loop.close()