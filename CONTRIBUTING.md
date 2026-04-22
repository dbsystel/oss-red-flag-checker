<!--
SPDX-FileCopyrightText: 2023 DB Systel GmbH

SPDX-License-Identifier: Apache-2.0
-->

# Contributing to the Open Source Red Flag Checker

Thank you for your interest in our project. Contributions are welcome. Feel free to open an issue with questions or reporting ideas and bugs, or open pull requests to contribute code.

We are committed to fostering a welcoming, respectful, and harassment-free environment. Be kind!

## Development setup

Starting development is as easy as installing `uv` and running `uv sync` once.

In order to run the project in the new virtual environment, run `uv run ossrfc`.

## Typical contributions

### Add a new check

See commit `cc93fc8b07445e09b5b92de207632d86edc0125d` or
`a51d145b4837f09809752765112ea3782b9d1ab6` as an example:

1. `_licensing.py` (or another file that the new check relates to)
    * Add a new function for the check
1. `_report.py`
    * Add new attributes to the `RepoReport` dataclass if needed
1. `_analysis.py`
    * Add a new evaluation function in which you rate the finding
    * Apply the function in `analyse_report()`
1. `checker.py`
    * Add an ID for the check in the choices for the `--disable` and `--ignore` flags
    * Add the new check function in `check_repo()`
1. `README.md`
    * Add the new searched data point under the "Searched data" headline
    * Add its analysis under the "Analysis based on data" headline


## Commit Messages

This project follows the [**Conventional Commits**](https://www.conventionalcommits.org/) specification for commit messages. This is critical to support proper automation of the release process and changelog generation.

## Pull Requests

When contributing to this project, please open a pull request with a clear description of the changes you have made. The **title of your pull request** should follow the conventional commit format (e.g., `feat: add new feature`, `fix: correct a bug`, etc.).

Ensure to use the **Squash and merge** option when merging your pull request.

Both the PR title and merge method are required for a proper release process (see below).

## Release Process

This project uses [release-please](https://github.com/googleapis/release-please) and its respective GitHub Action to automate the release process. This automatically creates a pull request with the version bump and changelog updates whenever a commit is pushed to the default branch. The version bump is determined by the [conventional commit messages](https://www.conventionalcommits.org/) in the commit history since the last release. Once the release pull request is merged, a new release will be published on GitHub.

The relevant configuration for release-please can be found in the `.github/workflows/release-please.yaml` file and the `release-please-config.json` file. Ensure that the branch and project names are correctly set up in the workflow file and configuration file to match your repository's structure.
