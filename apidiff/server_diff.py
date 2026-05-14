"""Diff server objects between two OpenAPI specs."""

from dataclasses import dataclass
from typing import List, Optional

from apidiff.differ import ChangeType


@dataclass
class ServerChange:
    url: str
    change_type: ChangeType
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    field: Optional[str] = None

    def __str__(self) -> str:
        if self.change_type == ChangeType.REMOVED:
            return f"Server removed: {self.url}"
        if self.change_type == ChangeType.ADDED:
            return f"Server added: {self.url}"
        return f"Server '{self.url}' {self.field} changed: {self.old_value!r} -> {self.new_value!r}"

    def is_breaking(self) -> bool:
        """Removing a server or changing its URL is breaking."""
        return self.change_type == ChangeType.REMOVED or (
            self.change_type == ChangeType.MODIFIED and self.field == "url"
        )


@dataclass
class ServerDiffResult:
    changes: List[ServerChange]

    def has_breaking(self) -> bool:
        return any(c.is_breaking() for c in self.changes)

    def has_changes(self) -> bool:
        return bool(self.changes)

    def total(self) -> int:
        return len(self.changes)

    def summary_text(self) -> str:
        if not self.changes:
            return "No server changes."
        lines = [f"Server changes ({self.total()} total):"]
        for c in self.changes:
            tag = "[BREAKING]" if c.is_breaking() else "[non-breaking]"
            lines.append(f"  {tag} {c}")
        return "\n".join(lines)


def _servers_by_url(spec: dict) -> dict:
    servers = spec.get("servers", [])
    return {s["url"]: s for s in servers if "url" in s}


def diff_servers(base_spec: dict, head_spec: dict) -> ServerDiffResult:
    """Compare server lists between base and head specs."""
    base_servers = _servers_by_url(base_spec)
    head_servers = _servers_by_url(head_spec)

    changes: List[ServerChange] = []

    for url, base_server in base_servers.items():
        if url not in head_servers:
            changes.append(ServerChange(url=url, change_type=ChangeType.REMOVED))
        else:
            head_server = head_servers[url]
            for field in ("description", "variables"):
                bv = base_server.get(field)
                hv = head_server.get(field)
                if bv != hv:
                    changes.append(
                        ServerChange(
                            url=url,
                            change_type=ChangeType.MODIFIED,
                            old_value=str(bv),
                            new_value=str(hv),
                            field=field,
                        )
                    )

    for url in head_servers:
        if url not in base_servers:
            changes.append(ServerChange(url=url, change_type=ChangeType.ADDED))

    return ServerDiffResult(changes=changes)
