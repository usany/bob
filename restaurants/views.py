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
WEEKDAYS = [{'id': 0, 'name': '월', 'day': 'mon'}, {'id': 1, 'name': '화', 'day': 'tue'}, {'id': 2, 'name': '수', 'day': 'wed'}, {'id': 3, 'name': '목', 'day': 'thu'}, {'id': 4, 'name': '금', 'day': 'fri'}]
RESTAURANTS = [
    {'id': 1, 'title': '청운관 학생식당', 'campus': 'se', 'path': 'ch', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['점심']},
    {'id': 2, 'title': '청운관 교직원식당', 'campus': 'se', 'path': 'cg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심']},
    {'id': 3, 'title': '푸른솔 학생식당', 'campus': 'se', 'path': 'ph', 'mealsSemester': ['아침', '점심'], 'mealsVacation': ['아침', '점심']},
    {'id': 4, 'title': '푸른솔 교직원식당', 'campus': 'se', 'path': 'pg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심']},
    {'id': 5, 'title': '한국외대 인문관 식당', 'campus': 'se', 'path': 'hi', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁']},
    {'id': 6, 'title': '한국외대 교수회관 식당', 'campus': 'se', 'path': 'hg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심']},
    {'id': 7, 'title': '학생회관 학생식당', 'campus': 'gl', 'path': 'hh', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁']},
    {'id': 8, 'title': '학생회관 교직원식당', 'campus': 'gl', 'path': 'hg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심']},
    {'id': 9, 'title': '제2기숙사 식당', 'campus': 'gl', 'path': 'jg', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁']},
]
FIXED_MENU = {
 'ch' : [
    {
        'main': '만두라면, 치즈라면', 
        'side': None, 
        'price': 3000, 
        'time_date': None, 
        'time_category': ['아침', '간식'], 
        'time_detail': {'아침': ['09:00', '10:00'], '간식': ['15:00', '16:00']}, 
        'place': '청운관 학생식당', 
        'extra': None, 
        'non_pork': False
    },
    {
        "main": "속풀이라면",
        "side": None,
        "price": 3500,
        "time_date": None,
        "time_category": ["아침"],
        "time_detail": {"아침": ["09:00", "10:00"]},
        "place": "청운관 학생식당",
        "extra": None,
        "non_pork": False
    },
    {
        "main": "공깃밥",
        "side": None,
        "price": 800,
        "time_date": None,
        "time_category": ["아침", "간식"],
        "time_detail": {"아침": ["09:00", "10:00"], "간식": ["15:00", "16:00"]},
        "place": "청운관 학생식당",
        "extra": None,
        "non_pork": False
    },
    {
        "main": "짜계치",
        "side": None,
        "price": 3800,
        "time_date": None,
        "time_category": ["간식"],
        "time_detail": {"간식": ["15:00", "16:00"]},
        "place": "청운관 학생식당",
        "extra": None,
        "non_pork": False
    },
    {
        "main": "콘치즈불닭면",
        "side": None,
        "price": 3800,
        "time_date": None,
        "time_category": ["간식"],
        "time_detail": {"간식": ["15:00", "16:00"]},
        "place": "청운관 학생식당",
        "extra": None,
        "non_pork": False
    }
 ]
}

def _restaurants_for_campus(campus):
    return [r for r in RESTAURANTS if r['campus'] == campus]


def _restaurant_dict_by_path(path):
    for r in RESTAURANTS:
        if r['path'] == path:
            return r
    return None


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
    menu_items = _restaurants_for_campus('se')
    return render(request, 'pages/home.html', {'items': menu_items, 'location': 'se'})


def home_gl(request):
    """Home page — GL location"""
    menu_items = _restaurants_for_campus('gl')
    return render(request, 'pages/home.html', {'items': menu_items, 'location': 'gl'})


def menu_list(request, path):
    """Display menu items for the restaurant selected on the home page."""
    location = 'gl' if request.path.startswith('/gl/') else 'se'
    r = _restaurant_dict_by_path(path)
    title = r['title'] if r else RESTAURANT_TITLES.get(path, path)
    meal_tabs = [{'id': m, 'label': m} for m in (r['mealsSemester'] if r else [])]

    db_restaurant = MenuItem.objects.filter(url=path).first()
    tabs = []
    if db_restaurant:
        for child in db_restaurant.children.all():
            sub_items = list(child.children.all())
            tabs.append({
                'id': child.url,
                'label': child.title,
                'items': sub_items if sub_items else [child],
            })

    if not tabs:
        tabs = [
            {'id': day['day'], 'label': day['name'], 'items': []}
            for day in WEEKDAYS
        ]

    return render(request, 'pages/menu_list.html', {
        'tabs': tabs,
        'restaurant': {'title': title, 'meal_tabs': meal_tabs, 'path': path},
        'location': location,
        'items': {},
        'menu': FIXED_MENU[path]
    })


def menu_detail(request, path, meal):
    """Display details for a specific menu item"""
    # menu_item = get_object_or_404(MenuItem, url=path)
    menu_item = {'title': path, 'meal': meal, 'order': 0}
    location = 'gl' if request.path.startswith('/gl/') else 'se'
    return render(request, 'pages/menu_detail.html', {'menu_item': menu_item, 'location': location})


# @staff_member_required
def admin_view(request):
    """Custom admin view for managing menu items"""
    items = MenuItem.objects.all()
    return render(request, 'pages/admin_view.html', {'items': items})
