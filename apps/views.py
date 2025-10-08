from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required



from apps.decorators import superuser_or_senior_required
def login_view(request):
    if request.method == 'POST':
        username_or_empid = request.POST.get('username')
        password = request.POST.get('password')

        user = None

        # 1. First check if username_or_empid is employee_id
        try:
            emp_profile = EmployeeProfile.objects.get(employee_id=username_or_empid)
            user = authenticate(request, username=emp_profile.user.username, password=password)
        except EmployeeProfile.DoesNotExist:
            # 2. If not employee_id, try with username
            user = authenticate(request, username=username_or_empid, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {
                'error': 'Invalid Username/Employee ID or Password'
            })

    return render(request, 'login.html')
def logout_view(request):
    logout(request)
    return redirect('login')
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import EmployeeProfile, JobAssignment, DailyLog
@login_required
def home(request):
    user = request.user
    employee = EmployeeProfile.objects.filter(user=user).first()

    # Jobs
    completed_jobs = JobAssignment.objects.filter(
        assigned_to=employee, is_completed=True
    ).order_by('-due_date')
    jobs = JobAssignment.objects.filter(
        assigned_to=employee, is_completed=False
    ).order_by('due_date')

    # Daily log for today
    today = date.today()
    try:
        log, created = DailyLog.objects.get_or_create(employee=employee, date=today)
    except Exception as e:
        log, created = None, False
        print(f"Error fetching/creating log: {e}")

    # All jobs for dropdown (only active ones)
    try:
        assignments = JobAssignment.objects.filter(
            assigned_to=employee, is_completed=False
        )
    except Exception as e:
        assignments = []
        print(f"Error fetching assignments: {e}")

    if request.method == "POST" and log:
        try:
            # If POD is not yet submitted, update POD + job
            if not log.pod:
                log.pod = request.POST.get("pod", "")
                related_assignment_id = request.POST.get("related_assignment")
                if related_assignment_id:
                    log.related_assignment = get_object_or_404(
                        JobAssignment, id=related_assignment_id
                    )
                log.save()

            # If POD is already submitted and EOD is not, allow EOD submission
            if log.pod and not log.eod:
                log.eod = request.POST.get("eod", "")
                log.is_eod_submitted = True
                log.save()
        except Exception as e:
            print(f"Error processing POST data: {e}")

        return redirect('home')

    context = {
        'user': user,
        'employee': employee,
        'total_employees': EmployeeProfile.objects.count(),
        'employee_list': EmployeeProfile.objects.select_related('user').all(),
        'jobs': jobs,
        'completed_jobs': completed_jobs,
        'assignments': assignments,
        'log': log,  # Pass the daily log object (may be None if error)
    }
    return render(request, 'home.html', context)


from django.contrib.auth.models import User

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db.models import Max
from django.contrib.auth.models import User
from .models import EmployeeProfile
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_welcome_email(user, emp_profile):
    subject = "Welcome to Jezt AI!"
    from_email = "noreply@jeztai.com"
    to_email = user.email

    # Render HTML content
    html_content = render_to_string("welcome_email.html", {
        "username": user.username,
        "employee_id": emp_profile.employee_id,
        "department": emp_profile.department,
        "position": emp_profile.position,
        "company": "Jezt AI"
    })

    # Plain text fallback
    text_content = f"""
    Hi {user.username},

    Welcome to Jezt AI!

    Your Employee ID is: {emp_profile.employee_id}
    Department: {emp_profile.department}
    Position: {emp_profile.position}

    We are excited to have you on board.

    Regards,
    Jezt AI Team
    """

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


