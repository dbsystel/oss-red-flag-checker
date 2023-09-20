# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for _matching.py"""

from ossrfc._licensing import cla_in_files, dco_in_files, inoutbound
from ossrfc._report import RepoReport


def test_cla_in_files(fake_report: RepoReport):
    """Search for CLA requirements in README and CONTRIBUTING files"""

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


def test_dco_in_files(fake_report: RepoReport):
    """Search for DCO requirements in README and CONTRIBUTING files"""

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


def test_inoutbound(fake_report: RepoReport):
    """Search for inbound=outbound rules in README and CONTRIBUTING files"""

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
