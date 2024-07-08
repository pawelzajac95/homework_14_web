from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from starlette import status

from database.db import get_db
from database.models import User

class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
        Verify password.
        
        :param plain_password: Takes a regular password as arguments.
        :type plain_password: str
        :param hashed_password: hashed password.
        :type hashed_password: str
        :return: Returns a boolean value indicating whether plain and hashed passwords match.
        :rtype: boolean
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Password encryption.

        :param password: regular password.
        :type password: str
        :return: Takes a plain password as an argument and returns an encoded password using the 'hash' method of the 'pwd_context' object.
        :rtype: str
        """
        return self.pwd_context.hash(password)

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# define a function to generate a new access token
async def create_access_token(data: dict, expires_delta: Optional[float] = None):
    """
    Generating new "access_token".

    :param data: A dictionary containing the data that will be encoded and placed in the JWT token.
    :type data: dict
    :param expires_delta: Optional argument specifying expiration time.
    :type expires_delta: float
    :return: A function that generates a new "access_token" with a specified validity period.
    :rtype: str
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
    encoded_access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_access_token

# define a function to generate a new refresh token
async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    """
    New refresh access token.
    
    :param data: A dictionary containing the data that will be encoded and placed in the JWT token.
    :type data: dict
    :param expires_delta: Optional argument specifying expiration time.
    :type expires_delta: float
    :return: Information is added to the dictionary about when the token was created (iat), when it expired (exp), and that it is a refresh token (scope).
    :rtype: str
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
    encoded_refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_refresh_token

async def get_email_form_refresh_token(refresh_token: str):
    """
    Extracting the user's email address.
    
    :param refresh_token: Information about the token, when it was created, when it expired, and that it is a refresh token.
    :type refresh_token: str
    :return: The function is used to extract the user's email address. If the token is successfully decoded and has a valid scope, the function returns the user's email.
    :rtype: str
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload['scope'] == 'refresh_token':
            email = payload['sub']
            return email
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    User authentication based on their access token.
    
    :param token: A class to extract a token from a request.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: The user authentication function extracts the email address and uses it to query the database for user information.
    :rtype: HTTP
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
# Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload['scope'] == 'access_token':
            email = payload["sub"]
            if email is None:
                raise credentials_exception
        else:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    user: User = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
