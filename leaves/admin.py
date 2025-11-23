from django.contrib import admin
from .models import LeaveRequest


class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date', 'created_at']
    search_fields = ['employee__name', 'employee__email']
    readonly_fields = ['created_at', 'updated_at', 'approval_date']
    fieldsets = (
        ('Leave Information', {
            'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'status')
        }),
        ('Approval Information', {
            'fields': ('approval_date',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'approved' and not obj.approval_date:
            from django.utils import timezone
            obj.approval_date = timezone.now()
        super().save_model(request, obj, form, change)


admin.site.register(LeaveRequest, LeaveRequestAdmin)
