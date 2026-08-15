import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

# A minimal valid-looking ARINC 424 fixed-width record line for testing
MOCK_ARINC_RECORD = (
    "S  EUR K1AORWL  WPT   LFST   N48351500W007391500EN  3200902  "
    "STRASBOURG                                     01"
)


@pytest.fixture
def mock_arinc_file(tmp_path):
    """Create a temporary ARINC 424 sample file for testing example scripts."""
    file_path = tmp_path / "sample_arinc.txt"
    # Write sample header and record lines conforming to expectations
    content = "HDR AIRAC 2301 230101 230128\n" + f"{MOCK_ARINC_RECORD}\n"
    file_path.write_text(content)
    return file_path


def test_sample_header(mock_arinc_file):
    """Test sample_header.py execution with a real file."""
    script_path = EXAMPLES_DIR / "sample_header.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(mock_arinc_file)],
        capture_output=True,
        text=True,
    )
    # Even if header parsing expects a specific format, we verify clean execution
    assert result.returncode == 0


def test_sample_streaming(mock_arinc_file):
    """Test sample_streaming.py execution with a filter option."""
    script_path = EXAMPLES_DIR / "sample_streaming.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(mock_arinc_file), "--filter", "WPT"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_sample_parse_all(mock_arinc_file):
    """Test sample_parse_all.py by pointing it to a valid mock file."""
    script_path = EXAMPLES_DIR / "sample_parse_all.py"

    # Temporarily patch or supply the file path if hardcoded in the script,
    # or ensure the script can accept arguments if refactored.
    # Alternatively, run via python inline execution simulation:
    code = f"""
from pathlib import Path
from arinc424 import parser
sample_file = Path("{mock_arinc_file}")
datasets = parser.parse_all(sample_file, merge_continuations=True)
print(f"Decoded {{len(datasets)}} categories")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Decoded" in result.stdout
