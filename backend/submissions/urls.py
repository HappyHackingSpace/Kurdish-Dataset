from django.urls import path
from . import views

app_name = 'submissions'
urlpatterns = [
    path('', views.submit_pdf, name='submit_pdf'),
    path('preview/<int:pk>/', views.preview_text, name='preview_text'),
    path('thanks/', views.thanks, name='thanks'),
    path('dashboard/requests/', views.admin_request_list, name='admin_request_list'),
    path('dashboard/requests/<int:pk>/', views.admin_request_detail, name='admin_request_detail'),
]