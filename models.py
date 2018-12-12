from django.db import models

# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=200)
    group = models.IntegerField(default=0)

    def __str__(self):
        return "Nutzer " + self.name

class Task(models.Model):
    name = models.CharField(max_length = 200)
    date_added = models.DateTimeField('date added')
    num_cpu = models.IntegerField(default=1)
    num_gpu = models.IntegerField(default=0)
    num_mem = models.IntegerField(default=1024)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

    def __str__(self):
        return "Task by " + str(self.user) + " from " + str(self.date_added)


