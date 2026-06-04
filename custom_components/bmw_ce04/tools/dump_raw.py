#!/usr/bin/env python3
"""
bmw_ce04 — raw data dump (for contributors).

Standalone helper for anyone who wants to contribute a data sample from their
BMW Motorrad — WITHOUT installing Home Assistant, HACS, or this integration.
It logs in with a CarData Client ID and prints + saves the raw API response for
their bike(s), so they can share it to help support more models.

By default the output is MASKED: VIN, ID hashes, GPS coordinates and the bike
name are replaced with "REDACTED". The analytically useful fields (typeKey,
vehicleType, energyLevel/fuelLevel, ranges, tyre pressure, units, etc.) are kept
as-is. Pass --full to disable masking (then the file contains your VIN/GPS — do
not share it).

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
       Windows: python dump_raw.py            (add  --full  for an unmasked dump)
       macOS:   python3 dump_raw.py           (add  --full  for an unmasked dump)
  4. Open the printed URL, log in with your BMW ID, approve.
  5. Share the saved bmw_motorrad_dump.json — AND mention your model and
     market/region.
"""

import base64
import hashlib
import json
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
CLIENT_ID = "PASTE-YOUR-CARDATA-CLIENT-ID"
COUNTRY = "en-EN"   # if the fetch returns nothing/404, try your locale: en-GB, de-DE, ...
# ---------------------------------------------------------------------------

AUTH_HOST = "https://customer.bmwgroup.com"
API_HOST = "https://cpp.bmw-motorrad.com"
DEVICE_CODE_ENDPOINT = "/gcdm/oauth/device/code"
TOKEN_ENDPOINT = "/gcdm/oauth/token"
BIKES_ENDPOINT_TMPL = "/v2/service/{country}/bmc-user-bikes"

# Keys whose values are masked by default (compared lowercased).
SENSITIVE = {
    "vin", "hashedshortvin", "hashedlongvin", "vehicleid", "itemid",
    "userid", "userid#itemtype", "name",
    "lastconnectedlat", "lastconnectedlon", "latitude", "longitude",
}


def _pkce():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def _post(url, *, json_body=None, form=None):
    if json_body is not None:
        data, ctype = json.dumps(json_body).encode(), "application/json"
    else:
        data, ctype = urllib.parse.urlencode(form).encode(), "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Accept": "application/json", "Content-Type": ctype})
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
        "Authorization": f"Bearer {token}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def mask(obj):
    if isinstance(obj, dict):
        return {k: ("REDACTED" if k.lower() in SENSITIVE else mask(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask(x) for x in obj]
    return obj


def main():
    full = "--full" in sys.argv
    client_id = CLIENT_ID.strip().lower()
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

    print("\n=== [3/3] Fetching raw data ===")
    url = f"{API_HOST}{BIKES_ENDPOINT_TMPL.format(country=COUNTRY)}"
    print(url)
    status, body = _get(url, token)
    print(f"-> HTTP {status}")
    if status >= 400:
        print("   " + body[:600])
        print("\n!! Auth worked but the data endpoint refused. If you're outside "
              "Sweden, try changing COUNTRY at the top (e.g. en-GB, de-DE).")
        return

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("   (non-JSON response)\n   " + body[:600])
        return

    out = data if full else mask(data)
    pretty = json.dumps(out, indent=2, ensure_ascii=False)

    fname = "bmw_motorrad_dump_full.json" if full else "bmw_motorrad_dump.json"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(pretty)

    print("\n" + "=" * 60)
    print(pretty[:4000])
    if len(pretty) > 4000:
        print("... (truncated in terminal; the full content is in the file)")
    print("=" * 60)
    print(f"\n>> Saved to {fname}")
    if full:
        print("!! This is the FULL, UNMASKED dump (contains VIN/GPS). Keep it private.")
    else:
        print(">> Masked dump — safe to share. (VIN, IDs, GPS and name are REDACTED.)")
    print("\nWhen sharing, please also mention:")
    print("   • your model (e.g. CE 04, R 1250 GS, F 900 R)")
    print("   • your market / region (e.g. Sweden, UK, Germany) — relevant for units")


if __name__ == "__main__":
    main()
