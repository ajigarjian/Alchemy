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
   path("overview", views.overview, name="overview"),
   path("questions/<str:control_family_name>", views.questions, name="questions"),

    #API Calls
    path("answer", views.answer, name="answer"),
    path('get_answer', views.get_answer, name='get_answer'),
    path("create_update_org", views.create_update_org, name="create_update_org")
 ]