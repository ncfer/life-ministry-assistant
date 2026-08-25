<p align="center">
  <img src="assets/logo.png" alt="Life &amp; Ministry Assistant" width="420">
</p>

<p align="center"><i><a href="README.es.md">Leer en español →</a></i></p>

Generates assignment slips (PDF/JPG) and calendar reminders from the
Life and Ministry Meeting Workbook, and sends them over WhatsApp — no
Excel, no macros, no BulkPDF/Wine. Works on Linux, Windows and Mac.

There are two ways to use it: with a **window** (built for anyone, no
computer skills needed) or from the **terminal** (faster once you're
used to it). Both do the same thing under the hood.

<p align="center">
  <img src="docs/screenshots/en/home.png" width="49%" alt="Home screen">
  <img src="docs/screenshots/en/workbook_picker.png" width="49%" alt="Picking the meeting workbook, with the Padlet source already configured">
</p>
<p align="center">
  <img src="docs/screenshots/en/contacts.png" width="49%" alt="Contact list editor">
  <img src="docs/screenshots/en/message.png" width="49%" alt="WhatsApp message template editor with live preview">
</p>

## Features

- **Assignment slips** — generates the official S-89-style PDF/JPG slip
  for every assignment that has one, straight from the Life and
  Ministry Meeting workbook PDF. No manual copy-pasting.
- **Calendar reminders** — attaches a `.ics` file, a Google Calendar
  link, or both to each assignment, so it lands straight on the
  person's phone calendar.
- **Meeting reminders, beyond just the slip roles** — a separate flow
  that reminds *everyone* with a part that week (Bible reading, Living
  as Christians talks, prayers, Treasures/Digging Gems…, not only the
  roles that get an official S-89 slip). It sends that week's program
  photo with a short personalized caption for each participant.
- **Three ways to bring in the workbook**: pick a local PDF, pull it
  straight from a Padlet board (if your congregation posts it there),
  or from a Google Drive link — no manual downloading once it's set up.
- **WhatsApp sending, automated but careful** — drives a real Chrome/
  Chromium window over WhatsApp Web (not an unofficial API pretending
  to be WhatsApp), with pauses between sends and a manual confirmation
  step before anything goes out.
- **Smart contact matching** — looks up each person's phone number
  automatically; if it can't find an exact match it suggests the
  closest name instead of silently failing or sending nothing.
- **Editable message templates with a live preview** — change the
  wording without touching code. Placeholders like `{name}` or `{date}`
  fill themselves in, and you see exactly what the recipient will get
  before anything is sent.
- **Send history** — every batch you send (assignments and reminders)
  is logged, so you can check who got what and when.
- **Two ways to use it** — a full windowed mode for anyone, or a
  scriptable terminal/CLI mode for advanced or batch use.
- **Switchable UI language** and a **light/dark theme**, both
  changeable from Settings at any time.
- **Runs anywhere** — Linux, Windows and Mac, either as a single-file
  executable or straight from source.

## Installation (first time only)

No terminal or computer skills needed: unzip the folder wherever you
want and double-click your system's launcher:

- **Windows:** if `LifeMinistryAssistant.exe` exists in this folder, use
  it — it doesn't need Python installed (everything's bundled), it's
  about 150–200 MB, and it starts right up. If it doesn't exist, use
  `launch_gui.bat` instead (does the same thing, but needs Python
  installed and shows up as a console window). You can create a Desktop
  shortcut by right-clicking either one → "Create shortcut".
  (`LifeMinistryAssistant.exe` doesn't ship pre-built in the zip because of
  its size — whoever distributes the app can build it once by running
  `build_exe.bat` on a real Windows machine, see the comment inside that
  file. `LifeMinistryAssistant.exe` doesn't download a browser on its own:
  if it can't find Chrome, Edge or Chromium installed when sending over
  WhatsApp, it tells you clearly what to install. `launch_gui.bat` still
  offers to download its own browser automatically the first time if
  needed, same as before.)
- **Mac:** `launch_gui.command` (don't use `launch_gui.sh` for
  double-clicking — Mac would open it as a text file instead of running
  it). The first time, Mac may warn that it's from "an unidentified
  developer" — right-click the file → **Open**, and confirm the prompt
  (only needed that one time).
- **Linux:** double-click `launch_gui.sh` (if your file manager asks
  what to do, choose "Run" or "Run in terminal"), or from a terminal:
  `./launch_gui.sh`.

The first time you open it, everything installs itself — the Python
environment, all dependencies, and the browser for WhatsApp if needed —
so it takes a few minutes and needs an internet connection; leave the
window open until it finishes. After that, it opens instantly.

You only need **Python 3** installed beforehand (if you don't have it,
the launcher itself tells you with a download link —
[python.org/downloads](https://www.python.org/downloads/); on Windows,
check the "Add python.exe to PATH" box during installation) and, if you
want to send over WhatsApp using your own Chrome instead of a downloaded
one, **Google Chrome** already installed — if you don't have it, the
launcher downloads its own browser automatically, no action needed.

## Windowed mode (recommended)

The first time, it'll ask you to set up the paths (where the S-89
assignment template PDF is, where to save generated files, etc.) —
done once from the window itself, no files to touch by hand. The S-89
template PDF isn't included — ask whoever gave you this folder, or use
the one your congregation already has.

