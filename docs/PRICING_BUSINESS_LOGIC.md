# Logica de Negocio de Precios (Seed de Alta Fidelidad)

Este documento define la logica usada por el seed oficial para que:

1. El precio de venta no sea arbitrario.
2. La receta de materiales (BOM) sea coherente con la evidencia visual del producto.
3. El precio cubra costo productivo real, salarios, gastos indirectos y margen.

Implementacion tecnica: scripts/seed_pricing_rules.py
Consumido por: scripts/seed_products.py y scripts/seed_bom.py

---

## 1) Objetivo

El objetivo del seed no es solo llenar tablas, sino producir un catalogo demostrable para negocio:

- Producto con imagenes suficientes por SKU.
- Producto con BOM consistente contra su perfil visual.
- Precio de venta calculado con una estructura financiera replicable.

---

## 2) Reglas de Fidelidad Visual

### 2.1 Minimo de imagenes

Cada SKU debe tener al menos 4 imagenes en scripts/seed_product_images.json.

Si un SKU no cumple, el seed falla (fail-fast) para evitar datos de baja calidad.

### 2.2 Senal visual (visual signal)

Para cada SKU se calcula una senal visual con:

- Numero de imagenes
- Diversidad de formatos (jpg, png, webp, avif)
- Firma deterministica de URLs

Esta senal genera un multiplicador suave que ajusta consumos visualmente sensibles
(acabados, tapiceria, materiales exteriores) y evita catalogos planos con BOM identica.

---

## 3) Coherencia Visual-Material (BOM)

Cada categoria tiene un perfil de negocio con materiales esperados.

Ejemplos:

- Salas (tapizado): debe incluir combinaciones de tela/espuma y resorte/correa.
- Muebles de jardin (exterior): debe incluir materiales de exterior (ej. tzalam/rattan)
  y proteccion exterior (ej. barniz marino o tornilleria inox).
- Gabineteria (closets/cocina/TV): debe incluir base estructural y herrajes funcionales.

Si una BOM no cumple el perfil, el seed falla.

Esto asegura que el producto que se ve en catalogo tenga una receta de fabricacion
coherente con su tipo visual/comercial.

---

## 4) Formula de Costo y Precio

Variables:

- DM: Costo directo de materiales (con merma)
- DMa: Costo de materiales ajustado (incluye buffer de consumibles)
- DL: Mano de obra directa (horas * tarifa * carga salarial)
- CIF: Carga fabril (indirectos de planta)
- OPEX: Carga operativa
- QA: Calidad + empaque
- CP: Costo de produccion total
- M: Margen objetivo por perfil
- PV: Precio de venta

### 4.1 Costo directo de materiales con merma

Para cada renglon del BOM:

DM_linea = cantidad * precio_unitario * (1 + merma_pct/100)

DM = suma(DM_linea)

### 4.2 Ajuste de materiales

DMa = DM * (1 + buffer_materiales_por_perfil)

Este buffer cubre consumibles no atomizados y diferencias operativas de taller.

### 4.3 Mano de obra (incluye salarios)

Horas de trabajo estimadas:

horas = base_perfil + (volumen_m3 * horas_por_m3_perfil)
        + (items_bom * horas_por_item_perfil)
        + bonos_visuales

DL = horas * tarifa_hora * factor_carga_salarial

Notas:

- tarifa_hora: costo directo de mano de obra.
- factor_carga_salarial: integra prestaciones/carga patronal.

### 4.4 Indirectos

CIF = (DMa + DL) * pct_carga_fabril_perfil
OPEX = (DMa + DL) * pct_operativo_global
QA = DMa * pct_qa_empaque_global

### 4.5 Costo de produccion y precio

CP = DMa + DL + CIF + OPEX + QA
PV = CP / (1 - M)

Regla comercial final:

- El precio se redondea hacia arriba al multiplo de 50 para estandar comercial.

---

## 5) Perfiles por Categoria

Cada categoria tiene parametros propios:

- Horas base y complejidad
- Buffer de materiales
- Carga fabril
- Margen objetivo
- Materiales esperados

Esto evita usar una sola formula plana para todo el catalogo.

---

## 6) Endurecimiento del Seed

El seed se considera endurecido porque:

1. Falla si faltan imagenes minimas por SKU.
2. Falla si BOM no es coherente con perfil visual-material.
3. Falla si falta precio de materia prima para algun material del BOM.
4. Recalcula precio automaticamente para cada producto (no usa precio estatico hardcodeado).
5. Usa la misma logica en seed_products.py y seed_bom.py para evitar divergencias.

---

## 7) Flujo recomendado de ejecucion

Orden oficial (resumen):

1. scripts/seed_raw_materials.py
2. scripts/seed_products.py
3. scripts/seed_product_images.py
4. scripts/seed_purchase.py
5. scripts/seed_bom.py
6. scripts/seed_inventory.py

O en una sola corrida:

- scripts/seed_all.py

---

## 8) Resultado esperado para demos de alta fidelidad

- Catalogo visual consistente por SKU.
- BOM funcional y creible para cada tipo de mueble.
- Precio explicable en terminos de costo productivo, salarios, indirectos y margen.
- Menor riesgo de inconsistencias entre equipos (ventas, produccion y costos).
