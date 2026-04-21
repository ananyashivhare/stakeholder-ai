import streamlit as st
import os
from dotenv import load_dotenv
from ai_engine import personalise_message, STAKEHOLDERS
from auth import register_user, login_user, check_usage_limit, increment_usage
from auth import get_pending_users, get_all_users, approve_user, deny_user

load_dotenv()
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

st.set_page_config(
    page_title='StakeholderAI - Personalise Project Updates Instantly',
    page_icon='🎯',
    layout='wide',
    initial_sidebar_state='expanded'
)

if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False


def show_login_page():
    st.title('🎯 StakeholderAI')
    st.subheader('Transform one project update into 5 personalised messages - instantly')
    st.divider()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader('Login')
        email = st.text_input('Email', key='login_email')
        password = st.text_input('Password', type='password', key='login_pass')
        if st.button('Login', type='primary', use_container_width=True):
            if not email or not password:
                st.error('Please enter your email and password.')
            else:
                success, result = login_user(email, password)
                if success:
                    st.session_state.user = result
                    st.session_state.page = 'app'
                    st.rerun()
                else:
                    st.error(result)

    with col2:
        st.info('New here? Request access using the form below.')
        if st.button('Request Access', use_container_width=True):
            st.session_state.page = 'register'
            st.rerun()

    st.divider()
    admin_code = st.text_input(
        'Admin',
        placeholder='Admin access only',
        key='admin_code',
        type='password',
        label_visibility='collapsed'
    )
    if admin_code and admin_code == ADMIN_PASSWORD:
        st.session_state.admin_logged_in = True
        st.session_state.page = 'admin'
        st.rerun()


def show_register_page():
    st.title('🎯 Request Access - StakeholderAI')
    st.info('Fill in your details below. You will receive an email once your access is approved (usually within 24 hours).')
    st.divider()

    with st.form('register_form'):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input('Full Name *')
            email = st.text_input('Work Email *')
            company = st.text_input('Company / Organisation *')
        with col2:
            job_title = st.text_input('Job Title *')
            password = st.text_input('Create Password *', type='password')
            confirm = st.text_input('Confirm Password *', type='password')
        submitted = st.form_submit_button(
            'Submit Access Request', type='primary', use_container_width=True)

    if submitted:
        if not all([full_name, email, company, job_title, password]):
            st.error('Please fill in all required fields.')
        elif password != confirm:
            st.error('Passwords do not match.')
        elif len(password) < 8:
            st.error('Password must be at least 8 characters.')
        elif '@' not in email:
            st.error('Please enter a valid email address.')
        else:
            with st.spinner('Submitting your request...'):
                success, msg = register_user(email, password, full_name, company, job_title)
            if success:
                st.success(msg)
                st.info('A notification has been sent to the admin. You will hear back within 24 hours.')
                st.balloons()
            else:
                st.error(msg)

    if st.button('Back to Login'):
        st.session_state.page = 'login'
        st.rerun()


