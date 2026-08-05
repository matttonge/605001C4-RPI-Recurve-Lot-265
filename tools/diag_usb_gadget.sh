#!/bin/bash
set +e
echo "MODEL: $(tr -d '\0' </proc/device-tree/model)"
echo "==== dt usb/dwc nodes ===="
find /proc/device-tree -iname '*dwc*' 2>/dev/null | head -40
find /proc/device-tree -iname 'usb@*' 2>/dev/null | head -40
echo "==== try modprobe dwc2 ===="
sudo modprobe -r g_serial libcomposite 2>/dev/null
sudo modprobe -v dwc2
echo "exit:$?"
lsmod | grep -E 'dwc|udc' || true
echo "==== udc ===="
ls -la /sys/class/udc 2>&1
ls -la /sys/bus/platform/drivers/dwc2 2>&1 | head -20
echo "==== bootloader ===="
vcgencmd bootloader_config 2>/dev/null | head -40
echo "==== config snippet ===="
sed -n '40,60p' /boot/firmware/config.txt 2>/dev/null || sed -n '40,60p' /boot/config.txt
echo "==== dmesg ===="
dmesg | grep -iE 'overlay|dwc2|Failed|UDC' | tail -30
echo "==== cmdline ===="
cat /proc/cmdline
