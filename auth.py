import bcrypt
import jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
import os

pwd_context = CryptContext(schemes=["bcrypt"])
SECRET_KEY = os.getenv('secret_key')
ALGORITHM = "HS256"

# Haszowanie hasła
def hash_password(password: str):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Weryfikacja haseł
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Generowanie tokena JWT
def create_jwt_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Dekodowanie tokena JWT
def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
