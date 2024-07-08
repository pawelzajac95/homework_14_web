import re
from typing import Callable
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Security, Request
from fastapi_limiter import FastAPILimiter
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routes import contacts, auth
from repository.auth import create_access_token, create_refresh_token, get_email_form_refresh_token, get_current_user, Hash
from database.db import get_db
from database.models import User
from conf.config import settings
from ipaddress import ip_address
from typing import Callable
import os, sys
import logging



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = FastAPI()
user_agent_ban_list = [r"Gecko", r"Python-urllib"]
hash_handler = Hash()
security = HTTPBearer()
origins = [
    "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api/auth')

banned_ips = []

class UserModel(BaseModel):
    username: str
    password: str


@app.post("/signup")
async def signup(body: UserModel, db: Session = Depends(get_db)):
    exist_user = db.query(User).filter(User.email == body.username).first()
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    new_user = User(email=body.username, password=hash_handler.get_password_hash(body.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"new_user": new_user.email}

@app.post("/login")
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not hash_handler.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
# Generate JWT
    access_token = await create_access_token(data={"sub": user.email})
    refresh_token = await create_refresh_token(data={"sub": user.email})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.get('/refresh_token')
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = await get_email_form_refresh_token(token)
    user = db.query(User).filter(User.email == email).first()
    if user.refresh_token != token:
        user.refresh_token = None
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await create_access_token(data={"sub": email})
    refresh_token = await create_refresh_token(data={"sub": email})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/secret")
async def read_item(current_user: User = Depends(get_current_user)):
    return {"message": 'secret router', "owner": current_user.email}

@app.on_event("startup")
async def startup():
    r = await redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, encoding="utf-8",
                          decode_responses=True)
    await FastAPILimiter.init(r)


@app.middleware("http")
async def ban_ips(request: Request, call_next: Callable):
    ip = ip_address(request.client.host)
    if ip in banned_ips:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
    response = await call_next(request)
    return response

@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    user_agent = request.headers.get("user-agent")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
    response = await call_next(request)
    return response

@app.get("/")
def read_root():
    return {"message": "Hello world"}

logger = logging.getLogger("uvicorn.error")

@app.on_event("startup")
async def startup_event():
    routes = [route.path for route in app.routes]
    logger.info(f"Available routes: {routes}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

