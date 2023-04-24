from django.urls import path
from . import views

app_name = "alchemy"
urlpatterns = [
     path("", views.index, name="index"),
     path("overview", views.overview, name="overview"),
     path("questions/<str:control_family_name>", views.questions, name="questions"),

    #API Calls
    path("answer", views.answer, name="answer"),
    path('get_answer/', views.get_answer, name='get_answer'),
 ]