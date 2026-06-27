import itertools
from pathlib import PurePosixPath

import anthropic
from anthropic.types import Message, ToolUseBlock, ToolParam
from pydantic import ValidationError

from foxglove.models import BATCH_SIZE, CampaignPlan, FileEntry, OperationParameters


class PlanningError(Exception):
    def __init__(self, message: str, *, is_api_error: bool = False) -> None:
        super().__init__(message)
        self.is_api_error = is_api_error


def deduplicate_paths(entries: list[FileEntry]) -> list[FileEntry]:
    seen: dict[str, int] = {}
    result: list[FileEntry] = []
    for entry in entries:
        if entry.path not in seen:
            seen[entry.path] = 1
            result.append(entry)
        else:
            seen[entry.path] += 1
            count = seen[entry.path]
            p = PurePosixPath(entry.path)
            new_path = f"{p.parent / p.stem} ({count}){p.suffix}"
            result.append(FileEntry(path=new_path, format=entry.format, summary=entry.summary))
    return result


def assign_epdf_passwords(entries: list[FileEntry], passwords: list[str]) -> list[FileEntry]:
    password_cycle = itertools.cycle(passwords)
    result: list[FileEntry] = []
    for entry in entries:
        if entry.format == "epdf":
            pw = next(password_cycle)
            result.append(
                FileEntry(
                    path=entry.path,
                    format=entry.format,
                    summary=f"{entry.summary}. Password: {pw}",
                )
            )
        else:
            result.append(entry)
    return result


def merge_plans(plans: list[CampaignPlan]) -> CampaignPlan:
    all_files: list[FileEntry] = []
    for plan in plans:
        all_files = [*all_files, *plan.files]
    return CampaignPlan(files=all_files)


def normalize_epdf_extensions(entries: list[FileEntry]) -> list[FileEntry]:
    result: list[FileEntry] = []
    for entry in entries:
        if entry.format == "epdf" and entry.path.endswith(".epdf"):
            p = PurePosixPath(entry.path)
            new_path = str(p.with_suffix(".pdf"))
            result.append(FileEntry(path=new_path, format=entry.format, summary=entry.summary))
        else:
            result.append(entry)
    return result


def post_process_plan(plans: list[CampaignPlan], passwords: list[str]) -> CampaignPlan:
    merged = merge_plans(plans)
    normalized = normalize_epdf_extensions(merged.files)
    deduped = deduplicate_paths(normalized)
    with_passwords = assign_epdf_passwords(deduped, passwords)
    return CampaignPlan(files=with_passwords)


def compute_batches(num_files: int, batch_size: int = BATCH_SIZE) -> list[tuple[int, int]]:
    full_batches = num_files // batch_size
    remainder = num_files % batch_size
    batches: list[tuple[int, int]] = [(i + 1, batch_size) for i in range(full_batches)]
    if remainder > 0:
        batches.append((full_batches + 1, remainder))
    return batches


def build_planning_prompt(
    batch_num: int,
    batch_size: int,
    formats: list[str],
    teams: list[str],
    company: str,
    file_content: str,
) -> str:
    return (
        f"Generate a list of exactly {batch_size} realistic file entries (batch {batch_num}).\n"
        f"Consider files created by {', '.join(teams)} for the company {company} "
        f"under this context: {file_content}.\n"
        f"Use only these formats: {', '.join(formats)}.\n"
        f"Each entry needs: path (relative, with team-based subdirectories), format, and summary."
    )


def _extract_campaign_plan(response: Message) -> CampaignPlan:
    for block in response.content:
        if isinstance(block, ToolUseBlock):
            tool_input: object = block.input
            try:
                return CampaignPlan.model_validate(tool_input)
            except ValidationError as e:
                raise PlanningError(f"Invalid plan structure from LLM: {e}") from e
    raise PlanningError("LLM did not return a tool_use response")


def plan_batch(
    client: anthropic.Anthropic,
    prompt: str,
    batch_size: int,
    model: str,
) -> CampaignPlan:
    tool_schema = CampaignPlan.model_json_schema()
    tool: ToolParam = {
        "name": "campaign_plan",
        "description": "A structured campaign plan with file entries",
        "input_schema": tool_schema,
    }
    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            tools=[tool],
            tool_choice={"type": "tool", "name": "campaign_plan"},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        raise PlanningError(f"API error: {e}", is_api_error=True) from e
    return _extract_campaign_plan(response)


def plan_campaign(
    client: anthropic.Anthropic,
    params: OperationParameters,
) -> CampaignPlan:
    batches = compute_batches(params.num_files)
    plans: list[CampaignPlan] = []
    for batch_num, batch_size in batches:
        prompt = build_planning_prompt(
            batch_num=batch_num,
            batch_size=batch_size,
            formats=params.formats,
            teams=params.teams,
            company=params.company,
            file_content=params.file_content,
        )
        plan = plan_batch(client, prompt, batch_size, params.model)
        plans.append(plan)
    return post_process_plan(plans, params.passwords)
