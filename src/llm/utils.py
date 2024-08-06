import PyPDF2
from docx import Document
import io
import re
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from ..models.candidate import Candidate
from ..receipt_radar.helper.helper import make_request
from ..constants import LLM_MODEL , MAX_TOKENS , TEMPERATURE,MAX_OUTPUT_TOKENS,MAX_INPUT_TOKENS
import os
import base64
from langchain_openai import OpenAI
import tiktoken
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import requests
import os
import json

api_key=os.getenv('OPENAI_API_KEY')

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def openai_response(model:OpenAI,input:str):
    result = model.invoke(input)
    return result


def contruct_prompt_v1(raw_text:str)->str:
    system_prompt = f"""Extract information from the following receipt OCR text and return a JSON object with these exact keys: brand, total_cost, location, purchase_category, brand_category, Date, currency, filename, payment_method, metadata.
    Rules:
    1. For total_cost, use the highest monetary value in the text.
    2. For brand_category, choose the closest match from: ["Fashion and Apparel", "Jewelry and Watches", "Beauty and Personal Care", "Automobiles", "Real Estate", "Travel and Leisure", "Culinary Services", "Home and Lifestyle", "Technology and Electronics", "Sports and Leisure", "Art and Collectibles", "Health and Wellness", "Stationery and Writing Instruments", "Children and Baby", "Pet Accessories", "Financial Services", "Airline Services", "Accommodation Services", "Beverages Services", "Services", "Insurance"]
    3. Format Date as dd-mm-yyyy.Strictly return the date in the format dd-mm-yyyy.
    4. For metadata field, return a json which gives summary of the receipt.Only consider the insurance receipt, return metadata json with fields like insurance_number, insurance_expiry, agent_details etc. metadata field will have only a json object strictly that summarize the receipt contents provided , if not a insurane receipt add it as null. 
    4. Use currency codes (e.g., USD, EUR) instead of symbols.
    5. Generate filename as 'PURCHASE_TYPE_BRAND_DATE' (e.g., 'clothing_gucci_20230715').
    6. If a value is not found, return null.
    7. If all values are null, return null.
    Ensure the strictly that output is a valid JSON object containing strictly the above keys, without any explanations.
    Here's the OCR text below analyse it and convert into json using keys provided in first line and using the rules provided in rules section:\n\n
    {raw_text}\n
    Generate a JSON response in the following format without using the ```json block. Ensure the output is properly formatted as plain text JSON.\n
    \n
    """
    return system_prompt

def ensure_token_limit_v1(text, model=LLM_MODEL, max_tokens=MAX_TOKENS):
    tokenizer = tiktoken.encoding_for_model(model)
    
    tokens = tokenizer.encode(text)
    
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        truncated_text = tokenizer.decode(truncated_tokens)
        print("Truncated text")
        return truncated_text
    else:
        return text

def structure_document_data_v1(raw_text:str)->dict:
    def tryfloat(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0
        
    prompt_to_llm = contruct_prompt_v1(raw_text)

    #checking how many tokens are there
    print("no of tokens")
    print(ensure_token_limit_v1(prompt_to_llm))
    # print("printing prompt")
    # print(prompt_to_llm)
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "OpenAI-Organization": os.environ['ORG_ID']
    }   

    data = {
        "model": "gpt-4o-mini",
        "max_tokens": MAX_TOKENS, 
        "messages": [{"role": "user", "content": f"{prompt_to_llm}"}],
        "temperature": TEMPERATURE
    }
    try:
        output = make_request(url, headers=headers, data=data, method='POST')
        print("printing output")
        print(output)
        content = output['choices'][0]['message']['content']
        print(content)
        candidate_data = json.loads(content)
        try:
            candidate_data['metadata'] = json.dumps(candidate_data['metadata'])
        except:
            if candidate_data['metadata']:
                candidate_data['metadata'] = str(candidate_data['metadata'])
            else:
                candidate_data['metadata'] = None
        candidate = Candidate(**candidate_data)
        print("open-ai dict response")
        print(candidate.__dict__)
        return candidate.__dict__
    except Exception as e:
        print(f"Request failed with status code: {e}")
        return None




def strcuture_document_data(raw_text:str)->dict:
    def tryfloat(value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    raw_text = ensure_token_limit(raw_text)
    try:
        model_name = LLM_MODEL
        temperature = 0.0
        model = OpenAI(model_name=model_name, temperature=temperature, max_tokens=MAX_OUTPUT_TOKENS)
                
        doc_query= (
            "Extract and return strictly a JSON object containing only the following keys: brand, total_cost, location, purchase_category, brand_category, Date , currency ,filename,payment_method .FOR total_cost LOOK FOR THE HIGHEST VALUE IN RECEIPT OCR TEXT. Ensure that if a value is not present in the OCR text, it is returned as null."    
        )
        
        parser = PydanticOutputParser(pydantic_object=Candidate)
        
        prompt = PromptTemplate(
            template="""Your primary goal is to take my receipt OCR text and then return back a parsable json.
            Below is the receipt OCR:.\n {raw_text} \n These are the format instructions telling you to convert the data into json :\n {format_instructions}\nDo not include descriptions or explanations from the Candidate class in the JSON output. The response must be a valid JSON object.\n Follow the below instrcution very strictly:\n {query} \n""",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions(),"raw_text":raw_text},
        )

        input = prompt.format_prompt(query=doc_query)
        result = openai_response(model,input.to_string())   

        class_object= parser.parse(result)
        dict_object=class_object.__dict__
        if all(value is None for value in dict_object.values()):
            print(dict_object)
            print("Got null for dict object")
 
        if dict_object['total_cost'] is not None:
            dict_object['total_cost'] = dict_object['total_cost'].split('.')[0].replace(',','')
            dict_object['total_cost'] = re.sub(r'\D', '', dict_object['total_cost'])
            dict_object['total_cost'] = tryfloat(dict_object['total_cost'])

        return dict_object
    except Exception as e:
        print(f"Error occurred: {e}")
        return {}

def ensure_token_limit(text, model=LLM_MODEL, max_tokens=MAX_INPUT_TOKENS):
    tokenizer = tiktoken.encoding_for_model(model)
    
    tokens = tokenizer.encode(text)
    
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        truncated_text = tokenizer.decode(truncated_tokens)
        print(truncated_text)
        return truncated_text
    else:
        return text


def extract_text_from_pdf(pdf_data):
    with io.BytesIO(pdf_data) as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text

def extract_text_from_docx(docx_data):
    doc = Document(io.BytesIO(docx_data))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_text_from_attachment(filename, data):
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(base64.urlsafe_b64decode(data))
    elif filename.endswith('.docx'):
        return extract_text_from_docx(base64.urlsafe_b64decode(data))
    else:
        # Add handling for other document types if needed
        return "Unsupported document type"