def generate_employee_id():
    """
    Generate next employee ID in format 0001, 0002, etc.
    Looks at the latest created EmployeeProfile.
    """
    last_id = EmployeeProfile.objects.aggregate(max_id=Max("employee_id"))["max_id"]
    if last_id:
        new_id = int(last_id) + 1
    else:
        new_id = 1
    return str(new_id).zfill(4)  # pad with zeros (e.g., 0001)

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        email = request.POST.get('email').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        department = request.POST.get('department')
        position = request.POST.get('position')

        # ✅ Validation
        if not username or not email or not password1 or not password2:
            return render(request, 'register.html', {'error': 'All fields are required.'})

        if password1 != password2:
            return render(request, 'register.html', {'error': 'Passwords do not match.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already exists.'})

        # ✅ Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        # ✅ Generate unique employee_id
        emp_id = generate_employee_id()

        # ✅ Create employee profile
        emp_profile = EmployeeProfile.objects.create(
            user=user,
            department=department,
            position=position,
            senior=None,
            employee_id=emp_id
        )
        emp_profile.save()
        send_welcome_email(user, emp_profile)
        # ✅ Auto login
        login(request, user)
        return redirect('home')

    return render(request, 'register.html')

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import EmployeeProfile, JobAssignment

# Decorator to allow only superusers
def superuser_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_superuser)(view_func)
    return decorated_view_func

@superuser_required
def full_employee_list(request):
    employees = EmployeeProfile.objects.all().select_related('user', 'senior')
    return render(request, 'full_employee_list.html', {'employees': employees})

