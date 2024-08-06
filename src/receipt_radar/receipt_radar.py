import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio
from typing import Optional
from .helper.message_parser import MessageParser
from .helper.helper import *
from src.models.message import Message
import concurrent.futures

async def fetch_receipts(access_token: str, brand_name: Optional[str], user_id: str, session_id: str):
    total_processed = 0
    
    page_token = None
    messages = []

    async def delayed_update():
        await asyncio.sleep(2.5)
        update_receipt_radar_history_status(session_id, "processing")
    
    asyncio.create_task(delayed_update())
    
    def fetch_message_wrapper(message_data):
        message_id = message_data.get("id")
        if message_id:
            message_data = fetch_message(message_id=message_id, access_token=access_token)
            return MessageParser(message_data, access_token).extract_message(message_id)   
        return None

    while True:
        print(f"Current receipts that are processed: {total_processed}")
        messages, next_page_token = fetch_emails(
            brand_name=brand_name,
            page_token=page_token,
            access_token=access_token,
        )

        # remove duplicate messages that are already processed in the backend
        messages = filter_messages(messages)

        print(f"After filter messages: {messages.__len__()}")

        if messages:
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures=[executor.submit(fetch_message_wrapper, message_data) for message_data in messages]
                for future in concurrent.futures.as_completed(futures):
                    message = future.result()
                    if message:
                        total_processed += 1
                        insert_message(message, session_id, user_id)
                        
        if next_page_token:
            page_token = next_page_token
        else:
            break
    print(f"Total messages processed: {total_processed}")
    
    update_receipt_radar_history_status(session_id, "completed", total_processed_receipts=total_processed)
    
    logging.info(f"Total Processed Messages : {total_processed}")
