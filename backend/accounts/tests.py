from django.test import TestCase
from django.core.exceptions import ValidationError
from core.constants import UserRole
from accounts.models import User
from accounts.validators import ProofBillPasswordValidator


class AccountsTestCase(TestCase):
    def test_case_insensitive_email_uniqueness(self):
        user = User.objects.create_user(
            email='TestUser@Example.Com',
            password='ValidPass123!',
            role=UserRole.CUSTOMER
        )
        self.assertEqual(user.email, 'testuser@example.com')

        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='TESTUSER@EXAMPLE.COM',
                password='ValidPass123!',
                role=UserRole.CUSTOMER
            )

    def test_proofbill_password_validator(self):
        validator = ProofBillPasswordValidator(min_length=9)

        # Too short (< 9 chars)
        with self.assertRaises(ValidationError):
            validator.validate('Pass12!')

        # Missing uppercase
        with self.assertRaises(ValidationError):
            validator.validate('password123!')

        # Missing lowercase
        with self.assertRaises(ValidationError):
            validator.validate('PASSWORD123!')

        # Missing special character
        with self.assertRaises(ValidationError):
            validator.validate('Password123')

        # Valid password
        try:
            validator.validate('ValidPass123!')
        except ValidationError:
            self.fail("Validator unexpectedly raised ValidationError for valid password!")

    def test_user_roles(self):
        admin = User.objects.create_superuser('admin@proofbill.io', 'AdminPass123!')
        self.assertTrue(admin.is_admin_user)
        self.assertTrue(admin.is_staff_user)
        self.assertFalse(admin.is_customer_user)

        staff = User.objects.create_user('staff@proofbill.io', 'StaffPass123!', role=UserRole.STAFF)
        self.assertFalse(staff.is_admin_user)
        self.assertTrue(staff.is_staff_user)
        self.assertFalse(staff.is_customer_user)

        cust = User.objects.create_user('cust@brightloop.io', 'CustPass123!', role=UserRole.CUSTOMER)
        self.assertFalse(cust.is_admin_user)
        self.assertFalse(cust.is_staff_user)
        self.assertTrue(cust.is_customer_user)

    def test_permission_and_scoping_rules(self):
        # 1. Unauthenticated request to dashboard redirects to login
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        # 2. Staff user cannot access admin-only staff creation
        staff = User.objects.create_user('staff2@proofbill.io', 'StaffPass123!', role=UserRole.STAFF)
        self.client.force_login(staff)
        staff_create_resp = self.client.get('/accounts/staff/create/')
        self.assertEqual(staff_create_resp.status_code, 403)

        # 3. Customer user cannot access staff dashboard
        cust1_user = User.objects.create_user('cust1@brightloop.io', 'CustPass123!', role=UserRole.CUSTOMER)
        self.client.force_login(cust1_user)
        dash_resp = self.client.get('/dashboard/')
        self.assertEqual(dash_resp.status_code, 403)
