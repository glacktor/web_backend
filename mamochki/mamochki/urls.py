"""
URL configuration for mamochki project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
# from mamochki.app import views
from app.views import JobList, JobDetail,RezumeList,RezumeDetail,RezumeJobDetail,UserView
from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('jobs/', JobList.as_view(), name='job-list'),
    path('jobs/<int:pk>/', JobDetail.as_view(), name='job-detail'),
    path('jobs/<int:pk>/image/', JobDetail.as_view(), name='job-update-image'),
    path('jobs/<int:pk>/draft/', JobDetail.as_view(), name='job-add-to-draft'),
    path('rezumes/', RezumeList.as_view(), name='rezume-list'),
    path('rezumes/<int:pk>/edit/', RezumeDetail.as_view(), name='rezume-detail-edit'),
    path('rezumes/<int:pk>/form/', RezumeDetail.as_view(), name='rezume-detail-form'),
    path('rezumes/<int:pk>/complete/', RezumeDetail.as_view(), name='rezume-detail-complete'),
    path('rezumes/<int:pk>/', RezumeDetail.as_view(), name='rezume-detail'),
    path('fights/<int:rezume_id>/jobs/<int:job_id>/', RezumeJobDetail.as_view(), name='rezume-job-detail'),
    path('users/<str:action>/', UserView.as_view(), name='user-action'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]