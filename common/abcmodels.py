from django.db import models

class TimeStampedModel(models.Model):
     created_on = models.DateTimeField(auto_now_add=True)
     last_updated_on = models.DateTimeField(auto_now=True)

     class Meta:
         abstract = True