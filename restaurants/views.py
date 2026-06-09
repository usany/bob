from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import MenuItem

# RESTAURANT_TITLES = {
#     'ph': '푸른솔 학생식당',
#     'pg': '푸른솔 교직원식당',
#     'ch': '청운관 학생식당',
#     'cg': '청운관 교직원식당',
#     'hi': '한국외대 인문관 식당',
#     'hg': '한국외대 교수회관 식당',
#     'hh': '학생회관 학생식당',
#     'jg': '제2기숙사 식당',
# }
MEALS = [{'id': 0, 'name': '아침', 'time': 'breakfast'}, {'id': 1, 'name': '점심', 'time': 'lunch'}, {'id': 2, 'name': '간식', 'time': 'snack'}, {'id': 3, 'name': '저녁', 'time': 'dinner'}]
WEEKDAYS = [{'id': 0, 'name': '월', 'day': 'mon'}, {'id': 1, 'name': '화', 'day': 'tue'}, {'id': 2, 'name': '수', 'day': 'wed'}, {'id': 3, 'name': '목', 'day': 'thu'}, {'id': 4, 'name': '금', 'day': 'fri'}]
RESTAURANTS = [
    {'id': 1, 'title': '청운관 학생식당', 'campus': 'se', 'path': 'ch', 'mealsSemester': ['아침', '점심', '간식', '저녁'], 'mealsSemesterTime': ['08:30~10:00 (간편식: 09:00~10:00)', '11:00~14:30', '15:00~16:00', '17:00~18:30'], 'mealsVacation': ['점심']},
    {'id': 2, 'title': '청운관 교직원식당', 'campus': 'se', 'path': 'cg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심'], 'mealsSemesterTime': ['11:30~14:00']},
    {'id': 3, 'title': '푸른솔 학생식당', 'campus': 'se', 'path': 'ph', 'mealsSemester': ['아침', '점심'], 'mealsVacation': ['아침', '점심'], 'mealsSemesterTime': ['08:30~10:00 (간편식: 09:00~10:00)', '11:00~14:30']},
    {'id': 4, 'title': '푸른솔 교직원식당', 'campus': 'se', 'path': 'pg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심'], 'mealsSemesterTime': ['11:30~14:00']},
    {'id': 5, 'title': '한국외대 인문관 식당', 'campus': 'se', 'path': 'hi', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁'], 'mealsSemesterTime': ['08:30~10:00 (간편식: 09:00~10:00)', '11:00~14:30', '17:00~18:30']},
    {'id': 6, 'title': '한국외대 교수회관 식당', 'campus': 'se', 'path': 'hg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심'], 'mealsSemesterTime': ['11:30~14:00']},
    {'id': 7, 'title': '학생회관 학생식당', 'campus': 'gl', 'path': 'hh', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁'], 'mealsSemesterTime': ['08:30~10:00 (간편식: 09:00~10:00)', '11:00~14:30', '17:00~18:30']},
    {'id': 8, 'title': '학생회관 교직원식당', 'campus': 'gl', 'path': 'hg', 'mealsSemester': ['점심'], 'mealsVacation': ['점심'], 'mealsSemesterTime': ['11:30~14:00']},
    {'id': 9, 'title': '제2기숙사 식당', 'campus': 'gl', 'path': 'jg', 'mealsSemester': ['아침', '점심', '저녁'], 'mealsVacation': ['아침', '점심', '저녁'], 'mealsSemesterTime': ['08:30~10:00 (간편식: 09:00~10:00)', '11:00~14:30', '17:00~18:30']},
]
FIXED_MENU = {
 'ch' : [
    {
        'main': '만두라면, 치즈라면', 
        'side': None, 
        'price': 3000, 
        'day': None, 
        'time_category': ['아침', '간식'], 
        'time_detail': {'아침': ['09:00', '10:00'], '간식': ['15:00', '16:00']}, 
        'place': 'ch', 
        'extra_menu': None,
        'extra_price': None,
        'non_pork': False,
        'storage_url': ''
    },
    {
        "main": "속풀이라면",
        "side": None,
        "price": 3500,
        "day": None,
        "time_category": ["아침"],
        "time_detail": {"아침": ["09:00", "10:00"]},
        "place": "ch",
        "extra_menu": None,
        "extra_price": None,
        "non_pork": False,
        "storage_url": ''
    },
    {
        "main": "공깃밥",
        "side": None,
        "price": 800,
        "day": None,
        "time_category": ["아침", "간식"],
        "time_detail": {"아침": ["09:00", "10:00"], "간식": ["15:00", "16:00"]},
        "place": "ch", 
        "extra_menu": None,
        "extra_price": None,
        "non_pork": False,
        "storage_url": ''
    },
    {
        "main": "짜계치",
        "side": None,
        "price": 3800,
        "day": None,
        "time_category": ["간식"],
        "time_detail": {"간식": ["15:00", "16:00"]},
        "place": "ch",
        "extra_menu": None,
        "extra_price": None,
        "non_pork": False,
        "storage_url": ''
    },
    {
        "main": "콘치즈불닭면",
        "side": None,
        "price": 3800,
        "day": None,
        "time_category": ["간식"],
        "time_detail": {"간식": ["15:00", "16:00"]},
        "place": "ch",
        "extra_menu": None,
        "extra_price": None,
        "non_pork": False,
        "storage_url": ''
    }
 ]
}

