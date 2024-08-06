from typing import Optional, List
from src.models.attachment import Attachment

class Message:              
    def __init__(self, message_id: str, body: Optional[str], attachments: Optional[List[Attachment]], company: str ,structured_data:Optional[List]):
        self.id = message_id
        self.body = body
        self.attachments = attachments
        self.company = company
        self.structured_data = structured_data
        

    def to_json(self, session_id: str, user_id: str) -> Optional[dict]:
        data = {
            "session_id": session_id,
            "message_id": self.id,
            "body": self.body,
            "user_id": user_id,
            "company":self.company,
            "attachment_id":self.attachments[0].attachment_id if self.attachments.__len__() > 0 else None,
        }
        try:
            if self.structured_data:
                data.update(self.structured_data[0])
            return data
        except:
            return None

