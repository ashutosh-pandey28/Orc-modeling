# combustion_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.simulation_input, name='simulation_input'),
    path('results/<int:run_id>/', views.simulation_results, name='simulation_results'),
    path('analysis/', views.analysis_view, name='analysis_view'), 
    path('compare/', views.compare_view, name='compare_view'), 
    path('validation/', views.validation_view, name='validation_view'), 

]