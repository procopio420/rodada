from modules.catalog.customization_views import CustomizationView, ChoiceAvailabilityView
from modules.payment_provider.refund_views import IntegratedRefundView, IntegratedRefundReconcileView
from modules.payment_provider.merchant_views import MerchantConnectionView, PaymentDeviceAuthorizationView, MerchantOAuthCallbackView
from modules.payment_provider.views import (PaymentCapabilitiesView, IntegratedPaymentCreateView, IntegratedPaymentDetailView, PaytimeWebhookView, SumUpWebhookView)
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path

from modules.ordering.views import OrderConfirmView, OrderItemTransitionView, ProductionQueueView, TabDetailView, TabListCreateView
from modules.ledger.views import PaymentCollectView, PaymentRefundView, TabCloseView
from modules.house_account.views import (CustomerListView, CustomerDetailView, PolicyView,
    TabLimitOverrideView, TabCustomerView, TabReassessView, TabApprovalRequestView, TabHouseHistoryView)
from modules.corrections.views import (
    CorrectionRefundSettlementView,
    OrderItemCancelView,
    PostProductionCorrectionView,
)
from modules.catalog.views import (ProductAvailabilityView, ProductListView, ProductSuggestView, ProductResolveView, LegacyProductResolveView, ProductEditView, ProductIconManageView, PublishedIconAssetView)
from modules.management.views import CalendarView, ReportView
from modules.cash.views import CashShiftListView
from modules.hospitality.views import (
    OccupancyAssignTabView,
    TableCleaningCompleteView,
    TableCleaningStartView,
    TableGuestOrderingBlockView,
    TableListCreateView,
    TableLocationView,
    TableOccupyView,
    TableReleaseView,
    ZoneListCreateView,
)
from modules.guest_access.views import (
    GuestCatalogView,
    GuestContextView,
    GuestOrderConfirmView,
    GuestQrResolveView,
    GuestTabCreateView,
)
from modules.cash.views import (
    CashCloseView,
    CashCountStartView,
    CashLateCorrectionView,
    CashPointActiveShiftView,
    CashPointCreateView,
    CashPointListView,
    CashReviewView,
    CashShiftDetailView,
    CashShiftOpenView,
    CashSupplyView,
    CashWithdrawalView,
)

from modules.access.views import (
    AccessAuditListView,
    AccessInvalidationFeedView,
    CurrentStaffView,
    DeviceDetailView,
    DeviceListView,
    SessionListView,
    SessionRevokeView,
    StaffMembershipDetailView,
    StaffMembershipListView,
    StaffLockView,
    StaffLoginView,
    StaffLogoutView,
    StaffReauthenticateView,
    StaffRefreshView,
    StaffSwitchOperatorView,
)


def health(request):
    return JsonResponse({"status": "ok"})


