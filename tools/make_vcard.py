#!/usr/bin/env python3
"""Write src/contact.vcf: the contact the business card's QR code opens, with the M⚡S icon
as the contact photo.

    python3 tools/make_vcard.py

Printed cards point at https://marksparks845.com/contact.vcf, so keep that path forever.
vCard 3.0, CRLF line endings, lines folded at 75 bytes. robots.txt keeps it out of search.
"""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTO = ROOT / "tools" / "icons" / "apple-touch-icon-512.png"   # square; Contacts crops it round
OUT = ROOT / "src" / "contact.vcf"

FIELDS = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    "N:Fielbig;Mark;;;",
    "FN:Mark Fielbig",
    "ORG:Mark Sparks LLC",
    "TEL;TYPE=WORK,VOICE:+1-845-464-1808",
    "EMAIL;TYPE=WORK,INTERNET:mark@marksparks845.com",
    "URL:https://marksparks845.com/",
    r"NOTE:Electrical\, smart home & carpentry · Dutchess County\, NY",
]


def fold(line):
    b = line.encode()
    out = [b[:75]]
    b = b[75:]
    while b:
        out.append(b" " + b[:74])
        b = b[74:]
    return b"\r\n".join(out)


def main():
    lines = FIELDS + ["PHOTO;ENCODING=b;TYPE=PNG:" + base64.b64encode(PHOTO.read_bytes()).decode(), "END:VCARD"]
    OUT.write_bytes(b"\r\n".join(fold(l) for l in lines) + b"\r\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
