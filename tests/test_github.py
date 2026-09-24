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
