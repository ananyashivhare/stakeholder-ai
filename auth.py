from supabase import create_client
import os, hashlib
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def hash_password(password):
    '''Simple password hashing — never store plain text passwords'''
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password, full_name, company, job_title):
    '''Register a new user — status is 'pending' until you approve'''
    try:
        # Check if email already exists
        existing = supabase.table('users').select('email').eq('email', email).execute()
        if existing.data:
            return False, 'Email already registered. Check your inbox or contact support.'

        # Insert new pending user
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
        return True, 'Registration successful! You will receive an email once approved.'
    except Exception as e:
        return False, f'Registration failed: {str(e)}'

def login_user(email, password):
    '''Returns (success, user_data_or_error_message)'''
    try:
        result = supabase.table('users').select('*').eq('email', email).eq('password_hash', hash_password(password)).execute()
        if not result.data:
            return False, 'Invalid email or password.'

        user = result.data[0]
        if user['status'] == 'pending':
            return False, 'Your account is pending approval. You will be notified by email.'
        if user['status'] == 'denied':
            return False, 'Your access request was not approved. Contact Anny.shivhare@gmail.com'
        return True, user
    except Exception as e:
        return False, f'Login error: {str(e)}'

def check_usage_limit(user_id, tier):
    '''Free tier: 10 uses/day. Paid: unlimited.'''
    from datetime import date
    if tier == 'paid': return True, 999  # unlimited

    FREE_LIMIT = 10
    today = str(date.today())
    user = supabase.table('users').select('uses_today, last_use_date').eq('id', user_id).execute().data[0]

    # Reset counter if it's a new day
    if user['last_use_date'] != today:
        supabase.table('users').update({'uses_today': 0, 'last_use_date': today}).eq('id', user_id).execute()
        return True, FREE_LIMIT

    remaining = FREE_LIMIT - user['uses_today']
    return remaining > 0, remaining

def increment_usage(user_id):
    '''Called after each successful AI generation'''
    from datetime import date
    user = supabase.table('users').select('uses_today').eq('id', user_id).execute().data[0]
    supabase.table('users').update({
        'uses_today': user['uses_today'] + 1,
        'last_use_date': str(date.today())
    }).eq('id', user_id).execute()

def get_pending_users():
    '''For your admin panel — returns all users awaiting your approval'''
    return supabase.table('users').select('*').eq('status', 'pending').execute().data

def approve_user(user_id):
    supabase.table('users').update({'status': 'approved'}).eq('id', user_id).execute()

def deny_user(user_id):
    supabase.table('users').update({'status': 'denied'}).eq('id', user_id).execute()