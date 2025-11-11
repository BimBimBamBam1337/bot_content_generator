import random

from robokassa import Robokassa
from robokassa.types import InvoiceType, RobokassaResponse
from src.config import settings

payment = Robokassa(
    merchant_login=settings.merchant_login,
    password1=settings.password1,
    password2=settings.password2,
    is_test=False,
)


def create_payment(user_id: int, price: int) -> RobokassaResponse:
    inv_id = random.randint(1, 2147483647)
    response = payment.generate_open_payment_link(
        out_sum=price, default_prefix=f"shp_user_id={user_id}", inv_id=inv_id
    )
    return response


async def check_status_payment(user_id: int):
    return await payment.get_payment_details(inv_id=user_id)
