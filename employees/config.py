from decouple import config

EXTERNAL_EMPLOYEE_API_URL = config(
    'EXTERNAL_EMPLOYEE_API_URL',
    default='https://jsonplaceholder.typicode.com/users'
)

