from django.contrib import admin
from .models import MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'order', 'parent')
    list_filter = ('parent',)
    search_fields = ('title', 'url')
    ordering = ('order',)