After that, each week you just need to:
1. **New weekly assignment** → pick the workbook PDF.
2. Check the week (or weeks) you want to generate.
3. Review the table: if someone's phone number wasn't found, it shows
   up highlighted in red with a suggestion button if there's a similar
   name in the list, or you can type it in by hand.
4. Preview each slip before continuing.
5. Choose whether to send a `.ics` file, a Google Calendar link, or
   both, check "I've reviewed this" and hit SEND.

**Send reminders** works the same way but covers everyone with a part
that week, not just the roles that get an official slip: pick the
workbook, review the table (same phone-number matching and preview),
and it sends that week's program photo with a personalized caption to
each participant — no `.ics`/calendar step here, since it's a quick
heads-up rather than a formal assignment.

From the home screen you can also edit contacts, the assignment and
reminder messages, and advanced settings (language, theme, WhatsApp
timing between sends) — all through forms, no files or commands.

## Terminal mode (advanced)

### 1. Editing the contact list

Contacts live in `contacts.csv`, a plain text file with two columns:
`name` and `phone`. Two ways to edit it, pick whichever's more
comfortable:

- **With a spreadsheet:** open `contacts.csv` with LibreOffice Calc,
  Excel or Google Sheets, edit it like a normal table, and save (keep
  the CSV format when saving).
- **With the terminal menu**, without touching any file by hand:
  ```bash
  python -m assistant.edit_contacts
  ```
  Lets you list, search, add/update and delete contacts through a
  numbered menu.

The phone number goes with the country code and no spaces, `+`, or
other symbols — e.g. a US number would be `15551234567`, a UK number
`447911123456`.

If you're coming from the old Excel file and want to bring over the
whole list at once:
```bash
python -m assistant.migrate_contacts "Assignment Template.xlsm" contacts.csv
```

### 2. Editing the WhatsApp message

The text that gets sent lives in `message.txt`, in plain language, no
code involved. You can change it however you like; the placeholders in
curly braces get filled in automatically with each assignment's data:

| Placeholder | Filled with |
|---|---|
| `{name}` | Person's full name |
| `{first_name}` | Person's first name only |
| `{helper}` | Helper's name (empty if none) |
| `{date}` | Meeting date |
| `{number}` | Assignment number |
| `{type}` | Assignment type (e.g. "Bible Reading") |
| `{link}` | Google Calendar link (if you choose to send it) |

Default example:
```
Hi {first_name}, just a reminder that you have an assignment coming up on {date}. You can add it to your calendar using the link or the file below. Thanks!

{link}
```

### 3. Generating the slips

```bash
python -m assistant.cli \
  --workbook "Meeting Workbook 09-10 2026.pdf" \
  --template "Assignment Template.pdf" \
  --month 2026-09
```

This generates a PDF, a JPG and a `.ics` file per person inside
`output/`, and prints a summary showing the phone number found for
each one (or a warning if none was found, to review by hand). Nothing
gets sent yet.

For a single week instead of a whole month:
```bash
--weeks 2026-09-09,2026-09-16
```

### 4. Sending over WhatsApp

Add `--send` to the same command. Before sending anything:
1. It asks whether you want to send the reminder as an `.ics` file, as
   a Google Calendar link, or both (or pass it directly with
   `--reminder ics|gcal|both`).
2. It shows you the summary and asks you to confirm by typing `y`.

The first time, a Chrome window will open with a QR code — scan it with
your phone (WhatsApp > Settings > Linked Devices) and you won't need to
do it again on future runs (the session is saved on your own computer).

**Is it safe?** There's no absolute guarantee, but the risk is low: it
sends to known contacts (not strangers or large lists), and it works by
controlling a real browser over WhatsApp Web — as if you were doing it
by hand, just automated — instead of using some unofficial library that
talks directly to WhatsApp. It also keeps pauses between messages so it
doesn't look like a mass send.

## Output structure

```
output/
└── 2026-09/
    ├── 2026-09-09 - 3 - Jane Doe.pdf
    ├── 2026-09-09 - 3 - Jane Doe.jpg
    ├── 2026-09-09 - 3 - Jane Doe.ics
    └── ...
```

## Sharing this app with someone else or another congregation

Run `./package.sh` (from a terminal, in your working copy) to generate
`dist/life-ministry-assistant-YYYYMMDD.zip`: a clean copy of the
project, without your contacts, your send history, your configuration,
any workbooks you've used, or your own customized message wording —
just the code and a sample `contacts.csv`. Share it as-is; whoever receives it just needs to
unzip it and follow the "Installation" section above. If you change
something in the code later, run `./package.sh` again to generate an
updated zip — no extra steps per operating system, it's the same
folder for Windows, Mac and Linux.
