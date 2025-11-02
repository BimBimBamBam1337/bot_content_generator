from robokassa import Robokassa
from robokassa.types import InvoiceType, RobokassaResponse
from src.config import settings

payment = Robokassa(
    merchant_login=settings.merchant_login,
    password1=settings.password1,
    password2=settings.password2,
    is_test=True,
)


def create_payment(user_id: int, price: int) -> RobokassaResponse:
    response = payment.generate_open_payment_link(out_sum=price, inv_id=user_id)
    return response


async def check_status_payment(signature: str):
    return await payment.is_result_notification_valid(signature=signature)
