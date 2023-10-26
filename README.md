<!--
SPDX-FileCopyrightText: 2023 DB Systel GmbH

SPDX-License-Identifier: Apache-2.0
-->

# Open Source Red Flag Checker

[![Test suites](https://github.com/dbsystel/oss-red-flag-checker/actions/workflows/test.yaml/badge.svg)](https://github.com/dbsystel/oss-red-flag-checker/actions/workflows/test.yaml)
[![REUSE status](https://api.reuse.software/badge/github.com/dbsystel/oss-red-flag-checker)](https://api.reuse.software/info/github.com/dbsystel/oss-red-flag-checker)
[![The latest version of reuse can be found on PyPI.](https://img.shields.io/pypi/v/oss-red-flag-checker.svg)](https://pypi.org/project/oss-red-flag-checker/)
[![Information on what versions of Python reuse supports can be found on PyPI.](https://img.shields.io/pypi/pyversions/oss-red-flag-checker.svg)](https://pypi.org/project/oss-red-flag-checker/)

This projects evaluates remote repositories by looking for typical red flags like CLAs (Contributor Licensing Agreements) but also indicators for governance, activity or licensing conditions we consider as good.

## Table of contents

* [Features](#features)
* [Installation](#installation)
* [Usage](#usage)
* [Caveats](#caveats)
* [Similar approaches](#similar-approaches)
* [License and copyright](#license-and-copyright)


## Features

[![asciicast](https://asciinema.org/a/TTgMvR8kyzusNCUL7VKlCzIaT.svg)](https://asciinema.org/a/TTgMvR8kyzusNCUL7VKlCzIaT)

### Searched data

The checker looks for the following data in remote repositories:

* CLA (Contributor License Agreement) mentioned in files and pull requests
* DCO (Developer Certificate of Origin) mentioned in files and pull requests
* inbound=outbound mentioned in files
* Existence of LICENSE/COPYING file
* Human and bot contributors to the project (based on Github stats)
* Last commits made by humans and bots

### Analysis based on data

Red flags:

* CLA mentioned in `README` or `CONTRIBUTING` files
* CLA as part of pull request actions/statuses
* No `LICENSE`/`COPYING` file in the repository
* The project only contains contributions by one person
* The last commit is more than 1 year old

Yellow flags:

* The project's main developer made more than 75% contributions than the next 10 most active contributors
* The last human commit is more than 1 year old but there have been newer commits made by bots (like dependabot or renovate)
* The last human commit is more than 90 days old

Green flags:
* DCO mentioned in `README` or `CONTRIBUTING` files
* DCO as part of pull request actions/statuses
* inbound = outbound mentioned in `README` or `CONTRIBUTING` files
* The project has an acceptable contribition distribution by multiple active developers
* The last human commit is less than 90 days old


## Installation

You must have the following dependencies installed:

* `git` >= 1.7.0
* `python` >= 3.8
* `pip3`

You can install the latest release using pip: `pip3 install oss-red-flag-checker`.

The command to run the program afterwards will be `ossrfc`.

### Install/develop using poetry

You can also run this tool via `poetry` that takes care of installing the correct dependencies in a clean environment. This also makes development very easy. We recommend to have at least poetry 1.1.0. Inside of the repository, run `poetry install` once and you are ready to go. If you update the repository, run this command again to fetch new versions and dependencies.

The command to run the programm will be `poetry run ossrfc`.

## Usage

You can find all supported flags by running `ossrfc --help`.

> [!NOTE]
> It is recommended to provide a GitHub Personal Access Token to avoid low API rate limits.
> Either use the `--token` argument or set the `GITHUB_TOKEN` environment variable.

Basic examples:

```sh
# Check a remote repository
ossrfc -r https://github.com/hashicorp/terraform
# Cache the cloned repository so subsequent checks are faster
ossrfc -r https://github.com/hashicorp/terraform --cache
# Return the results as JSON
ossrfc -r https://github.com/hashicorp/terraform --json
# Do not check for CLAs and DCOs in pull requests
ossrfc -r https://github.com/hashicorp/terraform -d cla-dco-pulls
# Ignore findings about contribution distribution
ossrfc -r https://github.com/hashicorp/terraform -i contributions
# Provide a list of repositories to be checked
ossrfc -f repos.txt
```

Here's a possible output in both the Markdown view as well as in JSON:

```md
# Report for hashicorp/terraform (https://github.com/hashicorp/terraform)

* 🚩 Licensing: A mention of Contributor License Agreements in the following file(s): .github/CONTRIBUTING.md
* 🚩 Licensing: A check for Contributor License Agreements in at least one status in pull request(s): 33656
* ✔ Contributions: The project has multiple contributors with an acceptable contribution distribution
* ✔ Contributions: The last commit made by a human is less than 90 days old (1 days)
```

```json
{
  "json_version": "1.0",
  "disabled_checks": [],
  "ignored_flags": [],
  "debug_mode": false,
  "repositories": [
    {
      "url": "https://github.com/hashicorp/terraform",
      "shortname": "hashicorp/terraform",
      "red_flags": [
        "cla",
        "cla"
      ],
      "yellow_flags": [],
      "green_flags": [
        "distributed-contributions",
        "actively-developed"
      ],
      "cla_files": [
        {
          "file": ".github/CONTRIBUTING.md",
          "indicators": [
            "- Contributor License Agreement (CLA): If this is your first contribution to Terraform you will be asked to sign the CLA."
          ]
        }
      ],
      "cla_pulls": [
        {
          "pull_request": 33656,
          "type": "status",
          "url": "https://api.github.com/repos/hashicorp/terraform/statuses/b53d89a08df10c85f6d4c546d2e54d4fab886d67",
          "indicators": [
            "Contributor License Agreement is signed.",
            "license/cla"
          ]
        }
      ],
      "dco_files": [],
      "dco_pulls": [],
      "inoutbound_files": [],
      "licensefiles": [
        "LICENSE"
      ],
      "maintainer_dominance": -2.83,
      "days_since_last_human_commit": 1,
      "days_since_last_bot_commit": 141,
      "analysis": [
        {
          "category": "Licensing",
          "ignored": false,
          "severity": "red",
          "indicator": "A mention of Contributor License Agreements in the following file(s): .github/CONTRIBUTING.md"
        },
        {
          "category": "Licensing",
          "ignored": false,
          "severity": "red",
          "indicator": "A check for Contributor License Agreements in at least one status in pull request(s): 33656"
        },
        {
          "category": "Contributions",
          "ignored": false,
          "severity": "green",
          "indicator": "The project has multiple contributors with an acceptable contribution distribution"
        },
        {
          "category": "Contributions",
          "ignored": false,
          "severity": "green",
          "indicator": "The last commit made by a human is less than 90 days old (1 days)"
        }
      ]
    }
  ]
}
```


## Caveats

### Opinionated analysis

The analysis and decisions for how certain indicators are considered red, yellow or green flags is highly opinionated and represents a snapshot about our (DB Systel GmbH's) current thinking.

You are free to use this tool. If certain criteria is not relevant for you, consider using the `--ignore` or `--disable` flags.

In the long run, it may be feasible to make the ratings configurable. Contributions are welcome if you are interested in it.


## Similar approaches

There are different initiatives that intend to evaluate the health or risks of Open Source projects. All of them have their particular focuses, strengths and weaknesses.

* [OpenSSF](https://openssf.org/) with a focus on security and their [scorecards](https://github.com/ossf/scorecard)
* [CHAOSS](https://chaoss.community/) with a focus on metrics about community health and metrics models

## License and copyright

The content of this repository is licensed under the [Apache 2.0 license](https://www.apache.org/licenses/LICENSE-2.0).

This repository is [REUSE](https://reuse.software) compliant. You can find licensing and copyright information for each file in the file header or accompying files.

The project has been started by DB Systel GmbH. [We welcome contributions from everyone](CONTRIBUTING.md).
