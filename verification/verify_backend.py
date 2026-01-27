import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.engine.hybrid_analyzer import analyzer
from app.models.scan import ScanRequest

async def verify():
    print("Starting Verification...")
    
    # Test Content
    vulnerable_code = """
def connect_db():
    password = "super_secret_password_123" # Hardcoded secret
    print("Connecting...") # Style violation
    # TODO: Implement retry logic
    execute_query("SELECT * FROM users WHERE id = " + user_input) # SQLi potential (though regex might miss complex flows, rule engine catches 'eval')
    eval(user_input) # RCE
"""

    license_content = """
    This software is licensed under the GNU General Public License v3 (GPL).
    """

    request = ScanRequest(
        repo_full_name="test/repo",
        pr_number=1,
        commit_sha="abc1234",
        files=[
            {"filename": "db.py", "content": vulnerable_code, "patch": vulnerable_code},
            {"filename": "LICENSE", "content": license_content, "patch": license_content}
        ]
    )

    print("Running Analyzer...")
    response = await analyzer.analyze(request)
    
    print(f"\nStatus: {response.status}")
    print(f"Summary: {response.summary}")
    print(f"Succeeded: {response.succeeded}")
    print("\nViolations:")
    for v in response.violations:
        print(f"[{v.severity}] {v.rule_id} ({v.category}): {v.message} at {v.file_path}:{v.line_number}")

    # Assertions
    rule_ids = [v.rule_id for v in response.violations]
    
    # Check for Secret
    assert "SAST-001" in rule_ids, "Failed to detect Hardcoded Secret (SAST-001)"
    # Check for Eval
    assert "SAST-002" in rule_ids, "Failed to detect Eval (SAST-002)"
    # Check for Print
    assert "LOG-001" in rule_ids, "Failed to detect Print (LOG-001)"
    # Check for License
    assert "LIC-001" in rule_ids, "Failed to detect Restricted License (LIC-001)"
    
    # Test Content for new rules
    audit_test_code = """
import os
import logging

class badClassName: # STYLE-002
    def run_cmd(self, user_input):
        query = "SELECT * FROM users WHERE id = " + user_input # SAST-004
        os.system("rm -rf " + user_input) # SAST-005
        
        try:
            logging.getLogger("test").info("Processing")
        except:
            pass # ERR-001
"""
    
    request_audit = ScanRequest(
        repo_full_name="test/repo-audit",
        pr_number=3,
        commit_sha="audit123",
        files=[{"filename": "app.py", "content": audit_test_code, "patch": audit_test_code}]
    )

    print("\nRunning Analyzer for Audit Gaps...")
    response_audit = await analyzer.analyze(request_audit)
    
    audit_ids = [v.rule_id for v in response_audit.violations]
    print(f"Violations Found: {audit_ids}")

    assert "SAST-004" in audit_ids, "Failed to detect SQL Injection (SAST-004)"
    assert "SAST-005" in audit_ids, "Failed to detect Unsafe OS Command (SAST-005)"
    assert "STYLE-002" in audit_ids, "Failed to detect Bad Class Name (STYLE-002)"
    assert "ERR-001" in audit_ids, "Failed to detect Bare Except (ERR-001)"
    
    # Test Config Override
    custom_config = """
rules:
  - id: "CUSTOM-001"
    pattern: "custom_bad_pattern"
    message: "Custom bad pattern detected"
    severity: "BLOCKING"
    category: "SECURITY"
"""
    custom_code = "var x = custom_bad_pattern;"

    request_override = ScanRequest(
        repo_full_name="test/repo-custom",
        pr_number=2,
        commit_sha="def456",
        files=[{"filename": "custom.js", "content": custom_code, "patch": custom_code}],
        config_override=custom_config,
        is_copilot_generated=True
    )

    print("\nRunning Analyzer with Config Override...")
    response_override = await analyzer.analyze(request_override)
    
    print(f"Summary: {response_override.summary}")
    for v in response_override.violations:
        print(f"[{v.severity}] {v.rule_id}: {v.message}")

    override_ids = [v.rule_id for v in response_override.violations]
    assert "CUSTOM-001" in override_ids, "Failed to detect custom rule via override"
    
    # Test Advisory Mode
    advisory_config = """
enforcement_mode: advisory
rules:
  - id: "BLOCKER-001"
    pattern: "block_me"
    message: "This should be blocking but ignored in advisory mode"
    severity: "BLOCKING"
    category: "SECURITY"
"""
    advisory_code = "var x = block_me;"

    request_advisory = ScanRequest(
        repo_full_name="test/repo-advisory",
        pr_number=4,
        commit_sha="adv123",
        files=[{"filename": "advisory.js", "content": advisory_code, "patch": advisory_code}],
        config_override=advisory_config
    )

    print("\nRunning Analyzer in ADVISORY Mode...")
    response_advisory = await analyzer.analyze(request_advisory)
    print(f"Succeeded: {response_advisory.succeeded}")
    print(f"Mode: {response_advisory.enforcement_mode}")
    
    assert response_advisory.succeeded == True, "Advisory mode failed to suppress blocking violation"
    assert response_advisory.enforcement_mode == "advisory", "Enforcement mode not set correctly"
    
    print("\n✅ Verification Passed!")

if __name__ == "__main__":
    asyncio.run(verify())
