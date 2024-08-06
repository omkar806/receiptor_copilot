from typing import List
import requests, logging
from src.constants import *
from src.models.message import Message
from src.models.supabase_models import Supabase_Client
import pycurl
from io import BytesIO
import json
from urllib.parse import quote
import time
from requests.exceptions import RequestException

def fetch_emails(brand_name: str, page_token: int, access_token: str):
    g_query = G_QUERY
    if brand_name is not None:
        g_query = G_BRAND_QUERY(brand_name)
    
    gmail_url = f"https://www.googleapis.com/gmail/v1/users/me/messages?q={g_query}&maxResults=20"
    if page_token:
        gmail_url += f"&pageToken={page_token}"
    
    # gmail_response = requests.get(gmail_url, headers={"Authorization": f"Bearer {access_token}"})
    # gmail_data = gmail_response.json()

    gmail_data = make_request(gmail_url, headers={"Authorization": f"Bearer {access_token}"})

    
    if "messages" in gmail_data:
        return gmail_data['messages'], gmail_data.get("nextPageToken", None)
    
    return [], gmail_data.get("nextPageToken", None)

def insert_message(message:Message, session_id, user_id):
    logging.info("inserting message")
    supabase = Supabase_Client().instance
    print("to_json")
    data = message.to_json(session_id, user_id)
    print(data)
    try:
        if data:
            response = (
                supabase.table("receipt_radar_structured_data_duplicate")
                .insert(data)
                .execute()
            )
            print("response:")
            print(response)
        else:
            print("error: Unable to store receipt because of value being null")
    except Exception as e:
        print("error: Unable to store receipt because of ", e)

def fetch_message(message_id: str, access_token: str):
    
    message_url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}"
    # message_response = requests.get(message_url, headers={"Authorization": f"Bearer {access_token}"})
    # message_data = message_response.json()
    message_data = make_request(message_url, headers={"Authorization": f"Bearer {access_token}"})
    return message_data

def filter_messages(messages: List[Message]):
    logging.info("filtering messages")
    supabase = Supabase_Client().instance
    existing_ids = [record['message_id'] for record in supabase.table("receipt_radar_structured_data_duplicate").select("message_id").execute().data]
    messages = [message for message in messages if message['id'] not in existing_ids]
    return messages

def insert_message_for_fine_tuning(raw_text, message_id):
    try:
        supabase = Supabase_Client().instance
        supabase.table("receipt_radar_fine_tuning_data").insert({"raw_text": raw_text, "message_id": message_id}).execute()
    except:
        print("error: unable to insert in fine tuning data")
        pass

def update_total_messages_count(session_id: str, total_messages_count: int):
    try:
        supabase = Supabase_Client().instance
        supabase.table("receipt_radar_history").update({"total_receipts": total_messages_count}).eq("id", int(session_id)).execute()
    except Exception as e:
        print(f"error: unable to update total messages count :: {e}")
        pass

def update_receipt_radar_history_status(session_id: str, status: str, total_processed_receipts: int = None):
    print(f"updating receipt radar history status for session_id: {session_id} with status: {status} and total_processed_receipts: {total_processed_receipts}")
    try:
        supabase = Supabase_Client().instance
        if total_processed_receipts:
            res = supabase.table("receipt_radar_history").update({"status": status, "total_processed_receipts": total_processed_receipts}).eq("id", int(session_id)).execute()
        else:
            res = supabase.table("receipt_radar_history").update({"status": status}).eq("id", int(session_id)).execute()
        print(f"response from update receipt radar history status: {res}")
    except Exception as e:
        print(f"error: unable to update receipt radar history status :: {e}")
        pass

def summarize_text(text: str, max_tokens: int = 500) -> str:
    """
    Summarize the input text using OpenAI's GPT-3.5-turbo model.

    Args:
    text (str): The input text to be summarized.
    max_tokens (int): The maximum number of tokens for the summary. Default is 500.

    Returns:
    str: The summarized text.
    """
    from langchain_openai import ChatOpenAI
    from langchain.chains.summarize import load_summarize_chain
    from langchain.docstore.document import Document
    import os

    # Ensure the OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Initialize the ChatOpenAI model
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")

    # Create a Document object from the input text
    doc = Document(page_content=text)

    # Load the summarization chain
    chain = load_summarize_chain(llm, chain_type="stuff")

    # Generate the summary
    summary = chain.run([doc])

    # Truncate the summary if it exceeds the max_tokens
    if len(summary.split()) > max_tokens:
        summary = " ".join(summary.split()[:max_tokens]) + "..."

    return summary


