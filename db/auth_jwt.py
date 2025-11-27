# db/auth_jwt.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

import jwt  # PyJWT

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my_jwt_secret")
JWT_ALGORITHM = "HS256"


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(hours=8)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
