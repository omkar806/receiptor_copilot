from pydantic import BaseModel
from supabase import create_client
from functools import lru_cache
from typing import Optional
import os

@lru_cache(maxsize=1)
class Supabase_Settings(BaseModel):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")



@lru_cache(maxsize=1)
class Supabase_Client:
    values = Supabase_Settings()
    instance = create_client(values.SUPABASE_URL, values.SUPABASE_ANON_KEY)


def AuthUser_Validator(apitoken: str) -> Optional[str]:
    supabase = Supabase_Client().instance
    try:
        user = supabase.auth.get_user(apitoken)
        return str(user.user.id)
    except Exception as e:
        return None