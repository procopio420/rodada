import re
import unicodedata
from django.db import migrations


def normalize_existing_names(apps, schema_editor):
    Product = apps.get_model('catalog', 'Product')
    products = list(Product.objects.using(schema_editor.connection.alias).all())
    keys = set()
    for product in products:
        value = unicodedata.normalize('NFKC', product.name).casefold().strip()
        value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))
        product.normalized_name = re.sub(r'\s+', ' ', value)
        key = (product.venue_id, product.normalized_name)
        if key in keys:
            raise RuntimeError('Catalog name normalization collision; reconcile products before migrating.')
        keys.add(key)
    # Temporary unique names avoid collisions with another row's previous spelling.
    for product in products:
        Product.objects.using(schema_editor.connection.alias).filter(pk=product.pk).update(normalized_name=f'__migration__{product.pk}')
    for product in products:
        Product.objects.using(schema_editor.connection.alias).filter(pk=product.pk).update(normalized_name=product.normalized_name)


class Migration(migrations.Migration):
    dependencies = [('catalog', '0004_icon_generation_request')]
    operations = [migrations.RunPython(normalize_existing_names, migrations.RunPython.noop)]
