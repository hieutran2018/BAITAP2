# All Rights Reserved. Copyright (c) 2021 Hitachi Solutions, Ltd.
import asyncio
import os
import tempfile
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
from typing import Any, Iterable, Tuple, Union
from zipfile import ZipFile

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.fileshare import ShareClient, ShareFileClient
from azure.storage.fileshare.aio import ShareClient as ShareClientAsync
from flask import send_file

import config.config_storage as config_storage
import logging_lib

logger = logging_lib.get_logger(__name__)


def get_az_share_client(
    storage_account_name: str, storage_key: str, share_name: str, is_async: bool = False, **kwargs
) -> Union[ShareClient, ShareClientAsync]:
    """Get Azure Share Client.

    :param storage_account_name: Storage account name.
    :param storage_key: Storage key.
    :param share_name: Share name
    :param is_async: If True create a Azure share client with async mode.
    :return: Azure share client.
    """
    # Create connection String.
    conn_str = "DefaultEndpointsProtocol={0};AccountName={1};AccountKey={2};EndpointSuffix={3}".format(
        config_storage.protocol,
        storage_account_name,
        storage_key,
        config_storage.suffix,
    )

    # Create Share client.
    if is_async:
        share_client = ShareClientAsync.from_connection_string(conn_str=conn_str, share_name=share_name)
    else:
        share_client = ShareClient.from_connection_string(conn_str=conn_str, share_name=share_name)
    return share_client


def list_files_in_directory_recursive(share_client: ShareClient, dir_path: str) -> Iterable[dict]:
    """Get all files in the directory.

    :param share_client:Azure share client.
    :param dir_path: Directory path.
    """
    for item in list(share_client.list_directories_and_files(dir_path)):
        file_path = dir_path + "/" + item["name"]
        if item["is_directory"]:
            yield from list_files_in_directory_recursive(share_client, file_path)
        else:
            item["path"] = file_path
            yield item


def get_files_size_and_files_path(az_files_info: Iterable) -> Tuple[int, list]:
    """Get files size and files path.

    :param az_files_info: Azure file information list.
    :return: Files size and files path
    """
    file_size: int = 0
    files_path: list = []
    for file_info in az_files_info:
        file_size += file_info["size"]
        files_path.append(file_info["path"])
    return file_size, files_path


def validate_request_data(share_client: ShareClient, dir_path: str) -> bool:
    """Validate request data.

    :param share_client: Azure share client.
    :param dir_path: Directory path
    :return: True if request data is valid.
    """
    is_valid = True

    # Get file client
    file_client = share_client.get_file_client(file_path=dir_path)
    # Check if is a directory path.
    if exist_az_file(file_client):
        is_valid = False
    return is_valid


def exist_az_file(file_client: ShareFileClient) -> bool:
    """Check if existed Azure File.

    :param file_client:
    :type file_client: ShareClient
    :return: True if  Azure file is existed.
    """
    try:
        file_client.get_file_properties()
        return True
    except ResourceNotFoundError:
        return False


def download_files_async(share_client: ShareClientAsync, files_path: list, folder_path: str) -> Any:
    """Download all files in the folder on Azure.

    :param share_client: Share client.
    :param files_path: Files path.
    :param folder_path: Folder path
    :return:
    """
    async def __download_files_async():
        """Download file async."""
        async with share_client:
            tasks = []
            try:
                for path in files_path:
                    # Get Azure file share client.
                    file_client = share_client.get_file_client(file_path=path)

                    # Create temporary folder to store download file from Azure
                    file_name = path.split("/")[-1]
                    path = path.replace(folder_path, "", 1)
                    file_path_tmp = os.path.join(
                        export_path, os.path.sep.join([x for x in path.split("/")[:-1] if x != ''])
                    )
                    os.makedirs(file_path_tmp, exist_ok=True)

                    # Execute download file
                    tasks.append(
                        asyncio.ensure_future(
                            __download_file_async(file_client, file_path_tmp + "/" + file_name)
                        )
                    )
                await asyncio.gather(*tasks)
            finally:
                await share_client.close()

    async def __download_file_async(file_client, file_path: str):
        """Down load a file from Azure file.

        :param file_client: Azure file client.
        :param file_path: File path.
        """
        with open(file_path, "wb") as file_data:
            stream = await file_client.download_file(retry_connect=5, retry_read=5)
            file_data.write(await stream.readall())

    def __get_event_loop():
        """Get event loop."""
        try:
            __loop = asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.SelectorEventLoop())
            __loop = asyncio.get_event_loop()
        return __loop

    def __get_all_file_paths(dir_path: str):
        """Get all files path of directory.

        :param dir_path:Directory path.
        :return:File path list.
        """
        # initializing empty file paths list
        # crawling through directory and subdirectories
        for root, sub_folders, files in os.walk(dir_path):
            for filename in files:
                # join the two strings in order to form the full filepath.
                filepath = os.path.join(root, filename)
                yield filepath

    # Create a temporary directory that will store files downloaded from Azure.
    # The temporary directory will auto deleted.:
    # Refer to: https://docs.python.org/3.8/library/tempfile.html#tempfile.TemporaryDirectory
    with tempfile.TemporaryDirectory(prefix="download_folder_") as temp_path:
        export_path = os.path.join(temp_path, "{}_{}".format(
            datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
            folder_path.split("/")[0]
        ))
        logger.debug("START download directory: {}".format(folder_path))
        with ThreadPoolExecutor(max_workers=config_storage.max_workers):
            loop = __get_event_loop()
            loop.run_until_complete(
                __download_files_async()
            )
        logger.debug("END download directory")

        zip_stream = BytesIO()
        with ZipFile(zip_stream, 'w') as zip_file:
            # writing each file one by one
            for file in __get_all_file_paths(export_path):
                zip_file.write(file, file.replace(export_path, ""))

        # Sets the reference point at the beginning of the file
        zip_stream.seek(0)
    return send_file(
        zip_stream, mimetype="application/zip",
        as_attachment=True,
        attachment_filename=folder_path.split("/")[0] + ".zip"
    )
