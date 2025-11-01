from robokassa import Robokassa
from robokassa.types import InvoiceType
from src.config import settings

payment = Robokassa(
    merchant_login=settings.merchant_login,
    password1=settings.password1,
    password2=settings.password2,
    is_test=True,
)


def create_payment_link(user_id: int, price: int):
    response = payment.generate_open_payment_link(out_sum=price, inv_id=user_id)
    return response.url


async def check_status_payment(user_id: int):
    return await payment.get_payment_details(inv_id=user_id)
