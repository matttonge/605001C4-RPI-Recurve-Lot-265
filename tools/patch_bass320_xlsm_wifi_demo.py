#!/usr/bin/env python3
"""Patch Bass-320 xlsm for Wi-Fi-only demo layout.

- Hide/remove USB GetFromRecurve button
- Rename Wi-Fi button to "Get Balloon Measurement Data" and place at AA2
- AA1 = "BMS IP Address:" label
- AB1 = Pi IP address (moved from AA1)
- Patch embedded VBA WIFI_IP_CELL AA1 → AB1
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
XLSM = ROOT / "Bln. Inspection Data Sheet Bass-320 Templet.xlsm"
NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
NS_XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
NS_X14 = "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main"


def _register_namespaces() -> None:
    ET.register_namespace("", NS_MAIN)
    ET.register_namespace("r", NS_R)
    ET.register_namespace("mc", NS_MC)
    ET.register_namespace("xdr", NS_XDR)
    ET.register_namespace("x14", NS_X14)
    ET.register_namespace("x15", "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main")


def _shared_strings(xml: bytes) -> tuple[list[str], ET.Element]:
    root = ET.fromstring(xml)
    strings: list[str] = []
    for si in root.findall(f"{{{NS_MAIN}}}si"):
        texts = [t.text or "" for t in si.findall(f".//{{{NS_MAIN}}}t")]
        strings.append("".join(texts))
    return strings, root


def _ensure_shared_string(strings: list[str], root: ET.Element, value: str) -> int:
    if value in strings:
        return strings.index(value)
    si = ET.SubElement(root, f"{{{NS_MAIN}}}si")
    t = ET.SubElement(si, f"{{{NS_MAIN}}}t")
    if value[:1].isspace() or value[-1:].isspace():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = value
    strings.append(value)
    root.set("count", str(int(root.get("count", "0")) + 1))
    root.set("uniqueCount", str(len(strings)))
    return len(strings) - 1


def _patch_shared_strings(xml: bytes) -> tuple[bytes, int, int]:
    strings, root = _shared_strings(xml)
    label_idx = _ensure_shared_string(strings, root, "BMS IP Address:")
    # Keep existing sample IP string if present; otherwise add a placeholder.
    ip_value = "192.168.68.64"
    if ip_value in strings:
        ip_idx = strings.index(ip_value)
    else:
        ip_idx = _ensure_shared_string(strings, root, ip_value)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), label_idx, ip_idx


def _set_cell_shared(sheet_xml: str, cell_ref: str, style: str, shared_idx: int) -> str:
    pattern = rf'<c r="{cell_ref}"[^/]*/>|<c r="{cell_ref}"[^>]*>.*?</c>'
    replacement = f'<c r="{cell_ref}" s="{style}" t="s"><v>{shared_idx}</v></c>'
    new_xml, n = re.subn(pattern, replacement, sheet_xml, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError(f"Could not patch cell {cell_ref}")
    return new_xml


def _patch_sheet_controls(sheet_xml: str) -> str:
    # Drop USB control; keep Wi-Fi control and move to AA2 (col 26, row 1).
    wifi_control = (
        '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
        '<mc:Choice Requires="x14">'
        '<control shapeId="1028" r:id="rId5" name="btnGetFromRecurveWifi">'
        '<controlPr defaultSize="0" print="0" autoFill="0" autoPict="0" '
        'macro="GetFromRecurveWifi">'
        '<anchor moveWithCells="1" sizeWithCells="1">'
        "<from>"
        "<xdr:col>26</xdr:col><xdr:colOff>0</xdr:colOff>"
        "<xdr:row>1</xdr:row><xdr:rowOff>19050</xdr:rowOff>"
        "</from>"
        "<to>"
        "<xdr:col>30</xdr:col><xdr:colOff>95250</xdr:colOff>"
        "<xdr:row>2</xdr:row><xdr:rowOff>95250</xdr:rowOff>"
        "</to>"
        "</anchor>"
        "</controlPr>"
        "</control>"
        "</mc:Choice>"
        "</mc:AlternateContent>"
    )
    controls_block = (
        '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
        '<mc:Choice Requires="x14">'
        f"<controls>{wifi_control}</controls>"
        "</mc:Choice>"
        "</mc:AlternateContent>"
    )
    new_xml, n = re.subn(
        r'<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
        r'<mc:Choice Requires="x14"><controls>.*?</controls></mc:Choice></mc:AlternateContent>',
        controls_block,
        sheet_xml,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError("Could not patch worksheet controls")
    return new_xml


def _patch_vml(vml: str) -> str:
    # Remove USB button shape; rewrite Wi-Fi button caption + AA2 anchor.
    vml = re.sub(
        r"<v:shape id=\"btnGetFromRecurve\".*?</v:shape>",
        "",
        vml,
        count=1,
        flags=re.S,
    )
    wifi_shape = """<v:shape id="btnGetFromRecurveWifi" o:spid="_x0000_s1028" type="#_x0000_t201"
  style='position:absolute;margin-left:0;margin-top:0;width:220pt;
  height:22pt;z-index:2;mso-wrap-style:tight' o:button="t" fillcolor="buttonFace [67]"
  o:insetmode="auto">
  <v:fill color2="buttonFace [67]" o:detectmouseclick="t"/>
  <o:lock v:ext="edit" rotation="t"/>
  <v:textbox style='mso-direction-alt:auto' o:singleclick="f">
   <div style='text-align:center'><font face="Arial" size="160" color="#000000">Get Balloon Measurement Data</font></div>
  </v:textbox>
  <x:ClientData ObjectType="Button">
   <x:Anchor>
    26, 0, 1, 2, 30, 10, 2, 10</x:Anchor>
   <x:PrintObject>False</x:PrintObject>
   <x:AutoFill>False</x:AutoFill>
   <x:FmlaMacro>GetFromRecurveWifi</x:FmlaMacro>
   <x:TextHAlign>Center</x:TextHAlign>
   <x:TextVAlign>Center</x:TextVAlign>
  </x:ClientData>
 </v:shape>"""
    new_vml, n = re.subn(
        r"<v:shape id=\"btnGetFromRecurveWifi\".*?</v:shape>",
        wifi_shape,
        vml,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise RuntimeError("Could not patch Wi-Fi VML button")
    return new_vml


def _patch_sheet_rels(rels: str) -> str:
    # Drop unused USB ctrlProp relationship rId4 if present; keep rId5 for Wi-Fi.
    return re.sub(
        r'<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/ctrlProp" Target="../ctrlProps/ctrlProp1.xml"/>',
        "",
        rels,
        count=1,
    )


def _patch_vba(vba: bytes) -> bytes:
    # Length-preserving replacements so VBA binary structure stays valid.
    replacements = [
        (b"AA1", b"AB1"),  # WIFI_IP_CELL and comments that fit
    ]
    out = vba
    for old, new in replacements:
        if len(old) != len(new):
            raise ValueError("VBA patch must be same length")
        out = out.replace(old, new)
    return out


def main() -> None:
    _register_namespaces()
    if not XLSM.exists():
        raise SystemExit(f"Missing {XLSM}")

    backup = XLSM.with_suffix(XLSM.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(XLSM, backup)

    with zipfile.ZipFile(XLSM, "r") as zin:
        contents = {name: zin.read(name) for name in zin.namelist()}

    ss_xml, label_idx, ip_idx = _patch_shared_strings(contents["xl/sharedStrings.xml"])
    contents["xl/sharedStrings.xml"] = ss_xml

    sheet = contents["xl/worksheets/sheet1.xml"].decode("utf-8")
    sheet = _set_cell_shared(sheet, "AA1", "8", label_idx)
    sheet = _set_cell_shared(sheet, "AB1", "8", ip_idx)
    sheet = _patch_sheet_controls(sheet)
    contents["xl/worksheets/sheet1.xml"] = sheet.encode("utf-8")

    contents["xl/drawings/vmlDrawing1.vml"] = _patch_vml(
        contents["xl/drawings/vmlDrawing1.vml"].decode("utf-8")
    ).encode("utf-8")

    contents["xl/worksheets/_rels/sheet1.xml.rels"] = _patch_sheet_rels(
        contents["xl/worksheets/_rels/sheet1.xml.rels"].decode("utf-8")
    ).encode("utf-8")

    contents["xl/vbaProject.bin"] = _patch_vba(contents["xl/vbaProject.bin"])

    tmp = XLSM.with_suffix(".xlsm.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in contents.items():
            # Store some OOXML parts uncompressed like Excel does for a few entries.
            compress = zipfile.ZIP_STORED if name in ("[Content_Types].xml",) else zipfile.ZIP_DEFLATED
            zout.writestr(name, data, compress_type=compress)
    tmp.replace(XLSM)
    print(f"Patched {XLSM.name}: AA1 label idx={label_idx}, AB1 IP idx={ip_idx}")


if __name__ == "__main__":
    main()
