# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Dataclass holding the analysis of a repository and functions to display it"""

import json
from dataclasses import asdict, dataclass, field
from io import StringIO

from github import Github
from termcolor import colored

# Version of the returned JSON in case there will be breaking changes
JSON_VERSION = "1.0"


@dataclass
class RepoReport:  # pylint: disable=too-many-instance-attributes
    """Data class that holds a report about a repository"""

    # NOTE: attributes ending with _ are removed in the final output as they are
    # only relevant for technical reasons

    url: str = ""
    shortname: str = ""
    repodir_: str = ""
    impossible_checks_: list = field(default_factory=list)
    github_: Github = Github()
    files_: list = field(default_factory=list)
    red_flags: list = field(default_factory=list)
    yellow_flags: list = field(default_factory=list)
    green_flags: list = field(default_factory=list)
    ignorelist_: list = field(default_factory=list)
    cla_searched_files_: list = field(default_factory=list)
    cla_files: list = field(default_factory=list)
    cla_pulls: list = field(default_factory=list)
    dco_searched_files_: list = field(default_factory=list)
    dco_files: list = field(default_factory=list)
    dco_pulls: list = field(default_factory=list)
    inoutbound_searched_files_: list = field(default_factory=list)
    inoutbound_files: list = field(default_factory=list)
    licensefiles: list = field(default_factory=list)
    # Contribution percentage of maintainer vs. next 10 most contributing devs
    # Default value is -1, meaning that no commit happened. See also days_since...
    maintainer_dominance: int = -1
    contributors_: list = field(default_factory=list)
    days_since_last_human_commit: int = -1
    days_since_last_bot_commit: int = -1
    analysis: list = field(default_factory=list)


def _dictify_report(report: RepoReport) -> dict:
    """Removes temporary/technical keys/attributes and returns a dictionary of
    the report, based on the dataclass"""
    return asdict(report)


def _listdict_reports(report: RepoReport) -> list:
    """Make a single or RepoReports a list of dicts"""
    if isinstance(report, list):
        report_list = []
        for single_report in report:
            report_list.append(_dictify_report(single_report))
    else:
        report_list = [_dictify_report(report)]

    return report_list


def _dict_skeleton() -> dict:
    """Create a skeleton for the final report"""
    return {
        "json_version": JSON_VERSION,
        "disabled_checks": [],
        "ignored_flags": [],
        "debug_mode": False,
        "repositories": [],
    }


def print_json_report(report: RepoReport, disabled_checks: list, debug: bool, ignore: list) -> None:
    """Print the raw result of the linting in a JSON"""
    report_dict = _dict_skeleton()

    report_dict["disabled_checks"] = disabled_checks
    report_dict["ignored_flags"] = ignore
    report_dict["debug_mode"] = debug
    report_dict["repositories"] = _listdict_reports(report)

    # Collect keys that end with an underscore which we consider to be temporary
    # attributes. If not in DEBUG mode, remove them from the dict
    for repo_report in report_dict["repositories"]:
        if not debug:
            removed_keys = []
            for key in repo_report.keys():
                if key.endswith("_"):
                    removed_keys.append(key)

            # Actually remove keys
            for key in removed_keys:
                repo_report.pop(key)
        # Even in Debug mode, delete github_ object
        else:
            repo_report.pop("github_")

    print(json.dumps(report_dict, indent=2, ensure_ascii=False))


def print_text_analysis(report_list: list):  # noqa: C901
    """Print a plain text analysis of the findings"""

    result = []
    # Go through each report separately
    for report in report_list:
        redflag = []
        yellowflag = []
        greenflag = []
        ignored = 0
        # Look at each analysed finding, check if it's ignored, and compile text
        for finding in report.analysis:
            if finding["ignored"]:
                ignored += 1
            else:
                if finding["severity"] == "red":
                    icon, category, indicator = "🚩", finding["category"], finding["indicator"]
                    redflag.append(f"{icon} {category}: {indicator}")
                if finding["severity"] == "yellow":
                    icon, category, indicator = "⚠️", finding["category"], finding["indicator"]
                    yellowflag.append(f"{icon} {category}: {indicator}")
                if finding["severity"] == "green":
                    icon, category, indicator = "✔", finding["category"], finding["indicator"]
                    greenflag.append(f"{icon} {category}: {indicator}")

        # Print text nicely if there was any finding
        out = StringIO()
        if report.analysis:
            # Headline for report
            out.write(colored(f"# Report for {report.shortname} ({report.url})\n", attrs=["bold"]))

            # Print findings in order of severity
            for msg in redflag + yellowflag + greenflag:
                out.write(f"\n* {msg}")

            # Print ignored finding count, if any
            if ignored:
                out.write(f"\n* 💡 There were {ignored} finding(s) that you explicitely ignored")

        if report.impossible_checks_:
            out.write(
                "\n* 💡 The follow checks could not be executed: "
                f"{', '.join(report.impossible_checks_)}"
            )

        result.append(out.getvalue())

    print("\n\n".join(result))
