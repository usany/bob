from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import MenuItem


def root_redirect(request):
    """Redirect to /gl or /se based on localStorage.location"""
    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
  const loc = localStorage.getItem('location');
  if (loc === 'gl') {
    window.location.replace('/gl');
  } else {
    window.location.replace('/se');
  }
</script>
</body>
</html>"""
    return HttpResponse(html)


def home(request):
    """Home page — SE location"""
    root_items = MenuItem.objects.filter(parent=None)
    menu_items = [
        {'id': 1, 'title': '푸른솔 학생식당', 'url': '1'},
        {'id': 2, 'title': '푸른솔 교직원식당', 'url': '2'},
        {'id': 3, 'title': '청운관 학생식당', 'url': '3'},
        {'id': 4, 'title': '청운관 교직원식당', 'url': '4'},
        {'id': 5, 'title': '한국외대 인문관 식당', 'url': '5'},
        {'id': 6, 'title': '한국외대 교수회관 식당', 'url': '6'},
    ]
    return render(request, 'pages/home.html', {'menu_items': root_items, 'items': menu_items})


def home_gl(request):
    """Home page — GL location"""
    menu_items = [
        {'id': 7, 'title': '학생회관 학생식당', 'url': '7'},
        {'id': 8, 'title': '학생회관 교직원식당', 'url': '8'},
        {'id': 9, 'title': '제2 식당', 'url': '9'},
    ]
    return render(request, 'pages/home.html', {'items': menu_items})


def menu_list(request):
    """Display all menu items as a tree structure"""
    root_items = MenuItem.objects.filter(parent=None)
    return render(request, 'pages/menu_list.html', {'menu_items': root_items})


def menu_detail(request, pk):
    """Display details for a specific menu item"""
    menu_item = MenuItem.objects.get(pk=pk)
    return render(request, 'pages/menu_detail.html', {'menu_item': menu_item})


# @staff_member_required
def admin_view(request):
    """Custom admin view for managing menu items"""
    items = MenuItem.objects.all()
    return render(request, 'pages/admin_view.html', {'items': items})
