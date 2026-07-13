#!/bin/bash
set -euo pipefail

if [ ! -f /etc/samba/smb.conf.bak.recurve ]; then
  sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak.recurve
fi

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
print("smb.conf updated")
PY

chmod 755 /home/rp/Desktop/Recurve/Data_Files || true

echo "=== Data_Files share ==="
sudo testparm -s 2>&1 | awk '/\[Data_Files\]/{flag=1} flag{print} /^\[/ && !/\[Data_Files\]/{if(seen++) exit}' 

sudo systemctl enable smbd nmbd >/dev/null
sudo systemctl restart smbd nmbd
echo "smbd: $(systemctl is-active smbd)"
echo "nmbd: $(systemctl is-active nmbd)"
echo "=== ports ==="
ss -ltn | grep -E ':139|:445' || true
echo "DONE"
