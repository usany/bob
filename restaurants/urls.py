"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('se/', views.home, name='home'),
    path('se/<str:path>/', views.menu_list, name='menu_list_se'),
    path('se/<str:path>/<str:meal>/', views.menu_detail, name='menu_detail_se'),
    path('gl/', views.home_gl, name='home_gl'),
    path('gl/<str:path>/', views.menu_list, name='menu_list_gl'),
    path('gl/<str:path>/<str:meal>/', views.menu_detail, name='menu_detail_gl'),
    path('admin/', admin.site.urls),
    # path('adminpage/', views.admin_view, name='admin_view'),
    # path('pages/', include('pages.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
    # Generic language/campus route - MUST BE LAST to avoid catching other routes
    path('<str:base>/<str:bases>/', views.home_menu, name='home_menu'),
    path('<str:base>/<str:bases>/<str:path>/', views.menu_list, name='home_menu'),
    path('<str:base>/<str:bases>/<str:path>/<str:meal>/', views.menu_detail, name='home_menu'),
]
