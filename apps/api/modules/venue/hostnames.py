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
