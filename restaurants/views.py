from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import MenuItem

RESTAURANT_TITLES = {
    'ph': '푸른솔 학생식당',
    'pg': '푸른솔 교직원식당',
    'ch': '청운관 학생식당',
    'cg': '청운관 교직원식당',
    'hi': '한국외대 인문관 식당',
    'hg': '한국외대 교수회관 식당',
    'hh': '학생회관 학생식당',
    'jg': '제2기숙사 식당',
}
MEALS = ['아침', '점심', '저녁']
WEEKDAYS = ['월', '화', '수', '목', '금']
restaurants = [
    {'id': 1, 'title': '푸른솔 학생식당', 'campus': 'se', 'path': 'ph', 'mealsSemester': ['아침', '점심'], 'mealsVacation': ['아침', '점심']},
    {'id': 2, 'title': '푸른솔 교직원식당', 'campus': 'se', 'path': 'pg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심']},
    {'id': 3, 'title': '청운관 학생식당', 'campus': 'se', 'path': 'ch', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['점심']},
    {'id': 4, 'title': '청운관 교직원식당', 'campus': 'se', 'path': 'cg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심']},
    {'id': 5, 'title': '한국외대 인문관 식당', 'campus': 'se', 'path': 'hi', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁']},
    {'id': 6, 'title': '한국외대 교수회관 식당', 'campus': 'se', 'path': 'hg', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁']},
    {'id': 7, 'title': '학생회관 학생식당', 'campus': 'gl', 'path': 'hh', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁']},
    {'id': 8, 'title': '학생회관 교직원식당', 'campus': 'gl', 'path': 'hg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심']},
    {'id': 9, 'title': '제2기숙사 식당', 'campus': 'gl', 'path': 'jg', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁']},
]

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
    menu_items = restaurants.filter(campus='se')
    return render(request, 'pages/home.html', {'items': menu_items, 'location': 'se'})


def home_gl(request):
    """Home page — GL location"""
    menu_items = restaurants.filter(campus='gl')
    return render(request, 'pages/home.html', {'items': menu_items, 'location': 'gl'})


def menu_list(request, path):
    """Display menu items for the restaurant selected on the home page."""
    location = 'gl' if request.path.startswith('/gl/') else 'se'
    restaurant = MenuItem.objects.filter(url=path).first()
    title = restaurant.title if restaurant else RESTAURANT_TITLES.get(path, path)
    mealsTabs = []
    for meal in MEALS:
        mealsTabs.append({
            'id': meal,
            'label': meal,
            'items': [],
        })
    tabs = []
    if restaurant:
        for child in restaurant.children.all():
            sub_items = list(child.children.all())
            tabs.append({
                'id': child.url,
                'label': child.title,
                'items': sub_items if sub_items else [child],
            })

    if not tabs:
        tabs = [
            {'id': f'day-{i}', 'label': day, 'items': []}
            for i, day in enumerate(WEEKDAYS)
        ]

    return render(request, 'pages/menu_list.html', {
        'mealsTabs': mealsTabs,
        'tabs': tabs,
        'restaurant': {'title': title},
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
