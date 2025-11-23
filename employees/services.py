import logging
import aiohttp
import asyncio
from urllib.parse import urlparse
from django.db import transaction
from .models import Employee
from .config import EXTERNAL_EMPLOYEE_API_URL
from core.exceptions import NetworkError, InvalidURLError, TimeoutError, InvalidDataError

logger = logging.getLogger('employees')


class EmployeeSyncService:
    @staticmethod
    def _validate_url(url):
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise InvalidURLError("Invalid URL format. Please provide a valid URL.")
            if result.scheme not in ['http', 'https']:
                raise InvalidURLError("URL must use http or https protocol.")
        except Exception as e:
            if isinstance(e, InvalidURLError):
                raise
            raise InvalidURLError("Invalid URL provided.")
    
    @staticmethod
    async def fetch_employees(url):
        EmployeeSyncService._validate_url(url)
        
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            try:
                                return await response.json()
                            except Exception as e:
                                logger.error(f"Failed to parse JSON response: {str(e)}")
                                raise InvalidDataError("Invalid response format from external API.")
                        elif response.status == 404:
                            raise InvalidURLError("The requested resource was not found. Please check the URL.")
                        elif response.status >= 500:
                            raise NetworkError("External service is currently unavailable. Please try again later.")
                        else:
                            raise NetworkError(f"External API returned an error (status {response.status}).")
                except asyncio.TimeoutError:
                    raise TimeoutError("Request timed out. Please try again later.")
                except aiohttp.ClientError as e:
                    logger.error(f"Network error: {str(e)}")
                    raise NetworkError("Unable to connect to external service. Please check your internet connection and try again.")
        except (NetworkError, InvalidURLError, TimeoutError, InvalidDataError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in fetch_employees: {str(e)}", exc_info=True)
            raise NetworkError("An unexpected error occurred while fetching data. Please try again later.")

    @staticmethod
    def sync_employees(employees_data):
        if not employees_data:
            return 0, 0
        
        emails = [emp.get('email') for emp in employees_data if emp.get('email')]
        if not emails:
            return 0, 0
        
        existing_employees = {
            emp.email: emp for emp in Employee.objects.filter(email__in=emails)
        }
        
        employees_to_create = []
        employees_to_update = []
        
        for emp_data in employees_data:
            email = emp_data.get('email')
            if not email:
                continue
            
            employee_data = {
                'name': emp_data.get('name', ''),
                'company_id': emp_data.get('id', 0),
                'joining_date': None
            }
            
            if email in existing_employees:
                employee = existing_employees[email]
                needs_update = (
                    employee.name != employee_data['name'] or
                    employee.company_id != employee_data['company_id']
                )
                if needs_update:
                    employee.name = employee_data['name']
                    employee.company_id = employee_data['company_id']
                    employees_to_update.append(employee)
            else:
                employees_to_create.append(Employee(email=email, **employee_data))
        
        new_count = 0
        updated_count = 0
        
        with transaction.atomic():
            if employees_to_create:
                Employee.objects.bulk_create(employees_to_create)
                new_count = len(employees_to_create)
                for emp in employees_to_create:
                    logger.info(f"New employee synced: {emp.email}")
            
            if employees_to_update:
                Employee.objects.bulk_update(employees_to_update, ['name', 'company_id'])
                updated_count = len(employees_to_update)
                for emp in employees_to_update:
                    logger.info(f"Employee updated: {emp.email}")
        
        return new_count, updated_count

