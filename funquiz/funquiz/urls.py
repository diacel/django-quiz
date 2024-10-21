from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('quize.urls')),
    path('admin/', admin.site.urls),
]