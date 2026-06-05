from django.core.management.base import BaseCommand
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from apps.loans.models import LoanApplication, LoanInstallmentSchedule
from decimal import Decimal

class Command(BaseCommand):
    help = 'Generate installment schedule for a loan'

    def add_arguments(self, parser):
        parser.add_argument('loan_id', type=int)

    def handle(self, *args, **options):
        loan = LoanApplication.objects.get(id=options['loan_id'])
        amount = loan.approved_amount
        rate = loan.interest_rate_applied / Decimal(100) / Decimal(12)  # monthly
        months = loan.duration
        emi = (amount * rate * (1+rate)**months) / ((1+rate)**months - 1)
        balance = amount
        due_date = loan.disbursement_date
        for i in range(1, months+1):
            interest = balance * rate
            principal = emi - interest
            if i == months:
                principal = balance
                emi = principal + interest
            schedule = LoanInstallmentSchedule(
                loan=loan,
                installment_no=i,
                due_date=due_date + relativedelta(months=i),
                principal_amount=principal,
                interest_amount=interest,
                total_due=principal + interest,
            )
            schedule.save()
            balance -= principal
        self.stdout.write(self.style.SUCCESS(f"Schedule generated for loan {loan.id}"))