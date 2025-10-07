from django.db import models
from django.contrib.auth.models import User

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=10, unique=True,null=True, blank=True)
    senior = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='juniors')
    is_senior = models.BooleanField(default=False)  # New field to mark senior status
    img=models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        role = "Senior" if self.is_senior else "Junior"
        return f"{self.user.username} ({self.position}) - {role}"
class JobAssignment(models.Model):
    assigned_to = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL)
    assigned_by = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='delegated_jobs')
    parent_job = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='child_jobs')  # new field
    description = models.TextField()
    date_assigned = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    is_resigned = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)
    
    def get_chain(self):
        chain = []
        job = self
        while job.parent_job is not None:
            chain.append(job)
            job = job.parent_job
        chain.append(job)
        return reversed(chain)
        
from django.utils import timezone
from datetime import timedelta

class DailyLog(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='daily_logs')
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)
    pod = models.TextField("Plan of Day")
    eod = models.TextField("End of Day", blank=True, null=True)
    is_eod_submitted = models.BooleanField(default=False)
    related_assignment = models.ForeignKey(JobAssignment, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('employee', 'date')

    
    def can_edit(self):
        """Returns True if within 2 hours of creation."""
        return timezone.now() <= self.created_at + timedelta(hours=2)


    def __str__(self):
        return f"{self.employee.user.username} log for {self.date}"

class JobReassignment(models.Model):
    job = models.ForeignKey(JobAssignment, on_delete=models.CASCADE, related_name='reassignments')
    from_employee = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='jobs_reassigned_from')
    to_employee = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='jobs_reassigned_to')
    reassigned_by = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='job_reassignments_made')
    reassigned_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reassigned job {self.job.id} from {self.from_employee.user.username if self.from_employee else 'N/A'} to {self.to_employee.user.username if self.to_employee else 'N/A'}"

class AssignmentHistory(models.Model):
    ACTION_CHOICES = [
        ('assigned', 'Assigned'),
        ('reassigned', 'Reassigned'),
        ('completed', 'Completed'),
    ]

    job = models.ForeignKey(JobAssignment, on_delete=models.CASCADE, related_name='history')
    from_employee = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments_given_up')
    to_employee = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments_received')
    action_by = models.ForeignKey(EmployeeProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignment_actions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action.title()} job {self.job.id} → {self.to_employee or 'N/A'} at {self.timestamp}"
    


class Conversation(models.Model):
    participants = models.ManyToManyField(EmployeeProfile, related_name="private_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        users = ", ".join([p.user.username for p in self.participants.all()])
        return f"Conversation between {users}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.user.username}: {self.message[:20]}"
