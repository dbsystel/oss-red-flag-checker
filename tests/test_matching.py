# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for _matching.py"""

from ossrfc._matching import find_patterns_in_list, lines_as_list


def test_find_patterns_in_list(cla_keywords, cla_input_data_match_true, cla_input_data_match_false):
    """Search for a list of patterns in one or multiple strings. The patterns
    can be regexes"""
    # Define some sample patterns and input data for testing
    # patterns = [r"\d+", r"apple"]
    # input_data = [
    #     "This is a 123 test",
    #     "I like apples",
    #     "No matches here",
    # ]

    # Test with empty fields
    assert find_patterns_in_list(cla_keywords) == []

    # Test with an empty input list
    assert find_patterns_in_list(cla_keywords, "") == []

    # Test with empty pattern list
    assert find_patterns_in_list([], *cla_input_data_match_true) == []

    # Test with matching fields and patterns
    assert find_patterns_in_list(cla_keywords, *cla_input_data_match_true) == [
        "## CLA",
        "Contribution License Agreement",
        "We require a signed CLA.",
        "agent: license/cla",
        "contributor licensing Agreement",
        "user: cla-bot",
    ]
    # Test with non-matching fields and patterns
    assert find_patterns_in_list(cla_keywords, *cla_input_data_match_false) == []

    # Test with CLA fields but no matching pattern
    assert find_patterns_in_list([r"no_match_pattern"], *cla_input_data_match_true) == []


def test_lines_as_list(fake_repository):
    """Return all lines of a file as list of lines"""
    assert lines_as_list(fake_repository / "README.md") == [
        "# Project Name",
        "",
        "You have to sign a CLA in order to contribute",
    ]
