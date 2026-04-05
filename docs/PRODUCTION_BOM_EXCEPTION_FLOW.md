# Flujo de Excepción de Producción

## Objetivo
Definir un flujo claro, coherente y auditable para el caso en que, durante la ejecución de una orden de producción, el productor detecta que la lista de materiales (BOM) original de esa orden está incompleta.

Este documento está orientado a cliente y operación: explica qué ocurre hoy en el sistema, qué decisiones se deben tomar y cómo garantizar trazabilidad.

---

## Principio Operativo: Snapshot de BOM

Al crear una orden de producción (OP), el sistema toma una foto (snapshot) de la BOM vigente en ese momento y la convierte en el plan de consumo de la OP.

Implicaciones:

1. La OP conserva su plan de materiales original durante su ciclo de vida.
2. Los cambios posteriores en la BOM maestra aplican a nuevas OP, no a OP ya creadas.
3. No existe recálculo automático retroactivo de materiales en una OP en curso.

Este comportamiento protege consistencia histórica y auditoría.

---

## Qué pasa si falta un material en una OP ya iniciada

Cuando el productor detecta que un material necesario no quedó en el plan snapshot de la OP:

1. El sistema no cancela automáticamente la OP por esta causa.
2. La OP no se corrige sola con la BOM maestra editada después.
3. El material faltante debe gestionarse como excepción operativa controlada.

---

## Política de Decisión

### Regla 1: No cancelación automática
La falta de un material en el snapshot no dispara cancelación automática.

### Regla 2: Corrección hacia adelante
Se corrige la BOM maestra para evitar que el problema se repita en futuras OP.

### Regla 3: Trazabilidad explícita
Todo consumo extraordinario fuera del snapshot debe dejar evidencia documentada.

### Regla 4: Cierre condicionado
La OP solo debe pasar a terminado cuando la operación real esté completada y el inventario refleje correctamente los consumos.

---

## Flujo Operativo Recomendado

### Fase 1. Detección y contención (Productor)

1. Detectar el faltante antes de cerrar la OP.
2. Mantener la OP en pendiente o en_proceso mientras se resuelve.
3. Notificar al responsable de producción o planeación.

Resultado esperado: evitar un cierre incorrecto de la OP.

### Fase 2. Validación y clasificación (Supervisor)

1. Confirmar si el faltante es real (omisión de BOM) o error de captura operativa.
2. Determinar si el material faltante está disponible en inventario.
3. Decidir ruta de resolución:
   - Ruta A: hay stock del faltante.
   - Ruta B: no hay stock y se requiere compra.

Resultado esperado: decisión operativa objetiva y documentada.

### Fase 3. Corrección estructural (Planeación)

1. Editar la BOM maestra del producto para incluir el material omitido.
2. Validar cantidades y unidad de medida.
3. Publicar la corrección para que aplique a nuevas OP.

Resultado esperado: evitar recurrencia.

### Fase 4. Ejecución de excepción en la OP actual (Operación)

1. Consumir físicamente el material faltante según operación real.
2. Registrar ajuste manual de inventario de materia prima con salida:
   - Tipo sugerido: AJUSTE_SALIDA.
   - Motivo obligatorio con formato estándar.
3. Capturar en el motivo el identificador de OP, causa y autorización.

Formato de motivo recomendado:

"Consumo extraordinario OP-<id> por omisión en BOM snapshot. Aprobado por <rol/nombre>."

Nota operativa:

- El formulario actual de ajuste no expone campo de referencia independiente; por eso el identificador de OP debe ir en el motivo.

Resultado esperado: inventario y auditoría alineados con el hecho real.

### Fase 5. Cierre de OP (Supervisor)

1. Revisar consumos normales capturados en la OP.
2. Verificar que los consumos extraordinarios ya estén reflejados en movimientos de materia prima.
3. Confirmar que no hay faltantes pendientes.
4. Cambiar estado de OP a terminado.

Resultado esperado: cierre íntegro, sin ocultar excepciones.

---

## Matriz de decisión rápida

### Escenario A: faltante detectado y hay stock

1. No cancelar OP.
2. Ajuste de salida con motivo estandarizado.
3. Corregir BOM maestra.
4. Continuar y cerrar OP.

### Escenario B: faltante detectado y no hay stock

1. No cerrar OP.
2. Gestionar compra/abasto.
3. Corregir BOM maestra.
4. Cuando llegue material, registrar ajuste y completar producción.
5. Cerrar OP.

### Escenario C: error grave de planeación que invalida totalmente la OP

1. Evaluar cancelación controlada de OP.
2. Si la OP está ligada a orden de cliente, evitar dejar todas las OP asociadas en cancelado al mismo tiempo.
3. Crear OP de reemplazo antes o en simultáneo a la cancelación para conservar continuidad operativa y de estado.

---

## Trazabilidad requerida

Para auditoría y control de cliente, cada incidente debe dejar rastro en:

1. Historial de cambios de estado de la OP.
2. Auditoría de cambios de la orden de cliente asociada (si aplica).
3. Movimientos de inventario de materia prima con motivo detallado.
4. Versión o timestamp de actualización de BOM maestra.

Mínimos de trazabilidad por incidencia:

1. ID de OP.
2. Material faltante.
3. Cantidad extraordinaria consumida.
4. Motivo y autorización.
5. Fecha y usuario que ejecutó el ajuste.

---

## Coherencia lógica del modelo

Este flujo es coherente con un modelo de manufactura auditable porque separa:

1. Planeación histórica (snapshot de la OP).
2. Corrección estructural (BOM maestra hacia adelante).
3. Ejecución real (consumos y ajustes operativos).

Así se evita mezclar pasado y futuro, sin perder control operativo del presente.

---

## Buenas prácticas para cliente

1. Estandarizar el texto de motivo para excepciones de BOM.
2. Definir un responsable de aprobación por turno.
3. Revisar semanalmente incidencias de omisión BOM.
4. Medir recurrencia por producto para mejora continua.

---

## Resumen ejecutivo

Cuando falta un material en una OP ya creada, la política correcta no es sobrescribir el snapshot ni cancelar automáticamente. La política correcta es:

1. Contener.
2. Corregir BOM maestra para nuevas OP.
3. Registrar consumo extraordinario con trazabilidad.
4. Cerrar la OP solo cuando la ejecución real esté completa.

Con esto se garantiza consistencia de datos, transparencia operativa y control para cliente.
