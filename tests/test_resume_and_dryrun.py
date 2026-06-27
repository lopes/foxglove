from foxglove.resume import ResumeAction, determine_resume_action


def test_manifest_exists_with_resume_flag():
    assert determine_resume_action(manifest_exists=True, resume_flag=True) == ResumeAction.RESUME


def test_manifest_exists_without_resume_flag():
    assert determine_resume_action(manifest_exists=True, resume_flag=False) == ResumeAction.PROMPT


def test_no_manifest_with_resume_flag():
    assert determine_resume_action(manifest_exists=False, resume_flag=True) == ResumeAction.FRESH_WITH_MESSAGE


def test_no_manifest_without_resume_flag():
    assert determine_resume_action(manifest_exists=False, resume_flag=False) == ResumeAction.FRESH
