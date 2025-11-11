import hashlib
from urllib import parse
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from loguru import logger

from src.database.engine import SessionFactory
from src.config import bot, dp, settings
from src.database.uow import UnitOfWork
from aiogram.types import Update

app = FastAPI()


def calculate_signature(
    login,
    cost,
    inv_id,
    password,
    user_id,
    user_telegram_id,
    product_id,
    is_result=False,
):
    if is_result:
        base_string = f"{cost}:{inv_id}:{password}"
    else:
        base_string = f"{login}:{cost}:{inv_id}:{password}"

    additional_params = {
        "shp_user_id": user_id,
        "Shp_user_telegram_id": user_telegram_id,
        "Shp_product_id": product_id,
    }

    for key, value in sorted(additional_params.items()):
        if value is not None:
            base_string += f":{key}={value}"

    return hashlib.md5(base_string.encode("utf-8")).hexdigest()


def parse_query_string(query: str) -> dict:
    return dict(parse.parse_qsl(query))


def check_signature_result(
    out_sum, inv_id, received_signature, password, user_id, user_telegram_id, product_id
) -> bool:
    signature = calculate_signature(
        settings.merchant_login,
        out_sum,
        inv_id,
        password,
        user_id,
        user_telegram_id,
        product_id,
        is_result=True,
    )
    return signature.lower() == received_signature.lower()


@app.post("/robokassa/result", response_class=PlainTextResponse)
async def robokassa_result(request: Request):
    """
    Обрабатывает ResultURL Robokassa, когда приходит строка запроса.
    """
    print(await request.body())
    logger.success("Получен ответ от Робокассы!")

    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    data = dict(parse_qsl(body_str))

    OutSum = data.get("OutSum") or data.get("out_summ")
    InvId = data.get("InvId") or data.get("inv_id")
    SignatureValue = data.get("SignatureValue") or data.get("crc")
    Shp_user_id = data.get("shp_user_id")
    Shp_user_telegram_id = data.get("Shp_user_telegram_id")
    Shp_product_id = data.get("Shp_product_id")

    if check_signature_result(
        out_sum=OutSum,
        inv_id=InvId,
        received_signature=SignatureValue,
        password=settings.password2,
        user_id=Shp_user_id,
        user_telegram_id=Shp_user_telegram_id,
        product_id=Shp_product_id,
    ):
        result = f"OK{InvId}"
        logger.info(f"Успешная проверка подписи для InvId: {Shp_user_id}")
        int_OutSum = int(float(OutSum))
        async with UnitOfWork(SessionFactory) as uow:
            if int_OutSum == 4999:
                subscription = await uow.subscription_repo.create(
                    user_id=int(Shp_user_id), cost=int_OutSum, trial=365
                )
                return
            subscription = await uow.subscription_repo.create(
                user_id=int(Shp_user_id), cost=int_OutSum, trial=30
            )
            if subscription:
                await bot.send_message(
                    chat_id=Shp_user_id,
                    text="Оплата прошла успешно. У вас активированна подписка",
                )
    else:
        result = "bad sign"
        logger.warning(f"Неверная подпись для InvId: {InvId}")

    logger.info(f"Ответ: {result}")
    return PlainTextResponse(result)
