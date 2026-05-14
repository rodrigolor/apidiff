"""Pipeline for running security diff between two spec files."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apidiff.loader import load_spec
from apidiff.security_diff import SecurityDiffResult, diff_security


@dataclass
class SecurityDiffPipelineResult:
    result: SecurityDiffResult
    base_path: str
    head_path: str

    @property
    def has_breaking(self) -> bool:
        return self.result.has_breaking

    @property
    def has_changes(self) -> bool:
        return self.result.has_changes

    @property
    def total(self) -> int:
        return len(self.result.changes)

    def summary_text(self) -> str:
        if not self.has_changes:
            return "No security scheme changes detected."
        lines = [f"Security scheme changes ({self.total} total):"]
        for change in self.result.changes:
            prefix = "[BREAKING]" if change.is_breaking() else "[non-breaking]"
            lines.append(f"  {prefix} {change}")
        return "\n".join(lines)


def run_security_diff_pipeline(
    base_path: str,
    head_path: str,
) -> SecurityDiffPipelineResult:
    base_spec = load_spec(base_path)
    head_spec = load_spec(head_path)
    result = diff_security(base_spec, head_spec)
    return SecurityDiffPipelineResult(
        result=result,
        base_path=base_path,
        head_path=head_path,
    )
