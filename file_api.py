# All Rights Reserved. Copyright (c) 2021 Hitachi Solutions, Ltd.
from typing import Union

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.fileshare import ShareClient
from flask import Blueprint, abort, request

import file_lib
import logging_lib
import response_lib
from config import config_storage

logger = logging_lib.get_logger(__name__)
file_api = Blueprint("file_api", __name__)


@file_api.route("/file/download-folder", methods=["POST"])
#@auth_login_required #FIXME: Uncomment this source code in the production environment.
def file_download_folder():
    """Download folder Azure File Share.

    :return: HTTP response.
    """

    # FIXME: In the production environment, please uncomment the below source codes.
    # 一般アカウントのみ実行可能
    # if account_type != account_lib.ACCOUNT_TYPE_GENERAL:
    #     return response_lib.error_response(403, 7)

    share_client: Union[ShareClient, None] = None
    try:
        # リクエストパラメータ取り出し
        path = request.json["path"]

        # FIXME: In the production environment, please uncomment the below source codes.
        # free-use配下, protected配下 のどちらでもない場合は不正
        # if not path.startswith("free-use") and not path.startswith("protected"):
        #     return response_lib.error_response(400, 3)

        # テナント情報からストレージ接続用の情報を取り出す
        # storage_account_name, storage_key = tenant_lib.tenant_get_storage_info(db, tenant_name)
        # share_name = storage_account_name

        # FIXME: In the production environment, please remove the below source code.
        storage_account_name = "feasstorage1"
        storage_key = "bzbrQbMbpGp0SbDURB8eFYpV4cOZkNqOeoBciyRLXrdjMIa3z6H6z6aMd31RyzZXTojOeU/AoILNPSvIOrF+zQ=="
        share_name = "file-share-1"

        # Get Share client
        share_client = file_lib.get_az_share_client(storage_account_name, storage_key, share_name)

        # Validate directory path
        if not file_lib.validate_request_data(share_client, path):
            return response_lib.error_response(400, 3)

        # Get Azure files information from the directory path.
        az_files_info = file_lib.list_files_in_directory_recursive(share_client, path)

        # Get files size and file path
        folder_size, files_path = file_lib.get_files_size_and_files_path(az_files_info)

        # Validate File Size
        if folder_size > config_storage.size_limit_folder:
            return response_lib.error_response(400, 20)

        # Get AZ share client Async
        share_client_async = file_lib.get_az_share_client(storage_account_name, storage_key, share_name, True)

        # Download all files in folder from Azure file share.
        return file_lib.download_files_async(share_client_async, files_path, path)
    except TypeError as e:
        logger.warning(e)
        return response_lib.error_response(400, 2)
    except KeyError as e:
        logger.warning(e)
        return response_lib.error_response(400, 3)
    except ResourceNotFoundError as e:
        logger.warning(e)
        return response_lib.error_response(400, 11)
    except Exception as e:
        logger.warning(e)
        abort(500, 0)
    finally:
        if share_client is not None:
            share_client.close()
