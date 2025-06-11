import httpx
from typing import Dict, Any, Optional


class PlanfixClient:
    def __init__(self, api_url: str, auth_token: str):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}",
        }
        self.client = httpx.AsyncClient(base_url=self.api_url, headers=self.headers)

    async def _call(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic method to call Planfix API"""
        url = f"{endpoint}" # Planfix API часто принимает .json в конце URL
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Planfix HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"Request failed: {e.__class__.__name__}: {str(e)}")
            print(f"URL: {e.request.url}")
            print(f"Full request object: {e.request}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred with Planfix API: {e}")
            raise

    async def get_contact(self, phone: str) -> Optional[int]:
        contact_data = {
            "offset": 0,
            "pageSize": 100,
            "fields": "id",
            "filters": [
                {
                    "type": 4003,
                    "operator": "equal",
                    "value": phone
                }
            ]
        }
        result = await self._call("contact/list", contact_data)
        print(result)
        res = result.get("contacts")
        if res is None:
            return None
        return result.get("contacts")[0].get('id')
    
    async def get_company_by_name(self, name: str) -> Optional[int]:
        data = {
            "offset": 0,
            "pageSize": 100,
            "fields": "id",
            "filters": [
                {
                    "type": 4014,
                    "operator": "equal",
                    "value": name
                }
            ]
        }
        result = await self._call("contact/list", data)
        return result.get("contacts")[0].get("id") if len(result.get("contacts")) > 0 else None

    async def get_company(self, inn: str) -> Optional[int] | None:
        data = {
            "offset": 0,
            "pageSize": 100,
            "fields": "id",
            "filters": [
                {
                    "type": 4101,
                    "operator": "equal",
                    "value": str(inn),
                    "field": 114520
                }
            ]
        }
        result = await self._call("contact/list", data)
        return result.get("contacts")[0].get("id") if len(result.get("contacts")) > 0 else None

    async def create_or_update_contact(self, contact_data: Dict[str, Any]) -> Optional[int]:
        """
        Creates or updates a contact/company in Planfix.
        Planfix POST /contact/ can create contact or company.
        If contact_data contains 'id', it will update.
        Returns the ID of the created/updated contact/company.
        """
        # Planfix API для /contact/ ожидает contact_data в корне, а не обертку
        result = await self._call("contact/", contact_data)
        return result.get("id") # Planfix возвращает ID нового/обновленного объекта

    async def create_task(self, task_data: Dict[str, Any]) -> Optional[int]:
        """
        Creates a task in Planfix.
        Returns the ID of the created task.
        """
        result = await self._call(f"task/", task_data)
        return result.get("id") # Planfix возвращает ID новой задачи

    async def close(self):
        await self.client.aclose()

    async def get_responsible_user_by_email(self, email: str) -> Optional[int]:
        """
        Get responsible user id in Planfix by email from Bitrix
        Args:
            email
        Returns:
            id user in PlanFix
        """
        data = {
            "offset": 0,
            "pageSize": 100,
            "fields": "id,name,midname,lastname, email",
            "filters": [
                {
                    "type": 9003,
                    "field": 0,
                    "operator": "equal",
                    "value": email
                }
            ]
        }
        user_data = await self._call("user/list", data)
        if user_data.get("result") == "success" and user_data.get("users"):
            return user_data["users"][0]["id"]