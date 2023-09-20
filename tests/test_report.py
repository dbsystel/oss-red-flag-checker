# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for _matching.py"""

from ossrfc._report import RepoReport


def test_report(fake_report: RepoReport):
    """Test whether the report setup worked well"""

    assert fake_report.shortname == "dbsystel/playground"

    assert fake_report.files_ == [
        "CONTRIBUTING.adoc",
        "CONTRIBUTING.md",
        "LICENSES",
        "README.adoc",
        "README.md",
        "src",
    ]
