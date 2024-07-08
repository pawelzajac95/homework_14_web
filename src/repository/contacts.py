from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from database.models import User
from database.models import Contact
from schemas import ContactCreate, UserModel
from typing import List




async def get_contact(db: Session, user: User, contact_id: int) -> Contact:
    """
    Retrieves a single contact with the specified ID for a specific user.
    
    :param db: The database session.
    :type db: Session
    :param user: The user to retrieve contact for.
    :type user: User
    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :return: The contact with the specified ID, or None if it does not exist.
    :rtype: Contact | None
    """
    return db.query(Contact).filter(and_(ContactCreate.id == contact_id, Contact.user_id == user.id)).first()

async def get_contacts(db: Session, user: User, search_query: str = None) -> List[Contact]:
    """
    Retrieves a list of notes for a specific user with specified pagination parameters.
    
    :param db: The database session.
    :type db: Session
    :param user: The user to retrieve contacts for.
    :type user: User
    :param search_query: Search for contacts by query.
    :type search_query: str
    :return: A list of contacts.
    :rtype: List[Contact]
    """
    query = db.query(Contact).filter(Contact.user_id == user.id)
    if search_query:
        search_filter = or_(
            Contact.first_name.ilike(f"%{search_query}%"),
            Contact.last_name.ilike(f"%{search_query}%"),
            Contact.email.ilike(f"%{search_query}%")
        )
        query = query.filter(search_filter)    
    return query.all()

async def create_contact(db: Session, contact: ContactCreate, user: User) -> Contact:
    """
    Creates a new note for a specific user.

    :param db: The database session.
    :type db: Session
    :param contact: The data for the contact to create.
    :type contact: ContactCreate
    :param user: The user to create the contact for.
    :type user: User
    :return: The newly created contact.
    :rtype: Contact
    """
    db_contact = Contact(first_name=contact.first_name, last_name=contact.last_name, email=contact.email, phone_number=contact.phone_number, birth_date=contact.birth_date, user=user)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

async def update_contact(db: Session, user: User, contact_id: int, contact: ContactCreate) -> Contact | None:
    """
    Updates a single contact with the specified ID for a specific user.
    
    :param db: The database session.
    :type db: Session
    :param user: The user to update contact for.
    :type user: User
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param contact: The updated data for the contact.
    :type contact: ContactCreate
    :return: The updated contact, or None if it does not exist.
    :rtype: Contact | None
    """
    db_contact = await get_contact(db, contact_id, user)
    if not db_contact:
        return None
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact

async def delete_contact(db: Session, user: User, contact_id: int) -> Contact | None:
    """
    Removes a single contact with the specified ID for a specific user.

    :param db: The database session.
    :type db: Session
    :param user: The user to remove the contact for.
    :type user: User
    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :return: The removed contact, or None if it does not exist.
    :rtype: Contact | None
    """
    db_contact = await get_contact(db, contact_id, user)
    if not db_contact:
        return None
    db.delete(db_contact)
    db.commit()
    return {"message": "Contact deleted successfully"}

async def get_contacts_upcoming_birthdays(db: Session) -> Contact | None:
    """
    List of contacts with upcoming birthdays
    
    :param db: The database session.
    :type db: Session
    :return: list of contacts who have birthdays this week, or None if it does not exist.
    :rtype: Contact | None
    """    
    today = datetime.today().date()
    end_date = today + timedelta(days=7)
    return db.query(Contact).filter(
        (Contact.birth_date >= today) & (Contact.birth_date <= end_date)
    ).all()

