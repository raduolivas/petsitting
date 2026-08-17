"""WSGI entrypoint for production servers (Gunicorn, uWSGI, etc.)."""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

# Prefer FLASK_ENV; default production only when not set and running under gunicorn
env = os.environ.get('FLASK_ENV') or os.environ.get('APP_ENV') or 'production'
app = create_app(env)
