from django.db import models
from apps.branches.models import Branch
from apps.members.models import Member

class LoanProduct(models.Model):
    FREQUENCY = [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')]
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField()
    installment_frequency = models.CharField(max_length=20, choices=FREQUENCY)
    processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    late_penalty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class LoanApplication(models.Model):
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('disbursed', 'Disbursed'), ('closed', 'Closed')]
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT)
    applied_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    duration = models.IntegerField()  # months
    interest_rate_applied = models.DecimalField(max_digits=5, decimal_places=2)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    applied_date = models.DateField()
    approved_date = models.DateField(null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    closed_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, related_name='approved_loans')

    def __str__(self):
        return f"{self.member.name} - {self.applied_amount}"

class LoanDisbursement(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    disbursement_date = models.DateField()
    method = models.CharField(max_length=50)
    reference_no = models.CharField(max_length=100, blank=True)

class LoanInstallmentSchedule(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    installment_no = models.IntegerField()
    due_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_due = models.DecimalField(max_digits=12, decimal_places=2)
    paid_principal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.loan} - Installment {self.installment_no}"