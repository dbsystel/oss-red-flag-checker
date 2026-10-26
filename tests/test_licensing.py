# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for _matching.py."""

from pathlib import Path

import pytest

from ossrfc._analysis import analyse_report
from ossrfc._git import create_filelist
from ossrfc._licensing import cla_in_files, dco_in_files, inoutbound, licensefile
from ossrfc._report import RepoReport


@pytest.mark.parametrize(
    "filename",
    [
        "LICENSE",
        "License",
        "COPYING",
        "LICENSE.md",
        "license",
        "license.md",
        "LiCeNsE.txt",
        "copying",
        "copying.md",
        "cOpYiNg.rst",
    ],
)
def test_licensefile_case_insensitive(tmp_path: Path, filename: str) -> None:
    """Recognize license files without reporting a missing-license red flag."""
    (tmp_path / filename).write_text("License text", encoding="utf-8")
    report = RepoReport(files_=create_filelist(str(tmp_path)))

    licensefile(report)
    analyse_report(report, [])

    assert report.licensefiles == [filename]
    assert "no-license-file" not in report.red_flags


def test_licensefile_reuse_directory(tmp_path: Path) -> None:
    """Continue recognizing the REUSE LICENSES directory."""
    (tmp_path / "LICENSES").mkdir()
    (tmp_path / "LICENSES" / "MIT.txt").write_text("License text", encoding="utf-8")
    report = RepoReport(files_=create_filelist(str(tmp_path)))

    licensefile(report)
    analyse_report(report, [])

    assert report.licensefiles == ["LICENSES"]
    assert "no-license-file" not in report.red_flags


def test_licensefile_missing(tmp_path: Path) -> None:
    """Keep reporting repositories that have no license file."""
    (tmp_path / "README.md").write_text("A project without a license", encoding="utf-8")
    report = RepoReport(files_=create_filelist(str(tmp_path)))

    licensefile(report)
    analyse_report(report, [])

    assert report.licensefiles == []
    assert "no-license-file" in report.red_flags


def test_cla_in_files(fake_report: RepoReport) -> None:
    """Search for CLA requirements in README and CONTRIBUTING files."""
    cla_in_files(fake_report)

    # Have all relevant files been searched?
    assert fake_report.cla_searched_files_ == [
        "CONTRIBUTING.adoc",
        "CONTRIBUTING.md",
        "README.adoc",
        "README.md",
    ]

    # Did you find the correct keywords in the respective files?
    assert fake_report.cla_files == [
        {
            "file": "CONTRIBUTING.adoc",
            "indicators": ["You have to sign a CLA in order to contribute"],
        },
        {"file": "README.md", "indicators": ["You have to sign a CLA in order to contribute"]},
    ]


def test_dco_in_files(fake_report: RepoReport) -> None:
    """Search for DCO requirements in README and CONTRIBUTING files."""
    dco_in_files(fake_report)

    # Have all relevant files been searched?
    assert fake_report.dco_searched_files_ == [
        "CONTRIBUTING.adoc",
        "CONTRIBUTING.md",
        "README.adoc",
        "README.md",
    ]

    # Did you find the correct keywords in the respective files?
    assert fake_report.dco_files == [
        {
            "file": "CONTRIBUTING.md",
            "indicators": ["A Developer Certificate of Origin is required"],
        },
    ]


def test_inoutbound(fake_report: RepoReport) -> None:
    """Search for inbound=outbound rules in README and CONTRIBUTING files."""
    inoutbound(fake_report)

    # Have all relevant files been searched?
    assert fake_report.inoutbound_searched_files_ == [
        "CONTRIBUTING.adoc",
        "CONTRIBUTING.md",
        "README.adoc",
        "README.md",
    ]

    # Did you find the correct keywords in the respective files?
    assert fake_report.inoutbound_files == [
        {
            "file": "README.adoc",
            "indicators": [
                "This project is covered under the simple inbound= outbound licensing rule."
            ],
        },
    ]
