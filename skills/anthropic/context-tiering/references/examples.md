# Context Tiering Examples

Real-world examples of L0 and L1 content for common file types.

## Node.js Express App

### L0 (app.js)
```
app.js - Express HTTP server entry point with middleware chain and route mounting. Key exports: app, startServer().
```

### L1 (app.js)
```markdown
# app.js

## Purpose
Main Express application entry point. Configures middleware (CORS, auth, body parsing),
mounts route handlers, and starts the HTTP server on the configured port.

## Key Exports / Entry Points
- `app` - configured Express instance
- `startServer(port)` - binds and listens

## Dependencies
- express - HTTP framework
- cors - CORS middleware
- ./routes/ - route handlers
- ./middleware/auth - JWT verification

## Relationships
- Called by: server.js (production), test setup
- Calls: routes/api.js, routes/websocket.js, middleware/auth.js
```

## Android Kotlin Activity

### L0 (MapFragment.kt)
```
MapFragment.kt - Google Maps fragment managing drone telemetry overlay and waypoint display. Key exports: MapFragment, onMapReady().
```

### L1 (MapFragment.kt)
```markdown
# MapFragment.kt

## Purpose
Fragment hosting Google Maps with real-time drone position markers, flight path
polylines, and tappable waypoint pins. Subscribes to ViewModel LiveData for
position updates.

## Key Exports / Entry Points
- `MapFragment` - Fragment class
- `onMapReady(map)` - initializes map layers and listeners
- `updateDronePosition(lat, lng, heading)` - moves drone marker

## Dependencies
- Google Maps SDK - map rendering
- DroneViewModel - telemetry LiveData
- WaypointRepository - stored waypoints

## Relationships
- Called by: MainActivity (navigation graph)
- Calls: DroneViewModel.observe(), WaypointRepository.getAll()
```

## Docker Compose

### L0 (docker-compose.yml)
```
docker-compose.yml - Multi-container orchestration for backend, frontend, MQTT broker, MySQL, Redis, and Nginx proxy. 8 services.
```

### L1 (docker-compose.yml)
```markdown
# docker-compose.yml

## Purpose
Defines the full application stack as containers. Backend (Node), frontend (React),
MQTT broker (Mosquitto), database (MySQL), cache (Redis), proxy (Nginx),
MinIO (object storage), and device-manager.

## Services
- `backend` - port 3000, depends on mysql, redis, mqtt
- `frontend` - port 80 via nginx
- `mqtt` - port 1883/9001, Mosquitto
- `mysql` - port 3306, persistent volume
- `redis` - port 6379
- `nginx` - port 443, TLS termination
- `minio` - port 9000, S3-compatible storage
- `device-manager` - DJI cloud bridge

## Volumes
- mysql-data, redis-data, minio-data

## Networks
- opensar-net (bridge)
```

## Directory L0/L1

### L0 (routes/)
```
routes/ - Express route handlers for REST API endpoints and WebSocket connections. 6 files.
```

### L1 (routes/)
```markdown
# routes/

## Purpose
All HTTP route definitions. Each file exports an Express Router
mounted by app.js under /api/*.

## Contents
- `api.js` - main REST endpoints (devices, missions, waypoints)
- `auth.js` - login, register, token refresh
- `dji.js` - DJI Cloud API proxy routes
- `websocket.js` - WebSocket upgrade and message routing
- `upload.js` - file/KMZ upload handling
- `health.js` - healthcheck endpoint

## Key Relationships
- Mounted by: app.js
- Uses: middleware/auth.js for protected routes
- Calls: services/ for business logic
```

## State Tracking Files

### current_task.md (example from an Android project)
```markdown
# Current Task State

## Active Task
- **Task**: Implement permanent member bind-code signup flow
- **Status**: in_progress
- **Started**: 2026-03-18
- **Files touched**: SignUpTypeFragment.kt, SignUpTypeScreen.kt, PermanentMemberBindCodeFragment.kt, PermanentMemberBindCodeScreen.kt, OpenSARApiService.kt, mobile_navigation.xml
- **Plan summary**: Add a new signup path where users enter a bind code provided by their organization. The bind code is validated against the backend API, and on success the user is linked to the organization's workspace.

## Completed Tasks (newest first)
### 2026-03-15 - GDPR consent system
- **What**: Added multi-language consent dialogs with granular opt-in for location sharing, analytics, and crash reporting
- **Files changed**: ConsentFragment.kt, ConsentScreen.kt, strings_consent.xml (EN/DE/FR/NL), ConsentPreferences.kt
- **Test result**: passed
- **Committed**: yes (a1b2c3d)
- **Pushed**: yes (main)

### 2026-03-10 - Android Auto area selection
- **What**: Implemented radius-based area filtering for Android Auto map view
- **Files changed**: AutoMapScreen.kt, AutoPreferences.kt, AutoSettingsFragment.kt
- **Test result**: passed
- **Committed**: yes (d4e5f6a)
- **Pushed**: yes (main)

## Pending / Next Steps
- Subscription billing integration (Google Play Billing Library)
- Settings screen subscription management UI
- Backend webhook for Play Store purchase verification
```

### current_spec.md (example from a Docker/backend project)
```markdown
# Current Specification

## Active Feature
- **Feature**: Search party personnel management API
- **Version**: 2.4.0
- **Branch**: feature/search-party-api

## Requirements
- [x] CRUD endpoints for search parties
- [x] Personnel assignment with role (leader, member, observer)
- [ ] Real-time party status via MQTT topic
- [ ] Party geofence with entry/exit notifications
- [ ] Integration with annotation system for area assignment

## Architecture Decisions
- Separate search-party microservice (port 3007) to keep main backend lean
- Uses opensar_enhanced database, not cloud_sample
- MQTT publishes to thing/product/{sn}/party/status for real-time updates

## Test Matrix
| Test | Status | Date | Notes |
|------|--------|------|-------|
| POST /api/party/create | passed | 2026-03-12 | Creates party with leader |
| GET /api/party/:id/members | passed | 2026-03-12 | Returns full roster |
| PUT /api/party/:id/assign | passed | 2026-03-13 | Assigns member with role |
| DELETE /api/party/:id | failed | 2026-03-14 | FK constraint on active members - needs cascade |
| MQTT party status broadcast | skipped | - | Waiting for MQTT bridge update |

## Release Checklist
- [x] All CRUD tests passing
- [ ] Delete cascade fix committed
- [ ] MQTT integration tested
- [ ] Code committed (hash: ...)
- [ ] Pushed to remote
- [ ] Version bumped in package.json
```
