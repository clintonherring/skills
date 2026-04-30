---
name: jet-pi-summary
description: >-
  Investigate production incidents using the Observability Data Lake (ODL) via AWS Athena.
  This skill responds to four explicit commands:
  - "pi timeline <channel>" — build a chronological incident timeline
  - "pi catchup <channel>" — summarise recent discussion and action items
  - "pi post-mortem <channel>" — generate a pre-filled post-mortem document
  - "pi prodmeet" — generate the daily production meeting host briefing
  The channel is a PI channel name like pi-12345.
  Do NOT run this skill for general questions about incidents — only when the user types "pi timeline", "pi catchup", "pi post-mortem", or "pi prodmeet".
metadata:
  owner: ai-platform
---

# ODL Incident Intelligence

Query the Observability Data Lake directly via AWS Athena to build incident timelines and catch-up summaries for production issues (PI channels).

## Prerequisites

- **jet-aws-athena skill** must be installed (provides `athena_query` via `athena_query.sh`)
- Valid AWS credentials for the ODL account (`528757785644`)
- The `odl-members` role assigned for `euw1-plt-prd-3`

## AWS Authentication

The data lake lives in the `euw1-plt-prd-3` environment (account `528757785644`). You need the `odl-members` role.

**Before doing anything else**, check if existing credentials already work:

```bash
aws sts get-caller-identity 2>/dev/null
```

- If this succeeds, credentials are already configured — **skip SSO login entirely** and proceed to querying.
- If this fails, the user needs to authenticate. Ask which method they use:
  - **SSO**: `aws sso login --profile <profile-name> && export AWS_PROFILE=<profile-name>`
  - **Static credentials**: Credentials in `~/.aws/credentials` (e.g. from a vault or role assumption). Just ensure `AWS_PROFILE` or `AWS_DEFAULT_PROFILE` is set if using a non-default profile.

Do NOT assume SSO is required. Many users have valid credentials via other methods (temporary credentials, role assumption, environment variables, or credential files).

## Running Athena Queries

Source the Athena helpers from `jet-aws-athena`. Then use `athena_query` to run SQL, passing the workgroup as the second argument:

```bash
source scripts/athena_query.sh

athena_query "YOUR_SQL_HERE" "odl_athena_workgroup"
```

This handles query submission, polling, and result fetching automatically. The ODL uses the `odl_athena_workgroup` workgroup.

### Data Cleaning

**Always pipe Athena output through the cleaner script** before processing results:

```bash
athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py
```

The cleaner ([references/clean-athena-output.py](references/clean-athena-output.py)) strips Slack mrkdwn formatting (user mentions, rich links, bold/italic/code markers, emoji shortcodes), decodes HTML entities, and normalises whitespace. This ensures the agent always receives clean plaintext — no manual cleanup needed.

Additionally, Jira text fields (`description`, `incident_impact_description`, `root_cause_description`, `timeline`) are stored as arrays in the data lake. The SQL queries use `array_join(field, chr(10))` to flatten them into plain text strings.

## Channel Name → Issue Key

PI Slack channels follow the naming convention `pi-NNNNN`. Convert to a Jira issue key by uppercasing:

```
pi-12345  →  PI-12345
pi-67890  →  PI-67890
```

**Important:** The Jira table uses uppercase keys (`PI-12345`) and the Slack table uses lowercase channel names (`pi-12345`).

Always ask the user for the PI channel name if not provided.

## Commands

This skill has four explicit commands. Do not guess the mode from natural language — only trigger on these exact patterns:

- `pi timeline <channel>` — Build a chronological incident timeline
- `pi catchup <channel>` — Summarise recent discussion and action items
- `pi post-mortem <channel>` — Generate a pre-filled post-mortem document
- `pi prodmeet` — Generate the daily production meeting host briefing

If the user mentions a PI channel without specifying a command, ask which one they want.

### pi timeline \<channel\>

