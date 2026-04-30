# Athena Queries Reference

SQL queries for the ODL data lake. All queries use Trino (Presto) syntax against the `transformed_db` database in the `AwsDataCatalog`.

**Important:** Always escape single quotes in user input by doubling them (`'` → `''`) before inserting into SQL.

---

## Tables

### transformed_data.jira_pi

Production issue (PI) tickets from Jira.

| Column | Type | Description |
|--------|------|-------------|
| `key` | string | Jira issue key (e.g. `PI-12345`) — **uppercase** |
| `summary` | string | Issue title |
| `status` | string | Current Jira status |
| `description` | string | Full issue description |
| `incident_impact_description` | string | Impact details |
| `root_cause_description` | string | Root cause analysis |
| `timeline` | string | Free-text timeline written by incident responders |
| `incident_start` | string | When the incident began (ISO 8601) |
| `created` | string | Jira created timestamp (ISO 8601) |
| `updated` | string | Jira last updated timestamp (ISO 8601) |
| `owners` | string | Owning Jira team |
| `priority` | string | Severity level (e.g. `Critical`, `Major`, `Minor`) |
| `labels` | array(string) | Labels applied to the issue (e.g. `Track`, `onhold`, `longtail`, `release_warranty`) |
| `component_names` | array(string) | Associated component names |
| `extract_timestamp` | string | When this data was last extracted |

### transformed_data.slack_pi

Slack messages from PI channels, ingested into the data lake.

| Column | Type | Description |
|--------|------|-------------|
| `channel_name` | string | Slack channel name (e.g. `pi-12345`) — **lowercase** |
| `timestamp_utc` | string | Message timestamp in UTC (ISO 8601) |
| `text` | string | Message content |
| `ts` | string | Slack message ID (used for deduplication) |
| `batch_retrieval_time_utc` | string | When this message batch was retrieved |

---

## PI Summary by Issue Key

Get Jira PI details for a specific issue.

```sql
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
FROM
    "transformed_data"."jira_pi" issue
WHERE
    key = '{ISSUE_KEY}'
    AND issue.updated = (SELECT MAX(updated) FROM transformed_data.jira_pi WHERE key = issue.key)
GROUP BY
    issue.key, issue.summary, issue.status, issue.description,
    issue.incident_impact_description, issue.root_cause_description,
    issue.timeline, issue.created, issue.updated, issue.incident_start
ORDER BY issue.key DESC
```

**Placeholder:** `{ISSUE_KEY}` — uppercase Jira key, e.g. `PI-12345`

---

## Slack Messages by Channel (Structured)

Get individual Slack messages for a PI channel, deduplicated.

```sql
WITH ranked_messages AS (
  SELECT channel_name, timestamp_utc, "text",
    ROW_NUMBER() OVER (PARTITION BY ts ORDER BY batch_retrieval_time_utc DESC) AS rn
  FROM "transformed_data"."slack_pi"
  WHERE channel_name = '{CHANNEL_NAME}'
)
SELECT channel_name, timestamp_utc, "text"
FROM ranked_messages
WHERE rn = 1
GROUP BY channel_name, timestamp_utc, "text"
```

**Placeholder:** `{CHANNEL_NAME}` — lowercase channel name, e.g. `pi-12345`

---

## Slack Messages by Channel (Aggregated)

Get all Slack messages as a single aggregated array.

```sql
WITH ranked_messages AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY ts ORDER BY batch_retrieval_time_utc DESC) AS rn
  FROM "transformed_data"."slack_pi"
  WHERE channel_name = '{CHANNEL_NAME}'
)
SELECT
    channel_name,
    array_agg(concat(timestamp_utc, ': ', "text", chr(10)) ORDER BY timestamp_utc) AS slack_channel_messages
FROM ranked_messages
WHERE rn = 1
GROUP BY channel_name
```

**Placeholder:** `{CHANNEL_NAME}` — lowercase channel name, e.g. `pi-12345`

---

## PI Records by Date Range

Get PI records created or updated within a date range.

```sql
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
FROM
    "transformed_data"."jira_pi" issue
WHERE
    from_iso8601_timestamp(issue.created) BETWEEN
        from_iso8601_timestamp('{SINCE}') AND from_iso8601_timestamp('{UNTIL}')
    AND issue.updated = (SELECT MAX(updated) FROM transformed_data.jira_pi WHERE key = issue.key)
GROUP BY
    issue.key, issue.summary, issue.status, issue.description,
    issue.incident_impact_description, issue.root_cause_description,
    issue.timeline, issue.created, issue.updated, issue.incident_start
ORDER BY issue.key DESC
```

**Placeholders:**
- `{SINCE}` — ISO 8601 start date, e.g. `2025-08-01T00:00:00Z`
- `{UNTIL}` — ISO 8601 end date, e.g. `2025-08-31T23:59:59Z`

To filter by `updated` instead, replace `issue.created` with `issue.updated` in the WHERE clause.

---

## PI Records by Team

Get PI records for a specific team.

```sql
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
FROM
    "transformed_data"."jira_pi" issue
JOIN "transformed_data"."platformmetadata_teams" pmd_teams
    ON pmd_teams.jira_team_owner = issue.owners
WHERE
    from_iso8601_timestamp(issue.created) >= current_timestamp - interval '7' day
    AND pmd_teams.id = '{TEAM_ID}'
    AND issue.updated = (SELECT MAX(updated) FROM transformed_data.jira_pi WHERE key = issue.key)
GROUP BY
    issue.key, issue.summary, issue.status, issue.description,
    issue.incident_impact_description, issue.root_cause_description,
    issue.timeline, issue.created, issue.updated, issue.incident_start
ORDER BY issue.key DESC
```

**Placeholder:** `{TEAM_ID}` — Platform metadata team ID

---

## Max Jira Extract Date

Check when the PI data was last refreshed.

```sql
SELECT MAX(extract_timestamp) FROM transformed_data.jira_pi
```

---

## All Open PIs (Prod Meet Briefing)

Comprehensive query returning all non-closed PIs with computed age and staleness. Used by `pi prodmeet` to generate the host briefing in a single query.

```sql
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
FROM "transformed_data"."jira_pi" issue
WHERE issue.status NOT IN ('Closed', 'Risk Accepted', 'Mitigated', 'Cancelled')
    AND issue.updated = (SELECT MAX(updated) FROM transformed_data.jira_pi WHERE key = issue.key)
GROUP BY
    issue.key, issue.summary, issue.status, issue.priority,
    issue.labels, issue.incident_start, issue.created, issue.updated
ORDER BY issue.created DESC
```

The agent categorises results client-side using these filters:

| Section | Filter |
|---------|--------|
| New PIs | `age_hours <= HOURS` (window depends on day of week) |
| Tracked PIs | `labels` contains `'Track'` |
| No Owner | `owners IS NULL` or empty |
| In-Progress (outside window) | `status = 'In Progress' AND age_hours > HOURS` |
| Pending Risk Accept | `status = 'Pending Risk Accept'` |
| Not Updated 7+ Days | `days_since_update >= 7` |
| Critical & Major | `priority IN ('Critical', 'Major')` |
| Over 50 Days Old | `age_days >= 50` |
