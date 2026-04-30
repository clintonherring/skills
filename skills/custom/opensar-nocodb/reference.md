# OpenSAR Database Schema Reference

Full column-level schema details for both databases.

---

## cloud_sample Database

### manage_device
Device registration and status tracking.

| Column | Type | Notes |
|--------|------|-------|
| device_sn | varchar(32) | PK (unique), drone/dock/RC serial |
| device_name | varchar(64) | Model name from dictionary |
| user_id | varchar(64) | Account that bound the device |
| nickname | varchar(64) | Custom display name |
| workspace_id | varchar(64) | Workspace FK |
| device_type | int | Maps to dictionary |
| sub_type | int | Maps to dictionary |
| domain | int | 0=drone, 1=payload, 2=RC, 3=dock |
| firmware_version | varchar(32) | Current firmware |
| compatible_status | tinyint(1) | 1=consistent, 0=inconsistent |
| child_sn | varchar(32) | Device controlled by gateway |
| bound_status | tinyint(1) | 1=bound, 0=not bound |
| login_time | bigint | Last device login timestamp |
| create_time / update_time | bigint | Timestamps |

### manage_device_dictionary
Product type enum lookup. Pre-seeded with DJI models + OpenSAR extensions.

| Column | Type | Notes |
|--------|------|-------|
| domain | int | 0=drone, 1=payload, 2=RC, 3=dock, 4=person |
| device_type | int | Product type code |
| sub_type | int | Product sub-type code |
| device_name | varchar(32) | Human-readable model name |
| device_desc | varchar(100) | Description/remark |

Key entries: Matrice 300 RTK, M30/M30T, Mavic 3E/3T/3M, M350 RTK, M3D/M3TD, DJI Dock/Dock2, Person/Ground Team (domain=4).

### manage_user
System accounts for web and pilot access.

| Column | Type | Notes |
|--------|------|-------|
| user_id | varchar(64) | UUID |
| username | varchar(32) | Account name |
| password | varchar(32) | Account password |
| workspace_id | varchar(64) | Workspace FK |
| user_type | smallint | 1=web, 2=pilot |
| mqtt_username / mqtt_password | varchar(32) | EMQX credentials |

### manage_workspace
Organization/workspace records.

| Column | Type | Notes |
|--------|------|-------|
| workspace_id | varchar(64) | UUID |
| workspace_name | varchar(64) | Display name |
| platform_name | varchar(64) | Platform identifier |
| bind_code | varchar(32) | Dock binding code (unique) |

### wayline_file
Uploaded wayline route files.

| Column | Type | Notes |
|--------|------|-------|
| wayline_id | varchar(64) | UUID |
| name | varchar(64) | Wayline name |
| drone_model_key | varchar(32) | Format: domain-type-sub_type |
| payload_model_keys | varchar(200) | Payload product enum |
| workspace_id | varchar(64) | Workspace FK |
| sign | varchar(64) | MD5 hash |
| template_types | varchar(32) | 0=waypoint |
| object_key | varchar(200) | MinIO/S3 object key |
| user_name | varchar(64) | Creator name |
| favorited | tinyint(1) | Favorite flag |

### wayline_job
Wayline mission execution records.

| Column | Type | Notes |
|--------|------|-------|
| job_id | varchar(45) | UUID |
| name | varchar(64) | Job name |
| file_id | varchar(45) | FK to wayline_file |
| dock_sn | varchar(45) | Executing dock SN |
| workspace_id | varchar(45) | Workspace FK |
| status | int | 1=pending, 2=in_progress, 3=success, 4=cancel, 5=failed |
| task_type | int | Task type code |
| wayline_type | int | Template type |
| execute_time | bigint | Actual start time |
| completed_time | bigint | Actual end time |
| begin_time | bigint | Planned start |
| end_time | bigint | Planned end |
| error_code | int | Error code if failed |
| rth_altitude | int | Return-to-home altitude (20-500m) |
| out_of_control | int | 0=go home, 1=hover, 2=land |
| media_count | int | Number of media files |

### media_file
Media files captured by drones. Includes OpenSAR geolocation extensions.

| Column | Type | Notes |
|--------|------|-------|
| file_id | varchar(64) | UUID |
| file_name | varchar(100) | Original filename |
| file_path | varchar(1000) | File path |
| workspace_id | varchar(64) | Workspace FK |
| object_key | varchar(1000) | MinIO/S3 key |
| drone | varchar(32) | Drone SN |
| payload | varchar(32) | Payload name |
| longitude | decimal(18,14) | **OpenSAR extension** - capture longitude |
| latitude | decimal(17,14) | **OpenSAR extension** - capture latitude |
| job_id | varchar(64) | FK to wayline_job |
| is_original | tinyint(1) | Original image flag |
| sub_file_type | int | 0=normal, 1=panorama |

