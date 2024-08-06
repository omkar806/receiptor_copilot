from fastapi import Request,APIRouter
from ..llm.chat_client import ChatClient
from src.models import supabase_models as sp
from ..receipt_radar.receipt_radar import fetch_receipts
import logging

router = APIRouter(prefix="/receipt-radar")

@router.post("/gmail")
async def receipt_radar_router(request:Request):
    body = await request.json()
    apitoken = body.get('supabase_authorisation', None)
    session_id = body.get('session_id', None)
    if not session_id:
        raise Exception("unable to get the session")
    if not apitoken:
        raise Exception("unable to authenticate the user")
    user_id = sp.AuthUser_Validator(apitoken)
    if not user_id:
        raise Exception("Unable to verify the user")
    
    access_token = body.get('access_token', None)
    logging.info(f"access_token:{access_token}")
    user_query = body.get('brand_name', None)
    logging.info(f"brand_name: {user_query}")
    if access_token is None:
        raise Exception("Unable to authenticate the google account")
    brand_name = None
    logging.info(f"user_query: {user_query}")
    logging.info(f"access_token : {access_token}")
    if user_query is not None:
        chat = ChatClient().create(conversation=[])
        response = chat.send_message(content=f"{user_query}", stream=False)
        if response.text == 'others':
            brand_name = None
        else:
            brand_name = response.text
    logging.info(f"brand_name: {brand_name}")
    await fetch_receipts(access_token, brand_name, user_id, session_id)
    return {"status": True}
