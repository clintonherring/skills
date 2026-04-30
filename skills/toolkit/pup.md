# pup (Datadog CLI)

## Location
The `pup` binary should be on PATH. If not found:
```powershell
# Check common locations
Get-Command pup -ErrorAction SilentlyContinue
```

## Environment
Always set the Datadog site to EU:
```powershell
$env:DD_SITE = "datadoghq.eu"
```

Or in bash:
```bash
export DD_SITE=datadoghq.eu
```

## Authentication
```powershell
pup auth login
```

## Notes
- JET uses the EU Datadog site (datadoghq.eu)
- Logs are in Flex Logs, not indexed logs
- Use `--storage=flex` for log queries
