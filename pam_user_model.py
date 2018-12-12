from django.contrib.auth.models import User

import pwd


class JobsSchedulerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    uid = pwd.getpwnam(self.user.username).pw_uid