### map_group
Map layer groups for organizing annotations.

| Column | Type | Notes |
|--------|------|-------|
| group_id | varchar(64) | UUID |
| group_name | varchar(64) | Layer name |
| group_type | int | 0=custom, 1=default, 2=app shared |
| workspace_id | varchar(64) | Workspace FK |
| is_distributed | tinyint(1) | Show on pilot map (1=yes) |
| is_lock | tinyint(1) | Prevent modifications (1=locked) |

### map_group_element
Individual map annotations (points, lines, polygons).

| Column | Type | Notes |
|--------|------|-------|
| element_id | varchar(64) | UUID |
| element_name | varchar(64) | Display name |
| group_id | varchar(64) | FK to map_group |
| element_type | smallint | 0=point, 1=line, 2=polygon |
| username | varchar(64) | Creator |
| color | varchar(32) | Hex color code |
| clamp_to_ground | tinyint(1) | Ground-clamped flag |

### map_element_coordinate
Coordinate data for map elements.

| Column | Type | Notes |
|--------|------|-------|
| element_id | varchar(64) | FK to map_group_element |
| longitude | decimal(18,14) | Longitude |
| latitude | decimal(17,14) | Latitude |
| altitude | decimal(17,14) | Altitude (NULL for points) |

### manage_device_hms
Device health management system messages.

| Column | Type | Notes |
|--------|------|-------|
| hms_id | varchar(45) | UUID |
| sn | varchar(45) | Reporting device SN |
| level | smallint | 0=notice, 1=caution, 2=warning |
| module | tinyint | 0=flight task, 1=device manage, 2=media, 3=hms |
| hms_key | varchar(64) | Message key for lookup |
| message_en | varchar(300) | English message text |

### manage_device_payload
Camera/sensor payloads on devices.

| Column | Type | Notes |
|--------|------|-------|
| payload_sn | varchar(32) | Payload serial (unique) |
| payload_name | varchar(64) | Model name |
| payload_type | smallint | Type from dictionary |
| payload_index | smallint | Mount position |
| device_sn | varchar(32) | Parent device SN |

---

## opensar_enhanced Database

### search_party
Core SAR operation record.

| Column | Type | Notes |
|--------|------|-------|
| party_id | varchar(64) | UUID (unique) |
| party_name | varchar(100) | Operation name |
| workspace_id | varchar(64) | FK to cloud_sample.manage_workspace |
| status | varchar(32) | planning, active, suspended, completed, closed, archived |
| priority | tinyint | 1=Critical, 2=High, 3=Normal, 4=Low |
| valid_from | bigint | Start timestamp (ms) |
| valid_till | bigint | End timestamp (NULL=ongoing) |
| incident_type | varchar(64) | missing person, disaster, etc. |
| incident_location | varchar(200) | General location description |
| command_post_element_id | varchar(64) | FK to map_group_element |
| description | varchar(1000) | Operation details |
| created_by | varchar(64) | Creator user ID |

### element_designation_types
Lookup table for SAR element categories. Pre-seeded with 18 types.

| Column | Type | Notes |
|--------|------|-------|
| type_code | varchar(32) | Machine code (unique): MUSTER_POINT, COMMAND_POST, etc. |
| type_name | varchar(64) | Human name |
| type_category | varchar(32) | OPERATIONAL, SAFETY, SEARCH, LOGISTICS, PERSONNEL |
| geometry_type | varchar(16) | point or polygon |
| default_color | varchar(7) | Hex color |
| display_order | int | UI sort order |
| is_active | tinyint(1) | Active flag |

Categories and codes:
- **OPERATIONAL**: MUSTER_POINT, RENDEZVOUS_POINT, STAGING_AREA, COMMAND_POST
- **SAFETY**: SAFE_ZONE, HAZARD_ZONE, EXCLUSION_ZONE, MEDICAL_POINT, REST_AREA
- **SEARCH**: ACTIVE_ZONE, SEARCH_SEGMENT, POINT_OF_INTEREST, LAST_KNOWN_POSITION
- **LOGISTICS**: LANDING_ZONE, EVACUATION_POINT
- **PERSONNEL**: PILOT, GROUND_TEAM, OPERATIONS_MASTER

