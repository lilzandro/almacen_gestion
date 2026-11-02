"""Regresión de navegación: cambiar de almacén no deja vistas huérfanas."""


def test_cambio_de_almacen_destruye_las_vistas_invalidadas():
    from ui.app import App

    class _Old:
        def __init__(self):
            self.destroyed = False

        def destroy(self):
            self.destroyed = True

    class _Stub:
        _warehouses = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        current_warehouse_id = 1

        def __init__(self):
            self._current_view_name = "movements"
            self.navigated = []
            self.products = _Old()
            self.movements = _Old()
            self.dashboard = _Old()
            self._views = {
                "products": self.products,
                "movements": self.movements,
                "dashboard": self.dashboard,
            }

        def _navigate(self, name):
            self.navigated.append(name)

    stub = _Stub()
    App._on_warehouse_change_by_name(stub, "B")

    assert stub.current_warehouse_id == 2
    assert stub.products.destroyed
    assert stub.movements.destroyed
    assert stub.dashboard.destroyed
    assert stub._views == {}
    assert stub.navigated == ["movements"]
