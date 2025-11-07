import hashlib
from urllib import parse
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from loguru import logger

from src.config import bot, dp, settings
from aiogram.types import Update

app = FastAPI()


def calculate_signature(
    *,
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
        base_string = f"{cost}:{inv_id}:{password}"  # Для ResultURL
    else:
        base_string = f"{login}:{cost}:{inv_id}:{password}"  # Для initital и SuccessURL

    additional_params = {
        "Shp_user_id": user_id,
        "Shp_user_telegram_id": user_telegram_id,
        "Shp_product_id": product_id,
    }

    for key, value in sorted(additional_params.items()):
        base_string += f":{key}={value}"

    return hashlib.md5(base_string.encode("utf-8")).hexdigest()


def parse_query_string(query: str) -> dict:
    return dict(parse.parse_qsl(query))


def check_signature_result(
    out_sum, inv_id, received_signature, password, user_id, user_telegram_id, product_id
) -> bool:
    signature = calculate_signature(
        login=settings.merchant_login,
        cost=out_sum,
        inv_id=inv_id,
        password=password,
        user_id=user_id,
        user_telegram_id=user_telegram_id,
        product_id=product_id,
        is_result=True,
    )
    return signature.lower() == received_signature.lower()


@app.post("/robokassa/result", response_class=PlainTextResponse)
async def robokassa_result(
    OutSum: str = Form(...),
    InvId: str = Form(...),
    SignatureValue: str = Form(...),
    Shp_user_id: str = Form(...),
    Shp_user_telegram_id: str = Form(...),
    Shp_product_id: str = Form(...),
):
    """ResultURL — Robokassa POST запрос после оплаты"""
    if check_signature_result(
        OutSum,
        InvId,
        SignatureValue,
        settings.password2,
        Shp_user_id,
        Shp_user_telegram_id,
        Shp_product_id,
    ):
        await bot.send_message(
            chat_id=int(Shp_user_telegram_id), text="Оплата прошла успешна"
        )
        return f"OK{InvId}"

    return {"status": "faild"}


@app.get("/robokassa/success", response_class=PlainTextResponse)
async def robokassa_success(request: Request):
    """SuccessURL — GET запрос после успешной оплаты"""
    params = parse_query_string(str(request.query_string))
    out_sum = params.get("OutSum")
    inv_id = params.get("InvId")
    signature = params.get("SignatureValue")
    user_id = params.get("Shp_user_id")
    user_telegram_id = params.get("Shp_user_telegram_id")
    product_id = params.get("Shp_product_id")

    if check_signature_result(
        out_sum,
        inv_id,
        signature,
        settings.password1,
        user_id,
        user_telegram_id,
        product_id,
    ):
        return "Thank you for using our service"
    return {"status": "faild"}
