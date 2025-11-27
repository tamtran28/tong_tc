# db/auth_jwt.py
from datetime import datetime
from datetime import timedelta

import jwt

from db.security import SECRET_KEY, ALGORITHM, get_token_expire_delta


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    data: {"sub": username, "role": "...", ...}
    """
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = get_token_expire_delta()

    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    """
    Giải mã token -> payload (dict); nếu token hết hạn/sai -> None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
