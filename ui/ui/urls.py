from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('domain_data/', include('domain_data.urls')),
    path('', include('domain_data.urls')),
    path('admin/', admin.site.urls),
]