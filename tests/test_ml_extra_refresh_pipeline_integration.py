"""Integration smoke tests for the ml-extra-refresh console entry point."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


# Why: Provide the repository root so integration helpers can locate artifacts relative to the source checkout.
@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


# Why: Synthesize a minimal console entry wrapper so subprocess-based tests can exercise the CLI without networked packaging steps.
@pytest.fixture(scope="session")
def console_script(tmp_path_factory: pytest.TempPathFactory) -> Path:
    script_dir = tmp_path_factory.mktemp("ml-extra-refresh-console")
    script_path = script_dir / "ml-extra-refresh"
    script_path.write_text(
        "#!/usr/bin/env python3\n"
        "from imagebbs.ml_extra_refresh_pipeline import main\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


# Why: Validate that the ml-extra-refresh console entry returns CI-friendly exit codes for matching and drifting baselines.
def test_ml_extra_refresh_console_script(console_script: Path, project_root: Path, tmp_path: Path) -> None:
    baseline_path = project_root / "docs/porting/artifacts/ml-extra-overlay-metadata.json"
    output_path = tmp_path / "generated" / "ml-extra-refresh.json"

    env = os.environ.copy()
    path_entries = [str(project_root), str(project_root / "src")]
    existing_path = env.get("PYTHONPATH")
    if existing_path:
        path_entries.append(existing_path)
    env["PYTHONPATH"] = os.pathsep.join(path_entries)

    success = subprocess.run(
        [
            str(console_script),
            "--baseline",
            str(baseline_path),
            "--metadata-json",
            str(output_path),
            "--if-changed",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert success.returncode == 0
    assert output_path.exists()
    assert "Metadata snapshot" in success.stdout

    success_json = subprocess.run(
        [
            str(console_script),
            "--baseline",
            str(baseline_path),
            "--metadata-json",
            str(output_path),
            "--if-changed",
            "--json",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert success_json.returncode == 0
    json_lines = success_json.stdout.splitlines()
    assert json_lines
    assert json_lines[0].startswith("Metadata snapshot")
    diff_payload = json.loads("\n".join(json_lines[1:]))
    assert diff_payload["matches"] is True

    mismatch_payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    mismatch_payload["load_address"] = "$ffff"
    mismatch_baseline = tmp_path / "mismatch.json"
    mismatch_baseline.write_text(json.dumps(mismatch_payload) + "\n", encoding="utf-8")

    failure = subprocess.run(
        [
            str(console_script),
            "--baseline",
            str(mismatch_baseline),
            "--metadata-json",
            str(tmp_path / "mismatch-output.json"),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert failure.returncode == 1
    assert "Drift detected relative" in failure.stdout


# Why: Ensure metadata-only mode succeeds without requiring a baseline artifact.
def test_ml_extra_refresh_console_metadata_only(
    console_script: Path, project_root: Path, tmp_path: Path
) -> None:
    output_path = tmp_path / "metadata-only" / "ml-extra-refresh.json"

    env = os.environ.copy()
    path_entries = [str(project_root), str(project_root / "src")]
    existing_path = env.get("PYTHONPATH")
    if existing_path:
        path_entries.append(existing_path)
    env["PYTHONPATH"] = os.pathsep.join(path_entries)

    result = subprocess.run(
        [
            str(console_script),
            "--metadata-json",
            str(output_path),
            "--metadata-only",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert output_path.exists()
    assert "Metadata snapshot" in result.stdout
