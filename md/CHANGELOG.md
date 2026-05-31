# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- **Migración de Escáneres a Productos**: El sistema ahora manage productos genéricos de almacén en lugar de escáneres específicos.
  - Vista de "Escáneres" cambiada a "Productos" (`ui/views/products.py`)
  - El código de barras ahora es el identificador principal para productos
  - Funciones de base de datos actualizadas para usar `get_all_products` en lugar de `get_all_scanners`

- **UI Updates**:
  - Título de la aplicación cambiado a "ScanStock — Sistema de Inventario de almacén"
  - Sidebar actualizado de "Control de Escáneres" a "Control de Inventario"
  - Navegación actualizada de "Escáneres" a "Productos"
  - Dashboard actualizado para mostrar estadísticas de productos (Total, Disponibles, Bajo Stock, Críticos, Inactivos)
  - Movimientos actualizado para usar productos en lugar de escáneres

- **Export**:
  - Excel exports actualizados para usar nombres de columnas de productos
  - `core/export.py` actualizado para usar `get_all_products`

### Fixed

- `dashboard.py`: Cambiado `get_scanner_counts()` a `get_product_counts()`
- `movements.py`: Funciones de escáneres substituidas por funciones de productos
- `core/export.py`: Imports actualizados y columnas corregidas

### Removed

- Referencias a funciones de escáneres que ya no existen (`get_scanners_by_status`, etc.)