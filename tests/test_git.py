# SPDX-FileCopyrightText: 2026 Umut Alisoglu
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for refreshing disposable local repository caches."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from git import Actor, Repo

from ossrfc._git import clone_or_pull_repository


def _commit_file(repo: Repo, text: str) -> None:
    """Commit synthetic contents without relying on the user's Git identity."""
    assert repo.working_tree_dir is not None
    (Path(repo.working_tree_dir) / "example.txt").write_text(text, encoding="utf-8")
    repo.index.add(["example.txt"])
    actor = Actor("Example User", "user@example.invalid")
    repo.index.commit("Update example", author=actor, committer=actor)


@pytest.fixture
def cached_repositories(tmp_path: Path) -> Iterator[tuple[Repo, Repo]]:
    """Create an origin and a cache entirely within the test's directory."""
    source_path = tmp_path / "origin"
    cache_path = tmp_path / "cache"
    with Repo.init(source_path, initial_branch="main") as source:
        _commit_file(source, "original\n")
        with Repo.clone_from(str(source_path), cache_path) as cache:
            yield source, cache


@pytest.mark.parametrize("staged", [False, True])
def test_refresh_preserves_dirty_cache(
    cached_repositories: tuple[Repo, Repo], staged: bool
) -> None:
    """Keep both staged and unstaged edits when refusing a dirty cache."""
    _, cache = cached_repositories
    assert cache.working_tree_dir is not None
    file_path = Path(cache.working_tree_dir) / "example.txt"
    file_path.write_text("local edit\n", encoding="utf-8")
    if staged:
        cache.index.add(["example.txt"])

    with patch("git.remote.Remote.fetch") as fetch:
        clone_or_pull_repository("https://example.invalid/project", cache.working_tree_dir)

    assert file_path.read_text(encoding="utf-8") == "local edit\n"
    assert cache.is_dirty()
    assert bool(cache.index.diff("HEAD")) is staged
    fetch.assert_not_called()


def test_refresh_skips_detached_cache(cached_repositories: tuple[Repo, Repo]) -> None:
    """Return before fetching a checkout without an active branch."""
    _, cache = cached_repositories
    cache.git.checkout(cache.head.commit.hexsha)
    previous_head = cache.head.commit.hexsha
    assert cache.working_tree_dir is not None

    with patch("git.remote.Remote.fetch") as fetch:
        clone_or_pull_repository("https://example.invalid/project", cache.working_tree_dir)

    assert cache.head.is_detached
    assert cache.head.commit.hexsha == previous_head
    fetch.assert_not_called()


def test_refresh_updates_clean_cache(cached_repositories: tuple[Repo, Repo]) -> None:
    """Continue fetching and updating a clean cache from its local origin."""
    source, cache = cached_repositories
    _commit_file(source, "upstream update\n")
    assert cache.working_tree_dir is not None

    clone_or_pull_repository(str(source.working_tree_dir), cache.working_tree_dir)

    assert cache.head.commit.hexsha == source.head.commit.hexsha
    assert (Path(cache.working_tree_dir) / "example.txt").read_text(
        encoding="utf-8"
    ) == "upstream update\n"
    assert not cache.is_dirty()