@superuser_required
def assign_senior_to_employee(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        senior_id = request.POST.get('senior_id')

        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        senior = get_object_or_404(EmployeeProfile, id=senior_id)

        employee.senior = senior
        employee.save()
        return redirect('full_employee_list')

    employees = EmployeeProfile.objects.all()
    seniors = EmployeeProfile.objects.filter(position__icontains='Senior')
    return render(request, 'assign_senior.html', {'employees': employees, 'seniors': seniors})

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import EmployeeProfile

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@superuser_required
def assign_senior_view(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        senior_id = request.POST.get('senior_id')

        employee = get_object_or_404(EmployeeProfile, id=employee_id)
        # Allow senior to be None (blank) to remove assignment
        senior = EmployeeProfile.objects.filter(id=senior_id).first() if senior_id else None

        # Prevent circular assignment (optional)
        if senior and senior == employee:
            error = "An employee cannot be their own senior."
            employees = EmployeeProfile.objects.all()
            seniors = employees.filter(position__icontains='Senior')
            return render(request, 'assign_senior.html', {'employees': employees, 'seniors': seniors, 'error': error})

        employee.senior = senior
        employee.save()
        return redirect('full_employee_list')

    employees = EmployeeProfile.objects.all()
    seniors = employees.filter(position__icontains='Senior')
    return render(request, 'assign_senior1.html', {'employees': employees, 'seniors': seniors})



def employee_list_view(request):
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        is_senior = request.POST.get('is_senior') == 'on'
        employee = get_object_or_404(EmployeeProfile, id=emp_id)
        employee.is_senior = is_senior
        employee.save()
        return redirect('employee_list')

    employee_list = EmployeeProfile.objects.select_related('user').all()
    return render(request, 'employee_list.html', {'employee_list': employee_list})

from django.shortcuts import render, redirect, get_object_or_404

from .models import EmployeeProfile, JobAssignment
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import EmployeeProfile, JobAssignment


@login_required
@superuser_or_senior_required
def assign_job(request):
    user = request.user
    is_superuser = user.is_superuser

    # handle parent_job if passed in querystring (for reassignment/sub-task)
    parent_job = None
    parent_job_id = request.GET.get("parent_job")
    if parent_job_id:
        parent_job = get_object_or_404(JobAssignment, id=parent_job_id)

    if is_superuser:
        # Superuser (HR) can assign job with or without assigning employee
        assignees = EmployeeProfile.objects.filter(is_senior=True)
        assigners = EmployeeProfile.objects.filter(is_senior=True)
    else:
        # Normal seniors can only assign jobs to their juniors
        assigners = EmployeeProfile.objects.filter(user=user)
        if not assigners.exists():
            return redirect('assign_job')  # or an error page
        assignees = EmployeeProfile.objects.all().exclude(user=user)

    if request.method == 'POST':
        assigned_to_id = request.POST.get('assigned_to')
        assigned_by_id = request.POST.get('assigned_by') if is_superuser else assigners.first().id
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        parent_job_id = request.POST.get('parent_job')  # from hidden field

        # Optional assigned_to: may be None or empty
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(EmployeeProfile, id=assigned_to_id)

        assigned_by = get_object_or_404(EmployeeProfile, id=assigned_by_id)

        parent_job = None
        if parent_job_id:
            parent_job = get_object_or_404(JobAssignment, id=parent_job_id)

        JobAssignment.objects.create(
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            parent_job=parent_job,   # ✅ store parent if any
            description=description,
            due_date=due_date
        )
        return redirect('assign_job')
    
    return render(request, 'assign_job.html', {
        'assignees': assignees,
        'assigners': assigners,
        'is_superuser': is_superuser,
        'parent_job': parent_job,   # ✅ safe: always defined
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import EmployeeProfile, JobAssignment

@login_required
def reassign_job(request, job_id):
    user = request.user
    try:
        senior_profile = EmployeeProfile.objects.get(user=user, is_senior=True)
    except EmployeeProfile.DoesNotExist:
        return redirect('dashboard')  # User is not senior or profile missing

    job = get_object_or_404(JobAssignment, id=job_id, assigned_to=senior_profile)

    juniors = EmployeeProfile.objects.filter(senior=senior_profile)

    if request.method == 'POST':
        new_assigned_to_id = request.POST.get('assigned_to')
        new_assigned_to = get_object_or_404(EmployeeProfile, id=new_assigned_to_id)

        # Create a new job assignment delegated to junior
        JobAssignment.objects.create(
            assigned_to=new_assigned_to,
            assigned_by=senior_profile,
            description=job.description,
            due_date=job.due_date
        )

        # Optionally mark original job completed or update status as delegated
        job.is_completed = True
        job.save()

        return redirect('dashboard')

    return render(request, 'reassign_job.html', {
        'job': job,
        'juniors': juniors,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import EmployeeProfile, JobAssignment
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
@login_required
def reassign_job(request, job_id):
    print('reassign_job called with job_id:', job_id)
    user = request.user
    senior_profile = EmployeeProfile.objects.filter(user=user, is_senior=True).first()


    # Ensure the senior is the one managing this job
    job = get_object_or_404(JobAssignment, id=job_id)
 
    if request.method == 'POST':
        new_assigned_to_id = request.POST.get('assigned_to')
        new_assigned_to = get_object_or_404(EmployeeProfile, id=new_assigned_to_id)
        print("Reassigning job", job.id, "from", job.assigned_to, "to", new_assigned_to)
        # ✅ Log the reassignment in history
        AssignmentHistory.objects.create(
            job=job,
            from_employee=job.assigned_to,
            to_employee=new_assigned_to,
            action_by=senior_profile,
            action="reassigned"
        )

        # ✅ Update current job
        job.assigned_to = new_assigned_to
        job.save()

        return redirect('home')

    return redirect('home')

from django.utils import timezone

@login_required
def complete_task(request, job_id):
    user = request.user
    employee_profile = EmployeeProfile.objects.filter(user=user).first()

    job = get_object_or_404(JobAssignment, id=job_id, assigned_to=employee_profile)

    if request.method == 'POST':
        job.is_completed = True
        job.completion_date = timezone.now().date()
        job.save()

        # Log completion in history
        AssignmentHistory.objects.create(
            job=job,
            from_employee=job.assigned_by,   # who originally assigned THIS job
            to_employee=employee_profile,    # who completed THIS job
            action_by=employee_profile,
            action="completed"
        )

        return redirect('home')

    return redirect('home')

def completed_tasks_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    employee = EmployeeProfile.objects.filter(user=user).first()
    completed_jobs = JobAssignment.objects.filter(assigned_to=employee, is_completed=True).order_by('-due_date')

    # Build a dictionary: {job: [chain]}
    jobs_with_chain = []
    for job in completed_jobs:
        # Walk up the parent_job chain
        chain = []
        current = job
        while current:
            chain.insert(0, current)  # insert at beginning to reverse order (origin → last)
            current = current.parent_job if hasattr(current, 'parent_job') else None
        jobs_with_chain.append({
            'final_job': job,
            'chain': chain,
        })

    context = {
        'jobs_with_chain': jobs_with_chain,
    }
    return render(request, 'completed_tasks.html', context)

@login_required
def completed_and_reassigned_tasks(request):
    user = request.user
    employee = EmployeeProfile.objects.filter(user=user).first()

    # Completed tasks assigned directly to the employee
    completed_tasks = JobAssignment.objects.filter(
        assigned_to=employee,
        is_completed=True,is_resigned=False
    ).order_by('-due_date')

    # Tasks reassigned to this employee via JobReassignment
    reassigned_tasks = JobAssignment.objects.filter(
        reassignments__to_employee=employee
    ).distinct().order_by('-due_date')

    context = {
        'completed_tasks': completed_tasks,
        'reassigned_tasks': reassigned_tasks,
    }

    return render(request, 'completed_tasks.html', context)




@login_required
def assigned_jobs(request):
    user = request.user
    employee = EmployeeProfile.objects.filter(user=user).first()

    # Completed tasks assigned directly to the employee
    tasks = JobAssignment.objects.filter(
        assigned_by=employee,
        is_resigned=False
    ).order_by('-due_date')

    # Tasks reassigned to this employee via JobReassignment
    reassigned_tasks = JobAssignment.objects.filter(
        reassignments__reassigned_by=employee
    ).distinct().order_by('-due_date')

    context = {
        'completed_tasks': tasks,
        'reassigned_tasks': reassigned_tasks,
    }

    return render(request, 'tasks.html', context)



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import EmployeeProfile, JobAssignment, AssignmentHistory

@login_required
def employee_jobs(request):
    # Get employee profile
    employee_user = request.user
    employee = get_object_or_404(EmployeeProfile, user=employee_user)
    print("Employee:", employee)
    # All jobs where this employee is the current assignee
  
    # Completed jobs by this employee
    completed_jobs = JobAssignment.objects.filter(
        assigned_to=employee, 
    ).order_by("-completion_date")

    # Reassigned jobs involving this employee (either gave or received)
    created_jobs = JobAssignment.objects.filter(
        assigned_by=employee
    ).order_by("-date_assigned")

    # Jobs this employee reassigned to someone else
    reassigned_jobs = AssignmentHistory.objects.filter(

        from_employee=employee  # only reassignments done by this employee
    ).order_by("-timestamp")
     # Prepare context
    context = {
        "employee": employee,
       
        "completed_jobs": completed_jobs,
        "created_jobs": created_jobs,
        "reassigned_jobs": reassigned_jobs
    }
    return render(request, "employee_jobs.html", context)




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import DailyLog, EmployeeProfile, JobAssignment

@login_required
def daily_log(request):
    user = request.user
    employee = get_object_or_404(EmployeeProfile, user=user)

    # Check if a log already exists for today
    today = date.today()
    log, created = DailyLog.objects.get_or_create(employee=employee, date=today)

    # Get all jobs assigned to this employee (optional for dropdown)
    assignments = JobAssignment.objects.filter(assigned_to=employee, is_completed=False)

    if request.method == "POST":
        log.pod = request.POST.get("pod", "")
        
        log.eod = request.POST.get("eod", "")
        
        related_assignment_id = request.POST.get("related_assignment")
        if related_assignment_id:
            log.related_assignment = get_object_or_404(JobAssignment, id=related_assignment_id)
        else:
            log.related_assignment = None

        log.is_eod_submitted = True  # mark submitted
        log.save()

        return redirect('daily_log')  # reload page or redirect to dashboard

    return render(request, "daily_log.html", {
        "log": log,
        "assignments": assignments,
    })



@login_required
def my_daily_logs(request):
    user = request.user
    employee = EmployeeProfile.objects.get(user=user)
    
    # Fetch all logs for this employee, latest first
    logs = DailyLog.objects.filter(employee=employee).order_by('-date')

    context = {
        "logs": logs
    }
    return render(request, "my_daily_logs.html", context)
from collections import defaultdict

@login_required
@superuser_or_senior_required
def all_employees_pod_status(request):
    # Fetch all logs, select related employee and user for efficiency
    logs = DailyLog.objects.select_related('employee', 'employee__user').order_by('-date', 'employee__user__username')

    # Group logs by date
    logs_by_date = defaultdict(list)
    for log in logs:
        logs_by_date[log.date].append(log)

    context = {
        "logs_by_date": dict(logs_by_date)
    }
    return render(request, "all_employees_pod.html", context)

from django.shortcuts import HttpResponse
from django.core.mail import send_mail

def send_eod_email_reminders():
    """
    Sends EOD reminder emails to all employees.
    """
    subject = "⏰ Reminder: Submit your POD and Eod Report"
    message = "Please don’t forget to submit your POD and EOD report!"
    from_email = "jezttechai@gmail.com"

    employees = EmployeeProfile.objects.all()
    for emp in employees:
        if emp.user.email:
            send_mail(subject, message, from_email, [emp.user.email])


from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def send_eod_email_view(request):
    """
    Manually trigger EOD emails (only accessible by staff/admins).
    """
    send_eod_email_reminders()
    return HttpResponse("EOD reminder emails sent successfully!")



@login_required
def profile_view(request):
    profile = EmployeeProfile.objects.get(user=request.user)

    if request.method == 'POST':
        department = request.POST.get('department')
        position = request.POST.get('position')
        if 'profile_image' in request.FILES:
            profile.img = request.FILES['profile_image']
            
        
        profile.department = department
        profile.position = position
        
        profile.save()  # save all changes including the image

        return render(request, 'profile.html', {
            'profile': profile,
            'success': 'Profile updated successfully!'
        })

    return render(request, 'profile.html', {'profile': profile})



from collections import Counter, defaultdict

def parse_usage_log(file_path="url_usage_log.txt"):
    feature_usage = Counter()
    user_usage = defaultdict(Counter)

    with open(file_path, "r") as f:
        for line in f:
            try:
                _, user_part, method, path = line.strip().split(" - ")
                user_id = user_part.split(" ")[0].replace("User:", "")
                feature_usage[path] += 1
                user_usage[user_id][path] += 1
            except ValueError:
                continue  # skip malformed lines

    return feature_usage, user_usage



from django.shortcuts import render


def usage_stats_view(request):
    feature_usage, user_usage = parse_usage_log()

    return render(request, "usage_stats.html", {
        "feature_usage": dict(feature_usage),
        "user_usage": {k: dict(v) for k, v in user_usage.items()},
    })


def no_permission_view(request):
    return render(request, 'no_permission.html')



from django.contrib import messages

@login_required
def edit_daily_log(request, log_id):
    user = request.user
    employee = EmployeeProfile.objects.get(user=user)
    log = get_object_or_404(DailyLog, id=log_id, employee=employee)

    # Restrict edits after 2 hours
    if not log.can_edit():
        messages.error(request, "You can only edit this log within 2 hours of creation.")
        return redirect('my_daily_logs')

    if request.method == 'POST':
        pod = request.POST.get('pod')
        eod = request.POST.get('eod')

        log.pod = pod
        log.eod = eod
        log.save()

        messages.success(request, "Log updated successfully!")
        return redirect('my_daily_logs')

    return render(request, "edit_daily_log.html", {"log": log})





from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Conversation, Message, EmployeeProfile


@login_required
def user_list(request):
    """
    List all users you can chat with (exclude yourself).
    """
    users = User.objects.exclude(id=request.user.id)
    return render(request, "user_list.html", {"users": users})


@login_required
def chat_view(request, conversation_id):
    """
    Display chat messages for a specific conversation.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    # Security check: user must be participant
    if request.user not in conversation.participants.all():
        return redirect('user_list')

    messages = conversation.messages.order_by('timestamp')
    return render(request, "chat_view.html", {
        "conversation": conversation,
        "messages": messages
    })

@login_required
def send_message(request, conversation_id):
    if request.method == "POST":
        conversation = get_object_or_404(Conversation, id=conversation_id)
        employee_profile = EmployeeProfile.objects.get(user=request.user)
        if employee_profile not in conversation.participants.all():
            return JsonResponse({"error": "Unauthorized"}, status=403)

        text = request.POST.get("text", "").strip()
        if text:
            msg = Message.objects.create(conversation=conversation, sender=employee_profile, message=text)
            return JsonResponse({
                "id": msg.id,
                "sender": msg.sender.user.username,
                "text": msg.message,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        return JsonResponse({"error": "Empty message"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=400)


from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator



@login_required
@csrf_exempt
def get_messages(request, conversation_id):
    """
    Return all messages for polling via AJAX.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user.employeeprofile not in conversation.participants.all():
        return JsonResponse({"error": "Unauthorized"}, status=403)

    messages = conversation.messages.order_by('timestamp')
    data = [{
        "id": msg.id,
        "sender": msg.sender.user.username,
        "text": msg.message,
        "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for msg in messages]

    return JsonResponse({"messages": data})


@login_required
def start_conversation(request, user_id):
    me = get_object_or_404(EmployeeProfile, user=request.user)
    other_user = get_object_or_404(EmployeeProfile, user__id=user_id)

    conv = Conversation.objects.filter(participants=me).filter(participants=other_user).first()

    if not conv:
        conv = Conversation.objects.create()
        conv.participants.add(me, other_user)

    messages = conv.messages.order_by('timestamp')

    # Get the other participant to show in the template title
    other_participant = conv.participants.exclude(id=me.id).first()

    return render(request, 'chat_view.html', {
        'conversation': conv,
        'messages': messages,
        'other_participant': other_participant,
    })


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message

@login_required
def check_unseen_messages(request, conversation_id):
    user_profile = request.user.employeeprofile
    count = Message.objects.filter(
        conversation_id=conversation_id,
        sender=user_profile,
        is_seen=False
    ).count()
    return JsonResponse({'unseen_count': count})

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # or handle CSRF as per your setup
@login_required
def mark_messages_as_seen(request, conversation_id):
    if request.method == 'POST':
        user_profile = request.user.employeeprofile
        # mark messages as seen where sender is NOT the current user
        Message.objects.filter(
            conversation_id=conversation_id,
            is_seen=False
        ).exclude(sender=user_profile).update(is_seen=True)
        
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'POST method required'}, status=400)
    

    from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden
from .models import EmployeeVaultFile
from .forms import VaultFileForm


@login_required
def vault_list(request):
    profile = request.user.employeeprofile
    # Combine files owned by the user and shared with the user
    files = EmployeeVaultFile.objects.filter(owner=profile) | profile.shared_vault_files.all()
    return render(request, "list.html", {"files": files.distinct()})


@login_required
def upload_vault_file(request):
    if request.method == "POST":
        form = VaultFileForm(request.POST, request.FILES)
        if form.is_valid():
            vault_file = form.save(commit=False)
            vault_file.owner = request.user.employeeprofile
            vault_file.save()
            form.save_m2m()
            return redirect("vault_list")
    else:
        form = VaultFileForm()
    return render(request, "upload.html", {"form": form})


@login_required
def download_vault_file(request, file_id):
    file_obj = get_object_or_404(EmployeeVaultFile, id=file_id)
    profile = request.user.employeeprofile

    # Check access rights
    if not (
        file_obj.owner == profile
        or profile in file_obj.shared_with.all()
        or file_obj.is_public
    ):
        return HttpResponseForbidden("You are not allowed to access this file.")

    file_obj.download_count += 1
    file_obj.save(update_fields=["download_count"])
    return FileResponse(file_obj.file.open("rb"), as_attachment=True)




@login_required
def employee_profile_view1(request, employee_id):
    profile = get_object_or_404(EmployeeProfile, id=employee_id)

    # Files shared with this employee
    shared_files = EmployeeVaultFile.objects.filter(shared_with=profile)

    return render(
        request,
        "profile1.html",
        {"profile": profile, "shared_files": shared_files},
    )