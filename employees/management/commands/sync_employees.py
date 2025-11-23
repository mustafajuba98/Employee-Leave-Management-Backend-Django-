from django.core.management.base import BaseCommand
import asyncio
import logging
from employees.config import EXTERNAL_EMPLOYEE_API_URL
from employees.services import EmployeeSyncService

logger = logging.getLogger('employees')


class Command(BaseCommand):
    help = 'Sync employees from external API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-url',
            type=str,
            default=EXTERNAL_EMPLOYEE_API_URL,
            help='External API URL to fetch employees from'
        )

    def handle(self, *args, **options):
        api_url = options['api_url']
        
        self.stdout.write(self.style.SUCCESS(f'Starting employee sync from: {api_url}'))
        
        try:
            employees_data = asyncio.run(EmployeeSyncService.fetch_employees(api_url))
            new_count, updated_count = EmployeeSyncService.sync_employees(employees_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSync completed successfully!\n'
                    f'New employees: {new_count}\n'
                    f'Updated employees: {updated_count}\n'
                    f'Total processed: {len(employees_data) if employees_data else 0}'
                )
            )
            
            logger.info(f"Employee sync completed. New: {new_count}, Updated: {updated_count}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Sync failed: {str(e)}'))
            logger.error(f"Employee sync failed: {str(e)}", exc_info=True)

