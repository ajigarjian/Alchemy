from django.urls import path
from . import views
from django.urls import include, path # Added for debugging
from django.conf import settings #Added for debugging
import debug_toolbar

app_name = "alchemy"
urlpatterns = [

    #Front-facing website
    path("", views.index, name="index"),
    path("register", views.register_view, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("contact", views.contact, name="contact"),

    # Public PWC Innovation routes
    path("assess", views.assess, name="assess"),
    path("generate_ai_assessment", views.generate_ai_assessment, name="generate_ai_assessment"),

    #Once logged in - app itself
    path("dashboard", views.dashboard, name="dashboard"),
    path('dashboard/<str:system>', views.dashboard, name='dashboard'),
    path('delete_system', views.delete_system, name='delete_system'),
    path('rename_system', views.rename_system, name='rename_system'),

    #API Calls

    #For the organization overview page
    path("create_update_org", views.create_update_org, name="create_update_org"),

    # For adding functionality to the dropdowns and text areas on the SSP page
    
 ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns