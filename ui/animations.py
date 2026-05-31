"""Utilidades de animación reutilizables para toda la aplicación."""


def animate_counter(widget, end_val: int, duration: int = 600, steps: int = 25):
    """Anima el texto de un CTkLabel contando de 0 hasta end_val."""
    if end_val <= 0:
        try:
            widget.configure(text="0")
        except Exception:
            pass
        return

    interval = max(10, duration // steps)

    def _step(i):
        t = min(i / steps, 1.0)
        eased = 1 - (1 - t) ** 2  # ease-out cuadrático
        current = int(end_val * eased)
        try:
            widget.configure(text=str(current))
        except Exception:
            return
        if i < steps:
            widget.after(interval, _step, i + 1)
        else:
            try:
                widget.configure(text=str(end_val))
            except Exception:
                pass

    _step(0)


def dialog_open(toplevel, duration: int = 200, steps: int = 10):
    """Fade + slide-up al abrir un CTkToplevel.
    Llamar con after(1, lambda: dialog_open(self)) al final de __init__."""
    toplevel.update_idletasks()
    full_w = toplevel.winfo_width()
    full_h = toplevel.winfo_height()
    if full_w <= 1 or full_h <= 1:
        return

    # Centrar relativo al padre, si no, centrar en pantalla
    try:
        parent = toplevel.master
        parent.update_idletasks()
        cx = parent.winfo_x() + (parent.winfo_width() - full_w) // 2
        cy = parent.winfo_y() + (parent.winfo_height() - full_h) // 2
    except Exception:
        sw = toplevel.winfo_screenwidth()
        sh = toplevel.winfo_screenheight()
        cx = (sw - full_w) // 2
        cy = (sh - full_h) // 2

    offset = 25
    interval = max(10, duration // steps)

    try:
        toplevel.attributes("-alpha", 0.0)
    except Exception:
        return  # alpha no soportado, omitir animación

    toplevel.geometry(f"{full_w}x{full_h}+{cx}+{cy + offset}")

    def _step(i):
        t = min(i / steps, 1.0)
        eased = 1 - (1 - t) ** 2
        alpha = min(1.0, t * 1.4)
        y_off = int(offset * (1 - eased))
        try:
            toplevel.geometry(f"{full_w}x{full_h}+{cx}+{cy + y_off}")
            toplevel.attributes("-alpha", alpha)
        except Exception:
            return
        if i < steps:
            toplevel.after(interval, _step, i + 1)
        else:
            try:
                toplevel.geometry(f"{full_w}x{full_h}+{cx}+{cy}")
                toplevel.attributes("-alpha", 1.0)
            except Exception:
                pass

    toplevel.after(10, lambda: _step(1))


def slide_in_frame(frame, parent, duration: int = 180, steps: int = 8):
    """Desliza un frame (grid) desde la derecha al mostrarlo.
    Usa place() durante la animación y restaura grid al terminar."""
    parent.update_idletasks()
    parent_w = parent.winfo_width()
    if parent_w <= 1:
        return

    grid_info = {k: v for k, v in frame.grid_info().items() if k != "in"}
    if not grid_info:
        return

    frame.grid_remove()
    interval = max(10, duration // steps)

    def _step(i):
        t = min(i / steps, 1.0)
        eased = 1 - (1 - t) ** 3  # ease-out cúbico
        x = int(parent_w * (1 - eased))
        try:
            frame.place(relwidth=1, relheight=1, x=x, y=0)
        except Exception:
            return
        if i < steps:
            frame.after(interval, _step, i + 1)
        else:
            try:
                frame.place_forget()
                frame.grid(**grid_info)
            except Exception:
                pass

    try:
        frame.place(relwidth=1, relheight=1, x=parent_w, y=0)
    except Exception:
        return
    frame.after(10, lambda: _step(1))
