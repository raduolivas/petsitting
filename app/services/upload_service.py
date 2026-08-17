"""Local image uploads (S3-ready interface)."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_sitter_photo(file: FileStorage, user_id: int) -> str | None:
    """Save uploaded photo; return relative URL path or None."""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError('Invalid file type. Use PNG, JPG, GIF or WebP.')

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f'sitter_{user_id}_{uuid.uuid4().hex[:12]}.{ext}')

    upload_root = Path(current_app.config.get(
        'UPLOAD_FOLDER',
        Path(current_app.root_path) / 'static' / 'uploads',
    ))
    dest_dir = upload_root / 'sitters'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    file.save(str(dest))

    # Relative path served by Flask static
    return f'/static/uploads/sitters/{filename}'
