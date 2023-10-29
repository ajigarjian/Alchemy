from django.contrib import admin
from django.db import connection
from .models import CustomUser, Client, System, NISTControl, NISTControlElement, ControlImplementationStatement, Question, Answer, ControlFamily, InformationCategory, InformationSubCategory, ControlImplementation, ImplementationStatus, ControlOrigination, ResponsibleRole

def delete_selected_custom_users(modeladmin, request, queryset):
    for custom_user in queryset:
        custom_user.delete()
        
        # Print foreign key constraints
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_key_list(AlchemyApp_customuser);')
            foreign_key_constraints = cursor.fetchall()
            print('Foreign key constraints:', foreign_key_constraints)
            
delete_selected_custom_users.short_description = "Delete selected CustomUsers"

class CustomUserAdmin(admin.ModelAdmin):
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            actions['delete_selected'] = (delete_selected_custom_users, 'delete_selected', delete_selected_custom_users.short_description)
        return actions

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Client)
admin.site.register(System)
admin.site.register(NISTControl)
admin.site.register(NISTControlElement)
admin.site.register(ControlImplementationStatement)
admin.site.register(ControlFamily)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(InformationCategory)
admin.site.register(InformationSubCategory)
admin.site.register(ControlImplementation)
admin.site.register(ImplementationStatus)
admin.site.register(ControlOrigination)
admin.site.register(ResponsibleRole)

