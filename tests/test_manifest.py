"""Manifest parser tests."""

from pathlib import Path

import pytest

from forgebot.manifest import ManifestError, load_bots, parse_manifest

GOOD = """---
name: demobot
description: test bot
permissions: [read:repo, write:pr]
triggers: [post-merge, file_added(runs/**/metrics.json)]
---

## Instructions
Do the thing.
"""


def write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / ".gitbot" / "bots" / name
    p.parent.mkdir(parents=True)
    p.write_text(text)
    return p


def test_parse_good_manifest(tmp_path):
    bot = parse_manifest(write(tmp_path, "bot.md", GOOD))
    assert bot.name == "demobot"
    assert bot.triggers == ["post-merge", "file_added(runs/**/metrics.json)"]
    assert "write:pr" in bot.permissions
    assert "Do the thing." in bot.instructions


def test_missing_frontmatter(tmp_path):
    p = write(tmp_path, "bad.md", "no frontmatter here")
    with pytest.raises(ManifestError):
        parse_manifest(p)


def test_empty_instructions(tmp_path):
    p = write(tmp_path, "bad.md", "---\nname: x\n---\n\n")
    with pytest.raises(ManifestError):
        parse_manifest(p)


def test_load_bots_empty_repo(tmp_path):
    assert load_bots(tmp_path) == []


def test_load_bots_finds_files(tmp_path):
    write(tmp_path, "a.md", GOOD)
    write(tmp_path, "b.md", GOOD.replace("demobot", "demobot2"))
    bots = load_bots(tmp_path)
    assert {b.name for b in bots} == {"demobot", "demobot2"}
