"""Fail-closed policy boundary; this module never imports or executes user strategies.
Future worker must supply an independently enforced sandbox, not self-attested flags.
"""
from dataclasses import dataclass
from .contracts import require


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    wall_seconds: int = 300
    memory_mib: int = 512
    cpu_millicores: int = 1000
    max_output_mib: int = 64
    network_enabled: bool = False
    secrets_enabled: bool = False
    read_only_input: bool = True
    non_root: bool = True

    def __post_init__(self):
        for name in ("wall_seconds", "memory_mib", "cpu_millicores", "max_output_mib"):
            v = getattr(self, name)
            require(type(v) is int and v > 0, f"invalid {name}")
        require(self.network_enabled is False and self.secrets_enabled is False
                and self.read_only_input is True and self.non_root is True,
                "custom strategy isolation cannot be weakened")


def execute_custom_strategy(*args, **kwargs):
    """Disabled until OS-level isolation and worker authorization are implemented."""
    raise NotImplementedError("Custom Python execution is disabled in M1; isolated worker required")
