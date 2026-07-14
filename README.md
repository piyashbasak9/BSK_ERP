# BSK ERP - Microfinance Enterprise Resource Planning System

A comprehensive Django-based Enterprise Resource Planning (ERP) solution designed specifically for Microfinance Institutions (MFIs), NGOs, and Cooperatives in Bangladesh. This system provides end-to-end management of member accounts, savings, loans, collections, and accounting operations with robust audit trails and role-based access control.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Running the Application](#-running-the-application)
- [Module Documentation](#-module-documentation)
- [Database Schema](#-database-schema)
- [Contributing](#contributing)
- [License](#license)

## Overview

BSK ERP is a full-featured management system that streamlines operations for microfinance organizations. It handles complex processes like member registration, savings account management, loan disbursement and collection, accounting reconciliation, and comprehensive reporting.

## ✨ Key Features

- **Multi-Branch Support**: Manage multiple branches with centralized control and isolated data views
- **Role-Based Access Control (RBAC)**: Granular permission management for different user roles
- **Comprehensive Audit Trail**: Complete logging of all system activities for compliance and accountability
- **Member Management**: Register and manage members with photo uploads and KYC verification
- **Savings Accounts**: Create and monitor individual and group savings accounts
- **Loan Management**: Handle loan applications, disbursement, repayment, and tracking
- **Collection Management**: Manage collection sheets and payment tracking
- **Double-Entry Accounting**: Complete accounting system with journal entries and account management
- **Dynamic Reports**: Generate detailed financial and operational reports
- **Excel/PDF Export**: Export data and reports in multiple formats
- **Interactive Grids**: User-friendly data tables with sorting, filtering, and pagination
- **Dashboard**: Real-time overview of key metrics and activities

## 🛠 Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 4.2.7 |
| Database | SQLite/PostgreSQL | - |
| Frontend | Bootstrap 5 | 5.x |
| Forms | django-crispy-forms | 2.1 |
| Bootstrap Integration | crispy-bootstrap5 | 0.7 |
| Image Processing | Pillow | 10.1.0 |
| Excel Support | openpyxl | 3.1.2 |
| PDF Generation | reportlab | 4.0.4 |
| Environment | python-dotenv | 1.0.0 |

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.8 or higher
- **pip**: Python package manager
- **Git**: For version control
- **virtualenv** or **venv**: Python virtual environment (recommended)

### Optional:
- **PostgreSQL**: For production database (SQLite is default for development)
- **Redis**: For caching and session management (optional)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd BSK_ERP
```

### 2. Create Virtual Environment

```bash
# On Linux/Mac
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env  # If template exists, or create manually
```

Add the following configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Optional - uses SQLite by default)
# DATABASE_URL=postgresql://user:password@localhost:5432/bsk_erp

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password

# Application Settings
ORGANIZATION_NAME=BSK ERP
CURRENCY_SYMBOL=৳
```

### 5. Database Migration

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 7. Load Dummy Data (Optional)

```bash
python manage.py shell < seed_dummy_data.py
```

Or use the Django shell:

```bash
python manage.py shell
```

## ⚙️ Configuration

### Key Settings Files

- **erp/settings.py**: Main Django configuration
- **erp/urls.py**: URL routing configuration
- **erp/utils/**: Custom utilities and middleware

### Important Settings

#### Installed Apps
The project includes the following Django apps:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'apps.authentication',      # User authentication
    'apps.branches',            # Branch management
    'apps.members',             # Member management
    'apps.savings',             # Savings accounts
    'apps.loans',               # Loan management
    'apps.collections',         # Collection management
    'apps.accounting',          # Accounting & journal entries
    'apps.reports',             # Report generation
    'apps.audit',               # Audit logging
    'apps.settings',            # System settings
]
```

#### Custom Middleware

```python
MIDDLEWARE = [
    # ... Django default middleware ...
    'erp.utils.middleware.BranchIsolationMiddleware',  # Multi-branch isolation
    'erp.utils.middleware.RBACMiddleware',             # Role-based access control
    'erp.utils.middleware.AuditMiddleware',            # Activity logging
    'apps.audit.middleware.AuditMiddleware',           # Detailed audit trail
]
```

## 📁 Project Structure

```
BSK_ERP/
├── apps/                          # Django applications
│   ├── authentication/            # User auth and login
│   ├── branches/                  # Multi-branch management
│   ├── members/                   # Member profiles and registration
│   ├── savings/                   # Savings account management
│   ├── loans/                     # Loan lifecycle management
│   ├── collections/               # Collection sheet and payment tracking
│   ├── accounting/                # Double-entry accounting system
│   ├── reports/                   # Report generation and export
│   ├── audit/                     # Audit logging and activity tracking
│   └── settings/                  # System configuration
├── erp/                           # Project settings
│   ├── settings.py                # Django configuration
│   ├── urls.py                    # URL routing
│   ├── wsgi.py                    # WSGI application
│   └── utils/                     # Custom utilities
│       ├── context_processors.py  # Template context
│       ├── middleware.py          # Custom middleware
│       └── tabulator.py           # Data table handling
├── templates/                     # HTML templates
│   ├── base.html                  # Base template
│   ├── dashboard.html             # Dashboard page
│   ├── login.html                 # Login page
│   └── [app-name]/                # App-specific templates
├── static/                        # Static files (CSS, JS)
│   ├── css/                       # Stylesheets
│   └── js/                        # JavaScript files
├── media/                         # User uploads (photos, etc.)
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── db.sqlite3                     # SQLite database (development)
└── README.md                      # This file
```

## 🚀 Running the Application

### Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Access the Admin Panel

Navigate to `http://localhost:8000/admin` and log in with your superuser credentials.

### Access the Application

Navigate to `http://localhost:8000` to access the main ERP interface.

### Collect Static Files (Production)

```bash
python manage.py collectstatic --noinput
```

## 📚 Module Documentation

### 1. **Authentication** (`apps/authentication`)
- User login and logout
- Password management
- Role assignment

### 2. **Branches** (`apps/branches`)
- Create and manage multiple branches
- Branch-specific data isolation
- Branch hierarchy management

### 3. **Members** (`apps/members`)
- Member registration with photo upload
- Member profile management
- Member status tracking (Active, Inactive, Suspended)
- KYC documentation

### 4. **Savings** (`apps/savings`)
- Create individual and group savings accounts
- Track savings transactions
- Generate savings reports
- Interest calculation (if applicable)

### 5. **Loans** (`apps/loans`)
- Loan application processing
- Loan approval and disbursement
- Payment tracking and collection
- Loan status monitoring
- Interest and principal calculation

### 6. **Collections** (`apps/collections`)
- Create collection sheets
- Track payments from members
- Generate collection reports
- Payment reconciliation

### 7. **Accounting** (`apps/accounting`)
- Chart of accounts management
- Journal entry creation
- Double-entry bookkeeping
- Account reconciliation
- Trial balance

### 8. **Reports** (`apps/reports`)
- Member reports
- Savings reports
- Loan reports
- Collection reports
- Financial statements
- Export to Excel/PDF

### 9. **Audit** (`apps/audit`)
- User activity logging
- System event tracking
- Audit trail generation
- Compliance reporting
- Activity dashboard

### 10. **Settings** (`apps/settings`)
- System configuration
- Organization settings
- User preferences
- Business rules configuration

## 🗄️ Database Schema

The project uses Django ORM for database management. Key models include:

- **User**: Django auth user model with extended profile
- **Branch**: Organization branches
- **Member**: Microfinance members
- **SavingsAccount**: Individual/group savings accounts
- **LoanApplication**: Loan requests and tracking
- **LoanDisbursement**: Loan payment records
- **Collection**: Payment collection sheets
- **Account**: Chart of accounts
- **JournalEntry**: Accounting journal entries
- **AuditLog**: Activity and event logging

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For issues, questions, or suggestions, please:
- Open an issue on GitHub
- Contact the development team at support@bskerp.com

## 🎯 Roadmap

- [ ] Mobile app for field operations
- [ ] Advanced analytics and BI dashboards
- [ ] Mobile money integration
- [ ] Real-time SMS notifications
- [ ] Multi-language support
- [ ] API documentation (REST/GraphQL)
- [ ] Performance optimization
- [ ] Cloud deployment guides

## 🔒 Security Considerations

- Always change the SECRET_KEY in production
- Keep DEBUG=False in production
- Use HTTPS in production
- Regularly update dependencies
- Use strong database passwords
- Implement proper backup strategies
- Enable two-factor authentication for admin users

---

**Last Updated**: 2024
**Version**: 1.0.0