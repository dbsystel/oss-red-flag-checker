#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Check a repository for typical red flags"""

import argparse
import logging
import sys
import tempfile

from github import Github

from . import __version__
from ._analysis import analyse_report
from ._contributions import maintainer_dominance, old_commits
from ._git import (
    clean_cache,
    clone_or_pull_repository,
    create_filelist,
    create_repo_list,
    get_cache_dir,
    gh_token,
    shorten_repo_url,
)
from ._licensing import (
    LICENSEINFO_EXTRA_PATHS,
    cla_in_files,
    cla_or_dco_in_pulls,
    dco_in_files,
    inoutbound,
    licensefile,
)
from ._report import RepoReport, print_json_report, print_text_analysis

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Also print INFO output",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="Also print DEBUG output. Includes --verbose. Prints both JSON and Markdown",
)
parser.add_argument(
    "-j",
    "--json",
    action="store_true",
    help=(
        "Return all output and findings as JSON. It is more detailed than the "
        "default Markdown output and therefore helpful for a detailed analysis"
    ),
)
# Mutually exclusive arguments, but at least one required
parser_repos = parser.add_mutually_exclusive_group(required=True)
parser_repos.add_argument(
    "-r",
    "--repository",
    dest="repourl",
    help=(
        "A single Git repository URL to clone and check. "
        "Example: -r https://github.com/microsoft/vscode"
    ),
)
parser_repos.add_argument(
    "-f",
    "--repo-file",
    dest="repofile",
    help=(
        "A list of Git repository URLs to clone and check, one URL per line. "
        "Use '-' to read from stdin. "
        "Example: -f repos.txt"
    ),
)
parser.add_argument(
    "-c",
    "--cache",
    action="store_true",
    help="Cache cloned remote repositories to speed up subsequent checks",
)
parser.add_argument(
    "-t",
    "--token",
    default="",
    help=(
        "A personal GitHub.com token to lift API limits. Can also be provided via "
        "GITHUB_TOKEN environment variable. If both are given, this argument's value will be used"
    ),
)
parser.add_argument(
    "-d",
    "--disable",
    action="append",
    default=[],
    choices=[
        "cla-files",
        "dco-files",
        "cla-dco-pulls",
        "inbound-outbound",
        "licensefile",
        "contributions",
        "commit-age",
    ],
    help="Disable the search for certain red or green flags. Can be used multiple times.",
)
parser.add_argument(
    "-i",
    "--ignore",
    action="append",
    default=[],
    choices=["cla", "dco", "inbound-outbound", "licensefile", "contributions", "commit-age"],
    help="Ignore certain red or green flags. Can be used multiple times.",
)
# Maintenance "commands"
parser_repos.add_argument(
    "--cache-clean", action="store_true", help="Maintenance: Clean the cache directory, then exit"
)
parser_repos.add_argument(
    "--version", action="store_true", help="Show the version of ossrfc, then exit"
)


def configure_logger(args) -> logging.Logger:
    """Set logging options"""
    log = logging.getLogger()
    logging.basicConfig(
        encoding="utf-8",
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Set loglevel based on --verbose and --debug flag
    if args.debug:
        log.setLevel(logging.DEBUG)
    elif args.verbose:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARN)

    return log


def check_enabled(disabled_checks: list, check_name: str) -> bool:
    """Check if the given check has been disabled by the user via a -d parameter"""
    if check_name in disabled_checks:
        logging.info("Check '%s' has been disabled", check_name)
        return False

    return True


def check_repo(repo: str, gthb: Github, disable: list, cache: bool) -> RepoReport:  # noqa: C901
    """Run all checks on a single repository and return a report"""
    # Initialise the report dataclass
    report = RepoReport()

    report.url = repo
    report.shortname = shorten_repo_url(report.url)

    logging.info("Checking repository %s", report.url)

    # Clone repo, depending on cache status
    if cache:
        report.repodir_ = get_cache_dir(report.url)
    else:
        repodir_object = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        report.repodir_ = repodir_object.name

    clone_or_pull_repository(report.url, report.repodir_)

    # List all first-level files of the repository and relevant extra paths
    # for CLAs
    report.files_ = create_filelist(report.repodir_, *LICENSEINFO_EXTRA_PATHS)

    # Checks that can only run if repo is on github.com
    if "github.com" in report.url:
        # Populate Github object
        report.github_ = gthb

        # CLA/DCO: Search in Pull Request actions and statuses
        if check_enabled(disable, "cla-dco-pulls"):
            cla_or_dco_in_pulls(report)

        # Contributors: Check for dominance of one contributor
        if check_enabled(disable, "contributions"):
            maintainer_dominance(report)
    else:
        report.impossible_checks_.extend(["cla-dco-pulls", "contributions"])
        logging.warning(
            "Repository '%s' is not on github.com, therefore we cannot check for: "
            "CLA/DCO in pull requests, contributor dominance",
            report.url,
        )

    # CLA: Search in in README and CONTRIBUTING files
    if check_enabled(disable, "cla-files"):
        cla_in_files(report)
    # DCO: Search in in README and CONTRIBUTING files
    if check_enabled(disable, "dco-files"):
        dco_in_files(report)

    # inbound=outbound: Search in in README and CONTRIBUTING files
    if check_enabled(disable, "inbound-outbound"):
        inoutbound(report)

    # licensefile: Search for LICENSE/COPYING files
    if check_enabled(disable, "licensefile"):
        licensefile(report)

    # licensefile: Search for LICENSE/COPYING files
    if check_enabled(disable, "commit-age"):
        old_commits(report)

    # Delete temporary directory for a remote repo if it shall not be cached
    if not cache:
        logging.info("Deleting temporary directory in which remote repository has been cloned to")
        repodir_object.cleanup()

    # Return finalised report to be added list of reports
    return report


def main():
    """Main function"""
    args = parser.parse_args()

    # Set logger settings
    configure_logger(args=args)

    # Execute maintenance commands if set, then exit
    if args.cache_clean:
        clean_cache()
    if args.version:
        print("oss-red-flag-checker " + __version__)
    if any([args.cache_clean, args.version]):
        sys.exit(0)

    repos = create_repo_list(args.repourl, args.repofile)

    # Get GitHub token from argument or environment, create GitHub object
    gthb = gh_token(args.token)

    # Loop checks for each repository
    report_list = []
    for repo in repos:
        # Search for indicators in the repository
        report = check_repo(repo, gthb, args.disable, args.cache)
        # Analyse and evaluate the findings
        analyse_report(report, args.ignore)
        # Add full report to report list
        report_list.append(report)

    if args.json or args.debug:
        print_json_report(report_list, args.disable, args.debug, args.ignore)
    if not args.json or args.debug:
        print_text_analysis(report_list)


if __name__ == "__main__":
    main()