Build a chronological incident timeline combining Jira data and Slack messages.

**Trigger:** `pi timeline pi-12345`

**Workflow:**

1. Extract the channel name from the command (e.g. `pi-12345`)
2. Convert to issue key: `PI-12345`
3. Source the ODL helpers and run the Jira PI summary query (replace `PI-12345` with the actual key):

```bash
source scripts/athena_query.sh

athena_query "
SELECT
    issue.key,
    issue.summary,
    issue.status,
    array_join(issue.description, chr(10)) AS description,
    array_join(issue.incident_impact_description, chr(10)) AS incident_impact_description,
    array_join(issue.root_cause_description, chr(10)) AS root_cause_description,
    array_join(issue.timeline, chr(10)) AS timeline,
    CONCAT('https://justeattakeaway.atlassian.net/browse/', issue.key) AS issue_url,
    issue.incident_start,
    issue.created,
    issue.updated
FROM transformed_data.jira_pi issue
WHERE key = 'PI-12345'
    AND issue.updated = (SELECT MAX(updated) FROM transformed_data.jira_pi WHERE key = issue.key)
GROUP BY
    issue.key, issue.summary, issue.status, issue.description,
    issue.incident_impact_description, issue.root_cause_description,
    issue.timeline, issue.created, issue.updated, issue.incident_start
ORDER BY issue.key DESC
" "odl_athena_workgroup" | python3 references/clean-athena-output.py
```

4. Run the Slack messages query (use **lowercase** channel name):

```bash
athena_query "
WITH ranked_messages AS (
  SELECT channel_name, timestamp_utc, text,
    ROW_NUMBER() OVER (PARTITION BY ts ORDER BY batch_retrieval_time_utc DESC) AS rn
  FROM transformed_data.slack_pi
  WHERE channel_name = 'pi-12345'
)
SELECT channel_name, timestamp_utc, text
FROM ranked_messages
WHERE rn = 1
GROUP BY channel_name, timestamp_utc, text
" "odl_athena_workgroup" | python3 references/clean-athena-output.py
```

5. Merge the results into a unified timeline using the parser script.

   Save the cleaned Athena output from steps 3 and 4 to temporary files, then pass them directly to the parser:

   ```bash
   # Save cleaned query results (re-run queries or save output from steps 3-4)
   athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py > /tmp/pi-jira.json
   athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py > /tmp/pi-slack.json

   # Generate merged timeline directly from Athena JSON files
   python3 references/timeline-parser.py --jira-athena /tmp/pi-jira.json --slack-athena /tmp/pi-slack.json --local-tz
   ```

   The `--jira-athena` and `--slack-athena` flags read the Athena JSON format directly — no manual field extraction needed. The parser extracts the `timeline` and `created` fields from the Jira results, and the `timestamp_utc` and `text` columns from the Slack results automatically.

   The `--local-tz` flag auto-detects the user's machine timezone and displays all timestamps in their local time. Alternatively, use `--tz Europe/London` (or any IANA timezone) to specify explicitly.

   The parser handles:
   - Timezone detection from `TIMEZONE: [CEST]` directives in Jira text
   - Conversion of ~30 timezone abbreviations to IANA zones
   - Day rollover detection (when HH:MM goes backwards)
   - Merging Jira + Slack events into a single chronologically sorted timeline
   - Output format: `[ISO timestamp] | Source: Jira/Slack | Event: ...`

   If the parser fails or `python3` is unavailable, fall back to manually parsing timestamps as described below:
   - Parse the Jira `timeline` field (free-text with timestamps, often in format `HH:MM - Event description`)
   - Combine with Slack messages (each has `timestamp_utc` and `text`)
   - Sort all events chronologically by timestamp
   - Note the source of each event (Jira or Slack)

6. Present the timeline:
   - **Header**: Issue key, summary, status, and Jira link
   - **Timeline**: Chronological list with timestamps and source indicators
   - **Impact**: From `incident_impact_description`
   - **Root cause**: From `root_cause_description`
   - **Current status**: Jira status and last updated date

