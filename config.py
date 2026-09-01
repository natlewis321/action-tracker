import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _get_secret_key():
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    key_file = os.path.join(BASE_DIR, '.secret_key')
    if os.path.exists(key_file):
        with open(key_file) as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(key_file, 'w') as f:
        f.write(key)
    return key

SECRET_KEY = _get_secret_key()
DATABASE = os.path.join(BASE_DIR, 'action_tracker.db')
SESSION_LIFETIME_HOURS = 8
DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
