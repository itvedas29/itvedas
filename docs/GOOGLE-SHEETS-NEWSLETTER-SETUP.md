# Google Sheets newsletter signup setup

The homepage signup sends an opted-in email to `/api/subscribe`. The Cloudflare
Pages Function forwards it to a Google Apps Script web app; the script writes
the address and consent record to the `Newsletter Subscribers` tab in the
bound spreadsheet. The Apps Script webhook secret is never sent to the browser.

## Bind the script to the Sheet

1. Open the shared ITVedas spreadsheet.
2. Select **Extensions > Apps Script**.
3. Replace the editor contents with [`integrations/google-sheets-newsletter/Code.gs`](../integrations/google-sheets-newsletter/Code.gs) and save.
4. In Apps Script, open **Project Settings > Script Properties > Add script property**. Set the property name to `NEWSLETTER_WEBHOOK_SECRET` and the value to a newly generated, high-entropy secret. Do not put this value in the spreadsheet, source control, or browser code.
5. Select **Deploy > New deployment > Web app**. Set **Execute as** to your account and **Who has access** to **Anyone**, then deploy and authorize access to the bound spreadsheet. The shared secret is required for writes; the endpoint URL is not a substitute for it.
6. Copy the deployed web app URL. It should end in `/exec`.
7. In Cloudflare Pages, open the ITVedas project's **Settings > Variables and Secrets** and add these production variables:
   - `GOOGLE_SHEETS_WEB_APP_URL`: the deployed `/exec` URL.
   - `GOOGLE_SHEETS_WEBHOOK_SECRET`: the same secret as the Apps Script property.
8. Redeploy the site after adding the variables.

The script creates a `Newsletter Subscribers` tab with a header row on first
signup. It stores the UTC signup time, normalized email, signup source, consent,
and subscription status. Duplicate addresses are not added. No quiz addresses
are sent to this endpoint.

## Verify

Submit the homepage form with an email address you control and check that one
row appears in the tab. Submit it again to confirm the duplicate is not added.
Check that an unchecked consent box prevents submission. Keep the spreadsheet
restricted to people who need access; do not publish it to the web.

If Apps Script code is changed after deployment, create a new deployment
version (or edit the existing deployment to use the new version).
