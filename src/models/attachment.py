
class Attachment:
    def __init__(self, attachment_len:int,filename: str, data: str,attachment_id:str):
        self.attachment_len = attachment_len
        self.filename = filename
        self.data = data
        self.attachment_id =attachment_id