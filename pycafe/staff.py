import functools
import datetime
import time
import smtplib
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from flask import current_app as app
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from email.mime.text import MIMEText
from .db import StaffUser

bp = Blueprint('staff', __name__, url_prefix='/staff')

# Staff login function
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = StaffUser.query_one(username=username)

        if user is None:
            # Login failure due to incorrect username
            error = 'Login failure!'
        elif user.is_locked():
            # User exists -> check if account is locked
            error = 'Account locked!'
        elif check_password_hash(user.password, password):
            # Password is correct -> login user, set Session, clear failed login info and redirect to proper page
            session.clear()
            session['username'] = user.username
            # Clear failed logins information in user record
            user.failed_login_attempts = 0
            user.locked_since = "0000-00-00 00:00:00"
            if user.save():
                # Redirect to proper application page
                if user.is_admin:
                    return redirect(url_for('admin.main_page'))
                else:
                    return redirect(url_for('cashdesk.main_page'))
            else:
                error = "Database save error!"
        else:
            # Username correct, but password not -> failed login attempt
            error = 'Login failure!'
            # Record failed login in user record
            user.failed_login_attempts +=1
            if user.failed_login_attempts > app.config['MAX_FAILED_LOGIN_ATTEMPTS']:
                user.locked_since = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
            if not user.save():
                error += "\nDatabase save error!"

        flash(error)

    return render_template('staff/login.html')

# Executed before processing each request, fetches 'user' from 'session'
@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        g.user = StaffUser.query_one(username=username)

# Staff logout function
@bp.route('/logout', methods=('GET', 'POST'))
def logout():
    session.clear()
    return redirect(url_for('staff.login'))

@bp.route('/change_password', methods=('GET', 'POST'))
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        current = request.form['current']
        new = request.form['new']
        confirm = request.form['confirm']
        error = None
        user = StaffUser.query_one(username=username)

        if user is None:
            # Login failure due to incorrect username
            error = "Username not recognized!"
            time.sleep(5) # Small delay to disrupt automatic username scanning
        elif check_password_hash(user.password, current):
            # Current password is correct -> verify new and change
            if new == confirm:
                if new != '':
                    # New password is acceptable -> update user in Database
                    user.password = generate_password_hash(new)
                    if user.save():
                        error = "Password change succesful!"
                    else:
                        error += "Password not changed - Database save error!"
                else:
                    error = "New password cannot be empty!"
            else:
                error = "New password and Confirm password don't match!"
        else:
            # Username correct, but current password not -> failed login attempt
            error = "Current password incorrect! Registering failed login attempt"
            # Record failed login in user record
            user.failed_login_attempts +=1
            if user.failed_login_attempts > app.config['MAX_FAILED_LOGIN_ATTEMPTS']:
                user.locked_since = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
            if not user.save():
                error += "\nDatabase save error!"
            time.sleep(5) # Small delay to disrupt automatic username scanning

        flash(error)
        return redirect(url_for('staff.login'))

    else: # method == 'GET'
        return render_template('staff/change_password.html')

@bp.route('/reset_password', methods=('GET', 'POST'))
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        if username == '':
            error = "Username required!"
        else:
            user = StaffUser.query_one(username=username)
            if user is None:
                error = "Username not recognized!"
                time.sleep(5) # Small delay to disrupt automatic username scanning
            else:
                # generate link and send it to user's e-mail address
                if user.is_admin:
                    # Admin users must contact System Admin to reset account at system console
                    error = "Please contact PyCafe System Admin to reset your account"
                else:
                    # connect to email server with connection parameters set in app config
                    try:
                        email_host = smtplib.SMTP(host=app.config['ADMIN_EMAIL_HOST_ADDRESS'], port=app.config['ADMIN_EMAIL_HOST_TLS_PORT'])
                    except Exception as e:
                        error = "Failed to connect to e-mail server! "+str(e)
                        flash(error)
                        return render_template('staff/reset_password.html')

                    try:
                        email_host.starttls()
                    except Exception as e:
                        error = "Failed to establish TLS connection with e-mail server! "+str(e)
                        flash(error)
                        return render_template('staff/reset_password.html')

                    try:
                        email_host.login(app.config['ADMIN_EMAIL_ACCOUNT'], app.config['ADMIN_EMAIL_PASSWORD'])
                    except Exception as e:
                        error = "Failed to login to e-mail server! "+str(e)
                        flash(error)
                        return render_template('staff/reset_password.html')

                    # prepare reset link
                    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
                    token = serializer.dumps({'userid': user.id})
                    reset_url = url_for("staff.reset_password2", _external=True)+"?token="+token

                    # create and send mail message
                    message_text = app.config['RESET_EMAIL_MESSAGE']+reset_url
                    message = MIMEText(message_text)
                    message['Subject'] = app.config['RESET_EMAIL_SUBJECT']
                    message['From'] = app.config['ADMIN_EMAIL_ACCOUNT']
                    message['To'] = user.email
                    try:
                        email_host.send_message(message)
                        error = "E-mail with reset link sent. Link expires in "+app.config['RESET_PASSWORD_LINK_EXPIRATION_FOR_HUMANS']
                    except Exception as e:
                        error = "Failed to send reset link e-mail message! "+str(e)


                flash(error)
                return redirect(url_for('staff.login'))

            flash(error)
            return render_template('staff/reset_password.html')

    else:
        return render_template('staff/reset_password.html')

@bp.route('/reset_password2', methods=('GET', 'POST'))
def reset_password2():
    if request.method == 'POST':
        token = request.form['token']
        new_password = request.form['new']
        confirm_password = request.form['confirm']

        if new_password != confirm_password:
            flash("Password mismatch. Try again")
            return render_template('staff/reset_password2.html', token=token)

        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        error = ''
        try:
            reset_request = serializer.loads(token, max_age=app.config['RESET_PASSWORD_LINK_EXPIRATION_SECONDS'])
        except SignatureExpired:
            error = "Reset link expired! Request a new link"
        except BadSignature:
            error = "Invalid token! Please contact your Manager"
        except Exception as e:
            error = "Error processing reset link! "+str(e)

        if error != '':
            flash(error)
            return redirect(url_for('staff.login'))

        # User ID is encoded in token passed from 'staff/reset_password2.html' from
        user = StaffUser.query_one(id=reset_request['userid'])
        if user is None:
            flash("Invalid user in reset link! Please contact your Manager")
            return redirect(url_for('staff.login'))
        else:
            user.password = generate_password_hash(new_password)
            if user.save():
                error = "Password reset succesfully"
            else:
                error = "Database save error!"

            flash(error)
            return redirect(url_for('staff.login'))

    else:
        token = request.args.get('token', '')
        if token == '':
            flash("Invalid password reset link! Missing token")
            return redirect(url_for('staff.login'))
        else:
            return render_template('staff/reset_password2.html', token=token)

# Login required decorator for other views
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('staff.login'))

        return view(**kwargs)

    return wrapped_view

# Admin login required decorator for other views
def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('staff.login'))
        staff_user = StaffUser(username=g.user.username)
        if staff_user.read().is_admin:
            return view(**kwargs)
        else:
            flash("Admin login required!")
            return redirect(url_for('staff.login'))

    return wrapped_view
