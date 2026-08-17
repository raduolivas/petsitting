import os
from datetime import timedelta


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-insecure-key-change-me'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_CURRENCY = os.environ.get('STRIPE_CURRENCY', 'eur')

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', '')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '1') == '1'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Pawbnb <noreply@pawbnb.local>')
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', '0') == '1'

    # Uploads
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '')

    # Rate limiting storage (memory | redis://...)
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    TALISMAN_ENABLED = True
    FORCE_HTTPS = False
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'instance', 'pawbnb.db'
        ),
    )
    TALISMAN_ENABLED = False
    FORCE_HTTPS = False
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', '1') == '1'


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', '1') == '1'
    TALISMAN_ENABLED = True

    @classmethod
    def init_app(cls, app):
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            if os.environ.get('ALLOW_SQLITE_IN_PROD') == '1':
                app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/lib/pawbnb/pawbnb.db'
            else:
                raise RuntimeError(
                    'DATABASE_URL must be set in production (e.g. postgresql://...)'
                )
        if not os.environ.get('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY must be set in production')


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    TALISMAN_ENABLED = False
    SECRET_KEY = 'test-secret'
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_STORAGE_URI = 'memory://'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
