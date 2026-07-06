Statiq Charger Availability Monitor
Checks the availability status of your Statiq EV charger page every 5
minutes and emails you whenever it changes (e.g. available → occupied,
or back to available).
Monitored page:
`https://www.statiq.in/uk-rudrapur-hotel-rudra-continental-ev-charging-station-id-8632`
This runs for free on GitHub Actions, so it works even when your
computer is off. Setup takes about 5 minutes.
1. Create a GitHub repo
Go to https://github.com/new, create a new private repo (e.g. `charger-monitor`).
Upload these three files/folders, keeping the folder structure:
`monitor.py`
`requirements.txt`
`.github/workflows/check_charger.yml`
Easiest way: on the repo page, use "Add file" → "Upload files" and
drag all of them in (GitHub preserves the `.github/workflows/` path
automatically if you drag the whole folder, or you can create the
file manually at that path via "Create new file").
2. Get a Gmail App Password (for sending the alert email)
You don't need a new email account — just an "app password" for your
existing Gmail so this script can send mail on your behalf without
needing your real password.
Go to https://myaccount.google.com/apppasswords (you may need
2-Step Verification turned on first: https://myaccount.google.com/signinoptions/two-step-verification).
Create an app password named e.g. "charger monitor".
Copy the 16-character password shown — you'll paste it into GitHub next.
(Using a different provider like Outlook? It works the same way —
just use their SMTP host, e.g. `smtp.office365.com`.)
3. Add secrets to your GitHub repo
In your repo: Settings → Secrets and variables → Actions → New repository secret.
Add each of these:
Secret name	Value
`CHARGER_URL`	`https://www.statiq.in/uk-rudrapur-hotel-rudra-continental-ev-charging-station-id-8632?longLat=79.389541,28.975838`
`SMTP_HOST`	`smtp.gmail.com`
`SMTP_PORT`	`587`
`SMTP_USER`	your Gmail address
`SMTP_PASS`	the 16-character app password from step 2
`NOTIFY_EMAIL`	the email address you want alerts sent to (can be same as SMTP_USER)
4. Turn it on
The workflow already runs automatically every 5 minutes once it's in
the repo (see the `cron` line in `check_charger.yml`). To test it
immediately instead of waiting:
Go to the Actions tab in your repo.
Click "Check charger status" in the sidebar.
Click "Run workflow" → Run workflow.
Click into the run to see the logs and confirm it worked.
The first run just records the current status as a baseline (no email
sent). From the second run onward, you'll get an email any time the
status changes.
Adjusting the check frequency
Edit the cron line in `.github/workflows/check_charger.yml`:
Every 5 minutes: `*/5 * * * *` (default)
Every 15 minutes: `*/15 * * * *`
Every hour: `0 * * * *`
Note: GitHub Actions free tier gives you 2,000 minutes/month on
private repos, and each run takes well under a minute, so even 5-minute
checks comfortably fit within the free quota. Public repos have
unlimited minutes.
If the site changes its layout
Statiq could update their website design at some point, which might
break the parsing logic in `monitor.py` (the `fetch_statuses`
function). If you start seeing errors in the Actions log about "No
connector status found," let me know and I can update the parser.
