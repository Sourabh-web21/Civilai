from rest_framework.views import exception_handler
from utils.response_utils import CivilErrorResponse, CivilResponse


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response.status_code != 200 or response.status_code != 201 or \
            isinstance(exc, (CivilErrorResponse, CivilResponse)) is False:
        return CivilErrorResponse(status=response.status_code, error_message=exc.detail, resp_data=[])
    return response
