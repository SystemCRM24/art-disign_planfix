# my_project/app/services/bitrix_deal_processor.py
from typing import Dict, Any, Optional, List
from app.bitrix.bitrix_client import BitrixClient
from app.planfix.planfix_client import PlanfixClient


BITRIX_CONTRACT_FIELD = "UF_CRM_1741696673"
PLANFIX_CONTRACT_FIELD_ID = 114406

BITRIX_TO_PLANFIX_FIELD_MAP = {
    "UF_CRM_1741696651": 114386, # Поле "КП"
    "UF_CRM_1741696673": 114406, # Поле "Договор"
    "UF_CRM_1741696692": 114388, # Поле "Логотип для нанесения"
}


class BitrixDealProcessor:
    def __init__(self, bitrix_client: BitrixClient, planfix_client: PlanfixClient):
        self.bitrix_client = bitrix_client
        self.planfix_client = planfix_client

    async def _get_bitrix_entity_details(self, entity_id: Optional[str], get_function) -> Optional[Dict[str, Any]]:
        if entity_id and entity_id != "0":
            try:
                result = await get_function(int(entity_id))
                return result
            except Exception as e:
                print(f"Error fetching Bitrix entity {entity_id}: {e}")
        return None

    async def _get_planfix_user_id_from_bitrix_user(self, bitrix_user_id: str) -> int:
        """
        Attempts to find a Planfix user ID corresponding to a Bitrix user ID.
        Falls back to a default Planfix user ID from settings if not found.
        """
        bitrix_user_details = await self.bitrix_client.get_user(int(bitrix_user_id))
        if bitrix_user_details:
            user_email = bitrix_user_details.get("EMAIL")
            if user_email:
                planfix_user_id = await self.planfix_client.get_responsible_user_by_email(user_email)
                if planfix_user_id:
                    print(f"Found Planfix user ID {planfix_user_id} for Bitrix user {bitrix_user_id} ({user_email}).")
                    return planfix_user_id
        return planfix_user_id
    
    def _transform_phone_data(self, data: List[Dict]):
        result = []
        if not data:
            return []
        
        for item in data:
            phone_entry = {
                "number": item.get("VALUE"),
                "type": 1
            }
            result.append(phone_entry)
        return result

    async def process_deal(self, deal_id: int):
        print(f"Processing deal with ID: {deal_id}")

        deal = await self.bitrix_client.get_deal(deal_id)
        if not deal:
            print(f"Bitrix Deal {deal_id} not found or no data received. Aborting integration.")
            return

        contact_id_bitrix = deal.get("CONTACT_ID")
        company_id_bitrix = deal.get("COMPANY_ID")
        responsible_id_bitrix = deal.get("ASSIGNED_BY_ID")


        contact_details_bitrix: Optional[Dict[str, Any]] = None
        company_details_bitrix: Optional[Dict[str, Any]] = None

        files_with_context = await self.bitrix_client.download_files_from_deal(deal)
        
        # 2. Загружаем файлы в Planfix и создаем карту соответствия
        # { 'UF_CRM_1741696651': [12345], 'UF_CRM_1741696673': [12346, 12347], ... }
        planfix_files_map = {}
        if files_with_context:
            for file_data in files_with_context:
                try:
                    file_id = await self.planfix_client.upload_file(
                        filename=file_data['filename'],
                        file_content=file_data['content']
                    )
                    if file_id:
                        source_field = file_data['source_field']
                        # Если для этого поля еще нет списка ID, создаем его
                        if source_field not in planfix_files_map:
                            planfix_files_map[source_field] = []
                        planfix_files_map[source_field].append(file_id)
                except Exception as e:
                    print(f"Не удалось загрузить файл '{file_data['filename']}' в Planfix: {e}")

        if contact_id_bitrix:
            contact_details_bitrix = await self._get_bitrix_entity_details(contact_id_bitrix, self.bitrix_client.get_contact)

        company_details_bitrix = await self._get_bitrix_entity_details(company_id_bitrix, self.bitrix_client.get_company)   
        # --- Сопоставление ответственного пользователя для Planfix ---
        # --- Обработка данных для Planfix: Контакт и Компания ---
        contact_id: Optional[int] = None
        planfix_company_id: Optional[int] = None
        contact_id: Optional[int] = None
        company_id: Optional[int] = None
        planfix_task_responsible_id: Optional[int] = None

        if responsible_id_bitrix:
            planfix_task_responsible_id = await self._get_planfix_user_id_from_bitrix_user(
                responsible_id_bitrix
            )
        else:
            print(f"Bitrix deal {deal_id} has no ASSIGNED_BY_ID. Using default Planfix ID {planfix_task_responsible_id}.")

        if contact_details_bitrix:
            contact_name = contact_details_bitrix.get('NAME', '')
            contact_lastname = contact_details_bitrix.get('LAST_NAME', '')
            contact_email = contact_details_bitrix.get("EMAIL")[0]["VALUE"] if contact_details_bitrix.get("EMAIL") else None
            contact_details_bitrix.get("EMAIL")

            contact_phone = contact_details_bitrix.get("PHONE") if contact_details_bitrix.get("PHONE") else None
            contact_id = await self.planfix_client.get_contact(contact_phone)
            if contact_id is None:
                planfix_contact_data = {
                    "template": {
                        "id": 1
                    },
                    "name": str(contact_name),
                    "lastname": str(contact_lastname),
                    "isCompany": "false",
                    "email": str(contact_email),
                    "phones": self._transform_phone_data(contact_phone)
                }
                try:
                    contact_id = await self.planfix_client.create_or_update_contact(planfix_contact_data)
                    print(f"Planfix Contact processed: ID {contact_id}")
                except Exception as e:
                    print(f"НЕ ПОЛУЧИЛОСЬ СОЗДАТЬ КОНТАКТ- {contact_id_bitrix}: {e}")
        if company_details_bitrix:
            company_title = company_details_bitrix.get("TITLE", "Неизвестная компания")
            company_address = await self._get_bitrix_entity_details(company_id_bitrix, self.bitrix_client.get_address)
            company_email = company_details_bitrix.get("EMAIL")[0]["VALUE"] if company_details_bitrix.get("EMAIL") else None
            company_phone = company_details_bitrix.get("PHONE") if company_details_bitrix.get("PHONE") else None

            company_requisites = await self._get_bitrix_entity_details(company_id_bitrix, self.bitrix_client.get_requisites)
            if company_requisites:
                company_id = await self.planfix_client.get_company(company_requisites[0].get("RQ_INN"))
            else:
                company_id = await self.planfix_client.get_company_by_name(company_title)
            if company_id is None:
                planfix_company_data = {
                    "template": {
                        "id": 2
                    },
                    "name": str(company_title),
                    "address": str(company_address),
                    "email": str(company_email) if company_email else "",
                    "isCompany": "true",
                    "phones": self._transform_phone_data(company_phone),
                    "customFieldData": [
                        {
                            "field": {
                                "id": 114520
                            },
                            "value": str(company_requisites[0].get("RQ_INN")) if company_requisites else None
                        },
                        {
                            "field": {
                                "id": 114522
                            },
                            "value": str(company_requisites[0].get("RQ_KPP")) if company_requisites else None
                        },
                        {
                            "field": {
                                "id": 114526
                            },
                            "value": str(company_requisites[0].get("RQ_OGRN")) if company_requisites else None
                        },
                        {
                            "field": {
                                "id": 114528
                            },
                            "value": str(company_requisites[1].get("RQ_BIK")) if len(company_requisites) > 1 else None
                        },
                        {
                            "field": {
                                "id": 114530
                            },
                            "value": str(company_requisites[1].get("RQ_ACC_NUM")) if len(company_requisites) > 1 else None
                        }
                    ],
                    "contacts": [
                        {
                            "id": contact_id
                        }
                    ]
                }
                try:
                    company_id = await self.planfix_client.create_or_update_contact(planfix_company_data)
                    print(f"Planfix Company processed: ID {planfix_company_id}")
                except Exception as e:
                    print(f"не удалось создать компанию {company_id_bitrix}: {e}")
        # --- Формируем описание задачи для Planfix ---
        task_description_planfix = f"Сделка Bitrix24: {deal.get('TITLE', 'Без названия')}\n"
        if contact_details_bitrix:
            task_description_planfix += f"Контакт: {contact_details_bitrix.get('NAME', '')} {contact_details_bitrix.get('LAST_NAME', '')}\n"
            if contact_details_bitrix.get("EMAIL"):
                task_description_planfix += f"Email: {', '.join([e['VALUE'] for e in contact_details_bitrix['EMAIL'] if 'VALUE' in e])}\n"
            if contact_details_bitrix.get("PHONE"):
                task_description_planfix += f"Телефон: {', '.join([p['VALUE'] for p in contact_details_bitrix['PHONE'] if 'VALUE' in p])}\n"
        if company_details_bitrix:
            task_description_planfix += f"Компания: {company_details_bitrix.get('TITLE', 'Неизвестная компания')}\n"
            if company_details_bitrix.get("ADDRESS"):
                task_description_planfix += f"Адрес компании: {company_details_bitrix['ADDRESS']}\n"

        custom_field_payload = []
        for bitrix_field, planfix_field_id in BITRIX_TO_PLANFIX_FIELD_MAP.items():
            if bitrix_field in planfix_files_map:
                planfix_file_ids = planfix_files_map[bitrix_field]
                custom_field_payload.append({
                    "field": {"id": planfix_field_id},
                    "value": planfix_file_ids # Planfix ожидает список ID
                })

        print(planfix_task_responsible_id)
        planfix_main_task_data = {
            "name": "Подготовить и отправить клиенту договор и счёт.",
            "description": task_description_planfix,
            "assignees": {
                "users": [
                    {
                        "id": f"user:{str(planfix_task_responsible_id)}"
                    }
                ]
            },
            "counterparty": {
                "id": company_id
            },
            "template": {
                "id": 203
            },
            "customFieldData": custom_field_payload

        }

        planfix_main_task_id: Optional[int] = None
        try:
            planfix_main_task_id = await self.planfix_client.create_task(planfix_main_task_data)
            print(f"Planfix Main Task created: ID {planfix_main_task_id}")
        except Exception as e:
            print(f"Failed to create Planfix Main Task for Bitrix Deal ID {deal_id}: {e}")

        custom_field_data_for_contract = [
            {
                "field": {"id": 114502},
                "value": "дизайн-макет"
            }
        ]

        if BITRIX_CONTRACT_FIELD in planfix_files_map:
            # Если есть, получаем его ID
            contract_file_ids = planfix_files_map[BITRIX_CONTRACT_FIELD]
            
            # И добавляем в наш второй список
            custom_field_data_for_contract.append({
                "field": {"id": PLANFIX_CONTRACT_FIELD_ID},
                "value": contract_file_ids # Planfix ожидает список ID
            })
        # 3. Создать подзадачу "Подготовить дизайн" в Planfix
        if planfix_main_task_id:
            planfix_sub_task_data = {
                "name": "Подготовить дизайн.",
                "description": task_description_planfix,
                "assignees": {
                    "users": [
                        {
                            "id": f"user:{planfix_task_responsible_id}"
                        }
                    ]
                },
                "counterparty": {
                    "id": company_id
                },
                "parent": {
                    "id": planfix_main_task_id
                },
                "template": {
                    "id": 88
                },
                "customFieldData": custom_field_data_for_contract
            }
            try:
                planfix_sub_task_id = await self.planfix_client.create_task(planfix_sub_task_data)
                print(f"Planfix Sub-Task created: ID {planfix_sub_task_id}")
            except Exception as e:
                print(f"Failed to create Planfix Sub-Task for Bitrix Deal ID {deal_id}: {e}")
        else:
            print("Skipping Planfix Sub-Task creation as Main Task was not created.")