def summarize_text_without_llm(text: str, max_tokens: int = 800) -> str:
    """
    Summarize the input text without using an LLM, using a simple extractive method.

    Args:
    text (str): The input text to be summarized.
    max_tokens (int): The maximum number of tokens for the summary. Default is 500.

    Returns:
    str: The summarized text.
    """
    import re
    from collections import Counter

    # Preprocess the text
    sentences = re.split(r'(?<=[.!?])\s+', text)
    words = re.findall(r'\w+', text.lower())

    # Calculate word frequencies
    word_freq = Counter(words)

    # Score sentences based on word frequencies
    sentence_scores = []
    for sentence in sentences:
        score = sum(word_freq[word.lower()] for word in re.findall(r'\w+', sentence))
        sentence_scores.append((sentence, score))

    # Sort sentences by score in descending order
    ranked_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)

    # Select top sentences for summary
    summary_sentences = []
    token_count = 0
    for sentence, _ in ranked_sentences:
        sentence_tokens = len(sentence.split())
        if token_count + sentence_tokens > max_tokens:
            break
        summary_sentences.append(sentence)
        token_count += sentence_tokens

    # Join the selected sentences to form the summary
    summary = ' '.join(summary_sentences)

    return summary



def make_request(url, headers, method='GET', useRequests=True, max_retries=3, backoff_factor=0.3, data=None):
    """
    Makes an HTTP request using requests or pycurl with retry logic.
    
    Args:
        url (str): The API endpoint URL.
        headers (dict): A dictionary of headers.
        method (str): The HTTP request method ('GET', 'POST', etc.).
        useRequests (bool): Whether to use the requests library (True) or pycurl (False).
        max_retries (int): Maximum number of retry attempts.
        backoff_factor (float): Factor to multiply the delay between retries.
        data (dict): JSON payload for POST requests (optional).

    Returns:
        dict: The JSON response data.
    """
    for attempt in range(max_retries):
        try:
            if useRequests:
                response = requests.request(method, url, headers=headers, json=data, verify=False)
                response.raise_for_status()
                return response.json()
            else:
                buffer = BytesIO()
                c = pycurl.Curl()

                try:
                    # Set the URL
                    print("URl")
                    print(url)
                    c.setopt(c.URL, quote(url, safe=':/?&='))

                    # Set the HTTP headers
                    formatted_headers = [f"{key}: {value}" for key, value in headers.items()]
                    c.setopt(c.HTTPHEADER, formatted_headers)

                    # Set the request method
                    if method == 'POST':
                        c.setopt(c.POST, 1)
                        if data:
                            json_data = json.dumps(data).encode('utf-8')
                            c.setopt(c.POSTFIELDS, json_data)
                            c.setopt(c.HTTPHEADER, formatted_headers + ['Content-Type: application/json'])
                    elif method == 'PUT':
                        c.setopt(c.CUSTOMREQUEST, 'PUT')
                    elif method == 'DELETE':
                        c.setopt(c.CUSTOMREQUEST, 'DELETE')
                    elif method == 'HEAD':
                        c.setopt(c.NOBODY, 1)
                    else:
                        c.setopt(c.CUSTOMREQUEST, method)

                    # Capture the response data
                    c.setopt(c.WRITEDATA, buffer)

                    # Execute the request
                    c.perform()

                    # Get the HTTP response code
                    status_code = c.getinfo(pycurl.RESPONSE_CODE)

                    # Get the response data
                    response_data = buffer.getvalue().decode('utf-8')
                    
                    # Parse JSON response
                    response_data = json.loads(response_data)
                    return response_data

                except pycurl.error as e:
                    response_data = f"An error occurred: {str(e)}"
                    status_code = None
                finally:
                    # Cleanup
                    c.close()
        
        except (RequestException, pycurl.error, json.JSONDecodeError) as e:
            if attempt == max_retries - 1:
                raise  # Re-raise the last exception if all retries are exhausted
            
            # Calculate delay using exponential backoff
            delay = backoff_factor * (2 ** attempt)
            print(f"Request failed. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
    
    # This line should never be reached due to the raise in the loop
    raise Exception("Max retries exceeded")