from rest_framework import serializers
from catalog.models import Product
from ledger.models import Adjustment, Payment
from pos.models import Order, OrderItem, ServicePoint, Tab
from pos.services import exposure_cents
from django.db.models import Sum


class ProductSerializer(serializers.ModelSerializer):
    icon_key = serializers.CharField(source="canonical_item.icon_key", read_only=True)
    class Meta: model = Product; fields = ["id", "name", "description", "active", "available", "current_price_cents", "fulfillment_station", "icon_key"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta: model = OrderItem; fields = ["id", "product", "product_name", "quantity", "unit_price_cents", "fulfillment_station", "state", "created_at", "accepted_at", "preparing_at", "ready_at", "picked_up_at", "delivered_at", "cancelled_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta: model = Order; fields = ["id", "tab", "status", "created_at", "confirmed_at", "items"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta: model = Payment; fields = ["id", "amount_cents", "method", "status", "created_at", "confirmed_at"]


class AdjustmentSerializer(serializers.ModelSerializer):
    class Meta: model = Adjustment; fields = ["id", "amount_cents", "type", "reason", "created_at"]


class TabSerializer(serializers.ModelSerializer):
    exposure_cents = serializers.SerializerMethodField()
    charges_cents = serializers.SerializerMethodField()
    payments_cents = serializers.SerializerMethodField()
    service_point_code = serializers.CharField(source="service_point.code", read_only=True)
    orders = OrderSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    adjustments = AdjustmentSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.display_name", read_only=True)
    relationship = serializers.SerializerMethodField()
    class Meta: model = Tab; fields = ["id", "venue", "customer", "customer_name", "relationship", "label", "status", "service_point", "service_point_code", "operating_limit_cents", "limit_overridden_at", "opened_at", "closed_at", "charges_cents", "payments_cents", "exposure_cents", "orders", "payments", "adjustments"]
    def get_exposure_cents(self, obj): return exposure_cents(obj)
    def get_charges_cents(self, obj): return obj.charges.aggregate(total=Sum("amount_cents"))["total"] or 0
    def get_payments_cents(self, obj): return obj.payments.filter(status=Payment.Status.CONFIRMED).aggregate(total=Sum("amount_cents"))["total"] or 0
    def get_relationship(self, obj):
        if not obj.customer_id: return None
        relationship = obj.customer.relationships.filter(venue_id=obj.venue_id).first()
        return relationship.status if relationship else None