### pi catchup \<channel\>

Summarise recent discussion and action items from a PI channel.

**Trigger:** `pi catchup pi-12345`

**Workflow:**

1. Extract the channel name from the command (e.g. `pi-12345`)
2. Convert to issue key: `PI-12345`
3. Fetch Slack messages and save cleaned output:
   ```bash
   athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py > /tmp/pi-slack.json
   ```
4. Fetch Jira context and save cleaned output:
   ```bash
   athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py > /tmp/pi-jira.json
   ```
5. Run the timeline parser directly on the saved files:
   ```bash
   python3 references/timeline-parser.py --jira-athena /tmp/pi-jira.json --slack-athena /tmp/pi-slack.json --local-tz
   ```
6. Synthesise a catchup summary from both data sources. Structure the output as:
   - **Summary**: Brief overview of the incident and current state (from Jira summary + status)
   - **Key themes**: Main topics discussed in the Slack channel
   - **Action items**: Concrete actions mentioned or assigned in chat
   - **Open questions**: Unresolved questions from the discussion
   - **Next steps**: What needs to happen next based on the conversation
   - **Current status**: Jira status and latest update timestamp

### pi post-mortem \<channel\>

Generate a post-mortem document pre-filled with incident data from Jira and Slack.

**Trigger:** `pi post-mortem pi-12345`

**Workflow:**

1. Extract the channel name from the command (e.g. `pi-12345`)
2. Convert to issue key: `PI-12345`
3. Fetch Jira data and save cleaned output:
   ```bash
   athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py > /tmp/pi-jira.json
   ```
4. Fetch Slack messages and save cleaned output:
   ```bash
   athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py > /tmp/pi-slack.json
   ```
5. Run the timeline parser directly on the saved files:
   ```bash
   python3 references/timeline-parser.py --jira-athena /tmp/pi-jira.json --slack-athena /tmp/pi-slack.json --local-tz
   ```
6. Read the post-mortem template from [references/post-mortem-template.md](references/post-mortem-template.md)
7. Pre-fill the template with data from the queries:
   - **Summary of root cause**: From Jira `root_cause_description` (keep the placeholder prompts if the field is empty)
   - **Impact**: From Jira `incident_impact_description`
   - **Timeline in "What happened during the incident"**: Replace the `00:00 Something happened` placeholder with the actual merged timeline from step 5. **Each event MUST be a markdown list item** so it renders as separate lines in previews and Google Docs:
     ```
     - 08:33 PI channel created, topic set
     - 08:35 Infrastructure thread shared
     - 08:39 Team investigating, no order loss
     ```
     Use the display timezone timestamps (not raw ISO 8601). One list item per event.
   - Leave all *italicised prompts*, **Q&A sections**, and **#ACTION** placeholders intact — these are facilitator guides for the meeting
   - Leave the "What went well?" section, actions table, and Part 2 reminders unchanged
8. Write the filled template to `post-mortem-<CHANNEL>.md` in the current working directory (e.g. `post-mortem-pi-12345.md`)
9. Tell the user the file has been created and remind them to:
   - Review and edit the document before the post-mortem meeting
   - Link it to the Jira PI ticket after the meeting

### pi prodmeet

Generate a structured briefing for the Daily Production Meeting host. Automatically adjusts the lookback window and focus areas based on the day of the week, following the Prod Meet Guide.

**Trigger:** `pi prodmeet` (no channel argument needed)

The user may optionally specify a time window override: `pi prodmeet 96h` (for post-Bank-Holiday). If not provided, the window is determined by the day of the week.

**Workflow:**

