from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = 'healthy'
    except Exception:
        db_status = 'unhealthy'
    
    cache_status = 'healthy'
    try:
        cache.set('health_check', 'ok', 1)
        if cache.get('health_check') != 'ok':
            cache_status = 'unhealthy'
    except Exception:
        cache_status = 'unhealthy'
    
    overall_status = 'healthy' if db_status == 'healthy' and cache_status == 'healthy' else 'degraded'
    
    return Response(
        {
            'status': overall_status,
            'database': db_status,
            'cache': cache_status,
            'timestamp': timezone.now().isoformat()
        },
        status=status.HTTP_200_OK if overall_status == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    )
