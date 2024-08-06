G_QUERY = f'(subject:"your order" OR subject:receipts OR subject:receipt OR subject:invoice OR subject:invoices OR subject:"insurance" OR subject:"health report" OR category:purchases OR label:receipts OR label:invoices OR label:insurance OR label:health)'

LLM_MODEL = "gpt-4o-mini"

MAX_OUTPUT_TOKENS=280

MAX_INPUT_TOKENS=4096

MAX_TOKENS = 2000
TEMPERATURE = 0.0

def G_BRAND_QUERY(brand_name: str): f'(subject:"your order" OR subject:receipts OR subject:receipt OR subject:invoice OR subject:invoices OR subject:"insurance" OR subject:"health report" OR category:purchases OR label:receipts OR label:invoices OR label:insurance OR label:health) AND ({brand_name})'