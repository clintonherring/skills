# Wiz CLI & API Scripts

## wiz_api.sh location
The Wiz API helper script is at:
```
C:/.agents/skills/wiz-skill/scripts/wiz_api.sh
```

## Sourcing on Windows (Git Bash / WSL)
```bash
source C:/.agents/skills/wiz-skill/scripts/wiz_api.sh
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

## Notes
- Wiz API functions (wiz_query, wiz_list_issues, wiz_search_projects, wiz_vuln_report) are defined in wiz_api.sh
- These require WIZ_CLIENT_ID and WIZ_CLIENT_SECRET environment variables or a cached token
