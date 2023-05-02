from django.contrib import admin
from .models import CustomUser, Client, System, NISTControl, Question, Answer, ControlFamily, InformationCategory, InformationSubCategory

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Client)
admin.site.register(System)
admin.site.register(NISTControl)
admin.site.register(ControlFamily)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(InformationCategory)
admin.site.register(InformationSubCategory)