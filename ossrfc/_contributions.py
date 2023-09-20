# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Check a repo for different stats about contributions"""

import logging
from datetime import datetime

from git import Repo
from github import NamedUser, PaginatedList

from ._git import gh_api_call
from ._matching import find_patterns_in_list
from ._report import RepoReport

# Indicators in a user name that it's a bot
BOT_KEYWORDS = [r"(?i)^renovate", r"(?i)^dependabot", r"(?i)^weblate$"]


def _get_contributor_stats(report: RepoReport) -> list:
    """Get contributor stats of a repo by GitHub API"""

    repo = gh_api_call(report.github_, report.github_, "get_repo", full_name_or_id=report.shortname)

    # Get all contributors
    # Limit the list of contributors to 30 users (one API page) which is
    # completely sufficient
    contributors: PaginatedList.PaginatedList[NamedUser.NamedUser] = gh_api_call(
        report.github_, repo, "get_contributors"
    )[:30]

    # Get stats for all contributors: login, type, contributions
    return [
        {
            "login": str(c.login),
            "type": c.type,
            "contributions": int(c.contributions),
            # deactivated because each name resolution costs another API call
            # "name": c.name,
        }
        for c in contributors
    ]


def maintainer_dominance(report: RepoReport) -> None:
    """Check whether a single developer has a large dominance in a project,
    based on contribution stats"""

    # Get all contributors, ordered by contributions
    contributors = _get_contributor_stats(report)

    # Filter out bots
    human_contributors = []
    for contributor in contributors:
        bot_type = contributor["type"] == "Bot"
        bot_name = find_patterns_in_list(BOT_KEYWORDS, contributor["login"])

        # If not detected as human, remove unneeded keys and add to list
        if not bot_type and not bot_name:
            contributor.pop("type")
            human_contributors.append(contributor)
        else:
            logging.debug(
                "Contributor '%s' has been detected as a bot and is therefore not "
                "considered in the predominant contributor check",
                contributor["login"],
            )

    # Add the first 11 contributors to the report for debug purposes
    report.contributors_ = human_contributors[:11]

    # Try to rate the significance of the contributor with the most commits
    # * If they are the only contributor or all the others only have less than 3
    #   contributions, we consider it bad
    # * If the next 10 developers have at least 25% the contributions number of
    #   the main contributor, we consider it somewhat OK, but not good
    # * Otherwise, we consider it good

    # Only one developer
    if len(human_contributors) <= 1:
        report.maintainer_dominance = 1
    # More than 1 developer
    else:
        maindev: dict = human_contributors[0]
        nextdevs: list = human_contributors[1:11]

        maindev_contribs = int(maindev["contributions"])
        nextdevs_contribs = sum(item["contributions"] for item in nextdevs)

        # Calculate percentage of the main dev contributions and add rating
        dominance = round(1 - nextdevs_contribs / maindev_contribs, 2)
        report.maintainer_dominance = dominance


def _extract_all_commits(directory) -> list:
    """Extract all commits from a local Git repository"""
    repo = Repo(directory)
    mainbranch = repo.head.reference

    commits = list(repo.iter_commits(rev=mainbranch))

    # Get a list of all commits of the repo
    return [
        {
            "name": str(c.author),
            "email": c.author.email,
            "date": datetime.utcfromtimestamp(c.authored_date).date(),
            "hash": c.hexsha,
        }
        for c in commits
    ]


def _commit_date_diff(commits: list) -> int:
    """Calculate the date difference in days between today and the last commit"""
    # If no commits, return -1
    if len(commits) == 0:
        return -1

    # compare days difference between today and the last commit date
    newest_commit_date, newest_commit_author = commits[0]["date"], commits[0]["name"]
    logging.debug("Newest detected commit on %s by %s", newest_commit_date, newest_commit_author)
    return (datetime.today().date() - newest_commit_date).days


def old_commits(report: RepoReport):
    """Get the age in days of the newest commit made by a human in a repo"""
    commits = _extract_all_commits(report.repodir_)

    # Filter out commits by bots
    human_commits = []
    bot_commits = []
    for commit in commits:
        bot_name = find_patterns_in_list(BOT_KEYWORDS, commit["name"])

        # If not detected as human, add to list
        if not bot_name:
            human_commits.append(commit)
        else:
            bot_commits.append(commit)

    report.days_since_last_human_commit = _commit_date_diff(human_commits)
    report.days_since_last_bot_commit = _commit_date_diff(bot_commits)
