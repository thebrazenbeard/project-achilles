from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SecurityFinding:
    code: str
    path: str
    message: str


def _path(parent: str, key: str) -> str:
    return f"{parent}.{key}" if parent else key


def find_public_private_inventory_leaks(
    payload: Any,
    *,
    path: str = "",
) -> tuple[SecurityFinding, ...]:
    """Find public-artifact structures that expose private membership too directly."""
    findings: list[SecurityFinding] = []

    if isinstance(payload, Mapping):
        lower_path = path.lower()
        keys = {str(key).lower() for key in payload}

        if (
            "private" in lower_path
            and any(key in keys for key in {"sha256", "private_names_sha256"})
        ):
            scheme = str(
                payload.get("scheme")
                or payload.get("public_commitment_scheme")
                or ""
            ).upper()
            if "HMAC" not in scheme and "KEYED" not in scheme:
                findings.append(
                    SecurityFinding(
                        "UNKEYED_PRIVATE_SET_DIGEST",
                        path or "<root>",
                        "private identifier membership is exposed through an unkeyed digest",
                    )
                )

        for key, value in payload.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = _path(path, key_text)
            if key_lower in {
                "private_repositories",
                "private_repository_names",
                "private_workstreams",
                "private_workstream_ids",
            } and isinstance(value, Sequence) and not isinstance(
                value, (str, bytes)
            ):
                findings.append(
                    SecurityFinding(
                        "PRIVATE_IDENTIFIER_LIST",
                        child_path,
                        "public artifact contains an explicit private identifier list",
                    )
                )
            findings.extend(
                find_public_private_inventory_leaks(value, path=child_path)
            )

    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        for index, value in enumerate(payload):
            findings.extend(
                find_public_private_inventory_leaks(
                    value,
                    path=f"{path}[{index}]" if path else f"[{index}]",
                )
            )

    return tuple(findings)


def review_source_only_wave_policy(
    payload: Mapping[str, Any],
) -> tuple[SecurityFinding, ...]:
    findings: list[SecurityFinding] = []
    policy = payload.get("policy")
    if not isinstance(policy, Mapping):
        return (
            SecurityFinding(
                "WAVE_POLICY_MISSING",
                "policy",
                "portfolio execution wave has no explicit security/effect policy",
            ),
        )

    required_true = (
        "protected_effects_forbidden_without_separate_live_authority",
        "merge_forbidden",
        "deploy_forbidden",
        "credential_or_permission_changes_forbidden",
        "destructive_cleanup_forbidden",
    )
    for key in required_true:
        if policy.get(key) is not True:
            findings.append(
                SecurityFinding(
                    "PROTECTED_EFFECT_FENCE_MISSING",
                    f"policy.{key}",
                    f"{key} must be true for a source-only portfolio wave",
                )
            )

    if policy.get("priority_is_authority") is not False:
        findings.append(
            SecurityFinding(
                "PRIORITY_AUTHORITY_CONFUSION",
                "policy.priority_is_authority",
                "portfolio priority must never manufacture authority",
            )
        )

    items = payload.get("items")
    if isinstance(items, Sequence) and not isinstance(items, (str, bytes)):
        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                continue
            ceiling = item.get("effect_ceiling")
            if ceiling not in {"SOURCE_ONLY", "NO_EFFECT"}:
                findings.append(
                    SecurityFinding(
                        "ITEM_EFFECT_CEILING_EXCEEDED",
                        f"items[{index}].effect_ceiling",
                        "item exceeds source-only/no-effect ceiling",
                    )
                )

    return tuple(findings)
