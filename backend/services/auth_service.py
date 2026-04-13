from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt
from pydantic import BaseModel
import hashlib

# Secret key to sign the JWT token. In production, move to .env
SECRET_KEY = "super-secret-AI-Platform-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days 

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

def verify_password(plain_password, hashed_password):
    # Bcrypt has a 72-character limit. To safely handle longer passwords,
    # we hash the password with SHA-256 first.
    password_bytes = plain_password.encode('utf-8')
    pre_hashed = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    # hashed_password is usually stored as a string in DB, need bytes for bcrypt
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
        
    return bcrypt.checkpw(pre_hashed, hashed_password)

def get_password_hash(password):
    # Bcrypt has a 72-character limit. To safely handle longer passwords,
    # we hash the password with SHA-256 first.
    password_bytes = password.encode('utf-8')
    pre_hashed = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
