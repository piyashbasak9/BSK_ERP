from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from apps.authentication.models import User
from apps.branches.models import Branch
from apps.accounting.models import Account
from apps.savings.models import SavingsProduct
from apps.loans.models import LoanProduct

class Command(BaseCommand):
    help = 'Initialize system with default data'

    def handle(self, *args, **options):
        # Create Head Office branch
        head, _ = Branch.objects.get_or_create(code='HO', defaults={
            'name': 'Head Office', 'address': 'Dhaka', 'phone': '000', 'opening_date': '2020-01-01'
        })
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@bsk.com', 'admin123', branch=head)
            admin.save()

        # Create default Chart of Accounts
        accounts = [
            ('1010', 'Cash in Hand', 'Asset'), ('1020', 'Petty Cash', 'Asset'),
            ('2010', 'Member Savings', 'Liability'), ('3010', 'Loan Portfolio', 'Asset'),
            ('4010', 'Interest Income', 'Income'), ('5010', 'Staff Salary', 'Expense'),
        ]
        for code, name, typ in accounts:
            Account.objects.get_or_create(code=code, defaults={'name': name, 'account_type': typ})

        # Savings product
        SavingsProduct.objects.get_or_create(code='GEN', defaults={
            'name': 'General Savings', 'interest_rate': 5.00, 'min_balance': 500
        })
        # Loan product
        LoanProduct.objects.get_or_create(code='MICRO', defaults={
            'name': 'Micro Loan', 'interest_rate': 12.00, 'duration_months': 12,
            'installment_frequency': 'monthly', 'min_amount': 5000, 'max_amount': 50000
        })
        self.stdout.write(self.style.SUCCESS('System initialized.'))