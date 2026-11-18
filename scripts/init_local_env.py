#!/usr/bin/env python3
"""Create exclusive mode-0600 local Compose credentials; never print secrets."""
import os
import secrets
import subprocess
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
fd = os.open('.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as stream:
    stream.write(f'SOIL_IMPORT_PASSWORD={secrets.token_hex(24)}\nSOIL_SERVE_PASSWORD={secrets.token_hex(24)}\nCODE_REVISION={revision}\n')
print('Created .env with local-only credentials; source revision must be refreshed after commits.')
