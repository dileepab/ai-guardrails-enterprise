import os
import logging
import subprocess

# 1. SAST-001: Hardcoded Secret (modified to catch length >=3)
password = "123"
api_key = "abcdef123456"

# 8. STYLE-002: Bad Class Name (should be CapWords)
class badClassName:
    def __init__(self):
        # 5. LOG-002: Logger check
        self.logger = logging.getLogger("test")

    def dangerous_actions(self, user_input):
        # 4. LOG-001: Avoid print
        print("Starting dangerous actions...")

        # 2. SAST-002: Eval
        eval("2 + 2")

        # 3. SAST-003: Exec
        exec("import sys")

        # 6. SAST-004: SQL Injection (concatenation)
        query = "SELECT * FROM users WHERE name = '" + user_input + "'"
        
        # 7. SAST-005: System Command
        os.system("rm -rf /tmp/*")
        subprocess.call(["ls", "-la"])

        try:
            val = 1 / 0
        # 9. ERR-001: Bare Except
        except:
            print("Something went wrong")

# 10. LIC-001: Restricted License Header
# This software is released under the GNU General Public License v3.0
