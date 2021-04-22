from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('', include('django.contrib.auth.urls')),
    path('order/new/', views.new_order, name='new_order'),
    path('order/list/', views.order_list, name='order_list'),
    path('register/', views.register, name='register'),
    path('account/edit/', views.edit, name='edit'),
    path('account/dashboard/', views.dashboard, name='dashboard'),
    path('account/fund/', views.add_funds, name='add_funds'),
    path('staff/monitor/', views.profit_monitor, name='profit_monitor')
]
