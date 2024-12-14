from django.contrib import admin
from ingestion.models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('repo', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('repo', 'record')
    date_hierarchy = 'created_at'
