# my_project/app/api/v1/endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.services.bitrix_deal_processor import BitrixDealProcessor
from app.dependencies import get_bitrix_deal_processor

router = APIRouter()

@router.post("/")
async def process_bitrix_deal_webhook(
    deal_id: int = Query(..., description="ID of the Bitrix24 deal to process."),
    processor: BitrixDealProcessor = Depends(get_bitrix_deal_processor)
):
    """
    Receives a webhook from Bitrix24 containing a deal ID (as a query parameter) and processes it.
    """
    try:
        await processor.process_deal(deal_id)
        return {"message": f"Deal {deal_id} processing initiated successfully in Bitrix and Planfix."}
    except Exception as e:
        print(f"Error processing deal {deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process deal {deal_id}: {e}"
        )