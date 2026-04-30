# pdconfig — PagerDuty Configuration as Code

The **pdconfig** repo manages JET's PagerDuty configuration as Terraform code.

**Repo**: `git@github.je-labs.com:PlatformObservability/pdconfig.git`
**Clone location (if needed)**: `~/Projects/pdconfig`

Owned by Platform Observability. 26+ teams onboarded as of early 2026.

---

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [How to Make Changes](#how-to-make-changes)
3. [Team Directory Layout](#team-directory-layout)
4. [Naming Conventions](#naming-conventions)
5. [Service Defaults](#service-defaults)
6. [User Roles](#user-roles)
7. [Support Hours Pattern](#support-hours-pattern)
8. [Retrigger Workflows](#retrigger-workflows)
9. [Onboarding a New Team](#onboarding-a-new-team)
10. [Important Caveats](#important-caveats)

---

## Repository Structure

```
pdconfig/
├── modules/               # Reusable Terraform modules (team, service, user, etc.)
├── team/                  # One subdirectory per onboarded team
│   ├── example-team/      # Canonical template — copy this to onboard a new team
│   ├── consolidations-jefb/
│   ├── platform-observability/
│   └── ...                # 26+ teams total
├── .scripts/
│   └── retrigger-alerts.py   # Script used by retrigger cron workflows
└── .github/
    └── workflows/         # GitHub Actions: plan, apply, and 4 retrigger cron workflows
```

Each team directory has **isolated S3 Terraform state** — changes in one team's directory cannot affect another team.

---

## How to Make Changes

1. **Clone the repo** (if not already): `git clone git@github.je-labs.com:PlatformObservability/pdconfig.git ~/Projects/pdconfig`
2. **Create a feature branch**: `git checkout -b my-team/add-new-service`
3. **Edit the team files** (see [Team Directory Layout](#team-directory-layout) below)
4. **Open a PR** — a Terraform plan runs automatically as a CI check
5. **Review the plan output** — verify only expected resources change
6. **Merge to main** — Terraform apply runs automatically from main only

**Never apply directly from a feature branch.** Never make changes in the PagerDuty UI for resources managed by Terraform — they will be overwritten on the next apply.

There is **no dev/staging PagerDuty environment** — all Terraform changes go directly to production. Be careful.

---

## Team Directory Layout

Each team directory under `team/` contains:

```
team/my-team/
├── initialize.tf   # Terraform backend config (S3 state key) — change this when copying example-team
├── variables.tf    # locals{} block — schedule names, user emails, policy names, etc.
├── data.tf         # data sources — look up existing PD users/schedules by name/email
└── main.tf         # module calls — creates schedules, escalation policies, services
```

**Where to edit what:**
- `variables.tf` — change schedule names, team membership, escalation timeouts, service names
- `data.tf` — add data sources when you need to reference existing PD objects (e.g., a user that already exists)
- `main.tf` — add/remove/modify module calls to create PD resources

---

## Naming Conventions

| Resource | Convention | Example |
|----------|-----------|---------|
| Schedule | `Team Name - Schedule` | `Checkout - On Call` |
| Out-of-hours schedule | `team-OutofHours` | `checkout-OutofHours` |
| Shadow schedule | `Team Name - shadow` | `Checkout - shadow` |
| Escalation policy | `Team Name - Escalation Policy` | `Checkout - Escalation Policy` |
| Services | Prefixed by team or product area | `checkout-api`, `payments-processor` |

---

## Service Defaults

When a service is created via the standard module, these are the defaults:

| Setting | Default Value | Notes |
|---------|--------------|-------|
| `alert_creation` | `create_alerts_and_incidents` | Both alerts and incidents are created |
| `acknowledgement_timeout` | `1800` (30 min) | Auto-unacknowledge after 30 min |
| `urgency_type` | `severity_based` | Urgency derived from alert severity |
| Integration | Events API v2 | Created automatically |

---

## User Roles

| Role field | Value | When to use |
|-----------|-------|-------------|
| `user_role` | `limited_user` | Standard — use for all normal team members |
| `user_role` | `admin` | Platform Observability and specific team leads only |
| `team_role` | `manager` | Team lead / manager |
| `team_role` | `responder` | Standard on-call engineers |

Do not set `user_role = "admin"` unless specifically required.

---

## Support Hours Pattern

For non-24h teams, use `use_support_hours = true` in the service module. This works in conjunction with DevNull on the schedule:

- Steps urgency **down to `low`** outside business hours — low-urgency incidents do not escalate beyond the current on-call (DevNull), so the team and team lead are not paged overnight
- Steps urgency **back up** at the start of business hours
- DevNull never acknowledges, so incidents remain open and are re-triggered by the cron workflow next morning (see Retrigger Workflows)

Without `use_support_hours`, DevNull-held incidents would escalate up the escalation policy overnight, paging the whole team and team lead unnecessarily.

---

## Retrigger Workflows

Non-24h teams have overnight incidents that nobody is paged for (DevNull absorbs them). To ensure they're picked up the next morning, four GitHub Actions cron workflows in `.github/workflows/` re-trigger these incidents at business day start.

**The workflows run at UTC times corresponding to 08:00 local business time for different timezones.**

> **DST caveat**: The cron schedules are in UTC. When DST changes (March/October), the UTC offset shifts — someone must manually update the cron expressions. Check the workflows after DST changes.

### Adding a service to retrigger

1. Find the relevant retrigger workflow in `.github/workflows/` (match by timezone/country)
2. Add the PagerDuty service name to the `matrix` array in the workflow
3. Open a PR — no Terraform changes needed, just the workflow YAML

### Creating a new retrigger workflow

If no existing workflow covers the right timezone, create a new one by copying an existing retrigger workflow and updating:
- The cron schedule (convert target local time to UTC)
- The service matrix
- The job name

The workflow calls `.scripts/retrigger-alerts.py` with the service name as an argument.

---

## Onboarding a New Team

1. **Copy the example-team directory**:
   ```bash
   cp -r team/example-team team/my-new-team
   ```

2. **Update `initialize.tf`** — change the S3 state key to something unique for this team:
   ```hcl
   key = "pdconfig/team/my-new-team/terraform.tfstate"
   ```

3. **Update `variables.tf`** — set the team's schedule names, user emails, escalation timeouts

4. **Update `main.tf`** — configure schedules, escalation policy, and services using the modules

5. **Open a PR**, verify the plan, merge — apply runs automatically

---

## Important Caveats

- **No staging environment** — all changes go directly to production PagerDuty
- **Terraform is the source of truth** — manual UI changes will be overwritten
- **State is isolated per team** — you cannot accidentally break another team's config
- **The "Emergency - Tech Escalations" schedule** is a global last-resort escalation target referenced by some teams as the ultimate backstop. It is managed outside pdconfig (not in this repo).
