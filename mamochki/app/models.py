from django.db import models
from django.contrib.auth.models import User


class JobManager(models.Manager):
    def get_one_job(self, job_id):
        return self.get(id=job_id)


class Job(models.Model):
    STATUS_CHOICES = [
        ("a", "Active"),
        ("d", "Deleted")
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    salary = models.IntegerField()
    city = models.CharField(max_length=255)
    employer = models.CharField(max_length=255)
    photo = models.CharField(null=True, blank=True, max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')

    objects = JobManager()

    def __str__(self):
        return self.name


class RezumeManager(models.Manager):
    def get_one_rezume(self, rezume_id):
        return self.get(id=rezume_id)

    def get_total_jobs(self, rezume):
        return RezumeJob.objects.filter(fight=rezume).count()


class Rezume(models.Model):
    STATUS_CHOICES = [
        ('dr', "Draft"),
        ('del', "Deleted"),
        ('f', "Formed"),
        ('c', "Completed"),
        ('r', "Rejected")
    ]
    description = models.CharField(null=True, max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, max_length=9, default='dr')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rezumes')
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_rezumes')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='draft'), name='unique_draft_per_user')
        ]

    objects = RezumeManager()

    def __str__(self):
        return self.description


class RezumeJob(models.Model):
    rezume = models.ForeignKey(Rezume, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    experience = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['rezume', 'job'], name='unique_rezume_job')
        ]