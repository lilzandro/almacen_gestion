# Modelo Entidad-Relación - ScanStock

Este documento describe la estructura de la base de datos del sistema de inventario ScanStock.

## 1. Usuarios (users)

Tabla que almacena los usuarios del sistema.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Entero | Identificador único del usuario |
| nombre_usuario | Texto | Nombre de inicio de sesión (único) |
| hash_contraseña | Texto | Contraseña encriptada |
| rol | Texto | Rol del usuario: 'admin' o 'user' |
| fecha_creacion | Fecha | Cuándo se creó el usuario |

## 2. Proveedores (suppliers)

Table que guarda los proveedores de los productos.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Entero | Identificador único del proveedor |
| nombre | Texto | Nombre de la empresa proveedora |
| contacto | Texto | Teléfono, email o datos de contacto |
| direccion | Texto | Dirección física del proveedor |
| fecha_creacion | Fecha | Cuándo se registró el proveedor |

## 3. Empleados (employees)

Tabla del personal que puede recibir productos asignados.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Entero | Identificador único del empleado |
| nombre | Texto | Nombre completo del empleado |
| departamento | Texto | Área o departamento donde trabaja |
| codigo_empleado | Texto | Código único para identificar al empleado |
| fecha_creacion | Fecha | Cuándo se registró el empleado |

## 4. Productos (products)

Tabla principal que contiene todos los productos del inventario.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Entero | Identificador único del producto |
| nombre | Texto | Nombre o descripción del producto |
| descripcion | Texto | Detalles adicionales sobre el producto |
| codigo_barras | Texto | Código de barras único (para escanear) |
| sku | Texto | Código interno del producto |
| categoria | Texto | Categoría a la que pertenece |
| marca | Texto | Marca del produto |
| ubicacion | Texto | Dónde está guardado en el almacén |
| cantidad | Entero | Cantidad actual en inventario |
| cantidad_minima | Entero | Stock mínimo antes de alertar |
| precio_venta | Decimal | Precio al que se vende |
| precio_costo | Decimal | Cuánto costò comprarlo |
| estado | Texto | Estado: disponible, no disponible, inactivo |
| proveedor_id | Entero | Relacion con la tabla proveedores |
| fecha_creacion | Fecha | Cuándo se registró el producto |
| fecha_actualizacion | Fecha | Última vez que se.modificó |

## 5. Movimientos (movimientos)

Tabla que registra todas las entradas y salidas de productos.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Entero | Identificador único del movimiento |
| tipo | Texto | Tipo de operación: entrada, salida, devolucion, asignacion |
| producto_id | Entero | Producto quese afecta |
| empleado_id | Entero | Empleado relacionado (opcional) |
| usuario_id | Entero | Usuario que registra la operación |
| cantidad | Entero | Cuántas unidades se movieron |
| notas | Texto | Comentarios adicionales |
| fecha_hora | Fecha | Cuándo ocurrió el movimiento |

## Relaciones entre tablas

- **Productos → Proveedores**: Un producto puede tener un proveedor asignado (relación uno a muchos)
- **Movimientos → Productos**: Cada movimiento afecta a un producto (relación uno a muchos)
- **Movimientos → Empleados**: Un movimiento puede estar asociado a un empleado (relación uno a muchos)
- **Movimientos → Usuarios**: Todo movimiento es registrado por un usuario (relación uno a beaucoup)

## Explicación de los tipos de movimientos

| Tipo | Efecto en inventario |
|------|-------------------|
| entrada | Aumenta la cantidad del producto |
| salida | Disminuye la cantidad del producto |
| devolucion | Aumenta la cantidad (producto devuelto) |
| asignacion | Disminuye la cantidad (asignado a empleado) |

## Estados de los productos

| Estado | Significado |
|--------|------------|
| disponible | Hay unidades en stock |
| no disponible | Sin stock |
| inactivo | Producto dado de baja |