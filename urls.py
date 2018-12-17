from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    #path('', views.IndexView.as_view(), name='index'),
    path('', views.index_view, name='index'),
    path('create_job', views.job_create_view, name='create_job'),
    path('create_job_test', views.job_create_view_test, name='create_job_test'),
    path('create_job_entry', views.job_create_select_entrypoint_view, name='create_job_step2'),
    path('create_job_done', views.job_create_done_view, name='create_job_step3'),
    path('<int:id>/', views.job_details_view, name='details_job'),
    path('<int:id>/download_file/<int:file_id>', views.job_details_download_file, name='details_job_download_file'),
    path('<int:id>/download_all_files', views.job_details_download_all_files, name='details_job_download_all_files'),
    path('<int:id>/remove', views.job_remove_view, name='remove_job'),
    path('<int:id>/download_std_out', views.job_download_std_out_view, name='download_std_out'),
    path('login', auth_views.LoginView.as_view(template_name='job_submission/login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(template_name='job_submission/logout.html'), name='logout'),
    path('quick_start', TemplateView.as_view(template_name="job_submission/quick_start.html"), name='quick_start')
]
