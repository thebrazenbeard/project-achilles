from security.portfolio_publication_guard import (
    find_public_private_inventory_leaks,
    review_source_only_wave_policy,
)


def _codes(findings):
    return {finding.code for finding in findings}


def test_unkeyed_private_digest_is_rejected():
    payload = {
        "private_inventory": {
            "count": 18,
            "sha256": "0" * 64,
        }
    }
    findings = find_public_private_inventory_leaks(payload)
    assert "UNKEYED_PRIVATE_SET_DIGEST" in _codes(findings)


def test_keyed_private_commitment_is_not_flagged_as_unkeyed():
    payload = {
        "private_inventory": {
            "count": 18,
            "scheme": "HMAC_SHA256_PRIVATE_KEY_CANONICAL_V1",
            "sha256": "0" * 64,
        }
    }
    findings = find_public_private_inventory_leaks(payload)
    assert "UNKEYED_PRIVATE_SET_DIGEST" not in _codes(findings)


def test_count_only_private_inventory_is_public_safe():
    payload = {
        "private_inventory": {
            "count": 18,
            "public_commitment_scheme": "COUNT_ONLY_PUBLIC_V1",
            "exact_membership_publicly_committed": False,
        }
    }
    assert find_public_private_inventory_leaks(payload) == ()


def test_explicit_private_identifier_list_is_rejected():
    payload = {
        "private_repositories": ["owner/secret-one", "owner/secret-two"]
    }
    findings = find_public_private_inventory_leaks(payload)
    assert "PRIVATE_IDENTIFIER_LIST" in _codes(findings)


def test_source_only_wave_policy_passes():
    wave = {
        "policy": {
            "protected_effects_forbidden_without_separate_live_authority": True,
            "merge_forbidden": True,
            "deploy_forbidden": True,
            "credential_or_permission_changes_forbidden": True,
            "destructive_cleanup_forbidden": True,
            "priority_is_authority": False,
        },
        "items": [
            {"effect_ceiling": "SOURCE_ONLY"},
            {"effect_ceiling": "NO_EFFECT"},
        ],
    }
    assert review_source_only_wave_policy(wave) == ()


def test_wave_policy_rejects_permission_laundering_and_effect_expansion():
    wave = {
        "policy": {
            "protected_effects_forbidden_without_separate_live_authority": True,
            "merge_forbidden": False,
            "deploy_forbidden": True,
            "credential_or_permission_changes_forbidden": True,
            "destructive_cleanup_forbidden": True,
            "priority_is_authority": True,
        },
        "items": [{"effect_ceiling": "DEPLOY"}],
    }
    findings = review_source_only_wave_policy(wave)
    codes = _codes(findings)
    assert "PROTECTED_EFFECT_FENCE_MISSING" in codes
    assert "PRIORITY_AUTHORITY_CONFUSION" in codes
    assert "ITEM_EFFECT_CEILING_EXCEEDED" in codes
