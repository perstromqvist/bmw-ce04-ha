#!/usr/bin/env python3
"""
BMW CarData — get a GCDM access token.

Standalone helper that runs the OAuth 2.0 Device Code Flow and prints a CarData
**access token (GCDM Access Token / bearerAuth)** you can paste into BMW's online
API explorer:

    https://bmw-cardata.bmwgroup.com/customer/public/api-specification

Click "Authorize" there, paste the token, and you can try the CarData API calls
interactively.

NOTE  This authenticates against the CarData API (scope cardata:api:read), which
is NOT what this Home Assistant integration uses (that reads the CloudBike
endpoint). The CE 04 itself returns CU-104 there (no SIM / not a CarData
vehicle) — but a telematics-capable BMW (e.g. a car on the same account) will
return data. Your client must be subscribed to "CarData API" in the portal.

Stdlib only — needs just Python 3.8+.

GETTING PYTHON (if you don't already have it)
  - Windows: install from https://www.python.org/downloads/ and TICK
             "Add python.exe to PATH" in the installer. Then use `python`.
  - macOS:   open Terminal and type `python3` once; if it's missing, macOS
             offers to install it. (Or install from python.org.)
  - HA OS:   in the Terminal add-on, run `apk add python3` first.

RUNNING IT
  1. Save this file, then put your CarData Client ID in the line below.
  2. Open a terminal IN THE FOLDER where you saved this file:
       Windows: Shift + right-click the folder -> "Open PowerShell window here"
       macOS:   right-click the folder in Finder -> "New Terminal at Folder"
  3. Run it:
       Windows: python cardata_token.py
       macOS:   python3 cardata_token.py
  4. Open the printed URL, log in with your BMW ID, approve.
  5. Copy the printed token into the Swagger "Authorize" dialog (bearerAuth).

PRIVACY  The printed token grants access to your account's CarData for ~1 hour.
Do not share it. It expires on its own.
"""

import base64
import hashlib
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
CLIENT_ID = "PASTE-YOUR-CARDATA-CLIENT-ID"
# ---------------------------------------------------------------------------

AUTH_HOST = "https://customer.bmwgroup.com"
DEVICE_CODE_ENDPOINT = "/gcdm/oauth/device/code"
TOKEN_ENDPOINT = "/gcdm/oauth/token"
SCOPE = "authenticate_user openid cardata:api:read"


def _pkce():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def _post_form(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"raw": raw}


def main():
    client_id = CLIENT_ID.strip().lower()
    if "PASTE" in client_id.upper():
        print("!! Fill in CLIENT_ID first.")
        return

    verifier, challenge = _pkce()

    print(">> Requesting device code ...")
    status, dc = _post_form(f"{AUTH_HOST}{DEVICE_CODE_ENDPOINT}", {
        "client_id": client_id,
        "response_type": "device_code",
        "scope": SCOPE,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    if status >= 400 or "device_code" not in dc:
        print(f"!! Device code request failed ({status}): {dc}")
        print("   -> Check the Client ID, and that it's subscribed to the "
              "CarData API (scope cardata:api:read) in the portal.")
        return

    print("\n=== AUTHORIZE ===")
    print("Open this URL, log in, approve:")
    print("   " + (dc.get("verification_uri_complete") or dc.get("verification_uri", "")))
    print(f"(user code: {dc.get('user_code')})\n")

    interval = int(dc.get("interval", 5))
    deadline = time.time() + int(dc.get("expires_in", 600))
    print(">> Waiting for approval ", end="", flush=True)
    while time.time() < deadline:
        time.sleep(interval)
        print(".", end="", flush=True)
        status, tok = _post_form(f"{AUTH_HOST}{TOKEN_ENDPOINT}", {
            "client_id": client_id,
            "device_code": dc["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "code_verifier": verifier,
        })
        if status < 400 and "access_token" in tok:
            print("\n")
            print("=" * 68)
            print("ACCESS TOKEN (paste into the Swagger 'Authorize' -> bearerAuth):")
            print("=" * 68)
            print(tok["access_token"])
            print("=" * 68)
            print(f"scope     : {tok.get('scope')}")
            print(f"expires_in: {tok.get('expires_in')} seconds (~1 hour)")
            print("\n!! Sensitive — do not share this token. It expires on its own.")
            return
        err = tok.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        print(f"\n!! Token error ({status}): {tok}")
        return
    print("\n!! Timed out waiting for approval.")


if __name__ == "__main__":
    main()
