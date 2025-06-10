# my_project/app/dependencies.py
from typing import AsyncGenerator
from fastapi import Depends
from app.core.config import settings
from app.bitrix.bitrix_client import BitrixClient
from app.planfix.planfix_client import PlanfixClient
from app.services.bitrix_deal_processor import BitrixDealProcessor


async def get_bitrix_client() -> AsyncGenerator[BitrixClient, None]:
    client = BitrixClient(webhook_url=settings.BITRIX_WEBHOOK_URL)
    try:
        yield client
    finally:
        await client.close()


async def get_planfix_client() -> AsyncGenerator[PlanfixClient, None]:
    client = PlanfixClient(
        api_url=settings.PLANFIX_API_URL,
        auth_token=settings.PLANFIX_AUTH_TOKEN
    )
    try:
        yield client
    finally:
        await client.close()


async def get_bitrix_deal_processor(
    bitrix_client: BitrixClient = Depends(get_bitrix_client),
    planfix_client: PlanfixClient = Depends(get_planfix_client) # <--- Добавлено
) -> BitrixDealProcessor:
    return BitrixDealProcessor(
        bitrix_client=bitrix_client,
        planfix_client=planfix_client
    )