"""Utilidades de correo para mantener branding en emails de seguridad."""

from __future__ import annotations

import logging
import os
import typing as t

from flask import current_app
from flask_security.mail_util import MailUtil

LOGO_FILENAME = "logo-roble-disenio.png"
LOGO_CID = "company_logo"
TEMPLATES_WITH_INLINE_LOGO = {"reset_instructions", "reset_notice"}
logger = logging.getLogger(__name__)


def _get_logo_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "static", "src", "images", LOGO_FILENAME)


class BrandedMailUtil(MailUtil):
    """Adjunta logo inline a correos de seguridad seleccionados."""

    def send_mail(
        self,
        template: str,
        subject: str,
        recipient: str,
        sender: str | tuple,
        body: str,
        html: str | None,
        **kwargs: t.Any,
    ) -> None:
        try:
            if not current_app.extensions.get("mail", None):
                super().send_mail(
                    template=template,
                    subject=subject,
                    recipient=recipient,
                    sender=sender,
                    body=body,
                    html=html,
                    **kwargs,
                )
                return

            from flask_mail import Message

            if isinstance(sender, tuple) and len(sender) == 2:
                sender = (str(sender[0]), str(sender[1]))
            else:
                sender = str(sender)

            msg = Message(subject, sender=sender, recipients=[recipient])
            msg.body = body
            msg.html = html

            if template in TEMPLATES_WITH_INLINE_LOGO:
                logo_path = _get_logo_path()
                if os.path.isfile(logo_path):
                    with open(logo_path, "rb") as fp:
                        msg.attach(
                            filename=LOGO_FILENAME,
                            content_type="image/png",
                            data=fp.read(),
                            disposition="inline",
                            headers={"Content-ID": f"<{LOGO_CID}>"},
                        )

            mail = current_app.extensions.get("mail")
            mail.send(msg)  # type: ignore[attr-defined]
        except Exception as exc:
            # El envío de correo no debe romper el flujo principal de auth/seguridad.
            logger.error(
                "No se pudo enviar correo de seguridad '%s' a '%s': %s",
                template,
                recipient,
                exc,
                exc_info=True,
            )
