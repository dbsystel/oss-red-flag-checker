# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Functions that analyse and evaluate the findings"""

from ._report import RepoReport


def _evaluate_cla_files(report: RepoReport) -> None:
    """Evaluate CLA findings in files"""
    if report.cla_files:
        report.red_flags.append("cla")
        cla_filelist = [finding["file"] for finding in report.cla_files]
        report.analysis.append(
            {
                "category": "Licensing",
                "ignored": "cla" in report.ignorelist_,
                "severity": "red",
                "indicator": (
                    "A mention of Contributor License Agreements in the following file(s): "
                    f"{', '.join(cla_filelist)}"
                ),
            }
        )


def _evaluate_cla_pulls(report: RepoReport) -> None:
    """Evaluate CLA findings in pull requests"""
    if report.cla_pulls:
        report.red_flags.append("cla")
        # Get all affected pull request numbers and CI types and make them unique
        # Note: In the current state, there shouldn't be more than one of each,
        # but this is future-proof now
        pr_list = list({str(finding["pull_request"]) for finding in report.cla_pulls})
        ci_types = list({finding["type"] for finding in report.cla_pulls})

        report.analysis.append(
            {
                "category": "Licensing",
                "ignored": "cla" in report.ignorelist_,
                "severity": "red",
                "indicator": (
                    "A check for Contributor License Agreements in at least one "
                    f"{' and one '.join(ci_types)} in pull request(s): {', '.join(pr_list)}"
                ),
            }
        )


def _evaluate_dco_files(report: RepoReport) -> None:
    """Evaluate DCO findings in files"""
    if report.dco_files:
        report.green_flags.append("dco")
        dco_filelist = [finding["file"] for finding in report.dco_files]
        report.analysis.append(
            {
                "category": "Licensing",
                "ignored": "dco" in report.ignorelist_,
                "severity": "green",
                "indicator": (
                    "A mention of Developer Certificate of Origin in the following file(s): "
                    f"{', '.join(dco_filelist)}"
                ),
            }
        )


def _evaluate_dco_pulls(report: RepoReport) -> None:
    """Evaluate DCO findings in pull requests"""
    if report.dco_pulls:
        report.green_flags.append("dco")
        # Get all affected pull request numbers and CI types and make them unique
        # Note: In the current state, there shouldn't be more than one of each,
        # but this is future-proof now
        pr_list = list({str(finding["pull_request"]) for finding in report.dco_pulls})
        ci_types = list({finding["type"] for finding in report.dco_pulls})

        report.analysis.append(
            {
                "category": "Licensing",
                "ignored": "dco" in report.ignorelist_,
                "severity": "green",
                "indicator": (
                    "A check for Developer Certificate of Origin in at least one "
                    f"{' and one '.join(ci_types)} in pull request(s): {', '.join(pr_list)}"
                ),
            }
        )


def _evaluate_inoutbound_files(report: RepoReport) -> None:
    """Evaluate inbound=outbound findings in files"""
    if report.inoutbound_files:
        report.green_flags.append("inbound=outbound")
        inoutbound_filelist = [finding["file"] for finding in report.inoutbound_files]
        report.analysis.append(
            {
                "category": "Licensing",
                "ignored": "inbound-outbound" in report.ignorelist_,
                "severity": "green",
                "indicator": (
                    "A mention of inbound=outbound in the following file(s): "
                    f"{', '.join(inoutbound_filelist)}"
                ),
            }
        )


def _evaluate_licensefile(report: RepoReport) -> None:
    """Evaluate missing license file findings"""
    if not report.licensefiles:
        report.red_flags.append("no-license-file")
        report.analysis.append(
            {
                "category": "Licensing",
                "ignored": "licensefile" in report.ignorelist_,
                "severity": "red",
                "indicator": "The project does not seem to have a LICENSE or COPYING file",
            }
        )


