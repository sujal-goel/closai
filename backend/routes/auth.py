from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from services.auth_service import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token
)
from services.database import is_connected

router = APIRouter(tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization: str | None = None

class UserOut(BaseModel):
    name: str
    email: EmailStr
    organization: str | None = None


@router.post("/signup", response_model=Token)
async def signup(user: UserCreate):
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database connection failed")
        
    from services.database import users_collection
    collection = users_collection()
    
    # Check if user exists
    existing = await collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Create user
    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]
    
    await collection.insert_one(user_dict)
    
    # Authenticate and respond
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database connection failed")
        
    from services.database import users_collection
    collection = users_collection()
    
    user = await collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to inject the current user into protected endpoints."""
    from jose import JWTError, jwt
    from services.auth_service import SECRET_KEY, ALGORITHM, TokenData
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database disconnected")
        
    from services.database import users_collection
    user = await users_collection().find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)
