import hashlib
from urllib import parse
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from loguru import logger

from src.config import bot, dp, settings
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
        base_string = f"{cost}:{inv_id}:{password}"  # Для Result URL
    else:
        base_string = (
            f"{login}:{cost}:{inv_id}:{password}"  # Для initital URL и Success URL
        )

    additional_params = {
        "Shp_user_id": user_id,
        "Shp_user_telegram_id": user_telegram_id,
        "Shp_product_id": product_id,
    }
    for key, value in sorted(additional_params.items()):
        base_string += f":{key}={value}"
    logger.info(f"Base string for signature: {base_string}")
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
    print("signature", signature)
    print("received_signature", received_signature)
    return signature.lower() == received_signature.lower()


@app.post("/robokassa/result", response_class=PlainTextResponse)
async def robokassa_result(request: Request):
    """
    Обрабатывает ResultURL Robokassa, когда приходит строка запроса.
    """
    logger.success("Получен ответ от Робокассы!")

    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    data = dict(parse_qsl(body_str))

    OutSum = data.get("OutSum") or data.get(
        "out_summ"
    )  # используем ровно то, что пришло
    InvId = data.get("InvId") or data.get("inv_id")
    SignatureValue = data.get("SignatureValue") or data.get("crc")
    Shp_user_id = data.get("Shp_user_id")
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
        logger.info(f"Успешная проверка подписи для InvId: {InvId}")

        payment_data = {
            "user_id": int(Shp_user_id),
            "payment_id": SignatureValue,
            "price": int(float(OutSum)),
            "product_id": int(Shp_product_id),
            "payment_type": "robocassa",
        }

    else:
        result = "bad sign"
        logger.warning(f"Неверная подпись для InvId: {InvId}")

    logger.info(f"Ответ: {result}")
    return PlainTextResponse(result)


# @app.post("/robokassa/result", response_class=PlainTextResponse)
# async def robokassa_result(
#     data: Request,
#     # OutSum: str = Form(...),
#     # InvId: str = Form(...),
#     # SignatureValue: str = Form(...),
#     # Shp_user_id: str = Form(...),
#     # Shp_user_telegram_id: str = Form(...),
#     # Shp_product_id: str = Form(...),
# ):
#     """ResultURL — Robokassa POST запрос после оплаты"""
#     body_bytes = await data.body()
#     body_text = body_bytes.decode("utf-8")
#     print(body_text)
#     # if check_signature_result(
#     #     OutSum,
#     #     InvId,
#     #     SignatureValue,
#     #     settings.password2,
#     #     Shp_user_id,
#     #     Shp_user_telegram_id,
#     #     Shp_product_id,
#     # ):
#     #     await bot.send_message(
#     #         chat_id=int(Shp_user_telegram_id), text="Оплата прошла успешна"
#     #     )
#     #     return f"OK{InvId}"
#
#     return {"status": "faild"}
