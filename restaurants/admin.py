from django.contrib import admin
from restaurants.models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'main', 'side', 'price', 'order', 'non_pork')
    list_filter = ('non_pork', 'main', 'side')
    search_fields = ('title', 'main', 'side', 'place')
    ordering = ('order',)
