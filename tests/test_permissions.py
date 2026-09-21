from pathlib import Path

import pytest

from forgebot.manifest import ManifestError, parse_manifest
from forgebot.permissions import PermissionDenied, require


def test_require_denies_missing_scope():
    with pytest.raises(PermissionDenied):
        require(["read:repo"], "write:files", "testbot")


def test_manifest_rejects_unknown_scope(tmp_path: Path):
    p = tmp_path / "bot.md"
    p.write_text("---\nname: x\npermissions: [write:magic]\n---\nDo work.\n")
    with pytest.raises(ManifestError):
        parse_manifest(p)
