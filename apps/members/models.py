from django.db import models
from apps.branches.models import Branch
from apps.authentication.models import User
from django.utils import timezone

class Member(models.Model):
    GENDER = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    MARITAL = [('Single', 'Single'), ('Married', 'Married'), ('Widowed', 'Widowed'), ('Divorced', 'Divorced')]
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    member_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200)
    mother_name = models.CharField(max_length=200)
    spouse_name = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER)
    marital_status = models.CharField(max_length=20, choices=MARITAL)
    date_of_birth = models.DateField()
    nid = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    present_address = models.TextField()
    permanent_address = models.TextField()
    photo = models.ImageField(upload_to='member_photos/', blank=True)
    registration_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='members_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['branch', 'member_id']

    def __str__(self):
        return f"{self.member_id} - {self.name}"

class Nominee(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='nominees')
    name = models.CharField(max_length=200)
    relation = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    nid = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)

class MemberTransfer(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    from_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_out')
    to_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_in')
    transfer_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)