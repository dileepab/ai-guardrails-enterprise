import re
import json

class LicenseScanner:
    RESTRICTED_LICENSES = ["GPL", "AGPL", "Affero"]
    
    # Simple knowledge base of common packages with strong copyleft licenses (Demo purpose)
    KNOWN_RESTRICTED_PACKAGES = {
        "ffmpeg": "LGPL/GPL",
        "linux": "GPL-2.0",
        "bash": "GPL-3.0",
        "ghostscript": "AGPL"
    }

    @staticmethod
    def scan_content(filename: str, content: str) -> list[dict]:
        violations = []
        
        # 1. Check for explicit license strings in the file (e.g. "License: GPL")
        for lic in LicenseScanner.RESTRICTED_LICENSES:
            if re.search(rf"\b{lic}\b", content, re.IGNORECASE):
                violations.append({
                    "rule_id": "LIC-002",
                    "message": f"Restricted license term '{lic}' detected in dependency file configuration.",
                    "severity": "BLOCKING",
                    "category": "COMPLIANCE",
                    "file": filename,
                    "line": 1 # Generic line for file-level check
                })

        # 2. Heuristic check for known restricted packages
        if filename.endswith("package.json"):
            try:
                data = json.loads(content)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for pkg in deps:
                    if pkg in LicenseScanner.KNOWN_RESTRICTED_PACKAGES:
                         violations.append({
                            "rule_id": "LIC-003",
                            "message": f"Package '{pkg}' is known to use restricted license: {LicenseScanner.KNOWN_RESTRICTED_PACKAGES[pkg]}",
                            "severity": "BLOCKING",
                            "category": "COMPLIANCE",
                            "file": filename,
                            "line": 1
                        })
            except json.JSONDecodeError:
                pass # Ignore invalid JSON
        
        elif filename.endswith("requirements.txt"):
             for pkg in LicenseScanner.KNOWN_RESTRICTED_PACKAGES:
                 if re.search(rf"^\s*{pkg}\b", content, re.MULTILINE):
                     violations.append({
                            "rule_id": "LIC-003",
                            "message": f"Package '{pkg}' is known to use restricted license: {LicenseScanner.KNOWN_RESTRICTED_PACKAGES[pkg]}",
                            "severity": "BLOCKING",
                            "category": "COMPLIANCE",
                            "file": filename,
                            "line": 1
                        })

        return violations
