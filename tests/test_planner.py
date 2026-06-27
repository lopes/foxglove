from unittest.mock import MagicMock

import anthropic
import pytest
from anthropic.types import ToolUseBlock

from foxglove.models import CampaignPlan, OperationParameters
from foxglove.planner import (
    PlanningError,
    build_planning_prompt,
    compute_batches,
    plan_batch,
    plan_campaign,
)


def test_compute_batches_single_file():
    assert compute_batches(1) == [(1, 1)]


def test_compute_batches_exactly_one_batch():
    assert compute_batches(50) == [(1, 50)]


def test_compute_batches_two_batches():
    assert compute_batches(99) == [(1, 50), (2, 49)]


def test_compute_batches_four_batches():
    assert compute_batches(200) == [(1, 50), (2, 50), (3, 50), (4, 50)]


def test_build_planning_prompt_contains_context():
    prompt = build_planning_prompt(
        batch_num=1,
        batch_size=50,
        formats=["pdf", "docx"],
        teams=["it", "infra"],
        company="Acme Corp",
        file_content="IT infrastructure docs",
    )
    assert "it" in prompt
    assert "infra" in prompt
    assert "Acme Corp" in prompt
    assert "IT infrastructure docs" in prompt
    assert "pdf" in prompt
    assert "docx" in prompt
    assert "50" in prompt


def _make_tool_use_block(files: list[dict[str, str]]) -> ToolUseBlock:
    return ToolUseBlock(
        id="toolu_test",
        type="tool_use",
        name="campaign_plan",
        input={"files": files},
    )


def _make_api_response(files: list[dict[str, str]]) -> MagicMock:
    response = MagicMock()
    response.content = [_make_tool_use_block(files)]
    response.stop_reason = "tool_use"
    return response


def test_plan_batch_returns_campaign_plan():
    files = [
        {"path": "it/report.pdf", "format": "pdf", "summary": "A report"},
        {"path": "it/config.conf", "format": "conf", "summary": "Config"},
    ]
    client = MagicMock()
    client.messages.create.return_value = _make_api_response(files)

    result = plan_batch(client, "Generate 2 files", 2, "test-model")
    assert isinstance(result, CampaignPlan)
    assert len(result.files) == 2
    assert result.files[0].path == "it/report.pdf"


def test_plan_batch_api_error_raises_planning_error():
    client = MagicMock()
    client.messages.create.side_effect = anthropic.APIError(
        message="rate limited",
        request=MagicMock(),
        body=None,
    )

    with pytest.raises(PlanningError) as exc_info:
        plan_batch(client, "Generate files", 5, "test-model")
    assert exc_info.value.is_api_error


def test_plan_batch_invalid_response_raises_planning_error():
    client = MagicMock()
    response = MagicMock()
    response.content = []
    response.stop_reason = "end_turn"
    client.messages.create.return_value = response

    with pytest.raises(PlanningError) as exc_info:
        plan_batch(client, "Generate files", 5, "test-model")
    assert not exc_info.value.is_api_error


def _make_params(**overrides: str | int | list[str]) -> OperationParameters:
    defaults: dict[str, str | int | list[str]] = {
        "base_dir": "/tmp",
        "num_files": 75,
        "formats": ["pdf", "md"],
        "teams": ["it", "infra"],
        "company": "Acme",
        "file_content": "docs",
        "model": "test-model",
        "passwords": ["p1", "p2"],
    }
    return OperationParameters(**dict(defaults | overrides))  # type: ignore[arg-type]


def test_plan_campaign_merges_batches():
    batch1_files = [{"path": f"file{i}.pdf", "format": "pdf", "summary": f"File {i}"} for i in range(50)]
    batch2_files = [{"path": f"file{i}.md", "format": "md", "summary": f"File {i}"} for i in range(25)]

    client = MagicMock()
    client.messages.create.side_effect = [
        _make_api_response(batch1_files),
        _make_api_response(batch2_files),
    ]

    params = _make_params(num_files=75)
    result = plan_campaign(client, params)
    assert isinstance(result, CampaignPlan)
    assert len(result.files) == 75
    assert client.messages.create.call_count == 2
