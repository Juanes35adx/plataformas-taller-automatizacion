class ExcepcionNegocio(Exception):
    """La factura se rechaza por sus datos; no se reintenta."""


class ExcepcionSistema(Exception):
    """Falla del portal (503, caída); se reintenta."""
