---
name: opensar-nocodb
description: Browse and manage database records via NocoDB MCP servers. Covers two bases -- OpenSAR (default, cloud_sample + opensar_enhanced) and Tax (opt-in, only when user mentions "tax"). Use when querying, viewing, inserting, updating, or deleting database records, checking device status, managing search parties, verifying wayline data, investigating database issues, or working with tax records.
---

# NocoDB Database Access

Two NocoDB bases are available. OpenSAR is the default; Tax is only used when explicitly requested.

## Multi-Base Routing

| Base | MCP Server Name | When to Use |
|------|----------------|-------------|
| OpenSAR | `NocoDB Base - opensar` | **Default.** Use for ALL queries unless the user explicitly mentions "tax". |
| Tax | `NocoDB Base - Tax` | **Opt-in only.** Use ONLY when the user says "tax", "tax base", "tax table", or similar. |

Routing rules:
1. If the user does not mention "tax", always use `NocoDB Base - opensar` tools.
2. If the user explicitly mentions "tax", use `NocoDB Base - Tax` tools.
3. If ambiguous, ask the user which base they mean before querying.

## MCP Servers

### OpenSAR (default)

- **Server name**: `NocoDB Base - opensar`
- **Connection**: Configured in `~/.cursor/mcp.json` via `mcp-remote`
- **Auth**: Token-based (managed by MCP config, no manual auth needed)

### Tax (opt-in)

- **Server name**: `NocoDB Base - Tax`
- **Connection**: Configured in `~/.cursor/mcp.json` via `mcp-remote`
- **Auth**: Token-based (managed by MCP config, no manual auth needed)
- **Usage**: Only query this base when the user explicitly requests tax data. Use `getTablesList`, `getTableSchema`, `queryRecords`, etc. with the Tax server tools (prefixed `NocoDB Base - Tax`).

## Quick Start

1. Determine which base to use (see routing rules above)
2. Use `getTablesList` to discover available tables on the target base
3. Use `getTableSchema` to inspect columns before querying
4. Use `queryRecords`, `createRecords`, `updateRecords`, `deleteRecords` for CRUD operations

## Databases Overview

### cloud_sample (DJI Cloud API)

The standard DJI Cloud API database with OpenSAR extensions. Core device/flight management.

| Table | Purpose |
|-------|---------|
| `manage_device` | Registered devices (drones, docks, remote controllers) |
| `manage_device_dictionary` | Device product enum lookup (domain, type, sub_type, name) |
| `manage_device_payload` | Camera/sensor payloads attached to devices |
| `manage_device_firmware` | Firmware package records |
| `manage_device_hms` | Device health management system messages |
| `manage_device_logs` | Device log upload records |
| `manage_user` | System user accounts (web + pilot) |
| `manage_workspace` | Workspace/organization records |
| `wayline_file` | Uploaded wayline route files |
| `wayline_job` | Wayline mission execution records |
| `media_file` | Media files with OpenSAR lat/lng extensions |
| `map_group` | Map layer groups (default, shared, custom) |
| `map_group_element` | Map annotations (points, lines, polygons) |
| `map_element_coordinate` | Coordinates for map elements |
| `logs_file` | Uploaded device log files |
| `logs_file_index` | Boot index for log files |
| `manage_firmware_model` | Firmware-to-device model mapping |
| `device_flight_area` | Device flight area sync status |
| `flight_area_file` | Flight area definition files |
| `flight_area_property` | Flight area properties (geofence/NFZ) |

### opensar_enhanced (SAR Operations)

OpenSAR-specific tables for search and rescue operations management.

| Table | Purpose |
|-------|---------|
| `search_party` | SAR operations (status, priority, incident details) |
| `search_party_element` | Master assignment table for ALL party resources |
| `search_party_pilot` | Drone pilots assigned to operations |
| `search_party_ground_team` | Ground team members in the field |
| `search_party_operations_master` | Command staff and coordinators |
| `search_party_activity_log` | Audit trail for all party actions |
| `element_designation_types` | Lookup table for SAR element types (zones, points, personnel) |
| `annotation_requests` | Mobile frontend annotation requests |
| `mobile_devices` | Registered mobile devices for auth |

## Key Relationships

- `search_party.workspace_id` links to `cloud_sample.manage_workspace`
- `search_party_pilot.user_id` links to `cloud_sample.manage_user`
- `search_party_element.element_id` can reference `cloud_sample.map_group_element`
- `search_party_element.designation_type_id` links to `element_designation_types.id`
- `media_file.job_id` links to `wayline_job.job_id`
- `manage_device.device_type/sub_type/domain` maps to `manage_device_dictionary`

## Device Domain Reference

| Domain | Meaning |
|--------|---------|
| 0 | Drone |
| 1 | Payload (camera/sensor) |
| 2 | Remote Controller |
| 3 | Dock |
| 4 | Person/Ground Team (OpenSAR extension) |

## Common Queries

**Find all devices in a workspace:**
Look up `manage_device` filtered by `workspace_id`

**Check search party status:**
Look up `search_party` filtered by `status` (planning, active, suspended, completed, closed, archived)

**Get personnel for a party:**
Query `search_party_element` filtered by `party_id` and `element_type` (PILOT, GROUND_TEAM, OPERATIONS_MASTER)

**View wayline jobs:**
Query `wayline_job` filtered by `status` (1=pending, 2=in_progress, 3=success, 4=cancel, 5=failed)

**Check device dictionary:**
Query `manage_device_dictionary` to resolve device type/sub_type/domain to human-readable names

## Tax Base (opt-in)

The Tax base is a separate NocoDB instance for personal/business tax record management. It is completely independent from the OpenSAR databases.

- **Server name**: `NocoDB Base - Tax`
- **When to use**: Only when the user explicitly mentions "tax"
- **Table discovery**: Run `getTablesList` against the Tax server to see available tables. Run `getTableSchema` to inspect columns before querying.
- **Duplicate detection**: When checking for duplicates, query all records and compare key fields (amounts, dates, descriptions, vendor names, etc.) to identify rows with identical or near-identical values.

## Additional Resources

- For full column-level schema details, see [reference.md](reference.md)
