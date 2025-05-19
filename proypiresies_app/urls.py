# proypiresies_app/urls.py
from django.urls import path
from . import views

app_name = 'proypiresies_app'

urlpatterns = [
    path('aitiseis/', views.AitisiListView.as_view(), name='aitisi_list'),
    path('aitisi/new/', views.AitisiCreateView.as_view(), name='aitisi_create'),
    # Για τη φόρτωση προϋπηρεσιών σε νέα αίτηση βάσει εκπαιδευτικού:
    path('aitisi/new/for-teacher/', views.AitisiCreateView.as_view(), name='aitisi_create_for_teacher'),
    path('aitisi/<int:pk>/', views.AitisiDetailView.as_view(), name='aitisi_detail'),
    path('aitisi/<int:pk>/edit/', views.AitisiUpdateView.as_view(), name='aitisi_update'),
    path('aitisi/<int:pk>/teliki-egkrisi/', views.aitisi_teliki_egkrisi_pyseep, name='aitisi_teliki_egkrisi'),
    path('report/pyseep/<int:pyseep_id>/xlsx/', views.generate_pyseep_report_xlsx, name='report_pyseep_xlsx'),
    path('report/pyseep/<int:pyseep_id>/pdf/', views.generate_pyseep_report_pdf, name='report_pyseep_pdf'),
]