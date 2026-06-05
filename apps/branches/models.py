from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    opening_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name