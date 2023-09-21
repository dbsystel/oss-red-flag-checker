# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Global init file"""

from importlib.metadata import PackageNotFoundError, version

import git

try:
    __version__ = version("oss-red-flag-checker")
except PackageNotFoundError:
    # package is not installed
    repo = git.Repo(search_parent_directories=True)
    __version__ = repo.head.object.hexsha
