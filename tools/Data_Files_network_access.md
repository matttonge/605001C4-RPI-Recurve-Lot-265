# Access Recurve Data_Files from a Windows PC

These steps let a Windows PC open the Raspberry Pi `Data_Files` folder in File Explorer when both devices are on the same local network (LAN or Wi‑Fi).

Shared folder on the Pi:

`/home/rp/Desktop/Recurve/Data_Files`

Windows share name:

`Data_Files`

---

## Prerequisites

- Raspberry Pi user: `rp`
- Recurve app installed at: `/home/rp/Desktop/Recurve`
- PC and Pi on the **same local network**
- You know the Pi IP address (examples used here: `192.168.1.233` on wired LAN, `192.168.68.65` on Wi‑Fi)

Find the Pi IP from the Pi:

```bash
hostname -I
```

Or from a Windows PC:

```powershell
ping rp
```

If that fails, check your router’s device list for the Pi hostname (`605002B-2` or similar).

---

## Part A — One-time setup on the Raspberry Pi

### 1. Install Samba (if not already installed)

SSH into the Pi:

```bash
ssh rp@<PI_IP_ADDRESS>
```

Then:

```bash
sudo apt update
sudo apt install -y samba
```

### 2. Create / refresh the Data_Files share

From this repository, copy and run the setup script on the Pi:

```bash
# From your Windows development PC (example):
scp tools/setup_data_files_samba.sh rp@<PI_IP_ADDRESS>:~/
ssh rp@<PI_IP_ADDRESS> "sed -i 's/\r$//' ~/setup_data_files_samba.sh; bash ~/setup_data_files_samba.sh"
```

Or configure manually by appending this to `/etc/samba/smb.conf`:

```ini
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
```

Then restart Samba:

```bash
sudo systemctl enable smbd nmbd
sudo systemctl restart smbd nmbd
sudo systemctl is-active smbd
```

### 3. Confirm the share

On the Pi:

```bash
sudo testparm -s | grep -A20 '\[Data_Files\]'
ss -ltn | grep -E ':139|:445'
ls -ld /home/rp/Desktop/Recurve/Data_Files
```

You should see:

- share path = `/home/rp/Desktop/Recurve/Data_Files`
- ports `445` and `139` listening
- folder permissions at least `755` (`drwxr-xr-x`)

### 4. If your network is not 192.168.1.x or 192.168.68.x

Edit `/etc/samba/smb.conf` and add your subnet to `hosts allow`, for example:

```ini
hosts allow = 192.168.1. 192.168.68. 192.168.0. 10.0.0. 127.
```

Then:

```bash
sudo systemctl restart smbd nmbd
```

---

## Part B — Access from a Windows 11 PC

### 1. Confirm network connectivity

On the PC (PowerShell or Command Prompt):

```powershell
ping <PI_IP_ADDRESS>
```

Example:

```powershell
ping 192.168.68.65
```

### 2. Open the share in File Explorer

In the File Explorer address bar, enter:

```text
\\<PI_IP_ADDRESS>\Data_Files
```

Examples:

```text
\\192.168.68.65\Data_Files
\\192.168.1.233\Data_Files
```

The share is configured for guest access on allowed local subnets, so it should open without a password.

If Windows prompts for credentials, try:

- Username: `Guest`
- Password: (leave blank)

or

- Username: `rp`
- Password: (Pi login password, if Samba password was also set)

### 3. Optional — Map a drive letter

1. Open **This PC**
2. Select **Map network drive**
3. Choose a drive letter (for example `R:`)
4. Folder:

```text
\\<PI_IP_ADDRESS>\Data_Files
```

5. Check **Reconnect at sign-in** if desired
6. Finish

---

## What you can do with the share

- Copy lot `.xlsx` files to/from the PC
- Open lot files in Excel on the PC
- Back up `Data_Files` over the network

Avoid editing the same lot file on the Pi Recurve app and on the PC at the same time.

---

## Troubleshooting

| Symptom | What to check |
|--------|----------------|
| `ping` fails | PC and Pi not on same network; wrong IP; Wi‑Fi isolation enabled on router |
| “Windows cannot access …” | Samba not running: `sudo systemctl status smbd` |
| Share not listed | Use full path `\\IP\Data_Files` (not just `\\IP`) |
| Access denied | PC IP not in `hosts allow`; update subnet and restart `smbd` |
| Folder empty / permission error | On Pi: `chmod 755 ~/Desktop/Recurve/Data_Files` |
| Works on LAN IP but not Wi‑Fi IP | Use the IP for the network the PC is on |

Quick Samba restart on the Pi:

```bash
sudo systemctl restart smbd nmbd
```

---

## Related files in this repo

- `tools/setup_data_files_samba.sh` — creates/updates the `Data_Files` Samba share
- `tools/setup_recurve_samba.sh` — older helper (kept for reference; prefer Data_Files-only share)
