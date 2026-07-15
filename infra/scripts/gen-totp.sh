#!/usr/bin/env bash
# TOTP enrollment: secret on STDOUT (for capture), QR + guidance on STDERR.
# NEVER screenshot the QR -- it encodes the secret.
set -euo pipefail
python3 - << 'PY'
import base64, secrets, sys
sec = base64.b32encode(secrets.token_bytes(20)).decode()
uri = f"otpauth://totp/Keel%20Webchat?secret={sec}&issuer=Keel"
try:
    import qrcode
    q = qrcode.QRCode(border=1); q.add_data(uri)
    q.print_ascii(invert=True, out=sys.stderr)
except ImportError:
    print("qrcode module missing (apt: python3-qrcode); enroll via URI:", file=sys.stderr)
print(f"\nScan with your authenticator, or add manually:\n{uri}", file=sys.stderr)
print("Do NOT screenshot -- the QR encodes the secret.\n", file=sys.stderr)
print(sec)
PY
