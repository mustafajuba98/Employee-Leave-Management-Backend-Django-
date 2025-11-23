# Employee Leave Management API

Django REST API for managing employees and leave requests with role-based access control, comprehensive validation, and production-ready features.

## Tech Stack

- Django 5.2 (LTS)
- Django REST Framework 3.16.0
- JWT Authentication (djangorestframework-simplejwt)
- SQLite (configurable to MySQL)
- drf-spectacular (OpenAPI/Swagger)

## Features

- Employee management with external API sync
- Leave request workflow (create, approve, reject)
- Role-based permissions (HR, Employee)
- JWT authentication with refresh tokens
- Rate limiting and response caching
- Comprehensive validation and error handling
- Async operations for external API calls
- Structured logging with rotation
- Health check endpoint
- Interactive API documentation (Swagger)

## Quick Start

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Clone repository
git clone <repository-url>
cd Employee-Leave-Management

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Environment Variables

See `env.example` for required variables:

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated hosts
- `JWT_SECRET_KEY` - JWT signing key
- `JWT_ACCESS_TOKEN_LIFETIME` - Access token lifetime (minutes)
- `JWT_REFRESH_TOKEN_LIFETIME` - Refresh token lifetime (minutes)
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins
- `EXTERNAL_EMPLOYEE_API_URL` - External API URL for employee sync

## API Endpoints

### Authentication

- `POST /api/token/` - Obtain JWT tokens
- `POST /api/token/refresh/` - Refresh access token

### Employees (HR Only)

- `GET /api/employees/` - List employees (filtering, search, pagination)
- `POST /api/employees/` - Create employee
- `GET /api/employees/{id}/` - Get employee details
- `PATCH /api/employees/{id}/` - Update employee
- `DELETE /api/employees/{id}/` - Delete employee
- `POST /api/employees/sync/` - Sync from external API

### Leave Requests

- `GET /api/leaves/` - List leave requests (filters: status, leave_type, employee_id)
- `POST /api/leaves/` - Create leave request
- `GET /api/leaves/{id}/` - Get leave request details
- `PATCH /api/leaves/{id}/` - Update leave request (HR only)
- `PATCH /api/leaves/{id}/approve/` - Approve leave (HR only)
- `PATCH /api/leaves/{id}/reject/` - Reject leave (HR only)

### System

- `GET /api/health/` - Health check (database, cache status)
- `GET /api/docs/` - Swagger UI documentation
- `GET /api/schema/` - OpenAPI schema (JSON)

## Query Parameters

### Filtering

- `status` - Filter by status (pending, approved, rejected)
- `leave_type` - Filter by type (annual, sick, casual)
- `employee_id` - Filter by employee ID
- `company_id` - Filter employees by company ID

### Search

- `search` - Search in employee name/email or leave employee fields

### Ordering

- `ordering` - Order by field (prefix with `-` for descending)
  - Leaves: `created_at`, `start_date`, `end_date`, `status`, `leave_type`
  - Employees: `name`, `email`, `created_at`

### Pagination

- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

## Rate Limiting

- Authentication: 5 requests/minute
- Employee Sync: 10 requests/hour
- Create Leave: 20 requests/hour
- General API: 1000 requests/hour

## Caching

- Employee list: 5 minutes
- Leave requests list: 2 minutes

Cache varies by user (Authorization header).

## Management Commands

```bash
# Sync employees from external API
python manage.py sync_employees --api-url <url>
```

## Testing

```bash
pytest
```

Test files:
- `tests/test_api.py` - API endpoint tests
- `employees/tests.py` - Employee model tests
- `leaves/tests.py` - Leave request model tests

## Project Structure

```
├── config/              # Django settings, URLs
├── accounts/            # Custom User model
├── employees/           # Employee management
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── services.py      # Business logic (sync)
│   └── management/      # Management commands
├── leaves/              # Leave request management
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── core/                # Shared utilities
│   ├── permissions.py   # Custom permissions
│   ├── exceptions.py    # Exception handler
│   ├── validators.py    # Custom validators
│   ├── pagination.py    # Pagination config
│   ├── throttling.py    # Rate limiting
│   └── views.py         # Health check
├── logs/                # Log files
└── tests/               # Test suite
```

## Validation Rules

### Leave Requests

- End date must be after start date
- Dates cannot be in the past
- No overlapping approved leaves for same employee
- Only pending leaves can have status changed

### Employees

- Email must be unique
- Company ID must be positive
- Joining date cannot be in the future
- Name minimum 2 characters

## Security

- JWT authentication with token rotation
- Role-based access control
- Input validation at model, serializer, and view levels
- SQL injection protection (Django ORM)
- XSS protection
- CORS configuration
- Security headers (XSS filter, content type nosniff, frame options)
- HTTPS enforcement in production
- Environment-based secret management

## Logging

Logs are stored in `logs/`:

- `api.log` - General API operations
- `employee_sync.log` - Employee sync operations
- `errors.log` - Error logs

Automatic rotation: 10MB max, 5 backups.

## Design Decisions

**Custom User Model**: Role field instead of Django Groups for faster queries and simpler code.

**JWT Authentication**: Stateless, no DB lookup, industry standard, supports refresh tokens.

**SQLite Default**: Simple setup. MySQL configurable via environment variables.

**Async Operations**: Non-blocking external API calls for better performance.

**Modular Structure**: Separate apps for better organization and maintainability.

**Multi-level Validation**: Model, serializer, and view levels for defense in depth.

## Production Deployment

1. Set `DEBUG=False`
2. Configure `ALLOWED_HOSTS`
3. Set up HTTPS (SSL certificate)
4. Configure database backups
5. Set up monitoring and alerting
6. Use environment variables for all secrets
7. Configure proper CORS origins

## API Documentation

Interactive documentation available at `/api/docs/` (Swagger UI).

Postman collection included: `Employee_Leave_Management.postman_collection.json`
