from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_expense, name='add_expense'),
    path('list/', views.expense_list, name='expense_list'),
    path('challenges/', views.challenges_view, name='challenges'),
    path('achievements/', views.achievements_view, name='achievements'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('predictions/', views.predictions_view, name='predictions'),
    path('settings/', views.settings_view, name='settings'),
]
