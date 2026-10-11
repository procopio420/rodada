"""Import a verified venue menu from a reviewed, UTF-8 CSV.

The source PDF/Canva link must be reviewed before producing the CSV. This command
never attempts OCR, guesses prices/routing or reconciles missing catalog rows.
"""
import csv
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.catalog.models import FulfillmentStation, Product, normalize_product_name
from modules.venue.models import Venue


REQUIRED_COLUMNS = {"name", "category", "price_brl", "station"}
BRL_RE = re.compile(r"^(?:0|[1-9]\d*|[1-9]\d{0,2}(?:\.\d{3})+),\d{2}$")
STATIONS = {
    "BAR": FulfillmentStation.BAR,
    "KITCHEN": FulfillmentStation.KITCHEN,
    "COZINHA": FulfillmentStation.KITCHEN,
}


def parse_price_cents(value):
    raw = value.strip()
    if raw.startswith("R$"):
        raw = raw[2:].strip()
    if not BRL_RE.fullmatch(raw):
        raise ValueError("use Brazilian currency with two decimals, e.g. 12,50")
    return int(raw.replace(".", "").replace(",", ""))


def read_products(path):
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise CommandError("CSV vazio; campos obrigatórios: name,category,price_brl,station")
            missing = REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing:
                raise CommandError(f"Colunas ausentes: {', '.join(sorted(missing))}")
            products = []
            seen = set()
            for number, raw in enumerate(reader, start=2):
                if None in raw:
                    raise CommandError(f"Linha {number}: número inesperado de colunas")
                name = (raw["name"] or "").strip()
                category = (raw["category"] or "").strip()
                description = (raw.get("description") or "").strip()
                station_text = (raw["station"] or "").strip().upper()
                if not name or len(name) > 160:
                    raise CommandError(f"Linha {number}: nome obrigatório (máximo 160 caracteres)")
                if len(category) > 100 or len(description) > 600:
                    raise CommandError(f"Linha {number}: categoria/descrição excede o limite")
                if station_text not in STATIONS:
                    raise CommandError(f"Linha {number}: station deve ser BAR, KITCHEN ou COZINHA")
                try:
                    price_cents = parse_price_cents(raw["price_brl"] or "")
                except ValueError as exc:
                    raise CommandError(f"Linha {number}: preço inválido: {exc}") from exc
                normalized = normalize_product_name(name)
                if normalized in seen:
                    raise CommandError(f"Linha {number}: produto duplicado no arquivo: {name}")
                seen.add(normalized)
                products.append({
                    "name": name,
                    "normalized_name": normalized,
                    "category": category,
                    "description": description,
                    "price_cents": price_cents,
                    "fulfillment_station": STATIONS[station_text],
                })
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CommandError(f"Falha ao ler CSV: {exc}") from exc
    if not products:
        raise CommandError("CSV sem produtos; nenhuma alteração será realizada")
    return products


class Command(BaseCommand):
    help = "Pré-visualiza ou importa CSV revisado para o catálogo de um Venue (não desativa ausentes)."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="CSV UTF-8 com colunas name,category,price_brl,station[,description]")
        parser.add_argument("--venue-slug", default="bar-do-aderlan")
        parser.add_argument("--apply", action="store_true", help="Persistir após revisão do preview")
        parser.add_argument("--update-existing", action="store_true", help="Atualizar preço e metadados de nomes existentes")

    def handle(self, *args, **options):
        products = read_products(options["file"])
        venue = Venue.objects.filter(slug=options["venue_slug"]).first()
        if venue is None:
            raise CommandError("Venue não encontrado; provisionar primeiro (ex.: seed_demo).")

        created = updated = unchanged = skipped = 0
        with transaction.atomic():
            for item in products:
                normalized = item["normalized_name"]
                values = {k: v for k, v in item.items() if k != "normalized_name"}
                existing = Product.objects.select_for_update().filter(
                    venue=venue, normalized_name=normalized,
                ).first()
                if existing is None:
                    created += 1
                    if options["apply"]:
                        Product.objects.create(venue=venue, active=True, **values)
                    continue
                changed_fields = [
                    key for key, value in values.items() if getattr(existing, key) != value
                ]
                if not changed_fields:
                    unchanged += 1
                elif not options["update_existing"]:
                    skipped += 1
                else:
                    updated += 1
                    if options["apply"]:
                        for key in changed_fields:
                            setattr(existing, key, values[key])
                        existing.save(update_fields=changed_fields + ["updated_at"])

        mode = "APLICADO" if options["apply"] else "PREVIEW (sem gravação)"
        self.stdout.write(
            f"{mode} — Venue {venue.slug}: arquivo={len(products)}, "
            f"novos={created}, atualizados={updated}, "
            f"iguais={unchanged}, alterações ignoradas={skipped}."
        )
        if skipped:
            self.stdout.write(
                self.style.WARNING("Existentes divergentes preservados. Revise e use --update-existing se aprovado.")
            )
        if not options["apply"]:
            self.stdout.write("Use --apply para gravar após validar o arquivo e os preços.")
        self.stdout.write("Produtos ausentes no CSV NÃO foram desativados nem removidos.")
