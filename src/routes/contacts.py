from fastapi import APIRouter, Query, FastAPI, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas import ContactCreate, ContactResponse
from database.db import get_db
from repository.contacts import get_contact, create_contact, update_contact, delete_contact, get_contacts_upcoming_birthdays
from typing import List, Optional
from database import models
import database
from datetime import date, timedelta
from database.models import User, Contact
from repository import auth
from fastapi_limiter.depends import RateLimiter



models.Base.metadata.create_all(bind=database.db.engine)

app = FastAPI()
router = APIRouter(prefix='/contacts')

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_new_contact(contact: ContactCreate, db_session: Session = Depends(get_db), current_user: User = Depends(auth.get_current_user)):
    return await create_contact(db_session, contact, current_user)

@router.get("/", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    first_name: Optional[str] = Query(None, description="Filter by first name"),
    last_name: Optional[str] = Query(None, description="Filter by last name"),
    email: Optional[str] = Query(None, description="Filter by email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    query = db.query(models.Contact).filter(Contact.user_id == current_user.id)

    if first_name:
        query = query.filter(models.Contact.first_name.contains(first_name))
    if last_name:
        query = query.filter(models.Contact.last_name.contains(last_name))
    if email:
        query = query.filter(models.Contact.email.contains(email))

    contacts = query.offset(skip).limit(limit).all()
    return contacts

@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db_session: Session = Depends(get_db), current_user: User = Depends(auth.get_current_user)):
    contact = await get_contact(db_session, contact_id, current_user)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_existing_contact(contact_id: int, contact: ContactCreate, db_session: Session = Depends(get_db), current_user: User = Depends(auth.get_current_user)):
    updated_contact = await update_contact(db_session, contact_id, contact, current_user)
    if not updated_contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return updated_contact

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_contact(contact_id: int, db_session: Session = Depends(get_db), current_user: User = Depends(auth.get_current_user)):
    deleted = await delete_contact(db_session, contact_id, current_user)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

@router.get("/upcoming_birthdays/", response_model=List[ContactResponse])
def read_upcoming_birthdays(db: Session = Depends(get_db)):
    today = date.today()
    upcoming = today + timedelta(days=7)
    query = db.query(models.Contact).filter(
        models.Contact.birth_date >= today,
        models.Contact.birth_date <= upcoming
    )
    contacts = query.all()
    return contacts

app.include_router(router)