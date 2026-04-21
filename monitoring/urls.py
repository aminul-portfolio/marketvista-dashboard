from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("api/prices/", views.price_data, name="price_data"),

    # Authentication
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="monitoring/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", views.register, name="register"),

    # Project overview
    path(
        "overview/",
        TemplateView.as_view(template_name="monitoring/project_overview.html"),
        name="overview",
    ),

    # Legacy trade / risk routes kept temporarily
    path("trades/", views.TradeListView.as_view(), name="trade_list"),
    path("trades/add/", views.TradeCreateView.as_view(), name="trade_add"),
    path("trades/<int:pk>/edit/", views.TradeUpdateView.as_view(), name="trade_edit"),
    path("trades/<int:pk>/delete/", views.TradeDeleteView.as_view(), name="trade_delete"),
    path("trades/<int:pk>/", views.TradeDetailView.as_view(), name="trade_detail"),
    path("trades/<int:pk>/close/", views.close_trade, name="trade_close"),
    path("trades/export/csv/", views.export_trades_csv, name="export_trades_csv"),
    path("trades/export/excel/", views.export_trades_excel, name="export_trades_excel"),
    path("risk-calculator/", views.unified_risk_calculator, name="unified_risk_calculator"),

    # Alerts
    path("alerts/add/", views.alert_create, name="alert_add"),
    path("alerts/", views.alert_list, name="alert_list"),
    path("alerts/new/", views.create_alert, name="create_alert"),

    # Monitoring APIs
    path("api/ohlc/", views.ohlc_data, name="ohlc_data"),
    path("api/line-price-data/", views.line_price_data, name="line_price_data"),
    path("api/alerts/triggered/", views.triggered_alerts_api, name="triggered_alerts_api"),
    path("prices/export/csv/", views.export_prices_csv, name="export_prices_csv"),
]