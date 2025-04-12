from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from app.utils import create_access_token, decode_token, verify_password, get_password_hash
from app.models import User, Token
from pymongo import MongoClient
from datetime import timedelta
import os

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["portialabs"]
users_collection = db["users"]

@router.post("/signup")
async def signup(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    users_collection.insert_one({"email": user.email, "password": hashed_password})
    return {"message": "User created successfully"}

@router.post("/token", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token({"sub": user["email"]})
    refresh_token = create_access_token({"sub": user["email"]}, timedelta(days=7))
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token") 
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    new_access_token = create_access_token({"sub": payload["sub"]})
    refresh_token = create_access_token({"sub": payload["sub"]}, timedelta(days=7))
    response.set_cookie(key="access_token", value=new_access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/me")
async def get_me(request: Request):
    payload = decode_token(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": user["email"]}