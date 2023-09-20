# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Check a repository for licensing issues"""

import logging
import os

from ._git import gh_api_call
from ._matching import find_patterns_in_list, lines_as_list
from ._report import RepoReport

# Key words for CLA
CLA_KEYWORDS = [
    r"(?i)contribut(or|ion)s? licens(e|ing) agreement",
    r"\bCLA(s)?\b",  # clear-cut appearance of CLA or CLAs
    "license/cla",  # https://github.com/cla-assistant/cla-assistant
    "cla-bot",  # https://github.com/apps/cla-bot
]
# Key words for DCO
DCO_KEYWORDS = [
    r"(?i)developers? certificate of origin",
    r"\DCO\b",  # clear-cut appearance of DCO
    "Signed-off-by",
]
# Key words for inbound=outbound
INOUTBOUND_KEYWORDS = [r"(?i)inbound[ ]*=[ ]*outbound"]
# Additional non-first-level paths that shall be searched in for licensing
# information
LICENSEINFO_EXTRA_PATHS = [".github"]


def cla_in_files(report: RepoReport):
    """Search for CLA requirements in README and CONTRIBUTING files"""
    # Find CONTRIBUTING and README files
    report.cla_searched_files_ = find_patterns_in_list(
        [r"(?i)^(|.*\/)(readme|contributing)(\.[a-z]+)?$"], *report.files_
    )

    for file in report.cla_searched_files_:
        file_path = os.path.join(report.repodir_, file)
        file_lines = lines_as_list(file_path)

        if cla_matches := find_patterns_in_list(CLA_KEYWORDS, *file_lines):
            report.cla_files.append(
                {
                    "file": file,
                    "indicators": cla_matches,
                }
            )


def dco_in_files(report: RepoReport):
    """Search for DCO requirements in README and CONTRIBUTING files"""
    # Find CONTRIBUTING and README files
    report.dco_searched_files_ = find_patterns_in_list(
        [r"(?i)^(|.*\/)(readme|contributing)(\.[a-z]+)?$"], *report.files_
    )

    for file in report.dco_searched_files_:
        file_path = os.path.join(report.repodir_, file)
        file_lines = lines_as_list(file_path)

        if dco_matches := find_patterns_in_list(DCO_KEYWORDS, *file_lines):
            report.dco_files.append(
                {
                    "file": file,
                    "indicators": dco_matches,
                }
            )


def _cla_or_dco_in_checks(report, check_runs, newest_pull):
    """Part of cla_or_dco_in_pulls(), checking action runs pull requests"""
    for check in check_runs:
        logging.debug("Checking check-run %s", check.html_url)
        # If we have a CLA match, add to report
        if cla_matches := find_patterns_in_list(
            CLA_KEYWORDS, check.name, check.output.title, check.output.summary
        ):
            report.cla_pulls.append(
                {
                    "pull_request": newest_pull.number,
                    "type": "action",
                    "url": check.html_url,
                    "indicators": cla_matches,
                }
            )

        # If we have a DCO match, add to report
        if dco_matches := find_patterns_in_list(
            DCO_KEYWORDS, check.name, check.output.title, check.output.summary
        ):
            report.dco_pulls.append(
                {
                    "pull_request": newest_pull.number,
                    "type": "action",
                    "url": check.html_url,
                    "indicators": dco_matches,
                }
            )


def _cla_or_dco_in_statuses(report, statuses, newest_pull):
    """Part of cla_or_dco_in_pulls(), checking statuses in pull requests"""
    for status in statuses:
        logging.debug("Checking status %s", status.url)
        # If we have a CLA match, add to report
        if cla_matches := find_patterns_in_list(CLA_KEYWORDS, status.description, status.context):
            report.cla_pulls.append(
                {
                    "pull_request": newest_pull.number,
                    "type": "status",
                    "url": status.url,
                    "indicators": cla_matches,
                }
            )

        # If we have a DCO match, add to report
        if dco_matches := find_patterns_in_list(DCO_KEYWORDS, status.description, status.context):
            report.dco_pulls.append(
                {
                    "pull_request": newest_pull.number,
                    "type": "status",
                    "url": status.url,
                    "indicators": dco_matches,
                }
            )


def cla_or_dco_in_pulls(report: RepoReport) -> None:
    """Search for CLA or DCO requirements in Pull Requests"""

    repo = gh_api_call(report.github_, report.github_, "get_repo", full_name_or_id=report.shortname)

    # Get newest Pull Request against default branch as we assume that CLA
    # checks will definitely be activated for PRs against it
    basebranch = repo.default_branch
    try:
        newest_pull = gh_api_call(
            report.github_,
            repo,
            "get_pulls",
            sort="updated",
            state="all",
            direction="desc",
            base=basebranch,
        )[0]

    # List of pull requests is empty. We try it without the base branch first
    except IndexError:
        logging.debug(
            "Searching for pull request against base '%s' failed. Trying without base...",
            basebranch,
        )
        try:
            newest_pull = gh_api_call(
                report.github_, repo, "get_pulls", sort="updated", state="all", direction="desc"
            )[0]

        # Still no pull request returned. We assume there is no PR at all and
        # stop the function
        except IndexError:
            logging.warning("Searching for pull requests failed, probably because there are none")
            return

    logging.debug("Checking Pull Request #%s", newest_pull.number)

    # Get newest commit from newest PR
    newest_commit = gh_api_call(report.github_, newest_pull, "get_commits", reverse=True)[0]

    logging.debug("Checking commit %s", newest_commit.html_url)

    # Go through all checks runs (actions) for this commit, search for CLA and
    # DCO indicators
    check_runs = gh_api_call(report.github_, newest_commit, "get_check_runs")
    _cla_or_dco_in_checks(report, check_runs, newest_pull)

    # Go through all statuses runs for this commit, search for CLA and DCO indicators
    statuses = gh_api_call(report.github_, newest_commit, "get_statuses")
    _cla_or_dco_in_statuses(report, statuses, newest_pull)


def inoutbound(report: RepoReport):
    """Search for inbound=outbound rules in README and CONTRIBUTING files"""
    # Find CONTRIBUTING and README files
    report.inoutbound_searched_files_ = find_patterns_in_list(
        [r"(?i)^(|.*\/)(readme|contributing)(\.[a-z]+)?$"], *report.files_
    )

    for file in report.inoutbound_searched_files_:
        file_path = os.path.join(report.repodir_, file)
        file_lines = lines_as_list(file_path)

        if inoutbound_matches := find_patterns_in_list(INOUTBOUND_KEYWORDS, *file_lines):
            report.inoutbound_files.append(
                {
                    "file": file,
                    "indicators": inoutbound_matches,
                }
            )


def licensefile(report: RepoReport):
    """Search for a LICENSE/COPYING file. Also includes LICENSES directory
    according to REUSE. If absent, it's a red flag"""
    # Find CONTRIBUTING and README files or LICENSES directory
    report.licensefiles = find_patterns_in_list([r"^(LICENSE|License|COPYING)"], *report.files_)
