import asyncio
from fastapi import Request,APIRouter
import requests, logging
from ..constants import G_QUERY, G_BRAND_QUERY
from ..llm.chat_client import ChatClient
from src.receipt_radar.helper.helper import update_total_messages_count
from src.receipt_radar.helper.helper import make_request
router = APIRouter(prefix="/gmail")

@router.post("/total_messages")
async def get_total_messages(request:Request):
    body = await request.json()

    access_token = body.get('access_token', None)
    supabase_token = body.get('supabase_token', None)
    session_id = body.get('session_id', None)

    if access_token is None : return {"message":"Access token Invalid ! Try Again!"}

    if supabase_token is None : return {"message":"Supabase token Invalid ! Try Again!"}

    if session_id is None : return {"message":"Session id Invalid ! Try Again!"}

    user_query = body.get('brand_name') if body.get('brand_name') is not None else None

    brand_name = None
    logging.info(f"brand_name: {user_query}")
    logging.info(f"access_token : {access_token}")
    if user_query is not None:
        chat = ChatClient().create(conversation=[])
        response = chat.send_message(content=f"{user_query}", stream=False)
        if response.text == 'others':
            brand_name = None
        else:
            brand_name = response.text

    search_query = G_QUERY
    if brand_name is not None:
        search_query = G_BRAND_QUERY(brand_name)
    total_messages = 0
    page_token = None

    while True:
        gmail_url = f"https://www.googleapis.com/gmail/v1/users/me/messages?q={search_query}"
        if page_token:
            gmail_url += f"&pageToken={page_token}"
        
        gmail_data = make_request(gmail_url, headers={"Authorization": f"Bearer {access_token}"})

        if "messages" in gmail_data:
            total_messages += len(gmail_data["messages"])
        
        if "nextPageToken" in gmail_data:
            page_token = gmail_data["nextPageToken"]
        else:
            break
        pass

    print(f"total_messages from gmail api: {total_messages}")

    async def delayed_update():
        await asyncio.sleep(2.5)
        update_total_messages_count(session_id, total_messages)
    
    asyncio.create_task(delayed_update())

    return {"total_messages":total_messages}