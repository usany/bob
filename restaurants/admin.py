from django.contrib import admin
from restaurants.models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'main', 'side', 'price', 'place')
    list_filter = ('place', 'day', 'meal')
    search_fields = ('id', 'main', 'side', 'place')
    ordering = ('place',)
