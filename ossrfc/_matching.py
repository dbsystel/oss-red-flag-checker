# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Functions for matching things in things"""

import re


def find_patterns_in_list(patternlist: list, *fields: str):
    """Search for a list of patterns in one or multiple strings. The patterns
    can be regexes"""
    # Add relevant fields in which indicators may be hidden
    validfields = []
    for field in fields:
        if field:
            validfields.append(field)

    # Search for indicators in relevant fields using regex
    matches = [
        match for match in validfields if any(re.search(pattern, match) for pattern in patternlist)
    ]

    return sorted(matches)


def lines_as_list(filepath) -> list:
    """Return all lines of a file as list of lines"""
    with open(filepath, encoding="utf-8") as file:
        return [line.rstrip() for line in file]
