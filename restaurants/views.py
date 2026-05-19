from django.shortcuts import render, get_object_or_404
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
    # root_items = MenuItem.objects.filter(parent=None)
    menu_items = [
        {'id': 1, 'title': '푸른솔 학생식당', 'path': 'ph'},
        {'id': 2, 'title': '푸른솔 교직원식당', 'path': 'pg'},
        {'id': 3, 'title': '청운관 학생식당', 'path': 'ch'},
        {'id': 4, 'title': '청운관 교직원식당', 'path': 'cg'},
        {'id': 5, 'title': '한국외대 인문관 식당', 'path': 'hi'},
        {'id': 6, 'title': '한국외대 교수회관 식당', 'path': 'hg'},
    ]
    return render(request, 'pages/home.html', {'items': menu_items, 'location': 'se'})


def home_gl(request):
    """Home page — GL location"""
    menu_items = [
        {'id': 7, 'title': '학생회관 학생식당', 'path': 'hh'},
        {'id': 8, 'title': '학생회관 교직원식당', 'path': 'hg'},
        {'id': 9, 'title': '제2 식당', 'path': 'jg'},
    ]
    return render(request, 'pages/home.html', {'items': menu_items, 'location': 'gl'})


def menu_list(request, path):
    """Display menu items for the restaurant selected on the home page."""
    # restaurant = get_object_or_404(MenuItem, url=path)
    menu_items = path
    location = 'gl' if request.path.startswith('/gl/') else 'se'
    return render(request, 'pages/menu_list.html', {
        # 'menu_items': menu_items,
        # 'restaurant': restaurant,
        'menu_items': menu_items,
        'location': location,
    })


def menu_detail(request, pathname):
    """Display details for a specific menu item"""
    menu_item = get_object_or_404(MenuItem, url=pathname)
    location = 'gl' if request.path.startswith('/gl/') else 'se'
    return render(request, 'pages/menu_detail.html', {'menu_item': menu_item, 'location': location})


# @staff_member_required
def admin_view(request):
    """Custom admin view for managing menu items"""
    items = MenuItem.objects.all()
    return render(request, 'pages/admin_view.html', {'items': items})
