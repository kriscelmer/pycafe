# Global 'PyCafe' Application Settings

# This file lists all currently used settings and their default values.
# Additional settings can be added in this file or other '*.py' files in this directory
# Settings can be overriden by editing this file or other '*.py' files in this directory
# '*.py' files in this folder are processed in alphanumeric order produced by 'sorted()' in 'factory.py' module found in parent directory
# Put secrets in '99-secrets.py' file, which is listed in '.gitignore' file in this directory.

# Current version of PyCafe System
PYCAFE_VERSION = '1.5.1'

# Application Secret Key - used to generate session keys and password reset tokens for example
# Must be kept secret and secure!!!
# Generate new one with following command line:
# python -c 'import secrets; print(secrets.token_bytes(32))'
#
# 24 bytes -> 192 bits long secret key is sufficient for default Flask Session key
# we use 32 bytes -> 256 bits to increase entropy for session key
# and make password reset keys more secure

SECRET_KEY = 'place your secret key here'

# Staff User account settings
MAX_FAILED_LOGIN_ATTEMPTS = 3
ACCOUNT_LOCK_PERIOD_SECONDS = 300 # Staff User account is locked for 5 minutes

# Admin e-mail account for sending password reset e-mails
# Enter your e-mail account details here or in separate settings file, for example '99-secrets.py'.
# PyCafe is going to fail, when attempt is made to send password reset message with Admin e-mail account details as below.

ADMIN_EMAIL_HOST_ADDRESS='enter your e-mail server, for example smtp.gmail.com'
ADMIN_EMAIL_HOST_TLS_PORT=587
ADMIN_EMAIL_ACCOUNT='your e-mail account username/address' # Please make sure to enable access by 'Less sucure applications' for Gmail Account!
ADMIN_EMAIL_PASSWORD='your email account password'

# Reset Password e-mail message

RESET_EMAIL_MESSAGE = """\
Hello,

This is an automatic message from PyCafe System.
You have requested to reset your PyCafe account password.
If this is a mistake, please contact your Manager immediately.
Please use the link below to access password reset page:

"""
RESET_EMAIL_SUBJECT = "PyCafe System Account Reset"

# Password reset link expiration period in seconds

RESET_PASSWORD_LINK_EXPIRATION_SECONDS = 3600
RESET_PASSWORD_LINK_EXPIRATION_FOR_HUMANS = "1 hour"

# Permanent Session Lifetime period in seconds

PERMANENT_SESSION_LIFETIME = 86400 # 24 hours
