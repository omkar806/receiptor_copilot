import re
import base64
import requests
from src.models.message import Message
from src.models.attachment import Attachment
from src.receipt_radar.helper.helper import make_request
from src.llm import utils as ut
from .helper import insert_message_for_fine_tuning, summarize_text_without_llm
from typing import Optional, List, Dict
from bs4 import BeautifulSoup


class MessageParser:
    def __init__(self, message_data: dict, access_token: str) -> None:
        self.message_data = message_data
        self.access_token = access_token

    def extract_message(self, message_id: str):
        subject = MessageParser.extract_subject_from_mail(self.message_data)
        company_from_mail = MessageParser.extract_domain_name(
            self.message_data['payload']['headers'], subject)
        body = MessageParser.extract_html_from_mail(self.message_data)
        attachments, structed_attachment_data = MessageParser.extract_attachments_from_mail(
            self.access_token, self.message_data)
        return Message(message_id=message_id, body=body, attachments=attachments, company=company_from_mail, structured_data=structed_attachment_data)

    @staticmethod
    def get_company_type(company_name: str) -> str:
        company_types_dict = {'ao yun': 'wines and spirit', 'ardbeg': 'wines and spirit', 'belvedere': 'wines and spirit', 'bodega numanthia': 'wines and spirit', 'chandon': 'wines and spirit', 'château cheval blanc': 'wines and spirit', "château d'yquem": 'wines and spirit', 'château galoupet': 'wines and spirit', 'cheval des andes': 'wines and spirit', 'clos19': 'wines and spirit', 'cloudy bay': 'wines and spirit', 'colgin cellars': 'wines and spirit', 'dom pérignon': 'wines and spirit', 'domaine des lambrays': 'wines and spirit', 'eminente': 'wines and spirit', 'glenmorangie': 'wines and spirit', 'hennessy': 'wines and spirit', 'joseph phelps': 'wines and spirit', 'krug': 'wines and spirit', 'mercier': 'wines and spirit', 'moët & chandon': 'wines and spirit', 'newton vineyard': 'wines and spirit', 'ruinart': 'wines and spirit', 'terrazas de los andes': 'wines and spirit', 'veuve clicquot': 'wines and spirit', 'volcan de mi tierra': 'wines and spirit', 'woodinville': 'wines and spirit', 'berluti': 'Fashion & Leather Goods', 'celine': 'Fashion & Leather Goods', 'christian dior': 'Fashion & Leather Goods', 'emilio pucci': 'Fashion & Leather Goods', 'fendi': 'Fashion & Leather Goods', 'givenchy': 'Fashion & Leather Goods', 'kenzo': 'Fashion & Leather Goods', 'loewe': 'Fashion & Leather Goods', 'loro piana': 'Fashion & Leather Goods', 'louis vuitton': 'Fashion & Leather Goods', 'marc jacobs': 'Fashion & Leather Goods', 'moynat': 'Fashion & Leather Goods', 'patou': 'Fashion & Leather Goods', 'rimowa': 'Fashion & Leather Goods',
                              'acqua di parma': 'Perfumes & Cosmetics', 'benefit cosmetics': 'Perfumes & Cosmetics', 'cha ling': 'Perfumes & Cosmetics', 'fenty beauty by rihanna': 'Perfumes & Cosmetics', 'fresh': 'Perfumes & Cosmetics', 'givenchy parfums': 'Perfumes & Cosmetics', 'guerlain': 'Perfumes & Cosmetics', 'kenzo parfums': 'Perfumes & Cosmetics', 'kvd beauty': 'Perfumes & Cosmetics', 'loewe perfumes': 'Perfumes & Cosmetics', 'maison francis kurkdjian': 'Perfumes & Cosmetics', 'make up for ever': 'Perfumes & Cosmetics', 'officine universelle buly': 'Perfumes & Cosmetics', 'olehenriksen': 'Perfumes & Cosmetics', 'parfums christian dior': 'Perfumes & Cosmetics', 'stella by stella mccartney': 'Perfumes & Cosmetics', 'bulgari': 'Watches & Jewelry', 'chaumet': 'Watches & Jewelry', 'fred': 'Watches & Jewelry', 'hublot': 'Watches & Jewelry', 'repossi': 'Watches & Jewelry', 'tag heuer': 'Watches & Jewelry', 'tiffany & co.': 'Watches & Jewelry', 'zenith': 'Watches & Jewelry', '24s': 'Selective retailing', 'dfs': 'Selective retailing', 'la grande epicerie de paris': 'Selective retailing', 'le bon marché rive gauche': 'Selective retailing', 'sephora': 'Selective retailing', 'belmond': 'Other activities', 'cheval blanc': 'Other activities', 'connaissance des arts': 'Other activities', 'cova': 'Other activities', 'investir': 'Other activities', "jardin d'acclimatation": 'Other activities', 'le parisien': 'Other activities', 'les echos': 'Other activities', 'radio classique': 'Other activities', 'royal van lent': 'Other activities'}
        print(company_types_dict["louis vuitton"])
        return company_types_dict.get(company_name.lower(), 'Others')

    @staticmethod
    def extract_text_from_html_body(html_content: str) -> str:
        if not html_content:
            raise ValueError("HTML content is empty or None")

        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_body_from_mail(message_data: dict) -> str:
        body = None
        if "payload" in message_data:
            payload = message_data["payload"]
            if "parts" in payload:
                for part in payload["parts"]:
                    if 'mimeType' in part and (part['mimeType'] == 'text/plain' or part['mimeType'] == 'text/html'):
                        body_data = part['body'].get('data', '')
                        if body_data:
                            body_base64 = base64.urlsafe_b64decode(body_data)
                            body = MessageParser.extract_text_from_html_body(
                                body_base64)

            elif 'body' in payload:
                body_data = payload['body'].get('data', '')
                if body_data:
                    body_base64 = base64.urlsafe_b64decode(body_data)
                    body = MessageParser.extract_text_from_html_body(
                        body_base64)
            elif 'parts' in payload['body']:
                for part in payload['body']['parts']:
                    if 'mimeType' in part and (part['mimeType'] == 'text/plain' or part['mimeType'] == 'text/html'):
                        body_data = part['body'].get('data', '')
                        if body_data:
                            body_base64 = base64.urlsafe_b64decode(body_data)
                            body = MessageParser.extract_text_from_html_body(
                                body_base64)

        if not body:
            body = message_data.get('snippet', '')
        return body

    @staticmethod
    def extract_html_from_mail(message_data: dict) -> str:
        html_body = None
        if "payload" in message_data:
            payload = message_data["payload"]
            if "parts" in payload:
                for part in payload["parts"]:
                    if 'mimeType' in part and part['mimeType'] == 'text/html':
                        body_data = part['body'].get('data', '')
                        if body_data:
                            html_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            break

            elif 'body' in payload:
                body_data = payload['body'].get('data', '')
                if body_data:
                    html_body = base64.urlsafe_b64decode(body_data).decode('utf-8')

            elif 'parts' in payload['body']:
                for part in payload['body']['parts']:
                    if 'mimeType' in part and part['mimeType'] == 'text/html':
                        body_data = part['body'].get('data', '')
                        if body_data:
                            html_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            break

        if not html_body:
            html_body = f"<html><body>{message_data.get('snippet', '')}</body></html>"

        return html_body

    @staticmethod
    def extract_domain_name(payload: dict, subject: str) -> str:
        def extract_domain_from_email(email_string: str) -> Optional[str]:
            email_address = re.search(
                r'[\w\.-]+@[\w\.-]+', email_string).group()
            domain = email_address.split('@')[-1].split('.')[0]
            if email_address and domain:
                return domain
            else:
                return None

        domain_name = 'others'
        for fromdata in payload:
            if fromdata['name'] == 'From':
                domain_name = extract_domain_from_email(fromdata['value'])
                break
        if 'chanel' in subject.lower():
            return 'chanel'
        if 'louis vuitton' in subject.lower():
            return 'Louis Vuitton'
        return domain_name

    @staticmethod
    def extract_subject_from_mail(message_data: dict) -> str:
        if 'payload' in message_data and 'headers' in message_data['payload']:
            headers = message_data['payload']['headers']
            for header in headers:
                if header['name'] == 'Subject':
                    return header['value']
            return ""
        else:
            return ""

    @staticmethod
    def fetch_attachment_data(access_token: str, message_id: str, attachment_id: str) -> Dict:
        attachment_url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}/attachments/{attachment_id}"
        attachment_response = make_request(attachment_url, headers={"Authorization": f"Bearer {access_token}"})
        return attachment_response

    @staticmethod
    def extract_attachments_from_mail(access_token: str, message_data: dict) -> List[Attachment]:
        attachments = []
        structured_data = []
        is_password_protected = False
        st_str = {
            "brand": "INSERT BRAND NAME",
            "total_cost": "INSERT TOTAL COST",
            "location": "INSERT LOCATION FROM",
            "purchase_category": "INSERT PURCHASE CATEGORY",
            "brand_category": "INSERT BRAND CATEGORY",
            "Date": "INSERT RECEIPT DATE",
            "currency": "INSERT CURRENCY",
            "filename": "GENERATE A FILENAME",
            "payment_method": "INSERT PAYMENT METHOD"
        }
        
        struct_data = None
                    
        if "payload" in message_data and "parts" in message_data["payload"]:
            for part in message_data["payload"]["parts"]:
                if "body" in part and "attachmentId" in part["body"]:
                    attachment_id = part["body"]["attachmentId"]
                    attachment_data = MessageParser.fetch_attachment_data(
                        access_token, message_data["id"], attachment_id)
                    data = attachment_data.get("data", "")

                    # Check if the attachment is a password-protected PDF
                    filename = part.get("filename", "untitled.txt")
                    if filename.endswith(".zip") or filename.endswith(".ics") or filename.endswith(".txt") or filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".gif"):
                        continue
