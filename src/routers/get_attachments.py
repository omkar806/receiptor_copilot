from fastapi import Request,APIRouter
import requests
from src.receipt_radar.helper.helper import make_request
from src.models import supabase_models as sp
router = APIRouter(prefix="/view")


@router.post("/attachment")
async def get_total_messages(request:Request):
    body = await request.json()
    access_token = body.get('access_token',None)
    supabase_authorisation_token = body.get("supabase_authorisation",None)
    user_id = sp.AuthUser_Validator(supabase_authorisation_token)
    if not user_id:
        return {"User Unauthenticated !"}
    if access_token is None : return {"message":"Access token Invalid ! Try Again!"}
    message_id = body.get('message_id',None)
    attachment_id = body.get('attachment_id' , None)
    if message_id is None or attachment_id is None : 
        return {"Attachment Not Present !!"}
    
    attachment_url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}/attachments/{attachment_id}"

    try:
        attachment_data = make_request(attachment_url, headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        data = attachment_data.get('data',None)
        return {"message_id":message_id , "attachment_id":attachment_id , "file_data":data}
    except Exception as e:
        print(f"Error occured !! {e}")
        return {f"Exceptional error occured {e}!!"}