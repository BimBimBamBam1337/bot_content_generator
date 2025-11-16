from loguru import logger
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
)

from src.database.uow import UnitOfWork
from src.telegram.filters import OwnerFilter

from src.constants import *

router = Router()


@router.message(Command("owner"), OwnerFilter())
async def admin(message: Message, uow: UnitOfWork):
    await message.answer(
        text="""Команды владельца:  
/create_admin [id пользователя] — выдать права администратора  
/delete_admin [id пользователя] — убрать права администратора""",
    )


@router.message(Command("create_admin"), OwnerFilter())
async def create_admin(message: Message, uow: UnitOfWork):
    """Выдача прав администратора по id"""
    try:
        user_id = int(message.text.split()[1])
        async with uow:
            await uow.user_repo.update_user(user_id, is_admin=True)
        await message.answer(
            f"Пользователь с id {user_id} теперь является администратором."
        )
    except IndexError:
        await message.answer(
            "Ошибка: необходимо указать id пользователя. Пример: /create_admin 12345"
        )
    except ValueError:
        await message.answer("Ошибка: id пользователя должен быть числом.")


@router.message(Command("delete_admin"), OwnerFilter())
async def delete_admin(message: Message, uow: UnitOfWork):
    """Снятие прав администратора по id"""
    try:
        user_id = int(message.text.split()[1])
        async with uow:
            await uow.user_repo.update_user(user_id, is_admin=False)
        await message.answer(
            f"Пользователь с id {user_id} больше не является администратором."
        )
    except IndexError:
        await message.answer(
            "Ошибка: необходимо указать id пользователя. Пример: /delete_admin 12345"
        )
    except ValueError:
        await message.answer("Ошибка: id пользователя должен быть числом.")
