#!/usr/bin/env python3
"""
bmw_ce04 — pre-flight auth check.

Standalone troubleshooting tool. NOT part of the Home Assistant integration and
NOT installed by it — just a plain script you run by hand to verify, *outside*
Home Assistant, that your CarData Client ID and BMW account actually work.

It mirrors exactly what the integration does:
  1. OAuth 2.0 Device Code Flow against customer.bmwgroup.com
  2. one GET against cpp.bmw-motorrad.com for your bikes

If this prints your bike(s), your Client ID and account are fine — any remaining
problem is on the Home Assistant / integration side. If it fails here, the
problem is on the BMW side (Client ID, API subscription, or vehicle mapping).

Stdlib only — needs just Python 3.8+. On HA OS, run `apk add python3` first.

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
                (or: type `cd `, drag the folder into Terminal, press Enter)
  3. Run it:
       Windows: python check_auth.py
       macOS:   python3 check_auth.py
  4. Open the printed URL, log in with your BMW ID, approve.

PRIVACY  The output includes your VIN and last-parked GPS coordinates. Do not
paste it publicly without removing those.
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
COUNTRY = "en-EN"   # same default the integration uses
# ---------------------------------------------------------------------------

# These match the integration's const.py exactly.
AUTH_HOST = "https://customer.bmwgroup.com"
API_HOST = "https://cpp.bmw-motorrad.com"
DEVICE_CODE_ENDPOINT = "/gcdm/oauth/device/code"
TOKEN_ENDPOINT = "/gcdm/oauth/token"
BIKES_ENDPOINT_TMPL = "/v2/service/{country}/bmc-user-bikes"


def _pkce():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


def _post(url, *, json_body=None, form=None):
    if json_body is not None:
        data = json.dumps(json_body).encode()
        ctype = "application/json"
    else:
        data = urllib.parse.urlencode(form).encode()
        ctype = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Accept": "application/json", "Content-Type": ctype,
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body}


def _get(url, token):
    req = urllib.request.Request(url, method="GET", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def main():
    client_id = CLIENT_ID.strip().lower()   # integration lowercases it too
    if "PASTE" in client_id.upper():
        print("!! Fill in CLIENT_ID first.")
        return

    verifier, challenge = _pkce()

    print(">> [1/3] Requesting device code ...")
    status, dc = _post(f"{AUTH_HOST}{DEVICE_CODE_ENDPOINT}", json_body={
        "client_id": client_id,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    if status >= 400 or "device_code" not in dc:
        print(f"!! Device code request failed ({status}): {dc}")
        print("   -> Check the Client ID is correct (no spaces/newlines).")
        return

    print("\n=== [2/3] AUTHORIZE ===")
    print("Open this URL, log in, approve:")
    print("   " + (dc.get("verification_uri_complete") or dc.get("verification_uri", "")))
    print(f"(user code: {dc.get('user_code')})\n")

    interval = int(dc.get("interval", 5))
    deadline = time.time() + int(dc.get("expires_in", 600))
    token = None
    print(">> Waiting for approval ", end="", flush=True)
    while time.time() < deadline:
        time.sleep(interval)
        print(".", end="", flush=True)
        status, tok = _post(f"{AUTH_HOST}{TOKEN_ENDPOINT}", form={
            "client_id": client_id,
            "device_code": dc["device_code"],
            "code_verifier": verifier,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "response_type": "device_code",
        })
        if status < 400 and "access_token" in tok:
            token = tok["access_token"]
            print("\n>> Token OK.")
            break
        err = tok.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        print(f"\n!! Token error ({status}): {tok}")
        return
    if not token:
        print("\n!! Timed out waiting for approval.")
        return

    print("\n=== [3/3] Fetching bikes ===")
    url = f"{API_HOST}{BIKES_ENDPOINT_TMPL.format(country=COUNTRY)}"
    print(url)
    status, body = _get(url, token)
    print(f"-> HTTP {status}")
    if status >= 400:
        print("   " + body[:600])
        print("\n!! Auth worked but the bikes endpoint refused. Check your "
              "country/region and that the bike is on this BMW account.")
        return

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("   (non-JSON response)\n   " + body[:600])
        return

    # Mirror the integration's bike extraction.
    bikes = []
    if isinstance(data, dict):
        if isinstance(data.get("bmcUserBikes"), dict):
            bikes = data["bmcUserBikes"].get("bikes", [])
        elif isinstance(data.get("items"), list):
            bikes = data["items"]
        elif isinstance(data.get("bikes"), list):
            bikes = data["bikes"]
        else:
            bikes = [data]
    elif isinstance(data, list):
        bikes = data
    bikes = [b for b in bikes if not (isinstance(b, dict) and b.get("_deleted"))]

    print(f"\n>> SUCCESS — found {len(bikes)} bike(s):")
    for b in bikes:
        if not isinstance(b, dict):
            continue
        print(f"   • {b.get('name','?')}  "
              f"typeKey={b.get('typeKey')}  color={b.get('color')}  "
              f"SOC={b.get('energyLevel', b.get('fuelLevel'))}%  VIN={b.get('vin')}")

    print("\nYour Client ID and BMW account work. If Home Assistant still won't "
          "set up, the problem is on the integration/HA side, not BMW.")
    print("\n(Privacy: the lines above contain your VIN — remove it before "
          "sharing.)")


if __name__ == "__main__":
    main()
