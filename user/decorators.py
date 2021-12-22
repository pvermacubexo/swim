from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.request import Request
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def authorize(user_types):
    def _method_wrapper(func):
        def wrapper(instance, *args, **kwargs):
            request = __init_request(instance)
            if not request.user or request.user.is_anonymous:
                logger.warning(f"User need to login or a Anonymous user try to login!!")
                raise NotAuthenticated({"message": "Please login to continue"})
            if request.user.user_type in user_types:
                return func(request, *args, **kwargs)
            else:
                logger.warning(f"{request.user} don't have permission to access")
                raise PermissionDenied({"message": f"{request.user} don't have permission to access"})

        return wrapper

    return _method_wrapper


def __init_request(instance):
    if isinstance(instance, Request):
        return instance
    elif hasattr(instance, 'request'):
        return instance.request
    else:
        return Request()
