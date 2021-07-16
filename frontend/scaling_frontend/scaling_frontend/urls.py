"""scaling_frontend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.urls import path

from create_session.views import home_view
from session.views import session_view, contact_view
from list_sessions.views import list_sessions_view

urlpatterns = [
    path('', home_view, name='home'),
    path('list_sessions/', list_sessions_view, name='list_sessions'),
    path('session/', session_view, name='session'),
    path('contact/', contact_view, name='contact'),
    path('admin/', admin.site.urls),
]
