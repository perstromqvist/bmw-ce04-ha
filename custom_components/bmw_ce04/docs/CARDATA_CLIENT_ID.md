# How to Create and Get Your BMW CarData Client ID

To use this integration you need a **CarData Client ID** from BMW. It's free, you
create it once, and it's the credential that lets Home Assistant read your CE 04's
data through BMW's official CarData service.

This guide walks you through it from scratch. It takes about five minutes.

> **What is a Client ID?** Think of it as a key tied to your BMW account that says
> "this app is allowed to read my vehicle data." Home Assistant uses it, together
> with a one-time approval in your browser, to securely fetch data from BMW.

---

## Before you start

You'll need:

- A **BMW account** (BMW ID) — the same one you use in the **My BMW** app.
- Your **CE 04 added to that account**, with ConnectedRide active.
- A few minutes and a browser.

---

## Step 1 — Open the BMW CarData portal

Go to **[bmw-cardata.bmwgroup.com](https://bmw-cardata.bmwgroup.com)** and sign in
with your BMW account (the same login as the My BMW app).

![Step 1 — BMW CarData sign-in page](images/cardata-step1-login.png)
*Sign in with your BMW account. If you can log into the My BMW app, these are the same credentials.*

---

## Step 2 — Create a CarData client

In the portal, find the **API Clients** area (also shown as the **CarData API**
section) and click **Create CarData Client**.

A unique Client ID is generated and shown on screen. It looks like this:

```
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

(a long string of letters and numbers separated by dashes — a "UUID").

![Step 2 — Create CarData Client button and the generated ID](images/cardata-step2-create.png)
*Click "Create CarData Client". Your new Client ID appears — this is what you'll paste into Home Assistant.*

---

## Step 3 — Subscribe to the CarData API service (don't skip this)

Right after creating the client, you must **subscribe it to a service** — otherwise
the login will succeed but no data will come through.

Enable **"Request access to CarData API"** (the `cardata:api:read` permission), then
**Authorize / Save**.

You do **not** need "CarData Stream" for this integration — it reads data through the
regular API, not the live stream.

![Step 3 — Enable "Request access to CarData API" and authorize](images/cardata-step3-scope.png)
*Tick "Request access to CarData API", then authorize. The "CarData Stream" option is not needed here.*

> **⚠️ Known portal quirk:** the scope selection sometimes throws an error. If you see
> an error at the top of the page, **reload the page**, select the permission, **wait
> about 30 seconds**, and then save. It usually works on the second try.

---

## Step 4 — Copy your Client ID

Back in the **CarData API** section, copy your **Client ID** to the clipboard.
Keep it handy for the next step — and treat it as private, since it's linked to your account.

![Step 4 — Copy the Client ID](images/cardata-step4-copy.png)
*Copy the full Client ID. Make sure you grab the whole string, dashes included.*

---

## Step 5 — Paste it into Home Assistant

1. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
2. Search for **BMW CE 04** and select it.
3. **Paste your Client ID** and submit.
4. The next screen shows a **link** and a **code**. Open the link in your browser,
   sign in to BMW if asked, enter the code, and **approve** the request.
5. Only **after** the BMW page confirms the approval, return to Home Assistant and
   click **Submit**.

> **⚠️ Don't click Submit in Home Assistant too early.** Wait until the BMW page has
> confirmed your approval. Submitting before that leaves the setup stuck and you'll
> have to start over.

![Step 5 — Pasting the Client ID into the Home Assistant setup](images/cardata-step5-ha.png)
*The Home Assistant setup asks only for the Client ID. Everything else is handled automatically.*

---

## Troubleshooting

**"Failed to reach BMW CarData" / cannot connect**
Double-check that you pasted the **entire** Client ID (the full UUID, with dashes)
and that Home Assistant has internet access.

**Setup finishes but no data appears**
You most likely skipped **Step 3**. The client must be subscribed to the CarData API
service *before* you approve the device, or the tokens won't be allowed to read data.
Recreate the client if needed and make sure the service is enabled.

**"Authorization failed" / the code stopped working**
The code from the setup is only valid for a few minutes. If it expires, just start the
setup again to get a fresh code.

---

## Good to know

- You only create the Client ID **once** — reuse it if you ever re-add the integration.
- The Client ID is tied to your BMW account; keep it reasonably private.
- This is BMW's **free** CarData service. This integration only **reads** data — it
  never sends commands to your scooter.
