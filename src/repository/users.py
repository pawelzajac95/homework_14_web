from sqlalchemy.orm import Session

from database.models import User
from schemas import UserModel

async def get_user_by_email(email: str, db: Session) -> User:
    """
    Get user by email.
    
    :param email: User email.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: Takes an email and database session and returns a user object from the database if a user with that email address exists.
    :rtype: User
    """
    return db.query(User).filter(User.email == email).first()

async def create_user(body: UserModel, db: Session) -> User:
    """
    Create user in the database.
    
    :param body: The data for the user to create.
    :type body: UserModel
    :param db: The database session.
    :type db: Session
    :return: Adds a new user to the database.
    :rtype: User
    """
    new_user = User(**body.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    Updates a token for a specific user.
    
    :param user: The user to update the token for.
    :type user: User
    :param token: The updated data for the token.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: Updates the user's refresh_token field and applies changes to the database.
    :rtype: None
    """
    user.refresh_token = token
    db.commit()

async def confirmed_email(email: str, db: Session) -> None:
    """
    Email address verification.

    :param email: User email.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: Setting the value of the confirmed attribute in the database to True for the selected user.
    :rtype: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()