def show_main_app():
    user = st.session_state.user
    FREE_LIMIT = 10

    with st.sidebar:
        st.title('🎯 StakeholderAI')
        st.write(f"Welcome, **{user['full_name']}**")
        st.write(f"{user['company']} - {user['job_title']}")
        st.divider()

        can_use, remaining = check_usage_limit(user['id'], user['tier'])

        if user['tier'] == 'free':
            progress_val = remaining / FREE_LIMIT
            st.progress(progress_val, text=f'{remaining}/{FREE_LIMIT} uses remaining today')
            if remaining <= 3:
                st.warning('Running low on uses!')
                st.button('Upgrade to Unlimited', type='primary', use_container_width=True)
        else:
            st.success('Unlimited Plan Active')

        st.divider()
        if st.button('Logout', use_container_width=True):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()

    st.title('Transform Your Project Update')
    st.caption('Write once. Communicate perfectly to everyone.')
    st.divider()

    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        project_name = st.text_input(
            'Project Name',
            placeholder='e.g. PaymentPro ERP Migration'
        )
        update_text = st.text_area(
            'Your Project Update',
            height=200,
            placeholder='Paste your raw project update here... e.g. Sprint 4 delayed by 3 days due to API dependency issue with payment gateway. Root cause identified, fix in progress. New go-live: Nov 18. Budget impact: approximately INR 80,000 in additional dev hours.'
        )

    with col2:
        st.write('**Select your audiences:**')
        selected = []
        for name, data in STAKEHOLDERS.items():
            if st.checkbox(f"{data['icon']} {name}", value=True):
                selected.append(name)

    st.divider()

    can_use, remaining = check_usage_limit(user['id'], user['tier'])
    generate_btn = st.button(
        'Generate Personalised Messages',
        type='primary',
        use_container_width=True,
        disabled=not can_use
    )

    if not can_use:
        st.error(f'Daily limit reached ({FREE_LIMIT} uses). Resets at midnight. Upgrade for unlimited access.')

    if generate_btn:
        if not update_text.strip():
            st.error('Please enter your project update first.')
        elif not selected:
            st.error('Please select at least one audience.')
        else:
            with st.spinner('AI is crafting your personalised messages...'):
                results = personalise_message(
                    update_text, project_name or 'Your Project', selected)
                increment_usage(user['id'])

            st.success(f'Generated {len(results)} personalised messages!')
            st.divider()

            for stakeholder, data in results.items():
                with st.expander(f"{data['icon']} {stakeholder}", expanded=True):
                    st.markdown(data['message'])
                    st.button('Copy', key=f'copy_{stakeholder}')


def show_admin_panel():
    st.title('Admin Panel - StakeholderAI')
    st.warning('This panel is only accessible to you.')

    tab1, tab2 = st.tabs(['Pending Approvals', 'All Users'])

    with tab1:
        pending = get_pending_users()
        st.subheader(f'Pending Approvals ({len(pending)})')

        if not pending:
            st.success('No pending requests. You are all caught up!')
        else:
            for user in pending:
                with st.expander(f"{user['full_name']} - {user['company']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Email:** {user['email']}")
                        st.write(f"**Job Title:** {user['job_title']}")
                    with col2:
                        st.write(f"**Company:** {user['company']}")
                        st.write(f"**Requested:** {user['created_at'][:10]}")

                    col3, col4 = st.columns(2)
                    with col3:
                        if st.button('Approve', key=f"approve_{user['id']}", type='primary', use_container_width=True):
                            approve_user(user['id'])
                            st.success(f"Approved {user['full_name']}!")
                            st.rerun()
                    with col4:
                        if st.button('Deny', key=f"deny_{user['id']}", use_container_width=True):
                            deny_user(user['id'])
                            st.info(f"Denied {user['full_name']}.")
                            st.rerun()

    with tab2:
        all_users = get_all_users()
        st.subheader(f'All Users ({len(all_users)})')

        if not all_users:
            st.info('No users yet.')
        else:
            for user in all_users:
                status_icon = '✅' if user['status'] == 'approved' else '⏳' if user['status'] == 'pending' else '❌'
                tier_icon = '⚡' if user['tier'] == 'paid' else '🆓'
                with st.expander(f"{status_icon} {user['full_name']} - {user['company']} {tier_icon}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Email:** {user['email']}")
                        st.write(f"**Status:** {user['status']}")
                        st.write(f"**Tier:** {user['tier']}")
                    with col2:
                        st.write(f"**Uses Today:** {user['uses_today']}")
                        st.write(f"**Joined:** {user['created_at'][:10]}")

    st.divider()
    if st.button('Logout Admin', use_container_width=True):
        st.session_state.admin_logged_in = False
        st.session_state.page = 'login'
        st.rerun()


def main():
    if st.session_state.page == 'admin' and st.session_state.admin_logged_in:
        show_admin_panel()
    elif st.session_state.page == 'register':
        show_register_page()
    elif st.session_state.user:
        show_main_app()
    else:
        show_login_page()


if __name__ == '__main__':
    main()