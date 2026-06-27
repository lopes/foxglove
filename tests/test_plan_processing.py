from foxglove.models import CampaignPlan, FileEntry
from foxglove.planner import (
    assign_epdf_passwords,
    deduplicate_paths,
    merge_plans,
    normalize_epdf_extensions,
    post_process_plan,
)


def _entry(path: str, fmt: str = "md", summary: str = "desc") -> FileEntry:
    return FileEntry(path=path, format=fmt, summary=summary)


def test_deduplicate_paths_no_duplicates():
    entries = [_entry("a.md"), _entry("b.pdf", "pdf")]
    result = deduplicate_paths(entries)
    assert [e.path for e in result] == ["a.md", "b.pdf"]


def test_deduplicate_paths_with_duplicates():
    entries = [_entry("Report.md"), _entry("Report.md"), _entry("Report.md")]
    result = deduplicate_paths(entries)
    assert [e.path for e in result] == ["Report.md", "Report (2).md", "Report (3).md"]


def test_deduplicate_paths_different_directories():
    entries = [_entry("it/Report.md"), _entry("infra/Report.md")]
    result = deduplicate_paths(entries)
    assert [e.path for e in result] == ["it/Report.md", "infra/Report.md"]


def test_assign_epdf_passwords_cycles():
    entries = [
        _entry("a.pdf", "epdf", "Secret doc"),
        _entry("b.md", "md", "Readme"),
        _entry("c.pdf", "epdf", "Another doc"),
        _entry("d.pdf", "epdf", "Third doc"),
    ]
    result = assign_epdf_passwords(entries, ["p1", "p2"])
    assert result[0].summary == "Secret doc. Password: p1"
    assert result[1].summary == "Readme"
    assert result[2].summary == "Another doc. Password: p2"
    assert result[3].summary == "Third doc. Password: p1"


def test_assign_epdf_passwords_non_epdf_unchanged():
    entries = [_entry("a.md", "md", "Just a file")]
    result = assign_epdf_passwords(entries, ["p1"])
    assert result[0].summary == "Just a file"


def test_merge_plans():
    plan1 = CampaignPlan(files=[_entry("a.md"), _entry("b.md")])
    plan2 = CampaignPlan(files=[_entry("c.pdf", "pdf")])
    result = merge_plans([plan1, plan2])
    assert len(result.files) == 3
    assert [e.path for e in result.files] == ["a.md", "b.md", "c.pdf"]


def test_post_process_plan_composes_all():
    plan1 = CampaignPlan(files=[_entry("Report.md"), _entry("a.pdf", "epdf", "Secret")])
    plan2 = CampaignPlan(files=[_entry("Report.md")])
    result = post_process_plan([plan1, plan2], ["pw1"])
    paths = [e.path for e in result.files]
    assert paths == ["Report.md", "a.pdf", "Report (2).md"]
    epdf_entry = result.files[1]
    assert "Password: pw1" in epdf_entry.summary


def test_normalize_epdf_extensions_renames_to_pdf():
    entries = [
        _entry("infra/secret.epdf", "epdf", "Secret doc"),
        _entry("it/readme.md", "md", "Readme"),
        _entry("it/report.pdf", "pdf", "Report"),
    ]
    result = normalize_epdf_extensions(entries)
    assert result[0].path == "infra/secret.pdf"
    assert result[0].format == "epdf"
    assert result[1].path == "it/readme.md"
    assert result[2].path == "it/report.pdf"


def test_normalize_epdf_already_pdf_extension():
    entries = [_entry("doc.pdf", "epdf", "Already pdf ext")]
    result = normalize_epdf_extensions(entries)
    assert result[0].path == "doc.pdf"


def test_post_process_plan_normalizes_epdf_extensions():
    plan = CampaignPlan(files=[_entry("secret.epdf", "epdf", "Secret")])
    result = post_process_plan([plan], ["pw1"])
    assert result.files[0].path == "secret.pdf"
    assert result.files[0].format == "epdf"
