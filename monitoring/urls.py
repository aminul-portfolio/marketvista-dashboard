from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("watchlist/", views.watchlist_page, name="watchlist"),
    path("watchlist/add/<path:symbol>/", views.watchlist_add, name="watchlist_add"),
    path(
        "watchlist/remove/<path:symbol>/",
        views.watchlist_remove,
        name="watchlist_remove",
    ),

    path("signals/", views.signals_page, name="signals"),

    path("assets/", views.asset_list, name="asset_list"),
    path("assets/<path:symbol>/", views.asset_detail, name="asset_detail"),

    path("alerts/", views.alert_list, name="alert_list"),
    path("alerts/new/", views.create_alert, name="create_alert"),
    path("alerts/add/", views.create_alert, name="alert_add"),

    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="monitoring/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", views.register, name="register"),

    path("api/prices/", views.price_data, name="price_data"),
    path("api/ohlc/", views.ohlc_data, name="ohlc_data"),
    path("api/line-price-data/", views.line_price_data, name="line_price_data"),
    path(
        "api/alerts/triggered/",
        views.triggered_alerts_api,
        name="triggered_alerts_api",
    ),

    path("prices/export/csv/", views.export_prices_csv, name="export_prices_csv"),
]