#!/bin/bash
set -euo pipefail

sudo python3 <<'PY'
from pathlib import Path
import re

p = Path("/etc/samba/smb.conf")
text = p.read_text(encoding="utf-8")
text = re.sub(r"\n\[Recurve\][\s\S]*?(?=\n\[|\Z)", "", text)
text = re.sub(r"\n\[Data_Files\][\s\S]*?(?=\n\[|\Z)", "", text)
share = """

[Data_Files]
   comment = Recurve lot Data_Files only
   path = /home/rp/Desktop/Recurve/Data_Files
   browseable = yes
   read only = no
   guest ok = yes
   force user = rp
   force group = rp
   create mask = 0664
   directory mask = 0775
   hosts allow = 192.168.1. 192.168.68. 127.
"""
p.write_text(text.rstrip() + share + "\n", encoding="utf-8")
print("smb.conf updated to Data_Files-only share")
PY

chmod 755 /home/rp/Desktop/Recurve/Data_Files || true
sudo systemctl restart smbd nmbd
sudo testparm -s 2>/dev/null | grep -A20 '\[Data_Files\]'
echo "smbd: $(systemctl is-active smbd)"
