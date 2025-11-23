from rest_framework.throttling import UserRateThrottle


class AuthRateThrottle(UserRateThrottle):
    scope = 'auth'


class EmployeeSyncRateThrottle(UserRateThrottle):
    scope = 'employee_sync'


class CreateLeaveRateThrottle(UserRateThrottle):
    scope = 'create_leave'
