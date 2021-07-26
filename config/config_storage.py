"""Configuration  storage."""
# All Rights Reserved. Copyright (c) 2021 Hitachi Solutions, Ltd.

import os


protocol = "https"
suffix = "core.windows.net"
sys_storage_account_name = os.environ["SYSTEM_STORAGE_NAME"]
sys_storage_key = os.environ["SYSTEM_STORAGE_KEY"]

size_limit_folder = 1073741824  # 1GB = 1024 * 1024 * 1024 Bytes
"""Size limit of the folder (Unit is bytes)"""

max_workers = 10
"""Max workers. If MAX_WORKERS is None, 
 it will default to the number of processors on the machine, multiplied by 5.
"""
