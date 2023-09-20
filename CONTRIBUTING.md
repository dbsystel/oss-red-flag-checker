<!--
SPDX-FileCopyrightText: 2023 DB Systel GmbH

SPDX-License-Identifier: Apache-2.0
-->

# Contributing to the Open Source Red Flag Checker

Thanks for your interest in our project. Contributions are welcome. Feel free to open an issue with questions or reporting ideas and bugs, or open pull requests to contribute code.

We are committed to fostering a welcoming, respectful, and harassment-free environment. Be kind!

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
