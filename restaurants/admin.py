from django.contrib import admin
from restaurants.models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'main', 'side', 'price', 'order', 'pork')
    list_filter = ('pork', 'main', 'side')
    search_fields = ('title', 'main', 'side', 'place')
    ordering = ('order',)
