from django.core.exceptions import ValidationError

TENANT_DOMAIN = 'rodada.bar'
RESERVED_LABELS = frozenset(('www', 'app', 'api', 'admin', 'bar', 'cozinha', 'cliente', 'gerencia', 'atendimento', 'pedido', 'caixa', 'relatorios'))

def normalize_tenant_hostname(hostname):
    if not isinstance(hostname, str):
        raise ValidationError('Invalid hostname')
    host = hostname.strip().lower()
    suffix = '.' + TENANT_DOMAIN
    if not host.endswith(suffix):
        raise ValidationError('Hostname outside tenant domain')
    label = host[:-len(suffix)]
    if label in RESERVED_LABELS or not label or len(label) > 63:
        raise ValidationError('Invalid tenant label')
    if not label[0].isalnum() or not label[-1].isalnum() or any(not (c.isascii() and (c.islower() or c.isdigit() or c == '-')) for c in label):
        raise ValidationError('Invalid tenant label')
    return host


# Request-scoped venue identity; None preserves explicit legacy/native transport.
from contextvars import ContextVar
resolved_venue_id = ContextVar("rodada_host_venue_id", default=None)


def assert_staff_venue(venue_id):
    from modules.access.services import AccessServiceError
    expected = resolved_venue_id.get()
    if expected is not None and str(expected) != str(venue_id):
        raise AccessServiceError("VENUE_HOST_MISMATCH", "Sessão pertence a outro estabelecimento.", 403)
