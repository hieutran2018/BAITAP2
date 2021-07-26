"""Flask app."""
# All Rights Reserved. Copyright (c) 2021 Hitachi Solutions, Ltd.
from flask import Flask, jsonify, make_response
from werkzeug.exceptions import HTTPException, MethodNotAllowed

import error_lib
import logging_lib
import response_lib
from file_api import file_api

# Create logger.
logger = logging_lib.get_logger(__name__)

# Create app
app = Flask(__name__)

# Register blueprint
app.register_blueprint(file_api)


@app.route("/")
def index():
    """
    index
    存在を見せないので404にする
    :return:
    """
    return response_lib.error_response(404, 1)


# @app.errorhandler(500)
def error_500_handler(e):
    """
    エラーハンドラ(Internal Server Error)
    想定外のエラーを処理する。詳細をログに記録し、HTTPレスポンスには Internal Server Error とのみ返す。
    :param e: エラー情報
    :return: HTTPレスポンス
    """
    import traceback

    logger.error(traceback.format_exc())

    response = make_response(
        jsonify({"errorCode": 0, "errorMessage": error_lib.ERROR_MESSAGE[0]}), e.code
    )
    response_lib.add_headers(response)
    return response


@app.errorhandler(MethodNotAllowed)
def error_method_not_allowed_handler(e):
    """
    エラーハンドラ(Method不正)
    Method不正のエラーを処理する。
    :param e: エラー情報
    :return: HTTPレスポンス
    """
    import traceback

    logger.warning(traceback.format_exc())

    response = make_response(
        jsonify({"errorCode": 8, "errorMessage": error_lib.ERROR_MESSAGE[8]}), e.code
    )
    response_lib.add_headers(response)
    return response


@app.errorhandler(HTTPException)
def error_handler(e):
    """
    エラーハンドラ
    コール元で入力されたエラーコードからエラーメッセージを引き、HTTPレスポンスのJSONを成形する。
    :param e: エラー情報
    :return: HTTPレスポンス
    """
    # 自分で決めたエラーは response_libで返す。ここで返すのは、404など規定的なものや想定外の例外。
    response = make_response({"errorMessage": e.description, "errorCode": 99}, e.code)
    response_lib.add_headers(response)
    return response


if __name__ == "__main__":
    app.run()
