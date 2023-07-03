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
    path("FedRAMP/<str:control>", views.fedramp, name="fedramp"),

    # Public PWC Innovation routes
    path("assess", views.assess, name="assess"),
    path("generate_ai_assessment", views.generate_ai_assessment, name="generate_ai_assessment"),

    #Once logged in - app itself
    path("dashboard", views.dashboard, name="dashboard"),
    path('dashboard/<str:system>', views.dashboard, name='dashboard'),
    path('delete_system', views.delete_system, name='delete_system'),
    path('rename_system', views.rename_system, name='rename_system'),

    #For the graphs and SSP generation on the system dashboard page
    path('generate_ssp', views.generate_ssp, name='generate_ssp'),
    path('get_control_origination_data', views.get_control_origination_data, name='get_control_origination_data'),
    path('get_status_data', views.get_status_data, name='get_status_data'),
    path('get_implementation_family_data', views.get_implementation_family_data, name='get_implementation_family_data'),
    path('get_origination_data', views.get_origination_data, name='get_origination_data'),

    path("overview/<str:system>", views.overview, name="overview"),
    path("overview2/<str:system>", views.overview2, name="overview2"),
    path("questions/<str:control_family_name>", views.questions, name="questions"),

    path('implementation/<str:system>/<str:control_family>/', views.implementation, name='implementation'),

    #API Calls

    #For the organization overview page
    path("answer", views.answer, name="answer"),
    path('get_answer', views.get_answer, name='get_answer'),
    path("create_update_org", views.create_update_org, name="create_update_org"),

    # For adding functionality to the dropdowns and text areas on the SSP page
    path("update_implementation_status", views.update_implementation_status, name="update_implementation_status"),
    path("update_origination_status", views.update_origination_status, name="update_origination_status"),
    path("update_responsible_role", views.update_responsible_role, name="update_responsible_role"),
    path("add_role", views.add_role, name="add_role"),
    path("save_control_text", views.save_control_text, name="save_control_text"),
    path("generate_ai_statement", views.generate_ai_statement, name="generate_ai_statement"),

    path('api/get_roles/', views.get_roles, name='get_roles'),
    path('api/get_originations/', views.get_originations, name='get_originations'),
    
 ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns