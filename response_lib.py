"""Response lib."""
# All Rights Reserved. Copyright (c) 2021 Hitachi Solutions, Ltd.
from flask import Response, make_response, jsonify

import error_lib

header = {
    "Content-Security-Policy": "default-src 'self'",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": 1,
    "Strict-Transport-Security": "max-age=31536000",
}


def add_headers(response: Response):
    """Add headers to web app's response.

    Args:
        response (Response): app response.
    """
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = ("nosniff",)
    response.headers["X-XSS-Protection"] = (1,)
    response.headers["Strict-Transport-Security"] = "max-age=31536000"


def error_response(response_code: int, error_num: int):
    """Error response handler.

    Args:
        response_code (int): The response code.
        error_num (int): [description]

    Returns:
        (Response): The error response from web app.
    """
    response = make_response(
        jsonify(
            {
                "errorCode": error_num,
                "errorMessage": error_lib.ERROR_MESSAGE[error_num]
            }
        ),
        response_code,
    )
    add_headers(response)
    return response
