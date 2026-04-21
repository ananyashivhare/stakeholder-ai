from supabase import create_client
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import date

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def send_email_notification(user_name, user_email, user_company, user_job_title):
    try:
        sender = "Anny.shivhare@gmail.com"
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "New Access Request - StakeholderAI"
        msg['From'] = sender
        msg['To'] = sender

        body = f"""
Hello Ananya,

You have a new access request on StakeholderAI!

Name: {user_name}
Email: {user_email}
Company: {user_company}
Job Title: {user_job_title}

To approve or deny, log into your admin panel.
On the login page, enter your admin code in the box at the bottom.

Best,
StakeholderAI System
        """

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, gmail_password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Email notification failed: {str(e)}")
        return False


def register_user(email, password, full_name, company, job_title):
    try:
        existing = supabase.table('users').select('email').eq('email', email).execute()
        if existing.data:
            return False, 'Email already registered. Please login or contact support.'

        supabase.table('users').insert({
            'email': email,
            'full_name': full_name,
            'company': company,
            'job_title': job_title,
            'password_hash': hash_password(password),
            'status': 'pending',
            'tier': 'free',
            'uses_today': 0
        }).execute()

        send_email_notification(full_name, email, company, job_title)

        return True, 'Registration successful! You will receive an email once your access is approved within 24 hours.'
    except Exception as e:
        return False, f'Registration failed: {str(e)}'


def login_user(email, password):
    try:
        result = supabase.table('users').select('*').eq('email', email).eq(
            'password_hash', hash_password(password)).execute()

        if not result.data:
            return False, 'Invalid email or password.'

        user = result.data[0]

        if user['status'] == 'pending':
            return False, 'Your account is pending approval. You will be notified once approved.'
        if user['status'] == 'denied':
            return False, 'Your access request was not approved. Contact Anny.shivhare@gmail.com for help.'

        return True, user
    except Exception as e:
        return False, f'Login error: {str(e)}'


def check_usage_limit(user_id, tier):
    if tier == 'paid':
        return True, 999

    FREE_LIMIT = 10
    today = str(date.today())

    try:
        user = supabase.table('users').select(
            'uses_today, last_use_date').eq('id', user_id).execute().data[0]

        if user['last_use_date'] != today:
            supabase.table('users').update(
                {'uses_today': 0, 'last_use_date': today}).eq('id', user_id).execute()
            return True, FREE_LIMIT

        remaining = FREE_LIMIT - user['uses_today']
        return remaining > 0, remaining
    except Exception as e:
        return True, 10


def increment_usage(user_id):
    try:
        today = str(date.today())
        user = supabase.table('users').select(
            'uses_today').eq('id', user_id).execute().data[0]
        supabase.table('users').update({
            'uses_today': user['uses_today'] + 1,
            'last_use_date': today
        }).eq('id', user_id).execute()
    except Exception as e:
        print(f"Usage increment failed: {str(e)}")


def get_pending_users():
    try:
        return supabase.table('users').select('*').eq('status', 'pending').execute().data
    except Exception as e:
        return []


def get_all_users():
    try:
        return supabase.table('users').select('*').execute().data
    except Exception as e:
        return []


def approve_user(user_id):
    try:
        supabase.table('users').update(
            {'status': 'approved'}).eq('id', user_id).execute()
        return True
    except Exception as e:
        return False


def deny_user(user_id):
    try:
        supabase.table('users').update(
            {'status': 'denied'}).eq('id', user_id).execute()
        return True
    except Exception as e:
        return False


def upgrade_user_to_paid(user_id):
    try:
        supabase.table('users').update(
            {'tier': 'paid'}).eq('id', user_id).execute()
        return True
    except Exception as e:
        return False