from django.db import models
from apps.branches.models import Branch
from apps.members.models import Member
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


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
    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('closed', 'Closed')
    ]
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT)
    applied_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    duration = models.IntegerField()
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

    def generate_schedule(self, disbursement_date=None):
        """Generate full installment schedule using equal principal + reducing balance interest."""
        from .models import LoanInstallmentSchedule

        if not disbursement_date:
            disbursement_date = self.disbursement_date or date.today()

        # Delete existing schedule to avoid duplicates
        LoanInstallmentSchedule.objects.filter(loan=self).delete()

        principal = Decimal(self.approved_amount or self.applied_amount)
        annual_rate = Decimal(self.interest_rate_applied or self.product.interest_rate)
        monthly_rate = (annual_rate / Decimal('100')) / Decimal('12')
        num_installments = self.duration
        frequency = self.product.installment_frequency

        principal_per_installment = principal / Decimal(num_installments)
        remaining_principal = principal
        schedule_data = []

        for i in range(1, num_installments + 1):
            interest = remaining_principal * monthly_rate
            total_due = principal_per_installment + interest

            if frequency == 'monthly':
                due_date = disbursement_date + relativedelta(months=i - 1)
            elif frequency == 'weekly':
                due_date = disbursement_date + timedelta(weeks=i - 1)
            else:  # daily
                due_date = disbursement_date + timedelta(days=i - 1)

            schedule_data.append({
                'installment_no': i,
                'due_date': due_date,
                'principal_amount': principal_per_installment.quantize(Decimal('0.01')),
                'interest_amount': interest.quantize(Decimal('0.01')),
                'total_due': total_due.quantize(Decimal('0.01')),
            })
            remaining_principal -= principal_per_installment

        for data in schedule_data:
            LoanInstallmentSchedule.objects.create(
                loan=self,
                **data,
                paid_principal=Decimal('0.00'),
                paid_interest=Decimal('0.00'),
                paid_total=Decimal('0.00'),
                is_paid=False,
                late_fee=Decimal('0.00')
            )
        return schedule_data


class LoanDisbursement(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    disbursement_date = models.DateField()
    method = models.CharField(max_length=50)
    reference_no = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Disbursement of {self.amount} to {self.loan.member.name}"


class LoanInstallmentSchedule(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='installment_schedules')
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

    def make_payment(self, amount_paid, payment_date=None):
        from django.utils import timezone
        if payment_date is None:
            payment_date = timezone.now().date()

        remaining_due = self.total_due - self.paid_total
        if amount_paid > remaining_due:
            return False, f"Amount exceeds remaining due ({remaining_due})."
        if amount_paid <= 0:
            return False, "Payment amount must be positive."

        # Calculate late fee if paid after due date and not fully paid before
        if not self.is_paid and payment_date > self.due_date:
            days_late = (payment_date - self.due_date).days
            self.late_fee = (self.total_due * Decimal('0.001') * days_late).quantize(Decimal('0.01'))
            self.save()

        remaining_principal = self.principal_amount - self.paid_principal
        remaining_interest = self.interest_amount - self.paid_interest

        # Pay interest first, then principal
        interest_to_pay = min(amount_paid, remaining_interest)
        principal_to_pay = min(amount_paid - interest_to_pay, remaining_principal)

        self.paid_interest += interest_to_pay
        self.paid_principal += principal_to_pay
        self.paid_total = self.paid_principal + self.paid_interest
        self.paid_date = payment_date

        if self.paid_total >= self.total_due:
            self.is_paid = True
        self.save()

        # Check if all installments of the loan are paid, then close the loan
        loan = self.loan
        all_paid = not loan.installment_schedules.filter(is_paid=False).exists()
        if all_paid and loan.status != 'closed':
            loan.status = 'closed'
            loan.closed_date = payment_date
            loan.save()

        return True, f"Payment of {amount_paid} recorded. Remaining due: {self.total_due - self.paid_total}"