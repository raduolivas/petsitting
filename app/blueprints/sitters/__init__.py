from flask import Blueprint

bp = Blueprint('sitters', __name__)

from app.blueprints.sitters import routes  # noqa: E402, F401
