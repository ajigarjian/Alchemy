from django.urls import path
from . import views

app_name = "alchemy"
urlpatterns = [

   #Front-facing website
   path("", views.index, name="index"),
   path("register", views.register_view, name="register"),
   path("login", views.login_view, name="login"),
   path("logout", views.logout_view, name="logout"),
   path("contact",views.contact, name="contact"),

   #Once logged in - app itself
   path("dashboard/<str:client>", views.dashboard, name="dashboard"),
   path('dashboard/<str:client>/<str:system>', views.dashboard, name='dashboard'),
   path('delete_system', views.delete_system, name='delete_system'),
   path('rename_system', views.rename_system, name='rename_system'),

   path("overview/<str:system>", views.overview, name="overview"),
   path("overview2/<str:system>", views.overview2, name="overview2"),
   path("questions/<str:control_family_name>", views.questions, name="questions"),

   path("implementation/<str:system>/<str:family>", views.implementation, name="implementation"),

    #API Calls
    path("answer", views.answer, name="answer"),
    path('get_answer', views.get_answer, name='get_answer'),
    path("create_update_org", views.create_update_org, name="create_update_org")
 ]