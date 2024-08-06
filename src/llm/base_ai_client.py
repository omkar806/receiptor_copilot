import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class BaseAIClient:
    def __init__(self,system,model_response):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.system = system
        self.model = model_response

    def create(self, conversation):
        model = genai.GenerativeModel('gemini-pro')
        new_conversation = [
            {"role": 'user', "parts": [self.system]},
            {"role": 'model', "parts": [self.model]},
        ]
        new_conversation.extend(conversation)
        return model.start_chat(history=new_conversation)