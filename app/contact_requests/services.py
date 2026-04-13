"""Servicios del módulo de solicitudes de contacto/cita."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import abort
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.contact_request import ContactRequest
from app.models.customer import Customer
from app.models.customer_user import CustomerUser
from app.models.furniture_type import FurnitureType
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_inventory import ProductInventory
from app.shared.audit_logging import log_application_audit


class ContactRequestService:
    """Lógica de negocio para solicitudes comerciales."""

    @staticmethod
    def _split_full_name(full_name: str) -> tuple[str, str]:
        parts = [segment for segment in (full_name or "").split() if segment]
        if not parts:
            return "Cliente", "Personalizado"
        if len(parts) == 1:
            return parts[0], "Cliente"
        return parts[0], " ".join(parts[1:])

    @staticmethod
    def _normalize_request_type(raw_value: str | None) -> str:
        value = (raw_value or "").strip().lower()
        if value not in ContactRequest.VALID_TYPES:
            return "custom_furniture"
        return value

    @staticmethod
    def _normalize_status(raw_value: str | None) -> str:
        value = (raw_value or "").strip().lower()
        if value not in ContactRequest.VALID_STATUSES:
            raise ValueError("El estado de la solicitud no es válido.")
        return value

    @staticmethod
    def _parse_preferred_datetime(raw_value: str | None) -> datetime | None:
        value = (raw_value or "").strip()
        if not value:
            return None

        # datetime-local suele llegar como YYYY-MM-DDTHH:MM
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("La fecha de cita no tiene un formato válido.") from exc

    @staticmethod
    def _normalize_positive_int(raw_value: object, *, field_name: str) -> int:
        try:
            value = int(str(raw_value or "").strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} debe ser un número entero válido.") from exc

        if value < 1:
            raise ValueError(f"{field_name} debe ser mayor a 0.")
        return value

    @staticmethod
    def _normalize_positive_decimal(raw_value: object, *, field_name: str) -> Decimal:
        text_value = str(raw_value or "").strip()
        try:
            value = Decimal(text_value)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{field_name} debe ser un número válido.") from exc

        if value <= 0:
            raise ValueError(f"{field_name} debe ser mayor a 0.")

        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _normalize_delivery_date(raw_value: object) -> date:
        text_value = str(raw_value or "").strip()
        if not text_value:
            raise ValueError("La fecha estimada de entrega es obligatoria.")

        try:
            return date.fromisoformat(text_value)
        except ValueError as exc:
            raise ValueError(
                "La fecha estimada de entrega no tiene un formato válido."
            ) from exc

    @staticmethod
    def get_conversion_defaults(contact_request: ContactRequest) -> dict[str, str]:
        subject = (contact_request.subject or "").strip()
        if subject.lower().startswith("solicitud sobre:"):
            subject = subject.split(":", maxsplit=1)[1].strip()

        default_product_name = subject or f"Mueble personalizado #{contact_request.id}"

        linked_customer = contact_request.customer
        default_phone = (contact_request.phone or "").strip()
        if not default_phone and linked_customer:
            default_phone = (linked_customer.phone or "").strip()

        return {
            "product_name": default_product_name,
            "quantity": "1",
            "unit_price": "",
            "estimated_delivery_date": (date.today() + timedelta(days=21)).isoformat(),
            "phone": default_phone,
            "notes": "",
        }

    @staticmethod
    def _resolve_or_create_customer(
        contact_request: ContactRequest,
        *,
        preferred_phone: str | None,
        user_id: int | None,
    ) -> tuple[Customer, CustomerUser | None]:
        customer_user = contact_request.customer_user
        customer = contact_request.customer

        if customer is None and customer_user and customer_user.customer:
            customer = customer_user.customer

        normalized_email = (contact_request.email or "").strip().lower()

        if customer is None:
            customer = Customer.query.filter(
                Customer.email.ilike(normalized_email),
                Customer.status.is_(True),
            ).first()

        if customer_user is None and customer and customer.user_id:
            customer_user = CustomerUser.query.filter_by(
                id=customer.user_id,
                status=True,
            ).first()

        if customer is None:
            resolved_phone = (preferred_phone or contact_request.phone or "").strip()
            if not resolved_phone:
                raise ValueError(
                    "Debes capturar un teléfono para crear el cliente y convertir la solicitud."
                )

            first_name, last_name = ContactRequestService._split_full_name(
                contact_request.full_name
            )

            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=normalized_email,
                phone=resolved_phone,
                requires_freight=False,
                status=True,
                user_id=(customer_user.id if customer_user else None),
                created_by=user_id,
                updated_by=user_id,
            )
            db.session.add(customer)
            db.session.flush()

        if customer_user and customer.user_id != customer_user.id:
            customer.user_id = customer_user.id

        contact_request.customer_id = customer.id
        if customer_user:
            contact_request.customer_user_id = customer_user.id

        return customer, customer_user

    @staticmethod
    def _get_or_create_special_furniture_type(user_id: int | None) -> FurnitureType:
        furniture_type = (
            FurnitureType.query.filter(
                or_(
                    FurnitureType.slug == "muebles-personalizados",
                    FurnitureType.title.ilike("muebles personalizados"),
                )
            )
            .order_by(FurnitureType.id.asc())
            .first()
        )

        if furniture_type is None:
            furniture_type = (
                FurnitureType.query.filter(
                    FurnitureType.requires_contact_request.is_(True)
                )
                .order_by(FurnitureType.id.asc())
                .first()
            )

        if furniture_type:
            if not furniture_type.requires_contact_request:
                furniture_type.requires_contact_request = True
            if not furniture_type.status:
                furniture_type.status = True
            furniture_type.updated_by = user_id
            return furniture_type

        created = FurnitureType(
            title="Muebles personalizados",
            subtitle="Pedidos bajo especificaciones del cliente",
            image_url=None,
            slug="muebles-personalizados",
            requires_contact_request=True,
            status=True,
            created_by=user_id,
            updated_by=user_id,
        )
        db.session.add(created)
        db.session.flush()
        return created

    @staticmethod
    def _generate_special_sku(contact_request: ContactRequest) -> str:
        base_sku = f"CUST-REQ-{contact_request.id:05d}"
        sku = base_sku
        suffix = 1

        while Product.query.filter_by(sku=sku).first():
            suffix += 1
            sku = f"{base_sku}-{suffix}"

        return sku[:50]

    @staticmethod
    def create_from_public_form(
        form_data: dict,
        *,
        customer_user_id: int | None = None,
    ) -> ContactRequest:
        full_name = (form_data.get("full_name") or "").strip()
        email = (form_data.get("email") or "").strip().lower()
        phone = (form_data.get("phone") or "").strip() or None
        subject = (form_data.get("subject") or "").strip() or None
        message = (form_data.get("message") or "").strip()
        request_type = ContactRequestService._normalize_request_type(
            form_data.get("request_type")
        )
        preferred_datetime = ContactRequestService._parse_preferred_datetime(
            form_data.get("preferred_datetime")
        )

        if len(full_name) < 3:
            raise ValueError("Ingresa un nombre válido.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Ingresa un correo electrónico válido.")
        if len(message) < 10:
            raise ValueError("Describe tu solicitud con al menos 10 caracteres.")

        customer_user = None
        customer = None
        if customer_user_id:
            customer_user = CustomerUser.query.filter_by(
                id=customer_user_id,
                status=True,
            ).first()
            if customer_user:
                customer = customer_user.customer

        if customer is None:
            customer = Customer.query.filter(
                Customer.email.ilike(email),
                Customer.status.is_(True),
            ).first()

        contact_request = ContactRequest(
            full_name=full_name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            request_type=request_type,
            status="new",
            source="ecommerce",
            preferred_datetime=preferred_datetime,
            customer_id=(customer.id if customer else None),
            customer_user_id=(customer_user.id if customer_user else None),
        )

        db.session.add(contact_request)
        db.session.commit()
        return contact_request

    @staticmethod
    def get_requests(
        *,
        search_term: str = "",
        status: str = "all",
        request_type: str = "all",
        page: int = 1,
        per_page: int = 15,
    ):
        query = ContactRequest.query.options(
            joinedload(ContactRequest.assigned_to),
            joinedload(ContactRequest.customer),
        )

        normalized_status = (status or "all").strip().lower()
        if normalized_status != "all":
            query = query.filter(ContactRequest.status == normalized_status)

        normalized_type = (request_type or "all").strip().lower()
        if normalized_type != "all":
            query = query.filter(ContactRequest.request_type == normalized_type)

        if search_term.strip():
            term = f"%{search_term.strip()}%"
            query = query.filter(
                or_(
                    ContactRequest.full_name.ilike(term),
                    ContactRequest.email.ilike(term),
                    ContactRequest.subject.ilike(term),
                    ContactRequest.message.ilike(term),
                )
            )

        return query.order_by(ContactRequest.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

    @staticmethod
    def get_summary_metrics() -> dict[str, int]:
        open_statuses = ("new", "assigned", "in_progress")
        return {
            "total": ContactRequest.query.count(),
            "abiertas": ContactRequest.query.filter(
                ContactRequest.status.in_(open_statuses)
            ).count(),
            "sin_asignar": ContactRequest.query.filter(
                ContactRequest.status.in_(open_statuses),
                ContactRequest.assigned_to_id.is_(None),
            ).count(),
            "convertidas": ContactRequest.query.filter(
                ContactRequest.converted_order_id.isnot(None)
            ).count(),
        }

    @staticmethod
    def get_request_or_404(request_id: int) -> ContactRequest:
        contact_request = db.session.get(
            ContactRequest,
            request_id,
            options=[
                joinedload(ContactRequest.assigned_to),
                joinedload(ContactRequest.customer),
                joinedload(ContactRequest.customer_user),
            ],
        )
        if contact_request is None:
            abort(404)
        return contact_request

    @staticmethod
    def assign_to_user(request_id: int, user_id: int) -> ContactRequest:
        contact_request = ContactRequestService.get_request_or_404(request_id)
        contact_request.assigned_to_id = user_id
        if contact_request.status == "new":
            contact_request.status = "assigned"

        db.session.commit()
        return contact_request

    @staticmethod
    def update_status(
        request_id: int,
        *,
        status: str,
        internal_notes: str = "",
    ) -> ContactRequest:
        contact_request = ContactRequestService.get_request_or_404(request_id)
        normalized_status = ContactRequestService._normalize_status(status)

        contact_request.status = normalized_status
        normalized_notes = (internal_notes or "").strip()
        if normalized_notes:
            contact_request.internal_notes = normalized_notes

        db.session.commit()
        return contact_request

    @staticmethod
    def convert_to_special_order(
        request_id: int,
        *,
        form_data: dict,
        user_id: int | None = None,
    ) -> Order:
        contact_request = ContactRequestService.get_request_or_404(request_id)

        if contact_request.converted_order_id:
            raise ValueError("La solicitud ya fue convertida previamente en una orden.")

        product_name = (form_data.get("product_name") or "").strip()
        if len(product_name) < 3:
            raise ValueError("El nombre del producto especial es obligatorio.")

        quantity = ContactRequestService._normalize_positive_int(
            form_data.get("quantity"),
            field_name="La cantidad",
        )
        unit_price = ContactRequestService._normalize_positive_decimal(
            form_data.get("unit_price"),
            field_name="El precio unitario",
        )
        estimated_delivery_date = ContactRequestService._normalize_delivery_date(
            form_data.get("estimated_delivery_date")
        )

        preferred_phone = (form_data.get("phone") or "").strip() or None
        conversion_notes = (form_data.get("notes") or "").strip()

        try:
            customer, customer_user = ContactRequestService._resolve_or_create_customer(
                contact_request,
                preferred_phone=preferred_phone,
                user_id=user_id,
            )
            furniture_type = (
                ContactRequestService._get_or_create_special_furniture_type(
                    user_id=user_id
                )
            )

            sku = ContactRequestService._generate_special_sku(contact_request)

            description_parts = []
            if contact_request.subject:
                description_parts.append(contact_request.subject.strip())
            if contact_request.message:
                description_parts.append(contact_request.message.strip())

            product = Product(
                sku=sku,
                name=product_name,
                furniture_type_id=furniture_type.id,
                description=(
                    "\n\n".join(part for part in description_parts if part).strip()
                    or "Producto especial generado desde solicitud personalizada."
                ),
                specifications=(conversion_notes or None),
                price=unit_price,
                is_special_request=True,
                status=True,
                created_by=user_id,
                updated_by=user_id,
            )
            db.session.add(product)
            db.session.flush()

            db.session.add(
                ProductInventory(
                    product_id=product.id,
                    stock=0,
                    created_by=user_id,
                    updated_by=user_id,
                )
            )

            total = unit_price * quantity
            order_notes = [
                f"Generada desde solicitud personalizada #{contact_request.id}.",
            ]
            if contact_request.subject:
                order_notes.append(
                    f"Asunto original: {contact_request.subject.strip()}"
                )
            if conversion_notes:
                order_notes.append(f"Notas de conversión: {conversion_notes}")

            order = Order(
                customer_id=customer.id,
                order_date=datetime.now(),
                estimated_delivery_date=estimated_delivery_date,
                status="pendiente",
                total=total,
                payment_method_id=None,
                notes="\n".join(order_notes),
                source="manual",
                is_special_request=True,
                customer_user_id=(customer_user.id if customer_user else None),
                created_by_id=user_id,
            )
            db.session.add(order)
            db.session.flush()

            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=unit_price,
                )
            )

            contact_request.converted_order_id = order.id
            contact_request.status = "completed"

            conversion_trace = (
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
                f"Convertida a orden especial #{order.id}."
            )
            if contact_request.internal_notes:
                contact_request.internal_notes = (
                    f"{contact_request.internal_notes.rstrip()}\n{conversion_trace}"
                )
            else:
                contact_request.internal_notes = conversion_trace

            log_application_audit(
                table_name="orders",
                action="INSERT",
                user_id=user_id,
                previous_data=None,
                new_data=order.to_dict(),
            )

            db.session.commit()
            return order
        except Exception:
            db.session.rollback()
            raise