1. **Determine the time window** based on the current day of week:

   | Day | Window | Reason |
   |-----|--------|--------|
   | Monday | **72 hours** | Covers Friday, Saturday, Sunday |
   | Tuesday–Friday | **24 hours** | Previous working day only |
   | User override (e.g. `96h`) | **96 hours** | Post-Bank-Holiday or custom |

   The formatter script handles day-of-week detection and window selection automatically. You only need to pass `--hours N` if the user specifies an override (e.g. `pi prodmeet 96h`).

   Display the detected window to the user: e.g. "**Monday — using 72-hour window**"

2. **Source the Athena helpers and run the All Open PIs query**:

   ```bash
   source scripts/athena_query.sh

   athena_query "
   SELECT
       issue.key,
       issue.summary,
       issue.status,
       issue.priority,
       array_join(array_agg(DISTINCT issue.owners), ', ') AS owners,
       issue.labels,
       CONCAT('https://justeattakeaway.atlassian.net/browse/', issue.key) AS issue_url,
       issue.incident_start,
       issue.created,
       issue.updated,
       date_diff('day', from_iso8601_timestamp(issue.created), current_timestamp) AS age_days,
       date_diff('hour', from_iso8601_timestamp(issue.created), current_timestamp) AS age_hours,
       date_diff('day', from_iso8601_timestamp(issue.updated), current_timestamp) AS days_since_update
   FROM \"transformed_data\".\"jira_pi\" issue
   WHERE issue.status NOT IN ('Closed', 'Risk Accepted', 'Mitigated', 'Cancelled')
       AND issue.updated = (SELECT MAX(updated) FROM transformed_data.jira_pi WHERE key = issue.key)
   GROUP BY
       issue.key, issue.summary, issue.status, issue.priority,
       issue.labels, issue.incident_start, issue.created, issue.updated
   ORDER BY issue.created DESC
   " "odl_athena_workgroup"
   ```

