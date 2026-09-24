"""GitHub CLI adapter tests — no gh binary required."""

import pytest

from forgebot.github import GitHubError, comment_argv, gh_path


def test_comment_argv_exact():
    argv = comment_argv({"number": 7, "body": "hello"})
    assert argv == ["issue", "comment", "7", "--body", "hello"]


def test_comment_argv_with_repo():
    argv = comment_argv({"number": 7, "body": "hi", "repo": "octo/repo"})
    assert argv[-2:] == ["--repo", "octo/repo"]


def test_gh_path_missing(monkeypatch):
    monkeypatch.setattr("forgebot.github.shutil.which", lambda name: None)
    with pytest.raises(GitHubError, match="gh CLI not found"):
        gh_path()


from forgebot.github import pr_create_argv


def test_pr_create_argv_exact():
    argv = pr_create_argv({"title": "t", "body": "b"})
    assert argv == ["pr", "create", "--title", "t", "--body", "b"]


def test_pr_create_argv_optional_flags():
    argv = pr_create_argv(
        {"title": "t", "body": "b", "head": "feat", "base": "main", "repo": "octo/r"}
    )
    assert argv[-6:] == ["--head", "feat", "--base", "main", "--repo", "octo/r"]