#                     elif filename.lower().endswith('.pdf'):
#                         try:
#                             pdf_data = base64.b64decode(data)
#                             PyPDF2.PdfReader(io.BytesIO(pdf_data))
#                         except PyPDF2.errors.PdfReadError:
#                             print(f"The PDF {filename} is likely password-protected or corrupted.")
#                             is_password_protected = True
#                             continue
                    try:
                        raw_text = ut.extract_text_from_attachment(
                            filename, data)
                    except Exception as e:
                        print(f"Error processing attachment {filename}: {str(e)}")
                        continue
                    
                    # raw_text = summarize_text_without_llm(raw_text)
                    
                    # struct_data = ut.strcuture_document_data(raw_text)
                    struct_data = ut.structure_document_data_v1(raw_text)
                    insert_message_for_fine_tuning(raw_text, message_data["id"])
                    all_null = False
                    if struct_data:
                        for key, value in st_str.items():
                            if struct_data[key]:
                                if str(value) in str(struct_data[key]):
                                    struct_data[key] = None
                    if struct_data:
                        all_null = all(
                        value is None for value in struct_data.values())
                    if all_null:
                        struct_data = None

                    structured_data.append(struct_data)

                    attachments.append(Attachment(attachment_len=len(attachment_data.get(
                        "data", "")), filename=filename, data=attachment_data.get("data", ""),attachment_id=attachment_id))
        
         # If no attachments were processed, use the email body to process structured data
        
        if not struct_data:
            body = MessageParser.extract_body_from_mail(message_data)
            if body:
                struct_data = ut.structure_document_data_v1(body)
                insert_message_for_fine_tuning(body, message_data["id"])
                all_null = False
                if struct_data:
                    for key, value in st_str.items():
                        if struct_data[key] and str(value) in str(struct_data[key]):
                            struct_data[key] = None
                if struct_data:
                    all_null = all(value is None for value in struct_data.values())
                structured_data.append(None if all_null else struct_data)

        return attachments, structured_data