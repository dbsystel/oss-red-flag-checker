# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Git, GitHub and repository functions"""

import fileinput
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from shutil import rmtree
from time import sleep
from typing import Optional

from git import GitCommandError, Repo
from github import BadCredentialsException, Github, RateLimitExceededException
from platformdirs import user_cache_path


def create_repo_list(repourl, repofile):
    """Compile list of one or multiple repositories depending on given arguments"""
    if repourl:
        return [repourl]

    try:
        repos = []
        for line in fileinput.input(repofile):
            line = line.strip()
            # Ignore lines starting with #
            if line and not line.startswith("#"):
                repos.append(line)

        return repos

    except FileNotFoundError:
        sys.exit(f"ERROR: File {repofile} not found.")


def create_filelist(directory: str, *extra_dirs: str) -> list:
    """Create a list of files in the root level of the directory, and a
    list of relative directory names that shall also be inspected"""
    filelist = [os.path.join(file) for file in os.listdir(directory)]

    # Go through extra dirs, list their files, and prepend extra dir's name
    for extra_dir in extra_dirs:
        extra_dir_path = os.path.join(directory, extra_dir)
        if os.path.isdir(extra_dir_path):
            filelist.extend([os.path.join(extra_dir, file) for file in os.listdir(extra_dir_path)])

    return sorted(filelist)


def url_to_dirname(url: str) -> str:
    """Shorten and escape a repository URL so it can be used as a directory name"""
    # Remove http schema
    url = re.sub(r"^https?://", "", url)
    # Replace disallowed characters with underscores
    unix_escaped = re.sub(r"[^a-zA-Z0-9\-_]", "_", url)
    # Windows has some more limitations
    win_escaped = re.sub(r'[\\/:*?"<>|]', "_", unix_escaped)
    # Trim or truncate the name if it's too long (Windows limit: 260 characters)
    return win_escaped[:260]


def clean_cache() -> None:
    """Clean the whole cache directory"""
    cache_dir = user_cache_path("oss-red-flag-checker")
    logging.debug("Attempting to delete %s", cache_dir)
    try:
        rmtree(cache_dir)
        print("Cache cleaned")
    except FileNotFoundError:
        print("Cache directory does not exist")


def get_cache_dir(url: str) -> str:
    """Create/get a cache directory for the remote repository"""
    cachedir = os.path.join(user_cache_path("oss-red-flag-checker"), url_to_dirname(url))

    if not os.path.isdir(cachedir):
        logging.info("Creating cache directory: %s", cachedir)
        os.makedirs(cachedir)

    return cachedir


def clone_or_pull_repository(repo_url: str, local_path: str):
    """Clone a repository if local directory does not exist yet, or pull if it does"""
    # Local directory isn't empty so we assume it's been cached before
    if os.listdir(local_path):
        repo = Repo(local_path)
        if repo.head.is_detached or repo.is_dirty():
            logging.error(
                "HEAD of repository %s is detached or dirty. Did you make "
                "manual changes in the cached repository (%s)?",
                repo_url,
                local_path,
            )
        try:
            # fetch origin
            repo.remotes.origin.fetch()
            # reset --hard to origin/$branchname, assuming that the user did not
            # change the branch and that the project did not change their main
            # branch
            repo.git.reset(f"origin/{repo.head.ref}", "--hard")
        except (GitCommandError, TypeError) as exc:
            logging.error("Fetching and resetting to the newest commits failed: %s", exc)

        logging.info(
            "Repository already exists and has been successfully updated in %s", local_path
        )

    # Directory is empty, so probably a temp dir or first-time cache
    else:
        repo = Repo.clone_from(
            url=repo_url,
            to_path=local_path,
            # NOTE: I'm not sure how this works with fetching newer commits
            depth=100,  # do not fetch all commits
        )
        logging.info(
            "Repository didn't exist yet locally and has been successfully cloned to %s",
            local_path,
        )


def shorten_repo_url(url: str) -> str:
    """
    Convert a long repo URL to a more handy string.
    Example: https://github.com/dbsystel/foobar.git -> dbsystel/foobar
    """
    # Remove trailing slashes and spaces
    url = url.strip().strip("/")
    # Only last two segments of the URL's path
    name = "/".join(url.split("/")[-2:])
    # Remove .git if present
    if name.endswith(".git"):
        name = name[:-4]

    return name


def gh_token(token: str) -> Optional[Github]:
    """Get the GitHub token from argument or environment, while argument
    overrides"""
    if token:
        pass
    elif "GITHUB_TOKEN" in os.environ and os.environ["GITHUB_TOKEN"]:
        token = os.environ["GITHUB_TOKEN"]
    else:
        token = ""
        logging.warning(
            "No token for GitHub set. GitHub API limits for unauthorized requests "
            "are very low so you may quickly run into waiting times. "
            "Either use the --token argument or set the GITHUB_TOKEN environment "
            "variable to fix this."
        )

    # Log in with token
    if token:
        gthb = gh_login(token)
        try:
            # Make a test API request
            _ = gthb.get_user().login
            # Get current rate information from GitHub, especially the reset time
            logging.debug("Current rate limit: %s", gthb.get_rate_limit().core)
        except BadCredentialsException:
            logging.error(
                "The provided GitHub token seems to be invalid. Continuing without authentication"
            )
            # Return anonymous GitHub object
            gthb = Github()

        return gthb

    # No token provided, return empty Github object
    return Github()


def gh_login(token: str = "") -> Github:
    """Login to GitHub with an optional token"""
    if token:
        return Github(token)

    return Github()


def _gh_handle_ratelimit(gthb: Github, error_msg) -> None:
    """Activated if a rate limit exception occurred. Gets the current rate limit
    and reset time, and waits until then"""
    logging.warning(
        "You exceeded the GitHub API rate limit. Consider using a token (-t) "
        "which drastically lifts API limits. Error message: %s",
        error_msg,
    )

    # Get current rate information from GitHub, especially the reset time
    rate = gthb.get_rate_limit().core
    logging.debug("Current rate limit: %s", rate)

    # Sleep 5 seconds longer than API limit
    waituntil = rate.reset + timedelta(seconds=5)
    waitseconds = int((waituntil - datetime.utcnow()).total_seconds())

    logging.warning("Waiting %s seconds for end of API limit time", waitseconds)

    sleep(waitseconds)


def gh_api_call(gthb: Github, ghobject, method: str, reverse: bool = False, **kwargs):
    """Generic wrapper to make GitHub API calls via PyGithub while catching API
    limits"""
    result = None
    while not result:
        try:
            api_result = getattr(ghobject, method)(**kwargs)
            # Apply reversed order if requested
            result = api_result.reversed if reverse else api_result
        except RateLimitExceededException as exc:
            _gh_handle_ratelimit(gthb, exc)

    return result
