import os
import logging
from flask import Flask
from app.config import config_by_name
from app.extensions import db, login_manager, migrate, csrf


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        if config_name not in config_by_name:
            config_name = 'development'

    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        instance_relative_config=True,
    )

    app.config.from_object(config_by_name[config_name])

    cfg = config_by_name[config_name]
    if hasattr(cfg, 'init_app'):
        cfg.init_app(app)

    # Ensure instance folder exists (sqlite path)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Fix sqlite relative path when using DevelopmentConfig default
    uri = app.config.get('SQLALCHEMY_DATABASE_URI') or ''
    if uri.startswith('sqlite:///') and not uri.startswith('sqlite:////'):
        # Make absolute under instance
        db_name = uri.replace('sqlite:///', '')
        if not os.path.isabs(db_name):
            abs_path = os.path.join(app.instance_path, os.path.basename(db_name) or 'pawbnb.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + abs_path

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Security headers
    if app.config.get('TALISMAN_ENABLED'):
        try:
            from flask_talisman import Talisman
            Talisman(
                app,
                force_https=app.config.get('FORCE_HTTPS', False),
                content_security_policy=None,  # allow CDNs for Tailwind/Leaflet in MVP
            )
        except ImportError:
            app.logger.warning('flask-talisman not installed; security headers skipped')

    # Stripe key
    if app.config.get('STRIPE_SECRET_KEY'):
        try:
            import stripe
            stripe.api_key = app.config['STRIPE_SECRET_KEY']
        except ImportError:
            pass

    # Logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)

    # Blueprints
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.main import bp as main_bp
    from app.blueprints.sitters import bp as sitters_bp
    from app.blueprints.bookings import bp as bookings_bp
    from app.blueprints.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(sitters_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(api_bp)

    # Import models so Alembic sees them
    from app import models  # noqa: F401

    # CLI seed command
    @app.cli.command('seed')
    def seed_command():
        """Seed demo users and sitters."""
        from app.seed import seed_data
        seed_data()
        print('Seed complete.')

    return app