3. **Pipe the results through the formatter script** [references/prodmeet-formatter.py](references/prodmeet-formatter.py) to generate the briefing:

   ```bash
   # If user specified an hours override (e.g. "pi prodmeet 96h"):
   athena_query "..." "odl_athena_workgroup" 2>/dev/null | python3 references/prodmeet-formatter.py --hours 96

   # Otherwise let the formatter auto-detect from day of week:
   athena_query "..." "odl_athena_workgroup" 2>/dev/null | python3 references/prodmeet-formatter.py
   ```

   The formatter handles all categorisation, day-of-week logic, table rendering, weekly focus sections, and empty-section messages automatically. It reads the Athena JSON from stdin and writes the complete markdown briefing to both stdout and a local file.

   By default the formatter writes to `yyyy-mm-dd-prodmeet-notes.md` (today's date), overwriting any existing file for that day.

   Available flags:
   - `--hours N` — override the lookback window (e.g. `96` for post-Bank-Holiday)
   - `--day N` — override day of week (1=Monday ... 7=Sunday)
   - `--output FILE` — override the output filename (default: `yyyy-mm-dd-prodmeet-notes.md`)
   - `--no-output` — disable file output (print to stdout only)

4. **Present the formatter output** directly to the user, adding inline host notes as you go. Do not dump the entire briefing first and then add notes at the end. Instead, after each section's table, add host notes as a markdown list — one bullet per PI — highlighting anything the host should raise (missing details, no owner, no timeline, repeat issue, unclear impact, stale status). Only add notes where there is something worth calling out — skip PIs that look well-managed.

   Format each note as:
   ```
   - 🎙️ **PI-12345** — No owner assigned, summary is vague — ask for clarification
   - 🎙️ **PI-67890** — Created 3 days ago but still no timeline entry
   ```

   This applies to every section that lists individual PIs (New PIs, Tracked PIs, No Owner, In-Progress, and weekly focus sections). The Open PI Summary (counts table) does not need notes.

5. **Write the briefing with inline notes to the markdown file.** The formatter already writes to `yyyy-mm-dd-prodmeet-notes.md` by default. After adding your host notes, overwrite that file with the complete output including all `- 🎙️` host notes under each section, so the exported document matches what the user sees in chat.

6. **Tell the user the file has been created** (e.g. `2026-03-06-prodmeet-notes.md`) and remind them that the markdown file can be imported directly into Google Docs via **File → Open → Upload**.

**Output structure** (produced by the formatter, then annotated by you with 🎙️ host notes):

```
# 🏭 Prod Meet Briefing — <Day>, <Date>
**Window:** <HOURS>h | **Total open PIs:** <count>

---

## 📋 Daily Focus

### 1. New PIs (last <HOURS> hrs)
<Table of PIs where age_hours <= HOURS, columns: Key (linked), Summary, Priority, Status, Owner>
<If none: "✅ No new PIs in the last <HOURS> hours">

- 🎙️ **PI-XXXXX** — <host note for this PI>
- 🎙️ **PI-YYYYY** — <host note for this PI>

### 2. Tracked PIs
<PIs where labels array contains exact label 'Track'>
<If none: "✅ No tracked PIs">

- 🎙️ **PI-XXXXX** — <host note>

### 3. PIs with No Owner
<PIs where owners is NULL, empty, or 'unknown'>
<If none: "✅ All PIs have an owner">

- 🎙️ **PI-XXXXX** — <host note>

### 4. In-Progress PIs (outside <HOURS>h window)
<PIs where status = 'In Progress' AND age_hours > HOURS>
<Note: "Review these — In Progress means impact is ongoing. Move to Investigating if impact has stopped.">
<If none: "✅ No In-Progress PIs outside the window">

- 🎙️ **PI-XXXXX** — <host note>

### 5. Open PI Summary
<Count of open PIs grouped by status, as a small table>

---

## 📅 Weekly Focus — <Day-specific title>
<Only included on the appropriate day, see below>

- 🎙️ **PI-XXXXX** — <host note>
```

**Weekly Focus sections by day** (handled by the formatter):

- **Monday** — No weekly focus sections (daily focus only)
- **Tuesday** — Pending Risk Accept + PIs Not Updated in 7+ Days
- **Wednesday** — Open Critical & Major PIs
- **Thursday** — SRM Report Reminder
- **Friday** — PIs Over 50 Days Old

**Formatting rules:**
- PIs with status "Non-Issue" only appear in the "New PIs" section (so the host can verify they were correctly triaged). They are excluded from all other daily and weekly focus sections.
- The formatter already handles Jira links, table columns, and section structure
- Keep summaries concise — the host should be able to scan the briefing in 5 minutes
- After each section's table, add inline host notes as a markdown bullet list (`- 🎙️ **PI-XXXXX** — note`) — one bullet per PI so each renders on its own line
- The briefing ends with: "---\n*Briefing generated from ODL data. Check the [Prod Meet Dashboard](https://justeattakeaway.atlassian.net/) for real-time updates.*"

### Tips

- **SQL escaping**: Always escape single quotes in user input by doubling them (`'` → `''`) before inserting into SQL
- The Jira `timeline` field is free-text written by incident responders — it may contain timestamps in various formats (HH:MM, ISO 8601, relative times)
- The Slack `timestamp_utc` field is in ISO 8601 format and already in UTC
- For very active channels, there may be hundreds of Slack messages — focus on extracting themes and action items rather than listing every message
- Always include the Jira link (`https://justeattakeaway.atlassian.net/browse/PI-XXXXX`) in your output

## Reference

See [references/athena-queries.md](references/athena-queries.md) for all available SQL queries and table schemas.
See [references/clean-athena-output.py](references/clean-athena-output.py) for the data cleaning script (strips Slack mrkdwn, HTML entities, normalises whitespace).
See [references/timeline-parser.py](references/timeline-parser.py) for the timeline parsing and merging script.
See [references/prodmeet-formatter.py](references/prodmeet-formatter.py) for the prod meet briefing formatter.


