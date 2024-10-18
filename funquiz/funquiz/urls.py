from django.urls import path
from django.contrib import admin
from quize import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:question_id>/', views.detail, name='detail'),
    path('<int:question_id>/results/', views.results, name='results'),
    path('admin/', admin.site.urls)
]