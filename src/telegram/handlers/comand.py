from loguru import logger
from aiogram import Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder

from src.telegram.filters import SubscriptionExpiredFilter
from src.telegram.filters import AdminFilter
from src.database.uow import UnitOfWork
from src.telegram import texts
from src.telegram.keyboards.inline.keyboards import create_vertical_keyboard
from src.telegram.keyboards.inline import keyboards_text
from src.constants import PHOTOS_DIR

router = Router()


@router.message(CommandStart())
async def start(message: Message, uow: UnitOfWork, bot: Bot, state: FSMContext):
    """Регистрация пользователя и добавления thread для ассистента"""
    async with uow:
        user_exist = await uow.user_repo.get(message.from_user.id)  # type:ignore
        if user_exist is None:
            user = await uow.user_repo.create(message.from_user.id)  # type: ignore
            logger.info("Registrate user {}", user.id)
    album_builder = MediaGroupBuilder(caption=texts.start_text)

    photo_files = sorted(PHOTOS_DIR.glob("start_photo_*.jpg"))
    for photo_file in photo_files:
        album_builder.add(type="photo", media=FSInputFile(photo_file))

    await message.answer_media_group(
        media=album_builder.build(),
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=create_vertical_keyboard(keyboards_text.subscription_menu_buttons),
    )


@router.message(Command("pay"))
async def pay(message: Message):
    """Команда для оплаты"""

    await message.answer(
        text=texts.pay_text,
        reply_markup=create_vertical_keyboard(keyboards_text.how_much_buttons),
    )


@router.message(Command("promo"))
async def promo(message: Message, uow: UnitOfWork):
    """Команда для активации промо"""
    async with uow:
        user = await uow.user_repo.get(message.from_user.id)
        promo = await uow.promo_code_repo.get(message.text)

        if not promo:
            await message.answer(
                text=texts.not_right_promocode_text,
                reply_markup=create_vertical_keyboard(keyboards_text.go_back_to_menu),
            )
            return

        if message.text in user.used_promo_codes:
            await message.answer("Ты уже использовал этот промокод")
            return

        await uow.user_repo.add_promo_code(user, message.text)
    await message.answer(
        text=texts.promo_text,
    )


@router.message(Command("language"))
async def language(message: Message):
    """Команда для смены языка"""

    await message.answer(
        text=texts.chose_language_text,
        reply_markup=create_vertical_keyboard(keyboards_text.chose_language_buttons),
    )


@router.message(Command("generate"), SubscriptionExpiredFilter())
async def generate(message: Message):
    """Команда для генерирования текста"""

    await message.answer(
        text=texts.generate_command_text,
        reply_markup=create_vertical_keyboard(keyboards_text.assemble_posts_buttons),
    )


@router.message(Command("help"))
async def help(message: Message):
    """Команда для получения инфы о боте"""

    await message.answer(
        text=texts.help_text,
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    """Команда для отмены дейстивия"""
    await state.clear()
    await message.answer(
        text="Отменил действие",
    )


@router.message(Command("admin"), AdminFilter())
async def admin(message: Message, uow: UnitOfWork):
    """Команда для оплаты"""
    async with uow:
        all_users = await uow.user_repo.get_all()
        users_subscribed = await uow.subscription_repo.get_total_today()
        summ_subscribed = await uow.subscription_repo.get_total_cost_this_month()
    await message.answer(
        text=texts.statistic_text(len(all_users), users_subscribed, summ_subscribed),
        reply_markup=create_vertical_keyboard(keyboards_text.admin_buttons),
    )
