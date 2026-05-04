from django.shortcuts import render
from .models import MenuItem


def home(request):
    """Home page"""
    return render(request, 'menu/home.html')


def menu_list(request):
    """Display all menu items as a tree structure"""
    root_items = MenuItem.objects.filter(parent=None)
    return render(request, 'menu/menu_list.html', {'menu_items': root_items})


def menu_detail(request, pk):
    """Display details for a specific menu item"""
    menu_item = MenuItem.objects.get(pk=pk)
    return render(request, 'menu/menu_detail.html', {'menu_item': menu_item})
