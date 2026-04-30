# acli (Atlassian CLI)

## Location
The `acli` binary is at:
```
C:\Users\ClintonHerring\acli.exe
```

## Adding to PATH (if not found)
```powershell
$env:PATH = "C:\Users\ClintonHerring;$env:PATH"
```

## Verification
```powershell
acli --version
```

## Notes
- `acli` is used for Jira and Confluence operations
- It must be authenticated against the JET Jira instance
- If `acli` is not on PATH, always try `$env:USERPROFILE\acli.exe` first