### search_party_element
Master assignment table linking resources to parties. Each element can only belong to one party (unique element_id).

| Column | Type | Notes |
|--------|------|-------|
| party_id | varchar(64) | FK to search_party |
| element_id | varchar(255) | Universal ID: user-{id}, team-{id}, anno-{id} (unique) |
| element_type | varchar(50) | PILOT, GROUND_TEAM, MUSTER_POINT, ZONE, etc. |
| designation_type_id | int | FK to element_designation_types |
| priority | tinyint | 1=critical to 4=low |
| status | varchar(32) | active, standby, resting, offline, emergency, planning, archived |
| is_active | tinyint(1) | Currently active flag |
| role | varchar(50) | Role for personnel |
| assigned_teams | text | JSON array of team UUIDs |
| notes | text | Remarks |
| metadata | json | Flexible JSON data |
| activated_time | bigint | Assignment timestamp |
| deactivated_time | bigint | Removal timestamp |

### search_party_pilot
Drone pilots assigned to operations. One pilot per party (unique user_id).

| Column | Type | Notes |
|--------|------|-------|
| party_id | varchar(64) | FK to search_party |
| user_id | varchar(64) | FK to manage_user (unique) |
| device_sn | varchar(32) | Assigned drone/RC SN |
| role | varchar(32) | lead_pilot, pilot, backup_pilot, trainee_pilot |
| status | varchar(32) | active, standby, resting, offline, emergency |
| assigned_zone | varchar(64) | FK to map element |
| certification_level | varchar(32) | Qualification level |

### search_party_ground_team
Ground team members. One member per party (unique user_id).

| Column | Type | Notes |
|--------|------|-------|
| party_id | varchar(64) | FK to search_party |
| user_id | varchar(64) | FK to manage_user (unique) |
| name | varchar(100) | Full name |
| callsign | varchar(32) | Radio callsign |
| role | varchar(32) | team_leader, searcher, medic, k9_handler, technical_specialist, support |
| team_name | varchar(64) | Sub-team designation |
| device_sn | varchar(64) | Tracking device ID |
| status | varchar(32) | in_field, staging, resting, returning, off_duty, emergency |
| last_known_lat/lng | decimal | Last GPS position |
| last_known_time | bigint | Position timestamp |

### search_party_operations_master
Command staff and incident coordinators.

| Column | Type | Notes |
|--------|------|-------|
| party_id | varchar(64) | FK to search_party |
| user_id | varchar(64) | FK to manage_user |
| name | varchar(100) | Full name |
| role | varchar(32) | incident_commander, operations_chief, planning_chief, etc. |
| status | varchar(32) | on_duty, standby, off_duty |
| authority_level | tinyint | 1=Full, 2=Limited, 3=Observer |

### search_party_activity_log
Audit trail for all operations activity.

| Column | Type | Notes |
|--------|------|-------|
| party_id | varchar(64) | FK to search_party |
| activity_type | varchar(32) | party_management, personnel, element, communication, status_change, incident |
| actor_user_id | varchar(64) | Who performed the action |
| actor_name | varchar(100) | Actor name |
| target_type | varchar(32) | Target entity type |
| target_id | varchar(64) | Target entity ID |
| action | varchar(32) | Action verb |
| description | varchar(500) | Human-readable description |
| metadata | text | JSON context |
| timestamp | bigint | When it occurred |

### annotation_requests
Mobile frontend annotation requests linked to map elements.

| Column | Type | Notes |
|--------|------|-------|
| element_id | varchar(64) | FK to map_group_element (unique) |
| name | varchar(100) | Requester name |
| telephone | varchar(20) | International format phone |
| request_datetime | bigint | Unix timestamp (seconds) |
| workspace_id | varchar(64) | Workspace FK |
| status | varchar(32) | pending, in_progress, completed, cancelled |
| priority | tinyint | 1=urgent to 4=low |
| assigned_to | varchar(64) | Responder user ID |

### mobile_devices
Mobile device registration and access control.

| Column | Type | Notes |
|--------|------|-------|
| device_id | varchar(64) | Unique per registration |
| device_fingerprint | varchar(256) | Persistent across registrations |
| device_token | varchar(512) | JWT token |
| client_type | varchar(32) | web, mobile, tablet |
| status | varchar(32) | active, revoked, expired |
| request_count | int | Total API requests |
| ip_address | varchar(45) | Last known IP |
| revoked_at / revoked_by | bigint/varchar | Revocation tracking |
