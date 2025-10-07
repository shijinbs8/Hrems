from django.urls import path
from .views import *
urlpatterns=[
     path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('home/', home, name='home'),  # after login redirect
        path('register/',
             register_view, name='register'),
                path('employees/', full_employee_list, name='full_employee_list'),
    path('assign-senior/', assign_senior_to_employee, name='assign_senior_to_employee'),
        path('assign-senior1/', assign_senior_view, name='assign_senior1'),
        path('employees1/', employee_list_view, name='employee_list'),
        path('assign-job/', assign_job, name='assign_job'),
        path('jobs/reassign/<int:job_id>/',reassign_job, name='reassign_job'),
        path('tasks/complete/<int:job_id>/',complete_task, name='complete_task'),
            path('tasks/completed/',completed_and_reassigned_tasks, name='completed_tasks'),
            path('list/',employee_jobs, name='employee_jobs'),
             path('daily-log/',daily_log, name='daily_log'),
                 path('my-daily-logs/',my_daily_logs, name='my_daily_logs'),
                     path('all-employees-pod/',all_employees_pod_status, name='all_employees_pod'),
             path('send-eod/', send_eod_email_view, name='send_eod'),
                 path('profile/', profile_view, name='profile'),
                 path("usage-stats/", usage_stats_view, name="usage_stats"),
                 path('no-permission/',no_permission_view, name='no_permission'),
                     path('edit-daily-log/<int:log_id>/', edit_daily_log, name='edit_daily_log'),
   path('users/', user_list, name='user_list'),
    path('chat/start/<int:user_id>/', start_conversation, name='start_conversation'),
    path('chat/<int:conversation_id>/', chat_view, name='chat_view'),
    path('chat/<int:conversation_id>/send_message/', send_message, name='send_message'),
    path('chat/<int:conversation_id>/get_messages/',get_messages, name='get_messages'),
 # Check unseen messages count
    path('chat/<int:conversation_id>/check_unseen_messages/', check_unseen_messages, name='check_unseen_messages'),

    # Mark messages as seen
    path('chat/<int:conversation_id>/mark_messages_seen/', mark_messages_as_seen, name='mark_messages_as_seen'),













]