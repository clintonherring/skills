# Wiz CLI & API Scripts

## wiz_api.sh location
The Wiz API helper script is at:
```
C:\Users\ClintonHerring\Documents\ai\skills\jet\wiz-skill\scripts\wiz_api.sh
```

## Sourcing on Windows (Git Bash / WSL)
```bash
source "C:/Users/ClintonHerring/Documents/ai/skills/jet/wiz-skill/scripts/wiz_api.sh"
```

## PowerShell alternative
If running in PowerShell, the wiz-skill may need to be invoked differently. Check the wiz-skill SKILL.md for PowerShell-compatible commands.

## wizcli location
If `wizcli` is installed:
```
C:\Users\ClintonHerring\wizcli.exe
```

## Adding to PATH
```powershell
$env:PATH = "C:\Users\ClintonHerring;$env:PATH"
```

## Authentication

Interactive (browser-based, no secrets needed):
```powershell
wizcli auth --use-device-code
```

Service account (non-interactive):
```powershell
wizcli auth --id $env:WIZ_CLIENT_ID --secret $env:WIZ_CLIENT_SECRET
```

Auth file location (Windows):
```
C:\Users\ClintonHerring\AppData\Local\Wiz\auth.json
```

When using `wiz_api.sh` in Git Bash, set the auth file path:
```bash
export WIZ_AUTH_FILE="C:/Users/ClintonHerring/AppData/Local/Wiz/auth.json"
```

Check auth status:
```powershell
wizcli auth --print-token
```

Logout:
```powershell
wizcli auth --logout
```

## Notes
- Wiz API functions (wiz_query, wiz_list_issues, wiz_search_projects, wiz_vuln_report) are defined in wiz_api.sh
- These require WIZ_CLIENT_ID and WIZ_CLIENT_SECRET environment variables or a cached token
- For interactive use, prefer `wizcli auth --use-device-code` (opens browser for Okta SSO)