# def _restaurants_for_campus(campus):
#     return [r for r in RESTAURANTS if r['campus'] == campus]


# def _restaurant_dict_by_path(path):
#     for r in RESTAURANTS:
#         if r['path'] == path:
#             return r
#     return None


def root_redirect(request):
    """Redirect to /gl or /se based on localStorage"""
    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
  const lang = localStorage.getItem('base')
  const loc = localStorage.getItem('bases');
  if (lang === 'en') {
    if (loc === 'gl') {
        window.location.replace('en/gl/');
    } else {
        window.location.replace('en/se/');
    }
  } else {
    if (loc === 'gl') {
        window.location.replace('ko/gl/');
    } else {
        window.location.replace('ko/se/');
    }
  }
</script>
</body>
</html>"""
    return HttpResponse(html)


def home_menu(request, base, bases):
    restaurants_items = [r for r in RESTAURANTS if r['campus'] == bases]
    return render(request, 'pages/home.html', {'items': restaurants_items, 'location': bases, 'lang': base, 'base': base, 'bases': bases})
def home(request):
    """Home page — SE location"""
    restaurants_items = [r for r in RESTAURANTS if r['campus'] == 'se']
    return render(request, 'pages/home.html', {'items': restaurants_items, 'location': 'se', 'base': 'ko', 'bases': 'se'})


def home_gl(request):
    """Home page — GL location"""
    restaurants_items = [r for r in RESTAURANTS if r['campus'] == 'gl']
    return render(request, 'pages/home.html', {'items': restaurants_items, 'location': 'gl', 'base': 'ko', 'bases': 'gl'})


def menu_list(request, path, meal=None, base=None, bases=None):
    """Display menu items for the restaurant selected on the home page."""
    # Extract base and bases from URL if they're part of the path
    location = 'gl' if request.path.startswith('/gl/') else 'se'
    r = next(r for r in RESTAURANTS if r['path'] == path)
    title = r['title']
    all_meals = r['mealsSemester']
    weekdays = [d for d in WEEKDAYS if d['day'] == request.GET.get('day', WEEKDAYS[0]['day'])]
    meal_tabs = [
        {
            'id': next(meal['time'] for meal in MEALS if meal['name'] == m),
            'label': m,
            'meal_time': r['mealsSemesterTime'][r['mealsSemester'].index(m)]
        }
        for m in all_meals
    ]

    # State: which meal tab is active — read from GET param, default to first
    selected_meal = request.GET.get('meal', meal_tabs[0]['id'] if meal_tabs else None)
    selected_day = request.GET.get('day', weekdays[0]['day'] if weekdays else None)

    # Only pass dishes for the selected meal into context
    all_dishes = FIXED_MENU.get(path, [])
    filtered_dishes = [
        d for d in all_dishes
        if selected_meal in d.get('time_category', [])
    ] if selected_meal else all_dishes
    db_qs = MenuItem.objects.filter(place=path, meal=selected_meal, day=selected_day)
    filtered_dishes = filtered_dishes + list(db_qs)


    tabs = list(WEEKDAYS)

    return render(request, 'pages/menu_list.html', {
        'tabs': tabs,
        'restaurant': {'title': title, 'meal_tabs': meal_tabs, 'path': path},
        'selected_meal': selected_meal,
        'selected_day': selected_day,
        'location': location,
        'menu': filtered_dishes,
        'base': base or 'ko',
        'bases': bases or location,
        'path': path
    })


def menu_detail(request, path, meal, base=None, bases=None):
    """Display details for a specific menu item"""
    # menu_item = get_object_or_404(MenuItem, url=path)
    # menu_item = {'title': path, 'meal': meal, 'order': 0}
    location = next(r for r in RESTAURANTS if r['path'] == path)['title']
    menu_item = MenuItem.objects.filter(id=meal)[0]
    time = f"{menu_item.date[0:4]}-{menu_item.date[4:6]}-{menu_item.date[6:8]} {menu_item.day} {menu_item.meal}"
    return render(request, 'pages/menu_detail.html', {'menu_item': menu_item, 'image_url': 'https://objectstorage.ap-chuncheon-1.oraclecloud.com/n/ax0ym4amgnfk/b/bucket-20260516-0145/o/'+menu_item.main+'.png', 'location': location, 'time': time, 'base': base or 'ko', 'bases': bases or location, 'path': path, 'meal': meal})


# @staff_member_required
def admin_view(request):
    """Custom admin view for managing menu items"""
    items = MenuItem.objects.all()
    return render(request, 'pages/admin_view.html', {'items': items})
