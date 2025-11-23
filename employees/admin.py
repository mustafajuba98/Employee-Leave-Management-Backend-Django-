from django.contrib import admin
from .models import Employee


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'company_id', 'joining_date', 'created_at']
    list_filter = ['company_id', 'joining_date', 'created_at']
    search_fields = ['name', 'email', 'company_id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'email', 'company_id')
        }),
        ('Additional Information', {
            'fields': ('joining_date',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Employee, EmployeeAdmin)
