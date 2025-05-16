import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

API_SALT = os.getenv("API_SALT", "default_salt")


def verify_salt(x_api_salt: Optional[str] = Header(None)):
    if API_SALT != "default_salt" and (not x_api_salt or x_api_salt != API_SALT):
        raise HTTPException(status_code=403, detail="Invalid API salt")
    return x_api_salt
