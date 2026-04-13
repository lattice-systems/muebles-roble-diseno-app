"""Reglas de negocio para coherencia visual/material y pricing del seed.

Este modulo centraliza:
- Validaciones de fidelidad visual (imagenes por SKU)
- Coherencia entre perfil visual y lista de materiales BOM
- Ajuste ligero de consumos BOM segun senales visuales del set de imagenes
- Calculo de precio de venta con costo productivo real + salarios + indirectos + margen
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

IMAGE_DATA_FILE = Path(__file__).with_name("seed_product_images.json")
MIN_IMAGES_PER_PRODUCT = 4

LABOR_HOURLY_RATE = Decimal("95.00")
LABOR_BURDEN_FACTOR = Decimal("1.42")
OPERATING_OVERHEAD_PCT = Decimal("0.10")
QA_PACKAGING_PCT = Decimal("0.04")

MONEY_DECIMALS = Decimal("0.01")
QTY_DECIMALS = Decimal("0.001")


CATEGORY_PROFILE_RULES: dict[str, dict] = {
    "Salas": {
        "code": "tapizado",
        "base_labor_hours": Decimal("8.50"),
        "hours_per_m3": Decimal("8.70"),
        "hours_per_bom_item": Decimal("0.85"),
        "material_buffer_pct": Decimal("0.08"),
        "factory_overhead_pct": Decimal("0.17"),
        "target_margin_pct": Decimal("0.39"),
        "required_material_groups": [
            ("Tela", "Espuma"),
            ("Resorte", "Correa"),
        ],
    },
    "Comedores": {
        "code": "carpinteria_premium",
        "base_labor_hours": Decimal("8.00"),
        "hours_per_m3": Decimal("8.30"),
        "hours_per_bom_item": Decimal("0.78"),
        "material_buffer_pct": Decimal("0.07"),
        "factory_overhead_pct": Decimal("0.16"),
        "target_margin_pct": Decimal("0.37"),
        "required_material_groups": [
            ("Madera", "Cubierta", "Triplay", "Tablero"),
        ],
    },
    "Recamaras": {
        "code": "mixto_recamara",
        "base_labor_hours": Decimal("7.80"),
        "hours_per_m3": Decimal("8.10"),
        "hours_per_bom_item": Decimal("0.76"),
        "material_buffer_pct": Decimal("0.07"),
        "factory_overhead_pct": Decimal("0.16"),
        "target_margin_pct": Decimal("0.37"),
        "required_material_groups": [
            ("Madera", "Triplay", "Tablero", "Tela"),
        ],
    },
    "Closets y almacenamiento": {
        "code": "gabineteria",
        "base_labor_hours": Decimal("7.60"),
        "hours_per_m3": Decimal("7.50"),
        "hours_per_bom_item": Decimal("0.74"),
        "material_buffer_pct": Decimal("0.06"),
        "factory_overhead_pct": Decimal("0.15"),
        "target_margin_pct": Decimal("0.36"),
        "required_material_groups": [
            ("Tablero", "Triplay", "Madera"),
        ],
    },
    "Escritorios y oficina": {
        "code": "funcional_oficina",
        "base_labor_hours": Decimal("7.40"),
        "hours_per_m3": Decimal("7.20"),
        "hours_per_bom_item": Decimal("0.72"),
        "material_buffer_pct": Decimal("0.06"),
        "factory_overhead_pct": Decimal("0.15"),
        "target_margin_pct": Decimal("0.35"),
        "required_material_groups": [
            ("Tablero", "Madera", "Triplay"),
        ],
    },
    "Muebles para TV": {
        "code": "gabineteria",
        "base_labor_hours": Decimal("7.20"),
        "hours_per_m3": Decimal("7.00"),
        "hours_per_bom_item": Decimal("0.70"),
        "material_buffer_pct": Decimal("0.06"),
        "factory_overhead_pct": Decimal("0.15"),
        "target_margin_pct": Decimal("0.35"),
        "required_material_groups": [
            ("Tablero", "Madera", "Triplay"),
        ],
    },
    "Mesas": {
        "code": "carpinteria_premium",
        "base_labor_hours": Decimal("7.90"),
        "hours_per_m3": Decimal("8.20"),
        "hours_per_bom_item": Decimal("0.78"),
        "material_buffer_pct": Decimal("0.07"),
        "factory_overhead_pct": Decimal("0.16"),
        "target_margin_pct": Decimal("0.38"),
        "required_material_groups": [
            ("Madera", "Cubierta", "Tablero", "Triplay"),
        ],
    },
    "Estanterias y libreros": {
        "code": "gabineteria",
        "base_labor_hours": Decimal("6.90"),
        "hours_per_m3": Decimal("6.80"),
        "hours_per_bom_item": Decimal("0.68"),
        "material_buffer_pct": Decimal("0.06"),
        "factory_overhead_pct": Decimal("0.15"),
        "target_margin_pct": Decimal("0.34"),
        "required_material_groups": [
            ("Tablero", "Madera", "Triplay"),
        ],
    },
    "Cocina": {
        "code": "gabineteria_humeda",
        "base_labor_hours": Decimal("7.80"),
        "hours_per_m3": Decimal("7.30"),
        "hours_per_bom_item": Decimal("0.75"),
        "material_buffer_pct": Decimal("0.07"),
        "factory_overhead_pct": Decimal("0.16"),
        "target_margin_pct": Decimal("0.37"),
        "required_material_groups": [
            ("Tablero", "Triplay", "Madera"),
        ],
    },
    "Muebles infantiles": {
        "code": "infantil",
        "base_labor_hours": Decimal("6.70"),
        "hours_per_m3": Decimal("6.40"),
        "hours_per_bom_item": Decimal("0.66"),
        "material_buffer_pct": Decimal("0.06"),
        "factory_overhead_pct": Decimal("0.14"),
        "target_margin_pct": Decimal("0.35"),
        "required_material_groups": [
            ("Tablero", "Madera", "Triplay"),
        ],
    },
    "Muebles decorativos": {
        "code": "decorativo",
        "base_labor_hours": Decimal("7.30"),
        "hours_per_m3": Decimal("7.60"),
        "hours_per_bom_item": Decimal("0.74"),
        "material_buffer_pct": Decimal("0.07"),
        "factory_overhead_pct": Decimal("0.16"),
        "target_margin_pct": Decimal("0.38"),
        "required_material_groups": [
            ("Madera", "Tablero", "Tela"),
        ],
    },
    "Muebles de jardin": {
        "code": "exterior",
        "base_labor_hours": Decimal("9.20"),
        "hours_per_m3": Decimal("8.80"),
        "hours_per_bom_item": Decimal("0.88"),
        "material_buffer_pct": Decimal("0.09"),
        "factory_overhead_pct": Decimal("0.18"),
        "target_margin_pct": Decimal("0.42"),
        "required_material_groups": [
            ("Tzalam", "Rattan", "exterior"),
            ("Barniz marino", "Tornillo inox"),
        ],
    },
}


FINISH_KEYWORDS = ("Barniz", "Laca", "Sellador", "Tinta", "Pintura")
SCREW_KEYWORDS = ("Tornillo",)
GLUE_KEYWORDS = ("Pegamento",)
STAPLE_KEYWORDS = ("Grapa",)
PAINT_KEYWORDS = ("Pintura",)
SANDING_KEYWORDS = ("Lija",)
SOLVENT_KEYWORDS = ("Solvente",)
SEALER_KEYWORDS = ("Sellador",)
STRUCTURAL_KEYWORDS = (
    "Madera",
    "Tablero",
    "Triplay",
    "Cubierta",
    "Liston",
    "Rattan",
)
DISCRETE_COUNT_KEYWORDS = (
    "Tornillo",
    "Grapa",
    "Bisagra",
    "Corredera",
    "Jaladera",
    "Escuadra",
    "Rueda",
    "Herraje",
    "Resorte",
)
UPHOLSTERY_KEYWORDS = ("Tela", "Espuma", "Resorte", "Correa")
OUTDOOR_KEYWORDS = ("Rattan", "Tornillo inox", "Barniz marino", "Tzalam")
FUNCTIONAL_HARDWARE_KEYWORDS = ("Bisagra", "Corredera", "Jaladera", "Rueda")
HARDWARE_REQUIRED_TEXT_MARKERS = (
    "puerta",
    "cajon",
    "gaveta",
    "alacena",
    "closet",
    "ropero",
    "zapatera",
    "gabinete",
    "vitrina",
    "carro",
    "credenza",
    "buro",
    "comoda",
)

MIN_COMPONENT_LINES_BY_PROFILE: dict[str, int] = {
    "tapizado": 8,
    "carpinteria_premium": 8,
    "mixto_recamara": 8,
    "gabineteria": 8,
    "gabineteria_humeda": 8,
    "funcional_oficina": 8,
    "infantil": 8,
    "decorativo": 8,
    "exterior": 7,
}


@dataclass(frozen=True)
class VisualSignal:
    image_count: int
    format_diversity: int
    multiplier: Decimal


@dataclass(frozen=True)
class PriceQuote:
    sale_price: Decimal
    production_cost: Decimal
    direct_material_cost: Decimal
    adjusted_material_cost: Decimal
    labor_cost: Decimal
    factory_overhead: Decimal
    operating_overhead: Decimal
    qa_packaging_cost: Decimal
    target_margin_pct: Decimal
    labor_hours: Decimal
    profile_code: str
    image_multiplier: Decimal
    adjusted_template: list[dict[str, str]]


def _to_decimal(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_DECIMALS, rounding=ROUND_HALF_UP)


def _qty(value: Decimal) -> Decimal:
    return value.quantize(QTY_DECIMALS, rounding=ROUND_HALF_UP)


def _round_up_to_increment(
    value: Decimal, increment: Decimal = Decimal("50")
) -> Decimal:
    if increment <= 0:
        return _money(value)
    units = (value / increment).quantize(Decimal("1"), rounding=ROUND_CEILING)
    return _money(units * increment)


def _extract_file_extension(image_url: str) -> str:
    path = image_url.split("?", 1)[0].lower()
    match = re.search(r"\.([a-z0-9]+)$", path)
    if not match:
        return ""
    return match.group(1)


def load_images_by_sku() -> dict[str, list[str]]:
    if not IMAGE_DATA_FILE.exists():
        raise FileNotFoundError(f"No existe dataset de imagenes: {IMAGE_DATA_FILE}")

    data = json.loads(IMAGE_DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("seed_product_images.json debe ser un objeto SKU -> [urls]")

    images_by_sku: dict[str, list[str]] = {}
    for raw_sku, raw_urls in data.items():
        if not isinstance(raw_sku, str) or not isinstance(raw_urls, list):
            continue

        sku = raw_sku.strip().upper()
        urls = [url.strip() for url in raw_urls if isinstance(url, str) and url.strip()]
        if sku and urls:
            images_by_sku[sku] = urls

    return images_by_sku


def build_material_catalog(
    raw_materials_dataset: list[dict],
) -> dict[str, dict[str, Decimal]]:
    material_catalog: dict[str, dict[str, Decimal]] = {}
    for item in raw_materials_dataset:
        name = item.get("name")
        if not name:
            continue

        material_catalog[name] = {
            "unit_price": _to_decimal(item.get("unit_price", "0")),
            "waste_pct": _to_decimal(item.get("waste_percentage", "0")),
            "unit": str(item.get("unit") or ""),
        }

    return material_catalog


def get_profile_rule(category_name: str) -> dict:
    rule = CATEGORY_PROFILE_RULES.get(category_name)
    if rule is None:
        raise ValueError(
            f"No existe perfil de pricing para categoria '{category_name}'"
        )
    return rule


def get_visual_signal(image_urls: list[str]) -> VisualSignal:
    image_count = len(image_urls)
    format_diversity = len({_extract_file_extension(url) for url in image_urls if url})

    angle_boost = Decimal("1") + (Decimal(max(image_count - 1, 0)) * Decimal("0.012"))
    format_boost = Decimal("1") + (
        Decimal(max(format_diversity - 1, 0)) * Decimal("0.010")
    )

    signature_src = "|".join(sorted(image_urls))
    signature = hashlib.sha1(signature_src.encode("utf-8")).hexdigest()
    signature_steps = Decimal(str(int(signature[-2:], 16) % 6))
    signature_boost = Decimal("1") + (signature_steps * Decimal("0.004"))

    multiplier = _qty(angle_boost * format_boost * signature_boost)

    return VisualSignal(
        image_count=image_count,
        format_diversity=format_diversity,
        multiplier=multiplier,
    )


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _is_discrete_count_material(raw_material: str) -> bool:
    return _contains_any(raw_material, DISCRETE_COUNT_KEYWORDS)


def _qty_for_material(raw_material: str, value: Decimal) -> Decimal:
    if _is_discrete_count_material(raw_material):
        return value.quantize(Decimal("1"), rounding=ROUND_CEILING)
    return _qty(value)


def enrich_template_with_consumables(
    product_data: dict,
    base_template: list[dict[str, str]],
) -> list[dict[str, str]]:
    profile = get_profile_rule(product_data["type"])
    profile_code = profile["code"]

    enriched_template: list[dict[str, str]] = [
        {
            "raw_material": row["raw_material"],
            "quantity_required": str(
                _qty_for_material(
                    row["raw_material"],
                    _to_decimal(row["quantity_required"]),
                )
            ),
        }
        for row in base_template
    ]

    def has_material(keywords: tuple[str, ...]) -> bool:
        return any(
            _contains_any(item["raw_material"], keywords) for item in enriched_template
        )

    def add_if_missing(
        material_name: str,
        quantity_required: Decimal,
        match_keywords: tuple[str, ...],
    ) -> None:
        if has_material(match_keywords):
            return

        enriched_template.append(
            {
                "raw_material": material_name,
                "quantity_required": str(
                    _qty_for_material(material_name, quantity_required)
                ),
            }
        )

    # Consumibles basicos esperados en cualquier receta de carpinteria.
    add_if_missing(
        material_name="Pegamento blanco carpintero",
        quantity_required=Decimal("0.180"),
        match_keywords=GLUE_KEYWORDS,
    )
    add_if_missing(
        material_name="Lija abrasiva grano mixto",
        quantity_required=Decimal("2.000"),
        match_keywords=SANDING_KEYWORDS,
    )
    add_if_missing(
        material_name="Solvente limpieza acabados",
        quantity_required=Decimal("0.080"),
        match_keywords=SOLVENT_KEYWORDS,
    )

    if profile_code == "exterior":
        add_if_missing(
            material_name="Tornillo inox exterior 1 1/4",
            quantity_required=Decimal("18.000"),
            match_keywords=SCREW_KEYWORDS,
        )
        add_if_missing(
            material_name="Barniz marino exterior",
            quantity_required=Decimal("0.180"),
            match_keywords=FINISH_KEYWORDS,
        )
    else:
        interior_screw = (
            "Tornillo confirmat 7x50"
            if profile_code
            in {
                "gabineteria",
                "gabineteria_humeda",
                "funcional_oficina",
                "infantil",
            }
            else "Tornillo madera 1 1/4"
        )
        add_if_missing(
            material_name=interior_screw,
            quantity_required=Decimal("14.000"),
            match_keywords=SCREW_KEYWORDS,
        )

        interior_finish = (
            "Laca blanca semimate"
            if profile_code in {"gabineteria", "gabineteria_humeda", "infantil"}
            else "Barniz poliuretano mate"
        )
        add_if_missing(
            material_name=interior_finish,
            quantity_required=Decimal("0.150"),
            match_keywords=FINISH_KEYWORDS,
        )
        add_if_missing(
            material_name="Sellador nitrocelulosa",
            quantity_required=Decimal("0.100"),
            match_keywords=SEALER_KEYWORDS,
        )

    if profile_code == "tapizado":
        add_if_missing(
            material_name="Grapa tapiceria 1/2",
            quantity_required=Decimal("220.000"),
            match_keywords=STAPLE_KEYWORDS,
        )

    if profile_code in {"infantil", "decorativo"}:
        add_if_missing(
            material_name="Pintura esmalte base agua",
            quantity_required=Decimal("0.120"),
            match_keywords=PAINT_KEYWORDS,
        )

    return enriched_template


def _validate_required_groups(
    material_names: list[str], groups: list[tuple[str, ...]]
) -> None:
    for group in groups:
        if not any(_contains_any(name, group) for name in material_names):
            joined = ", ".join(group)
            raise ValueError(
                "BOM sin coherencia visual-material; falta algun material esperado de: "
                f"{joined}"
            )


def _validate_process_completeness(material_names: list[str]) -> None:
    required_blocks = {
        "fijacion": (
            "Tornillo",
            "Grapa",
            "Bisagra",
            "Corredera",
            "Jaladera",
            "Escuadra",
            "Rueda",
            "Herraje",
            "Resorte",
        ),
        "adhesivo": GLUE_KEYWORDS,
        "acabado": FINISH_KEYWORDS,
        "preparacion": ("Lija", "Solvente", "Sellador"),
    }

    for block_name, keywords in required_blocks.items():
        has_block = any(_contains_any(name, keywords) for name in material_names)
        if not has_block:
            raise ValueError(
                "BOM incompleto para proceso de taller; "
                f"falta bloque requerido: {block_name}"
            )


def _validate_professional_template(
    product_data: dict,
    adjusted_template: list[dict[str, str]],
    material_catalog: dict[str, dict[str, Decimal | str]],
) -> None:
    profile_code = get_profile_rule(product_data["type"])["code"]
    min_lines = MIN_COMPONENT_LINES_BY_PROFILE.get(profile_code, 8)
    if len(adjusted_template) < min_lines:
        raise ValueError(
            "BOM incompleto para nivel profesional; "
            f"lineas actuales={len(adjusted_template)}, minimo={min_lines}"
        )

    material_names = [row["raw_material"] for row in adjusted_template]
    if not any(_contains_any(name, STRUCTURAL_KEYWORDS) for name in material_names):
        raise ValueError("BOM sin nucleo estructural (madera/tablero/triplay)")

    if not any(_contains_any(name, DISCRETE_COUNT_KEYWORDS) for name in material_names):
        raise ValueError("BOM sin elementos de fijacion discreta")

    for row in adjusted_template:
        raw_material = row["raw_material"]
        quantity = _to_decimal(row["quantity_required"])
        material_data = material_catalog.get(raw_material)
        if material_data is None:
            continue

        unit = str(material_data.get("unit") or "")
        if _is_discrete_count_material(raw_material):
            if quantity != quantity.to_integral_value():
                raise ValueError(
                    f"Cantidad discreta no entera para '{raw_material}': {quantity}"
                )

        if unit == "Litro" and (
            quantity < Decimal("0.050") or quantity > Decimal("2.500")
        ):
            raise ValueError(
                f"Consumo fuera de rango para '{raw_material}' ({unit}): {quantity}"
            )

        if unit == "Metro lineal" and (
            quantity < Decimal("0.300") or quantity > Decimal("30.000")
        ):
            raise ValueError(
                f"Consumo fuera de rango para '{raw_material}' ({unit}): {quantity}"
            )


def _validate_wood_reference(product_data: dict, material_names: list[str]) -> None:
    wood_type = (product_data.get("wood_type") or "").strip()
    if not wood_type:
        return

    keywords_by_wood = {
        "Pino": ("Pino",),
        "Encino": ("Encino",),
        "Parota": ("Parota",),
        "Roble": ("Roble",),
        "Tzalam": ("Tzalam",),
        "MDF": ("MDF", "Tablero"),
        "Triplay": ("Triplay",),
    }
    expected_keywords = keywords_by_wood.get(wood_type)
    if not expected_keywords:
        return

    if not any(_contains_any(name, expected_keywords) for name in material_names):
        raise ValueError(
            f"BOM no refleja referencia de madera '{wood_type}' para {product_data['sku']}"
        )


def _requires_functional_hardware(product_data: dict) -> bool:
    searchable = " ".join(
        [
            str(product_data.get("name") or ""),
            str(product_data.get("description") or ""),
        ]
    ).lower()
    return any(marker in searchable for marker in HARDWARE_REQUIRED_TEXT_MARKERS)


def _validate_functional_hardware(
    product_data: dict, material_names: list[str]
) -> None:
    if not _requires_functional_hardware(product_data):
        return

    has_hardware = any(
        _contains_any(name, FUNCTIONAL_HARDWARE_KEYWORDS) for name in material_names
    )
    if not has_hardware:
        raise ValueError(
            f"BOM sin herrajes funcionales para producto con puertas/cajones: {product_data['sku']}"
        )


def validate_product_fidelity(
    product_data: dict,
    base_template: list[dict[str, str]],
    image_urls: list[str],
) -> None:
    if len(image_urls) < MIN_IMAGES_PER_PRODUCT:
        raise ValueError(
            f"{product_data['sku']} requiere >= {MIN_IMAGES_PER_PRODUCT} imagenes; "
            f"actual={len(image_urls)}"
        )

    profile = get_profile_rule(product_data["type"])
    material_names = [row["raw_material"] for row in base_template]

    _validate_required_groups(
        material_names=material_names,
        groups=profile.get("required_material_groups", []),
    )
    _validate_wood_reference(product_data=product_data, material_names=material_names)
    _validate_functional_hardware(
        product_data=product_data,
        material_names=material_names,
    )
    _validate_process_completeness(material_names=material_names)


def adjust_template_by_visual_signal(
    product_data: dict,
    base_template: list[dict[str, str]],
    visual_signal: VisualSignal,
) -> list[dict[str, str]]:
    profile = get_profile_rule(product_data["type"])
    profile_code = profile["code"]

    adjusted: list[dict[str, str]] = []
    for row in base_template:
        raw_material = row["raw_material"]
        quantity = _to_decimal(row["quantity_required"])
        multiplier = Decimal("1")

        if _contains_any(raw_material, FINISH_KEYWORDS):
            multiplier *= visual_signal.multiplier

        if profile_code == "tapizado" and _contains_any(
            raw_material, UPHOLSTERY_KEYWORDS
        ):
            upholstery_boost = Decimal("1") + (
                (visual_signal.multiplier - Decimal("1")) * Decimal("0.80")
            )
            multiplier *= upholstery_boost

        if profile_code == "exterior" and _contains_any(raw_material, OUTDOOR_KEYWORDS):
            outdoor_boost = Decimal("1") + (
                (visual_signal.multiplier - Decimal("1")) * Decimal("1.10")
            )
            multiplier *= outdoor_boost

        adjusted_qty = _qty_for_material(raw_material, quantity * multiplier)
        adjusted.append(
            {
                "raw_material": raw_material,
                "quantity_required": str(adjusted_qty),
            }
        )

    return adjusted


def calculate_direct_material_cost(
    adjusted_template: list[dict[str, str]],
    material_catalog: dict[str, dict[str, Decimal]],
) -> Decimal:
    total = Decimal("0")

    for row in adjusted_template:
        material_name = row["raw_material"]
        quantity = _to_decimal(row["quantity_required"])
        material_data = material_catalog.get(material_name)

        if material_data is None:
            raise ValueError(
                f"No existe precio de materia prima para '{material_name}'"
            )

        unit_price = material_data["unit_price"]
        waste_pct = material_data["waste_pct"]
        waste_factor = Decimal("1") + (waste_pct / Decimal("100"))
        total += quantity * unit_price * waste_factor

    return _money(total)


def _estimate_volume_m3(product_data: dict) -> Decimal:
    text = " ".join(
        str(value)
        for value in [
            product_data.get("specifications") or "",
            product_data.get("description") or "",
        ]
    )
    numbers = re.findall(r"(\d+(?:\.\d+)?)", text)
    if len(numbers) < 3:
        return Decimal("0.70")

    try:
        a = Decimal(numbers[0])
        b = Decimal(numbers[1])
        c = Decimal(numbers[2])
    except Exception:
        return Decimal("0.70")

    if a <= 0 or b <= 0 or c <= 0:
        return Decimal("0.70")

    volume_cm3 = a * b * c
    volume_m3 = volume_cm3 / Decimal("1000000")

    if volume_m3 < Decimal("0.08"):
        return Decimal("0.08")
    if volume_m3 > Decimal("2.60"):
        return Decimal("2.60")
    return volume_m3


def build_price_quote(
    product_data: dict,
    base_template: list[dict[str, str]],
    image_urls: list[str],
    material_catalog: dict[str, dict[str, Decimal]],
) -> PriceQuote:
    enriched_template = enrich_template_with_consumables(
        product_data=product_data,
        base_template=base_template,
    )

    validate_product_fidelity(
        product_data=product_data,
        base_template=enriched_template,
        image_urls=image_urls,
    )

    profile = get_profile_rule(product_data["type"])
    visual_signal = get_visual_signal(image_urls)
    adjusted_template = adjust_template_by_visual_signal(
        product_data=product_data,
        base_template=enriched_template,
        visual_signal=visual_signal,
    )
    _validate_professional_template(
        product_data=product_data,
        adjusted_template=adjusted_template,
        material_catalog=material_catalog,
    )

    direct_material_cost = calculate_direct_material_cost(
        adjusted_template=adjusted_template,
        material_catalog=material_catalog,
    )

    material_buffer_pct = _to_decimal(profile["material_buffer_pct"])
    adjusted_material_cost = _money(
        direct_material_cost * (Decimal("1") + material_buffer_pct)
    )

    volume_m3 = _estimate_volume_m3(product_data)
    labor_hours = (
        _to_decimal(profile["base_labor_hours"])
        + (volume_m3 * _to_decimal(profile["hours_per_m3"]))
        + (
            Decimal(str(len(adjusted_template)))
            * _to_decimal(profile["hours_per_bom_item"])
        )
        + (Decimal(str(visual_signal.image_count)) * Decimal("0.35"))
        + (Decimal(str(visual_signal.format_diversity)) * Decimal("0.20"))
    )
    labor_hours = _qty(labor_hours)

    labor_cost = _money(labor_hours * LABOR_HOURLY_RATE * LABOR_BURDEN_FACTOR)

    overhead_base = adjusted_material_cost + labor_cost
    factory_overhead = _money(
        overhead_base * _to_decimal(profile["factory_overhead_pct"])
    )
    operating_overhead = _money(overhead_base * OPERATING_OVERHEAD_PCT)
    qa_packaging_cost = _money(adjusted_material_cost * QA_PACKAGING_PCT)

    production_cost = _money(
        adjusted_material_cost
        + labor_cost
        + factory_overhead
        + operating_overhead
        + qa_packaging_cost
    )

    target_margin_pct = _to_decimal(profile["target_margin_pct"])
    if target_margin_pct >= Decimal("1"):
        raise ValueError("El margen objetivo no puede ser >= 100%")

    sale_price = _round_up_to_increment(
        production_cost / (Decimal("1") - target_margin_pct),
        increment=Decimal("50"),
    )

    return PriceQuote(
        sale_price=sale_price,
        production_cost=production_cost,
        direct_material_cost=direct_material_cost,
        adjusted_material_cost=adjusted_material_cost,
        labor_cost=labor_cost,
        factory_overhead=factory_overhead,
        operating_overhead=operating_overhead,
        qa_packaging_cost=qa_packaging_cost,
        target_margin_pct=_money(target_margin_pct * Decimal("100")),
        labor_hours=labor_hours,
        profile_code=profile["code"],
        image_multiplier=visual_signal.multiplier,
        adjusted_template=adjusted_template,
    )
