from enum import Enum


class ResumeAction(Enum):
    RESUME = "resume"
    PROMPT = "prompt"
    FRESH_WITH_MESSAGE = "fresh_with_message"
    FRESH = "fresh"


def determine_resume_action(*, manifest_exists: bool, resume_flag: bool) -> ResumeAction:
    if manifest_exists and resume_flag:
        return ResumeAction.RESUME
    if manifest_exists and not resume_flag:
        return ResumeAction.PROMPT
    if not manifest_exists and resume_flag:
        return ResumeAction.FRESH_WITH_MESSAGE
    return ResumeAction.FRESH