def readiness(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ready"})


from modules.tab_operations.views import OperationView, PreviewView, ServicePointView

urlpatterns = [
    path("", include("modules.realtime.urls")),
    path("catalog/products/<uuid:product_id>/customization/", CustomizationView.as_view()),
    path("catalog/products/<uuid:product_id>/customization/<str:kind>/<uuid:choice_id>/availability/", ChoiceAvailabilityView.as_view()),
    path("payments/device-authorizations/", PaymentDeviceAuthorizationView.as_view()),
    path("payments/<uuid:payment_id>/refunds/integrated/", IntegratedRefundView.as_view()),
    path("refunds/<uuid:refund_id>/reconcile/", IntegratedRefundReconcileView.as_view()),
    path("payments/merchant-connections/callback/", MerchantOAuthCallbackView.as_view()),
    path("payments/merchant-connections/", MerchantConnectionView.as_view()),
    path("payments/capabilities/", PaymentCapabilitiesView.as_view()),
    path("tabs/<uuid:tab_id>/payments/integrated/", IntegratedPaymentCreateView.as_view()),
    path("payments/<uuid:payment_id>/integrated/", IntegratedPaymentDetailView.as_view()),
    path("payments/webhooks/sumup/<uuid:venue_id>/", SumUpWebhookView.as_view()),
    path("payments/webhooks/paytime/<uuid:venue_id>/", PaytimeWebhookView.as_view()),
    path("tabs/<uuid:tab_id>/operations/", OperationView.as_view()),
    path("tabs/<uuid:tab_id>/operations/preview/", PreviewView.as_view()),
    path("service-points/", ServicePointView.as_view()),
    path("catalog/products/resolve/", LegacyProductResolveView.as_view()),
    path("cash/shifts/history/", CashShiftListView.as_view()),
    path("management/calendar/", CalendarView.as_view()),
    path("management/reports/", ReportView.as_view()),
    path("health/", health, name="health"),
    path("ready/", readiness, name="readiness"),
    path("auth/login/", StaffLoginView.as_view(), name="staff-login"),
    path("auth/refresh/", StaffRefreshView.as_view(), name="staff-refresh"),
    path("auth/me/", CurrentStaffView.as_view(), name="staff-me"),
    path("auth/lock/", StaffLockView.as_view(), name="staff-lock"),
    path("auth/logout/", StaffLogoutView.as_view(), name="staff-logout"),
    path("auth/switch-operator/", StaffSwitchOperatorView.as_view(), name="staff-switch-operator"),
    path("auth/reauthenticate/", StaffReauthenticateView.as_view(), name="staff-reauthenticate"),
    path("auth/invalidation-events/", AccessInvalidationFeedView.as_view(), name="access-invalidation-events"),
    path("manage/access/memberships/", StaffMembershipListView.as_view(), name="access-memberships"),
    path("manage/access/memberships/<uuid:membership_id>/", StaffMembershipDetailView.as_view(), name="access-membership-detail"),
    path("manage/access/devices/", DeviceListView.as_view(), name="access-devices"),
    path("manage/access/devices/<uuid:device_id>/", DeviceDetailView.as_view(), name="access-device-detail"),
    path("manage/access/sessions/", SessionListView.as_view(), name="access-sessions"),
    path("manage/access/sessions/<uuid:session_id>/revoke/", SessionRevokeView.as_view(), name="access-session-revoke"),
    path("manage/access/audit/", AccessAuditListView.as_view(), name="access-audit"),
    path("tabs/", TabListCreateView.as_view(), name="tab-list-create"),
    path("customers/", CustomerListView.as_view(), name="house-customers"),
    path("customers/<uuid:customer_id>/", CustomerDetailView.as_view(), name="house-customer-detail"),
    path("house-account/policies/", PolicyView.as_view(), name="house-policies"),
    path("tabs/<uuid:tab_id>/limit-override/", TabLimitOverrideView.as_view(), name="tab-limit-override"),
    path("tabs/<uuid:tab_id>/customer/", TabCustomerView.as_view(), name="tab-customer"),
    path("tabs/<uuid:tab_id>/reassess-policy/", TabReassessView.as_view(), name="tab-reassess"),
    path("tabs/<uuid:tab_id>/approval-request/", TabApprovalRequestView.as_view(), name="tab-approval-request"),
    path("tabs/<uuid:tab_id>/house-history/", TabHouseHistoryView.as_view(), name="tab-house-history"),
    path("tabs/<uuid:tab_id>/", TabDetailView.as_view(), name="tab-detail"),
    path("tabs/<uuid:tab_id>/orders/confirm/", OrderConfirmView.as_view(), name="order-confirm"),
    path("tabs/<uuid:tab_id>/payments/", PaymentCollectView.as_view(), name="payment-collect"),
    path("payments/<uuid:payment_id>/refunds/", PaymentRefundView.as_view(), name="payment-refund"),
    path("tabs/<uuid:tab_id>/close/", TabCloseView.as_view(), name="tab-close"),
    path("order-items/<uuid:item_id>/transition/", OrderItemTransitionView.as_view(), name="order-item-transition"),
    path("order-items/<uuid:item_id>/corrections/cancel/", OrderItemCancelView.as_view(), name="order-item-cancel"),
    path("order-items/<uuid:item_id>/corrections/post-production/", PostProductionCorrectionView.as_view(), name="order-item-post-production-correction"),
    path("corrections/<uuid:correction_id>/settle-refund/", CorrectionRefundSettlementView.as_view(), name="correction-settle-refund"),
    path("production/<str:station>/", ProductionQueueView.as_view(), name="production-queue"),
    path("dispatch/", include("modules.dispatch.urls")),
    path("catalog/suggestions/", ProductSuggestView.as_view()),
    path("catalog/resolve-or-create/", ProductResolveView.as_view()),
    path("catalog/products/<uuid:product_id>/", ProductEditView.as_view()),
    path("catalog/products/<uuid:product_id>/icon/", ProductIconManageView.as_view()),
    path("catalog/assets/<uuid:icon_id>/<str:filename>/", PublishedIconAssetView.as_view()),
    path("catalog/products/", ProductListView.as_view(), name="product-list"),
    path("catalog/products/<uuid:product_id>/availability/", ProductAvailabilityView.as_view(), name="product-availability"),
    path("hospitality/tables/", TableListCreateView.as_view(), name="table-list-create"),
    path("hospitality/zones/", ZoneListCreateView.as_view(), name="zone-list-create"),
    path("hospitality/tables/<uuid:table_id>/occupy/", TableOccupyView.as_view(), name="table-occupy"),
    path("hospitality/tables/<uuid:table_id>/location/", TableLocationView.as_view(), name="table-location"),
    path("hospitality/tables/<uuid:table_id>/guest-ordering/", TableGuestOrderingBlockView.as_view(), name="table-guest-ordering"),
    path("hospitality/tables/<uuid:table_id>/release/", TableReleaseView.as_view(), name="table-release"),
    path("hospitality/tables/<uuid:table_id>/cleaning/start/", TableCleaningStartView.as_view(), name="table-cleaning-start"),
    path("hospitality/tables/<uuid:table_id>/cleaning/complete/", TableCleaningCompleteView.as_view(), name="table-cleaning-complete"),
    path("hospitality/occupancies/<uuid:occupancy_id>/tabs/", OccupancyAssignTabView.as_view(), name="occupancy-assign-tab"),
    path("guest/qr/resolve/", GuestQrResolveView.as_view(), name="guest-qr-resolve"),
    path("guest/context/", GuestContextView.as_view(), name="guest-context"),
    path("guest/tabs/", GuestTabCreateView.as_view(), name="guest-tab-create"),
    path("guest/catalog/", GuestCatalogView.as_view(), name="guest-catalog"),
    path("guest/orders/confirm/", GuestOrderConfirmView.as_view(), name="guest-order-confirm"),
    path("cash/points/", CashPointListView.as_view(), name="cash-point-list"),
    path("cash/points/create/", CashPointCreateView.as_view(), name="cash-point-create"),
    path("cash/points/<uuid:cash_point_id>/active-shift/", CashPointActiveShiftView.as_view(), name="cash-point-active-shift"),
    path("cash/shifts/", CashShiftOpenView.as_view(), name="cash-shift-open"),
    path("cash/shifts/<uuid:shift_id>/", CashShiftDetailView.as_view(), name="cash-shift-detail"),
    path("cash/shifts/<uuid:shift_id>/supply/", CashSupplyView.as_view(), name="cash-supply"),
    path("cash/shifts/<uuid:shift_id>/withdrawal/", CashWithdrawalView.as_view(), name="cash-withdrawal"),
    path("cash/shifts/<uuid:shift_id>/count/start/", CashCountStartView.as_view(), name="cash-count-start"),
    path("cash/shifts/<uuid:shift_id>/close/", CashCloseView.as_view(), name="cash-close"),
    path("cash/shifts/<uuid:shift_id>/review/", CashReviewView.as_view(), name="cash-review"),
    path("cash/shifts/<uuid:shift_id>/late-corrections/", CashLateCorrectionView.as_view(), name="cash-late-correction"),
]
