# Future Ideas

Potential enhancements for the jet-bq skill. These are documented here for community feedback before investing implementation effort.

## Table Profiling Script

A Python or Bash script that takes a table reference and produces a comprehensive profile:

- Row count and table size
- Column-level stats: nulls, cardinality, min/max, top N values
- Partition and clustering info
- Sample rows

Example invocation:
```bash
python3 scripts/profile_table.py project.dataset.table
```

Expected output: Markdown-formatted profile report suitable for pasting into documents or Slack.

### Why this would be useful
- Currently requires multiple `bq` commands and manual SQL to profile a table
- A single command would standardize the profiling process
- Output could be used as context for query writing

## Report Generator Script

A script that takes a SQL query and produces formatted output:

- Markdown tables
- HTML reports with basic styling
- CSV export with proper headers

Example invocation:
```bash
python3 scripts/report.py --format=html --query="SELECT ..." --output=report.html
```

### Why this would be useful
- Standard `bq` output is not presentation-ready
- Teams frequently need to share query results in readable formats
- Could include basic charts using a lightweight library

## Schema Diff Tool

A script that compares two table schemas and reports differences:

```bash
python3 scripts/schema_diff.py project.dataset.table_v1 project.dataset.table_v2
```

### Why this would be useful
- Useful during migrations and schema evolution
- Can catch breaking changes before they reach production
- Could integrate with CI/CD pipelines

## Interactive Dashboard Generator

A script that takes a set of queries and produces a self-contained HTML dashboard:

- Multiple panels with tables and charts
- Date range selector
- Auto-refresh capability

### Why this would be useful
- Quick alternative to Looker/Data Studio for ad-hoc dashboards
- Self-contained HTML can be shared without tool access
- Useful for incident analysis or one-off investigations

## Dataset Documentation Generator

Auto-generate documentation for an entire dataset:

```bash
python3 scripts/document_dataset.py project.dataset
```

Output: Markdown file with all table schemas, row counts, descriptions, and relationships.

### Why this would be useful
- Datasets often lack documentation
- Auto-generated docs can serve as a starting point
- Could be run periodically and committed to a repo

---

If you find any of these ideas useful or have suggestions, raise it with the team.
