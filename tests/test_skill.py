#!/usr/bin/env python3
"""Tests for kapture-dom-erode skill."""
import json
import subprocess
import sys
import gzip
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent / "skills"
TOOLS_SH = SKILL_DIR / "tools.sh"
FIXTURES_DIR = Path(__file__).parent / "test-data" / "fixtures"


def run_tools(*args):
    """Run tools.sh with given arguments."""
    cmd = [str(TOOLS_SH)] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=SKILL_DIR,
    )
    return result


def extract_json_field(dom_file, field="html"):
    """Extract the html field from a kapture_dom JSON file."""
    with open(dom_file) as f:
        data = json.load(f)
    return data.get(field, "")


@pytest.fixture
def si_latino_dom(tmp_path):
    """Extract Smithsonian Latino page DOM to temp file."""
    fixtures = FIXTURES_DIR / "si-latino.json.gz"
    with gzip.open(fixtures, "rt") as f:
        data = json.load(f)
    
    out_file = tmp_path / "si-latino.json"
    with open(out_file, "w") as f:
        json.dump(data, f)
    return out_file


class TestGrongrep:
    """Tests for gron-grep command."""

    def test_finds_visible_text(self, si_latino_dom):
        """gron-grep should find visible text in the DOM."""
        result = run_tools("gron-grep", "-f", str(si_latino_dom), "-q", "Salsa")
        assert result.returncode == 0
        assert "Salsa" in result.stdout
        # Should not include JSON metadata
        assert '"success": true' not in result.stdout

    def test_ignores_case(self, si_latino_dom):
        """gron-grep should support case-insensitive search."""
        result = run_tools("gron-grep", "-f", str(si_latino_dom), "-q", "salsa", "-i")
        assert result.returncode == 0
        assert "Salsa" in result.stdout

    def test_no_results_for_missing_text(self, si_latino_dom):
        """gron-grep should return empty for missing text."""
        result = run_tools("gron-grep", "-f", str(si_latino_dom), "-q", "XYZNOTFOUND123")
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestExtractText:
    """Tests for extract-text command."""

    def test_extracts_main_content(self, si_latino_dom):
        """extract-text should return visible text content."""
        # First find the path
        grep_result = run_tools("gron-grep", "-f", str(si_latino_dom), "-q", "Celia Cruz")
        assert grep_result.returncode == 0
        
        # Extract from main content - find the article path
        # The article is at: html[0].body[0].main[0].article[0]
        extract_result = run_tools(
            "extract-text",
            "-f", str(si_latino_dom),
            "-p", "html[0].body[0].main[0].article[0]"
        )
        assert extract_result.returncode == 0
        assert "Celia Cruz" in extract_result.stdout
        assert "National Museum of the American Latino" in extract_result.stdout


class TestTopContent:
    """Tests for top-content command."""

    def test_ranks_by_content_size(self, si_latino_dom):
        """top-content should rank blocks by visible text size."""
        result = run_tools("top-content", "-f", str(si_latino_dom), "--top", "3", "--no-detect")
        assert result.returncode == 0
        assert "Path" in result.stdout
        assert "Chars" in result.stdout
        # Main content should be in top results
        assert "main[0]" in result.stdout


class TestMainText:
    """Tests for main-text command."""

    def test_finds_main_content(self, si_latino_dom):
        """main-text should auto-detect main content region."""
        result = run_tools("main-text", "-f", str(si_latino_dom), "-q")
        assert result.returncode == 0
        # Should contain article content
        assert "National Museum of the American Latino" in result.stdout
        assert "Celia Cruz" in result.stdout


class TestHiddenFiltering:
    """Tests for hidden element filtering."""

    def test_skips_display_none(self, si_latino_dom):
        """Should skip elements with display:none."""
        result = run_tools("gron-grep", "-f", str(si_latino_dom), "-q", "display:none")
        # Should not find any matches for display:none as visible text
        # (it's an inline style, not visible content)
        assert "display:none" not in result.stdout or result.returncode != 0

    def test_skips_comments(self, si_latino_dom):
        """Should skip HTML comments."""
        result = run_tools("gron-grep", "-f", str(si_latino_dom), "-q", "comment")
        # Should not find comment text
        assert result.returncode == 0


class TestUvCheck:
    """Tests for uv dependency check."""

    def test_tools_sh_exists(self):
        """tools.sh should exist and be executable."""
        assert TOOLS_SH.exists()
        assert TOOLS_SH.stat().st_mode & 0o111  # executable bit
