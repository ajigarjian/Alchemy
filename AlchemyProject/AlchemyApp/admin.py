from django.contrib import admin
from .models import CustomUser, Client, NISTControl, Question, Answer, ControlFamily, InformationCategory, InformationSubCategory

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone_number', 'client', 'is_staff', 'is_active')
    list_filter = ('client', 'is_staff', 'is_active')
    search_fields = ('email', 'client__client_name')

    fieldsets = (
        (None, {'fields': ('email', 'password', 'client')}),
        ('Personal info', {'fields': ('phone_number',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'client', 'phone_number', 'is_staff', 'is_active')
        }),
    )

    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Client)
admin.site.register(NISTControl)
admin.site.register(ControlFamily)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(InformationCategory)
admin.site.register(InformationSubCategory)

