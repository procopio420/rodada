from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CatalogUpgradeTests(TransactionTestCase):
    def test_main_icons_and_assets_survive_durable_generation_upgrade(self):
        executor = MigrationExecutor(connection)
        before = [('catalog', '0002_producticon')]
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            venue = apps.get_model('venue', 'Venue').objects.create(name='Legacy', slug='legacy-icon')
            product = apps.get_model('catalog', 'Product').objects.create(
                venue_id=venue.pk, name='Água', normalized_name='água',
                price_cents=500, fulfillment_station='BAR')
            apps.get_model('catalog', 'ProductIcon').objects.create(
                product_id=product.pk, source='UPLOADED', status='READY',
                published_asset_url='https://example.com/water.png')
            after = [('catalog', '0005_normalize_existing_names')]
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            icon = apps.get_model('catalog', 'ProductIcon').objects.get(pk=product.pk)
            assert icon.published_asset_url == 'https://example.com/water.png'
            assert icon.status == 'READY'
            assert icon.revision == 0
            assert apps.get_model('catalog', 'Product').objects.get(pk=product.pk).normalized_name == 'agua'
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
