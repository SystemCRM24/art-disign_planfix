# my_project/app/schemas/bitrix.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class BitrixContact(BaseModel):
    ID: str
    NAME: Optional[str] = None
    LAST_NAME: Optional[str] = None
    SECOND_NAME: Optional[str] = None
    EMAIL: Optional[List[dict]] = None
    PHONE: Optional[List[dict]] = None


class BitrixCompany(BaseModel):
    ID: str
    TITLE: Optional[str] = None
    ADDRESS: Optional[str] = None
    PHONE: Optional[List[dict]] = None


class BitrixDeal(BaseModel):
    ID: str
    TITLE: str
    CONTACT_ID: Optional[str] = None
    COMPANY_ID: Optional[str] = None


class BitrixTaskResult(BaseModel):
    task: dict


class BitrixError(BaseModel):
    error: str
    error_description: str


class BitrixDealWebhook(BaseModel):
    deal_id: int = Field(..., description="ID of the Bitrix24 deal to process.")


class PlanfixContactCreate(BaseModel):
    # Если известен ID контакта в Planfix, для обновления
    id: Optional[int] = None
    name: str = Field(..., description="Name of the contact/company.")
    type: Optional[str] = Field("CONTACT", description="Type of contact: 'CONTACT' or 'COMPANY'")
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    externalId: Optional[str] = Field(None, description="External ID, e.g., Bitrix contact ID.")


class PlanfixTaskCreate(BaseModel):
    title: str = Field(..., description="Title of the task.")
    description: Optional[str] = None
    responsible: Dict[str, int] = Field(..., description="Responsible user. E.g., {'id': 123}")
    parent: Optional[Dict[str, int]] = Field(None, description="Parent task. E.g., {'id': 123}")
    contact: Optional[Dict[str, int]] = Field(None, description="Related contact. E.g., {'id': 123}")
    company: Optional[Dict[str, int]] = Field(None, description="Related company. E.g., {'id': 123}")
    externalId: Optional[str] = Field(None, description="External ID, e.g., Bitrix deal ID.")
    deadline: Optional[Dict[str, str]] = None
