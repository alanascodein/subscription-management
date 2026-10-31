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

    def test_customer_registration(self):
        # GET registration page
        resp = self.client.get('/accounts/register/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Register Customer Account")

        # POST registration with valid data
        post_data = {
            'name': 'Alice Smith',
            'company_name': 'Smith Enterprises',
            'email': 'alice@smith.com',
            'phone': '+91 91234 56789',
            'billing_address': '42 Marine Drive, Kochi',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        }
        resp = self.client.post('/accounts/register/', post_data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/portal/')

        # Verify User and Customer exist
        from subscriptions.models import Customer
        user = User.objects.get(email='alice@smith.com')
        self.assertEqual(user.role, UserRole.CUSTOMER)
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Smith')

        customer = Customer.objects.get(email='alice@smith.com')
        self.assertEqual(customer.user, user)
        self.assertEqual(customer.name, 'Alice Smith')
        self.assertEqual(customer.company_name, 'Smith Enterprises')

    def test_password_reset_flow(self):
        # 1. GET password reset page
        resp = self.client.get('/accounts/password-reset/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Reset your password")

        # 2. POST password reset for existing user
        User.objects.create_user('resetme@example.com', 'OldPassword123!', role=UserRole.CUSTOMER)
        resp = self.client.post('/accounts/password-reset/', {'email': 'resetme@example.com'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/accounts/password-reset/done/')

        # 3. GET password reset done page
        done_resp = self.client.get('/accounts/password-reset/done/')
        self.assertEqual(done_resp.status_code, 200)
        self.assertContains(done_resp, "Check your email")

