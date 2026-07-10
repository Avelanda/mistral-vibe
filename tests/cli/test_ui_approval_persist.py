from __future__ import annotations

from pydantic import BaseModel
import pytest

from vibe.cli.textual_ui.app import VibeApp
from vibe.cli.textual_ui.widgets.approval_app import ApprovalApp
from vibe.core.config import ConfigFileError, VibeConfig
from vibe.core.config.harness_files import get_harness_files_manager


class _EmptyArgs(BaseModel):
    pass


_INVALID_MCP_CONFIG = """
[[mcp_servers]]
name = "legacy"
type = "stdio"
command = "echo"
"""


def _write_invalid_config() -> None:
    config_file = get_harness_files_manager().config_file
    assert config_file is not None
    config_file.write_text(_INVALID_MCP_CONFIG, encoding="utf-8")


def test_save_updates_raises_config_file_error_on_invalid_mcp_server() -> None:
    _write_invalid_config()
    with pytest.raises(ConfigFileError):
        VibeConfig.save_updates({"tools": {"bash": {"permission": "always"}}})


@pytest.mark.asyncio
async def test_permanent_approval_notifies_instead_of_crashing_on_invalid_config(
    vibe_app: VibeApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    notifications: list[str] = []

    def fake_notify(message: str, **_: object) -> None:
        notifications.append(message)

    async with vibe_app.run_test():
        monkeypatch.setattr(vibe_app, "notify", fake_notify)
        _write_invalid_config()
        message = ApprovalApp.ApprovalGrantedAlwaysPermanent(
            tool_name="bash", tool_args=_EmptyArgs(), required_permissions=[]
        )
        await vibe_app.on_approval_app_approval_granted_always_permanent(message)

    assert notifications
    assert "Invalid configuration" in notifications[0]
