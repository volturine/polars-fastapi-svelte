import json
import re

from scripts.scan_warnings import _load_allowlist, _scan


def test_scan_ignores_allowlisted_matches() -> None:
    matches = _scan(
        'ws proxy error: Error: write EPIPE\nall good',
        allowlist=[re.compile(r'ws proxy error: Error: write EPIPE')],
    )

    assert matches == []


def test_scan_reports_unclassified_matches() -> None:
    matches = _scan(
        'Warning: noisy output\nclean line',
        allowlist=[],
    )

    assert len(matches) == 1
    assert matches[0].pattern == 'Warning:'
    assert matches[0].line_number == 1


def test_load_allowlist_filters_by_scope(tmp_path) -> None:
    path = tmp_path / 'allowlist.json'
    path.write_text(
        json.dumps(
            [
                {'pattern': 'EPIPE', 'scope': 'just-test-e2e'},
                {'pattern': 'Warning:', 'scope': 'other-scope'},
            ]
        ),
        encoding='utf-8',
    )

    allowlist = _load_allowlist(path, 'just-test-e2e')

    assert len(allowlist) == 1
    assert allowlist[0].pattern == 'EPIPE'
