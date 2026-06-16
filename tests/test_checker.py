# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the --local flag in check_repo."""

from unittest.mock import patch

from github import Github

from ossrfc.checker import check_repo


def test_check_repo_local_skips_clone(fake_repository) -> None:
    """check_repo with local= uses the given path without cloning."""
    repo_url = "https://github.com/dbsystel/playground"

    with patch("ossrfc.checker.clone_or_pull_repository") as mock_clone:
        report = check_repo(
            repo=repo_url,
            gthb=Github(),
            disable=["cla-dco-pulls", "contributions", "commit-age"],
            cache=False,
            local=str(fake_repository),
        )

    mock_clone.assert_not_called()
    assert report.repodir_ == str(fake_repository)
    # File-based checks still ran using the local path
    assert len(report.files_) > 0
