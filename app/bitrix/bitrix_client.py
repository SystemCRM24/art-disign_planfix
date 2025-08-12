# my_project/app/core/bitrix_client.py
from fast_bitrix24 import BitrixAsync # <--- Используем BitrixAsync
from typing import Dict, Any, List
from urllib.parse import urlparse
import re
import httpx


class BitrixClient:
    def __init__(self, webhook_url: str):
        self.b = BitrixAsync(webhook_url)
        self.webhook_url = webhook_url
        parsed_url = urlparse(self.webhook_url)
        self.portal_domain = parsed_url.netloc
        self.webhook_auth = parsed_url.path.split('/')[3]

    async def download_files_from_deal(self, deal_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
            Находит все поля с файлами в данных сделки, скачивает их и возвращает 
            список словарей, каждый из которых содержит исходное поле, имя и бинарное содержимое.
            
            Returns:
                [
                    {'source_field': 'UF_CRM_1741696651', 'filename': 'kp.pdf', 'content': b'...'},
                    ...
                ]
        """
        if not deal_data:
            return []

        files_to_download = []
        for field_key, value in deal_data.items():
            if isinstance(value, dict) and 'downloadUrl' in value:
                files_to_download.append({'source_field': field_key, 'file_info': value})
            elif isinstance(value, list) and value and isinstance(value[0], dict) and 'downloadUrl' in value[0]:
                for file_item in value:
                    files_to_download.append({'source_field': field_key, 'file_info': file_item})

        if not files_to_download:
            return []

        downloaded_files_with_context = []
        async with httpx.AsyncClient() as client:
            for item in files_to_download:
                source_field = item['source_field']
                file_info = item['file_info']
                
                relative_url = file_info['downloadUrl']
                download_url_with_auth = f"https://{self.portal_domain}{relative_url}&login=yes"
                
                payload = {
                    "AUTH_FORM": "Y",
                    "TYPE": "AUTH",
                    "USER_LOGIN": "admin@systemcrm.ru",
                    "USER_PASSWORD": "IDGAF2025!"
                }

                try:
                    response = await client.post(
                        download_url_with_auth,
                        timeout=60.0,
                        data=payload
                    )

                    content_type = response.headers.get('content-type', '').lower()
                    if response.status_code == 200 and 'text/html' not in content_type:
                        file_content = response.content
                        filename = f"file_{file_info['id']}"

                        content_disposition = response.headers.get('Content-Disposition')
                        if content_disposition:
                            match = re.search(r'filename="([^"]+)"', content_disposition)
                            if match:
                                try:
                                    filename = match.group(1).encode('latin-1').decode('cp1251')
                                except Exception:
                                    filename = match.group(1)

                        downloaded_files_with_context.append({
                            'source_field': source_field,
                            'filename': filename,
                            'content': file_content,
                        })
                        print(f"Успешно скачан файл '{filename}' из поля {source_field}")
                    else:
                        print(f"Ошибка при скачивании файла из поля {source_field}. Статус: {response.status_code}")

                except Exception as e:
                    print(f"Исключение при скачивании файла из поля {source_field}: {e}")

        return downloaded_files_with_context

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

    async def get_requisites(self, company_id: int) -> Dict[str, Any]:
        result = []
        requisites = await self.b.get_all(
            'crm.requisite.list', 
            {"filter": {"ENTITY_ID": str(company_id)}})
        bank = None
        if requisites:
            result.append(requisites[0])
            bank = await self.b.get_all('crm.requisite.bankdetail.list', {
                "filter": {
                    "ID": requisites[0].get("ID")
                }
            })
        if bank:
            result.append(bank[0])
        return result
    
    async def close(self):
        pass
