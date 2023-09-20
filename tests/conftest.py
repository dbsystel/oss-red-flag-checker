# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Global fixtures and configuration."""

import os
import shutil
from pathlib import Path

import pytest

from ossrfc._git import create_filelist, shorten_repo_url
from ossrfc._licensing import CLA_KEYWORDS
from ossrfc._report import RepoReport

TESTS_DIRECTORY = Path(__file__).parent.resolve()
RESOURCES_DIRECTORY = TESTS_DIRECTORY / "resources"


def _create_fake_repository(tmpdir_factory) -> Path:
    """Create a temporary fake repository."""
    directory = Path(str(tmpdir_factory.mktemp("fake_repository")))
    for file_ in (RESOURCES_DIRECTORY / "fake_repository").iterdir():
        if file_.is_file():
            shutil.copy(file_, directory / file_.name)
        elif file_.is_dir():
            shutil.copytree(file_, directory / file_.name)

    # Get rid of those pesky pyc files.
    shutil.rmtree(directory / "src/__pycache__", ignore_errors=True)

    os.chdir(directory)
    return directory


@pytest.fixture()
def fake_repository(tmpdir_factory):
    """Return a fake repository directory"""
    return _create_fake_repository(tmpdir_factory)


@pytest.fixture()
def fake_report(tmpdir_factory) -> RepoReport:
    """Create a temporary empty RepoReport"""
    report = RepoReport()

    report.url = "https://github.com/dbsystel/playground"
    report.shortname = shorten_repo_url(report.url)
    report.repodir_ = str(_create_fake_repository(tmpdir_factory))
    report.files_ = create_filelist(report.repodir_)

    return report


@pytest.fixture
def cla_keywords():
    """CLA_KEYWORDS"""
    return CLA_KEYWORDS


@pytest.fixture
def cla_input_data_match_true():
    """Test strings for CLA that shall match"""
    return [
        "Contribution License Agreement",
        "contributor licensing Agreement",
        "## CLA",
        "We require a signed CLA.",
        "agent: license/cla",
        "user: cla-bot",
    ]


@pytest.fixture
def cla_input_data_match_false():
    """Test strings for CLA that NOT shall match"""
    return ["Much CLArity", "Contributors"]
