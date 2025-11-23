from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied, AuthenticationFailed, APIException
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import EmptyPage
import logging

logger = logging.getLogger('core')


class BaseAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred'
    default_code = 'error'

    def __init__(self, detail=None, code=None, status_code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail, code)


class NetworkError(BaseAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Unable to connect to external service. Please try again later.'
    default_code = 'network_error'


class InvalidURLError(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid URL provided. Please check the URL and try again.'
    default_code = 'invalid_url'


class TimeoutError(BaseAPIException):
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    default_detail = 'Request timed out. Please try again later.'
    default_code = 'timeout_error'


class InvalidDataError(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid data provided.'
    default_code = 'invalid_data'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': {},
            'code': 'error'
        }
        
        if isinstance(exc, NotFound):
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    error_message = exc.detail.get('detail', exc.detail.get('error', 'Resource not found'))
                    if isinstance(error_message, list):
                        error_message = error_message[0] if error_message else 'Resource not found'
                    custom_response_data['message'] = str(error_message)
                    custom_response_data['details'] = exc.detail
                elif isinstance(exc.detail, list):
                    custom_response_data['message'] = exc.detail[0] if exc.detail else 'Resource not found'
                    custom_response_data['details'] = {'error': custom_response_data['message']}
                else:
                    custom_response_data['message'] = str(exc.detail)
                    custom_response_data['details'] = {'error': custom_response_data['message']}
            else:
                custom_response_data['message'] = 'Resource not found'
                custom_response_data['details'] = {'error': 'Resource not found'}
            custom_response_data['code'] = 'not_found'
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, PermissionDenied):
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    error_message = exc.detail.get('detail', exc.detail.get('error', 'Permission denied'))
                    if isinstance(error_message, list):
                        error_message = error_message[0] if error_message else 'Permission denied'
                    custom_response_data['message'] = str(error_message)
                    custom_response_data['details'] = exc.detail
                elif isinstance(exc.detail, list):
                    custom_response_data['message'] = exc.detail[0] if exc.detail else 'Permission denied'
                    custom_response_data['details'] = {'error': custom_response_data['message']}
                else:
                    custom_response_data['message'] = str(exc.detail)
                    custom_response_data['details'] = {'error': custom_response_data['message']}
            else:
                custom_response_data['message'] = 'Permission denied'
                custom_response_data['details'] = {'error': 'Permission denied'}
            custom_response_data['code'] = 'permission_denied'
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, AuthenticationFailed):
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    error_message = exc.detail.get('detail', exc.detail.get('error', 'Authentication failed'))
                    error_code = exc.detail.get('code', 'authentication_failed')
                    if isinstance(error_message, list):
                        error_message = error_message[0] if error_message else 'Authentication failed'
                    custom_response_data['message'] = str(error_message)
                    custom_response_data['details'] = {
                        'error': str(error_message),
                        'code': str(error_code) if error_code != 'authentication_failed' else None
                    }
                    custom_response_data['details'] = {k: v for k, v in custom_response_data['details'].items() if v is not None}
                elif isinstance(exc.detail, list):
                    custom_response_data['message'] = exc.detail[0] if exc.detail else 'Authentication failed'
                    custom_response_data['details'] = {'error': custom_response_data['message']}
                else:
                    custom_response_data['message'] = str(exc.detail)
                    custom_response_data['details'] = {'error': custom_response_data['message']}
            else:
                custom_response_data['message'] = 'Authentication failed'
                custom_response_data['details'] = {'error': 'Authentication failed'}
            custom_response_data['code'] = 'authentication_failed'
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, (NetworkError, InvalidURLError, TimeoutError, InvalidDataError)):
            custom_response_data['message'] = exc.detail if hasattr(exc, 'detail') else str(exc)
            custom_response_data['code'] = exc.default_code if hasattr(exc, 'default_code') else 'error'
            custom_response_data['details'] = {'error': str(exc)}
            status_code = exc.status_code
        elif isinstance(exc, ValidationError) or isinstance(exc, DjangoValidationError):
            custom_response_data['message'] = 'Validation error'
            custom_response_data['code'] = 'validation_error'
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    custom_response_data['details'] = exc.detail
                    if exc.detail:
                        first_key = next(iter(exc.detail))
                        if isinstance(exc.detail[first_key], list):
                            custom_response_data['message'] = exc.detail[first_key][0] if exc.detail[first_key] else 'Validation error'
                        else:
                            custom_response_data['message'] = exc.detail[first_key] if isinstance(exc.detail[first_key], str) else 'Validation error'
                elif isinstance(exc.detail, list):
                    custom_response_data['details'] = {'non_field_errors': exc.detail}
                    custom_response_data['message'] = exc.detail[0] if exc.detail else 'Validation error'
                else:
                    custom_response_data['details'] = {'error': str(exc.detail)}
                    custom_response_data['message'] = str(exc.detail)
            else:
                if isinstance(exc, DjangoValidationError) and hasattr(exc, 'message_dict'):
                    message_dict = exc.message_dict
                    if '__all__' in message_dict:
                        custom_response_data['details'] = {'non_field_errors': message_dict['__all__']}
                        custom_response_data['message'] = message_dict['__all__'][0] if message_dict['__all__'] else 'Validation error'
                    else:
                        custom_response_data['details'] = message_dict
                        if message_dict:
                            first_key = next(iter(message_dict))
                            if isinstance(message_dict[first_key], list):
                                custom_response_data['message'] = message_dict[first_key][0] if message_dict[first_key] else 'Validation error'
                            else:
                                custom_response_data['message'] = message_dict[first_key] if isinstance(message_dict[first_key], str) else 'Validation error'
                elif isinstance(exc, DjangoValidationError) and hasattr(exc, 'messages'):
                    custom_response_data['details'] = {'non_field_errors': list(exc.messages)}
                    custom_response_data['message'] = list(exc.messages)[0] if exc.messages else 'Validation error'
                else:
                    custom_response_data['details'] = {'error': str(exc)}
            status_code = response.status_code if response else status.HTTP_400_BAD_REQUEST
        else:
            if hasattr(exc, 'detail'):
                if isinstance(exc.detail, dict):
                    custom_response_data['details'] = exc.detail
                    custom_response_data['message'] = 'Validation error'
                    custom_response_data['code'] = 'validation_error'
                elif isinstance(exc.detail, list):
                    custom_response_data['details'] = {'non_field_errors': exc.detail}
                    custom_response_data['message'] = exc.detail[0] if exc.detail else 'Validation error'
                    custom_response_data['code'] = 'validation_error'
                else:
                    custom_response_data['message'] = str(exc.detail)
            else:
                custom_response_data['message'] = str(exc)
            status_code = response.status_code if response else status.HTTP_400_BAD_REQUEST
        
        logger.error(f"Exception: {exc.__class__.__name__} - {custom_response_data['message']}", exc_info=True)
        
        return Response(custom_response_data, status=status_code)
    
    if isinstance(exc, EmptyPage):
        return Response(
            {
                'error': True,
                'message': 'Invalid page number',
                'details': {'error': 'The requested page does not exist'},
                'code': 'invalid_page'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    if isinstance(exc, KeyError):
        logger.error(f"KeyError: {str(exc)}", exc_info=True)
        return Response(
            {
                'error': True,
                'message': 'Invalid request data',
                'details': {'error': f'Missing required field: {str(exc)}'},
                'code': 'missing_field'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    logger.error(f"Unhandled exception: {exc.__class__.__name__} - {str(exc)}", exc_info=True)
    
    return Response(
        {
            'error': True,
            'message': 'An unexpected error occurred. Please try again later.',
            'details': {},
            'code': 'internal_error'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
