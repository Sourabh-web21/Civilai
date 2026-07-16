from rest_framework.response import Response
from rest_framework import status as rest_status


def get_http_status(status):
    """
    We will map status code in this method
    to return standard http status code.
    """

    if isinstance(status, str):
        http_status = rest_status.HTTP_200_OK

    elif isinstance(status, int) and status <= 110:
        http_status = rest_status.HTTP_200_OK
    else:
        try:
            http_status = int(status)
        except Exception as e:
            http_status = rest_status.HTTP_500_INTERNAL_SERVER_ERROR

    return http_status


class CivilResponse(Response):

    def __init__(self, resp_data=[], is_success=None, status=None, template_name=None, headers=None, exception=False,
                 content_type=None):

        if is_success:
            message = is_success
        else:
            message = "FAILURE"

        if isinstance(resp_data, str):
            resp_data = [resp_data]

        data_content = {
            'status': True,
            'status_code': status,
            'message': message,
            'results': resp_data,
        }

        http_status = get_http_status(status)

        super(CivilResponse, self).__init__(
            data=data_content,
            template_name=template_name,
            headers=headers,
            exception=exception,
            content_type=content_type,
            status=http_status
        )


class CivilErrorResponse(Response):

    def __init__(self, error_message=None, status=None, error_code=None,
                 exception=True, template_name=None, headers=None, content_type=None, resp_data=[]):

        if isinstance(resp_data, str):
            resp_data = [resp_data]

        data_content = {
            'status': False,
            'status_code': status,
            "message": error_message,
            "results": resp_data,
        }

        http_status = get_http_status(status)

        super(CivilErrorResponse, self).__init__(
            data=data_content,
            exception=exception,
            template_name=template_name,
            headers=headers,
            content_type=content_type,
            status=http_status
        )
