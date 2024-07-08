import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from database.models import Contact, User
from schemas import ContactCreate
from repository.contacts import(
    get_contacts,
    get_contact,
    create_contact,
    delete_contact,
    update_contact,
    
)

class TestContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().all.return_value = contacts
        result = await get_contacts(user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_note_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactCreate(title='test', desctiption='test contact')
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(result.title, body.title)
        self.assertEqual(result.description, body.description)
        self.assertTrue(hasattr(result, 'id'))

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await delete_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await delete_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        body = ContactCreate(title='test', description='test contact')
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_update_contact_not_found(self):
        contact = ContactCreate(title='test', description='test contact')
        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, contact=contact, user=self.user, db=self.session)
        self.assertIsNone(result)
            
if __name__ == '__main__':
    unittest.main()