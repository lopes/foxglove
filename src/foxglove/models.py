from pydantic import BaseModel, field_validator

SUPPORTED_FORMATS: frozenset[str] = frozenset(
    {"pdf", "epdf", "docx", "xlsx", "pptx", "md", "conf", "json", "xml"}
)

MAX_FILES: int = 200
BATCH_SIZE: int = 50

DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
DEFAULT_PASSWORDS: tuple[str, ...] = ("abc123", "root")

EXIT_SUCCESS: int = 0
EXIT_CLI_ERROR: int = 1
EXIT_ENV_ERROR: int = 2
EXIT_API_ERROR: int = 3
EXIT_PARTIAL: int = 4
EXIT_PLANNING_ERROR: int = 5


class FileEntry(BaseModel):
    model_config = {"frozen": True}

    path: str
    format: str
    summary: str

    @field_validator("format")
    @classmethod
    def format_must_be_supported(cls, v: str) -> str:
        if v not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {v}")
        return v


class CampaignPlan(BaseModel):
    model_config = {"frozen": True}

    files: list[FileEntry]


class OperationParameters(BaseModel):
    model_config = {"frozen": True}

    base_dir: str
    num_files: int
    formats: list[str]
    teams: list[str]
    company: str
    file_content: str
    model: str
    passwords: list[str]


class Manifest(BaseModel):
    model_config = {"frozen": True}

    operation: str
    parameters: OperationParameters
    files: list[FileEntry]
