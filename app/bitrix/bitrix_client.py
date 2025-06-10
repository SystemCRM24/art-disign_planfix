# my_project/app/core/bitrix_client.py
from fast_bitrix24 import BitrixAsync # <--- Используем BitrixAsync
from typing import Dict, Any, Optional, List


class BitrixClient:
    def __init__(self, webhook_url: str):
        self.b = BitrixAsync(webhook_url) # <--- Инициализируем BitrixAsync

    async def get_deal(self, deal_id: int) -> Dict[str, Any]:
        # get_all возвращает список, даже если ожидается один элемент
        deals = await self.b.get_all('crm.deal.get', {"ID": deal_id})
        print(deals)
        return deals if deals else None

    async def get_contact(self, contact_id: int) -> Dict[str, Any]:
        contacts = await self.b.get_all('crm.contact.get', {"ID": contact_id})
        return contacts if contacts else None

    async def get_company(self, company_id: int) -> Dict[str, Any]:
        companies = await self.b.get_all('crm.company.get', {"ID": company_id})
        return companies if companies else None

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        users = await self.b.get_all('user.get', {"ID": user_id})
        print(users)
        return users[0] if users else None
    
    async def get_address(self, id: int) -> str:
        address_dict = await self.b.get_all('crm.address.list', {"filter": {"ENTITY_ID": id}})  
        if address_dict:
            parts = [
                address_dict[0].get("COUNTRY"),
                address_dict[0].get("PROVINCE"),
                address_dict[0].get("REGION"),
                address_dict[0].get("CITY"),
                address_dict[0].get("POSTAL_CODE"),
                address_dict[0].get("ADDRESS_1"),
                address_dict[0].get("ADDRESS_2")
            ]
        else:
            return ""

        filtered_parts = [part for part in parts if part]

        return ", ".join(filtered_parts)

    async def get_requisites(self, deal_id: int) -> Dict[str, Any]:
        result = []
        requisites = await self.b.get_all('crm.requisite.list', {
            "filter": {
                "ENTITY_ID": str(deal_id)
            }
        })
        bank = await self.b.get_all('crm.requisite.bankdetail.list', {
            "filter": {
                "ID": requisites[0].get("ID")
            }
        })
        if requisites:
            result.append(requisites[0])
        if bank:
            result.append(bank[0])
        return result
    
    async def close(self):
        pass