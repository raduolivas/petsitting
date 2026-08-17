"""Email notifications with SMTP in production and console fallback in development."""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, url_for

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    if not to:
        return False

    cfg = current_app.config
    mail_server = cfg.get('MAIL_SERVER')
    mail_from = cfg.get('MAIL_DEFAULT_SENDER') or cfg.get('MAIL_USERNAME') or 'noreply@pawbnb.local'

    if not mail_server or cfg.get('MAIL_SUPPRESS_SEND'):
        logger.info('EMAIL (console) To=%s Subject=%s', to, subject)
        print(f'\n--- EMAIL ---\nTo: {to}\nSubject: {subject}\n{text_body or html_body}\n-------------\n')
        return True

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = mail_from
    msg['To'] = to
    if text_body:
        msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    try:
        port = int(cfg.get('MAIL_PORT', 587))
        use_tls = cfg.get('MAIL_USE_TLS', True)
        with smtplib.SMTP(mail_server, port, timeout=20) as server:
            if use_tls:
                server.starttls()
            username = cfg.get('MAIL_USERNAME')
            password = cfg.get('MAIL_PASSWORD')
            if username and password:
                server.login(username, password)
            server.sendmail(mail_from, [to], msg.as_string())
        logger.info('Email sent to %s: %s', to, subject)
        return True
    except Exception as exc:
        logger.exception('Failed to send email to %s: %s', to, exc)
        return False


def notify_booking_requested(booking) -> None:
    sitter_user = booking.sitter.user
    owner = booking.owner
    detail_url = url_for('bookings.detail', booking_id=booking.id, _external=True)
    subject = f'New booking request from {owner.name}'
    text = (
        f'Hi {sitter_user.name},\n\n'
        f'{owner.name} requested {booking.service_type} for {booking.dog_name or "their dog"} '
        f'from {booking.start_date} to {booking.end_date or booking.start_date}.\n'
        f'Total: EUR {booking.total_price:.2f} (authorized, not yet captured).\n\n'
        f'Accept or decline: {detail_url}\n'
    )
    html = (
        f'<p>Hi {sitter_user.name},</p>'
        f'<p><strong>{owner.name}</strong> requested <strong>{booking.service_type}</strong> '
        f'for <strong>{booking.dog_name or "their dog"}</strong> '
        f'({booking.start_date} – {booking.end_date or booking.start_date}).</p>'
        f'<p>Total held: <strong>EUR {booking.total_price:.2f}</strong></p>'
        f'<p><a href="{detail_url}">Review request</a></p>'
    )
    _send(sitter_user.email, subject, html, text)


def notify_booking_accepted(booking) -> None:
    owner = booking.owner
    detail_url = url_for('bookings.detail', booking_id=booking.id, _external=True)
    subject = 'Your booking was accepted!'
    text = (
        f'Hi {owner.name},\n\n'
        f'{booking.sitter.user.name} accepted your {booking.service_type} booking '
        f'for {booking.dog_name or "your dog"}. Payment has been captured.\n\n'
        f'Details: {detail_url}\n'
    )
    html = (
        f'<p>Hi {owner.name},</p>'
        f'<p><strong>{booking.sitter.user.name}</strong> accepted your booking. '
        f'Payment of <strong>EUR {booking.total_price:.2f}</strong> has been captured.</p>'
        f'<p><a href="{detail_url}">View booking</a></p>'
    )
    _send(owner.email, subject, html, text)


def notify_booking_declined(booking) -> None:
    owner = booking.owner
    detail_url = url_for('bookings.detail', booking_id=booking.id, _external=True)
    subject = 'Booking request declined'
    text = (
        f'Hi {owner.name},\n\n'
        f'{booking.sitter.user.name} declined your {booking.service_type} request. '
        f'Any payment hold has been released / refunded.\n\n{detail_url}\n'
    )
    html = (
        f'<p>Hi {owner.name},</p>'
        f'<p><strong>{booking.sitter.user.name}</strong> declined your request. '
        f'The payment authorization has been released.</p>'
        f'<p><a href="{detail_url}">View details</a></p>'
    )
    _send(owner.email, subject, html, text)
