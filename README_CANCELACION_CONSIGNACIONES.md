# Mejora de cancelación de consignaciones - Ticket #06302

## Alcance implementado

Se agregaron controles al botón `Cancelar` de `consignment.order` para evitar que una consignación cancelada deje albaranes activos o pendientes de validación.

### Reglas agregadas

1. Al cancelar una consignación, el módulo identifica albaranes relacionados por:
   - `origin = nombre de la consignación`
   - órdenes de venta relacionadas (`sale_order_id`, `sale_order_ids` y `sale.order.consignment_order_id`)
   - albaranes de las órdenes de venta relacionadas
   - retornos vinculados por `consignment_id`

2. Los albaranes no validados (`draft`, `waiting`, `confirmed`, `assigned`, etc.) se cancelan automáticamente.

3. Si existe un albarán validado (`done`) sin retorno completo validado, se bloquea la cancelación con un mensaje claro al usuario.

4. Si el albarán validado ya tiene retorno completo validado mediante trazabilidad nativa (`origin_returned_move_id` / `returned_move_ids`), se permite la cancelación.

5. Se deja trazabilidad en chatter de la consignación y del albarán cancelado automáticamente.

## Archivos modificados

- `models/consignment_order.py`
- `__manifest__.py` versión `17.0.1.1`

## Nota técnica

No se modificó el flujo de creación/aprobación/confirmación/venta de consignaciones. La mejora se concentra en el control previo a la cancelación.