def _evaluate_maintainer_dominance(report: RepoReport) -> None:
    """Evaluate maintainer dominance"""

    if report.maintainer_dominance == 1:
        report.red_flags.append("only-one-contributor")
        report.analysis.append(
            {
                "category": "Contributions",
                "ignored": "contributions" in report.ignorelist_,
                "severity": "red",
                "indicator": "The project only has one contributor",
            }
        )
    elif report.maintainer_dominance > 0.75:
        report.yellow_flags.append("predominant-main-contributor")
        report.analysis.append(
            {
                "category": "Contributions",
                "ignored": "contributions" in report.ignorelist_,
                "severity": "yellow",
                "indicator": (
                    "The top contributor has contributed more than 75% "
                    "of the contributions of the next 10 contributors"
                ),
            }
        )
    elif report.maintainer_dominance == -1:
        # check has been disabled
        pass
    else:
        report.green_flags.append("distributed-contributions")
        report.analysis.append(
            {
                "category": "Contributions",
                "ignored": "contributions" in report.ignorelist_,
                "severity": "green",
                "indicator": (
                    "The project has multiple contributors with an acceptable "
                    "contribution distribution"
                ),
            }
        )


def _evaluate_commit_date(report: RepoReport) -> None:
    """Evaluate newest commit date by both humans and bots"""

    hcom = report.days_since_last_human_commit
    bcom = report.days_since_last_bot_commit

    # No commit ever by both humans and bots. Either an empty repo (unlikely) or
    # the check has been disabled as -1 is the default value
    if hcom == -1 and bcom == -1:
        pass
    # No commit ever or older than 1 year by humans or bots
    elif (hcom > 365 or hcom == -1) and (bcom > 365 or bcom == -1):
        report.red_flags.append("orphaned")
        report.analysis.append(
            {
                "category": "Contributions",
                "ignored": "commit-age" in report.ignorelist_,
                "severity": "red",
                "indicator": (
                    "The last commit made by a human or a bot is more than 1 year old "
                    f"({hcom} days since last human commit)"
                ),
            }
        )
    # Human commit older than 1 year, but bot commit newer than 1 year
    elif (hcom > 365 or hcom == -1) and (bcom < 365):
        report.yellow_flags.append("orphaned-but-bot")
        report.analysis.append(
            {
                "category": "Contributions",
                "ignored": "commit-age" in report.ignorelist_,
                "severity": "yellow",
                "indicator": (
                    "The last commit made by a human is more than 1 year old but "
                    "there have been newer commits made by bots "
                    f"({hcom} days since last human commit, {bcom} since last bot commit)"
                ),
            }
        )
    # Human commit older than 90 days
    elif hcom > 90:
        report.yellow_flags.append("infrequent-updates")
        report.analysis.append(
            {
                "category": "Contributions",
                "ignored": "commit-age" in report.ignorelist_,
                "severity": "yellow",
                "indicator": (
                    "The last commit made by a human is more than 90 days old " f"({hcom} days)"
                ),
            }
        )
    # Human commit newer than 90 days
    else:
        report.green_flags.append("actively-developed")
        report.analysis.append(
            {
                "category": "Contributions",
                "ignored": "commit-age" in report.ignorelist_,
                "severity": "green",
                "indicator": (
                    "The last commit made by a human is less than 90 days old " f"({hcom} days)"
                ),
            }
        )


def analyse_report(report: RepoReport, ignorelist: list) -> None:
    """Analyse the report and evaluate the findings"""
    # Add list of ignored findings to report
    report.ignorelist_ = ignorelist

    # Evaluate CLA findings in files
    _evaluate_cla_files(report)

    # Evaluate CLA findings in pull requests
    _evaluate_cla_pulls(report)

    # Evaluate DCO findings in files
    _evaluate_dco_files(report)

    # Evaluate DCO findings in pull requests
    _evaluate_dco_pulls(report)

    # Evaluate inbound=outbound findings in files
    _evaluate_inoutbound_files(report)

    # Evaluate licensefile findings in files
    _evaluate_licensefile(report)

    # Evaluate contribution ratio
    _evaluate_maintainer_dominance(report)

    # Evaluate commit dates
    _evaluate_commit_date(report)
