from django.db import models

class Event(models.Model):
    repo = models.TextField()
    action = models.TextField()
    record = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.repo} - {self.action} at {self.created_at}"
