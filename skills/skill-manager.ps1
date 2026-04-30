# Skill Manager - Local skill repository management for OpenCode
# Inspired by OpenViking's context database paradigm
#
# Usage:
#   .\skill-manager.ps1 list [category]     - List skills (all|anthropic|jet|custom)
#   .\skill-manager.ps1 sync                - Pull latest from source locations
#   .\skill-manager.ps1 status              - Show modified skills vs source
#   .\skill-manager.ps1 add-example <skill> <name> - Create example template in a custom skill

param(
    [Parameter(Position=0)]
    [ValidateSet("list","sync","status","add-example")]
    [string]$Command,

    [Parameter(Position=1)]
    [string]$Arg1,

    [Parameter(Position=2)]
    [string]$Arg2
)

$SkillsRoot = $PSScriptRoot
$Categories = @("anthropic","jet","custom")

# Source locations (ordered by priority)
$Sources = @(
    "$env:USERPROFILE\.agents\skills",
    "C:\.agents\skills"
)

function Find-SourceSkill($name) {
    foreach ($s in $Sources) {
        $p = Join-Path $s $name
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Get-SkillCategory($name) {
    foreach ($cat in $Categories) {
        if (Test-Path (Join-Path $SkillsRoot "$cat\$name")) { return $cat }
    }
    return $null
}

switch ($Command) {
    "list" {
        $filter = if ($Arg1) { @($Arg1) } else { $Categories }
        foreach ($cat in $filter) {
            $dir = Join-Path $SkillsRoot $cat
            if (Test-Path $dir) {
                Write-Host "`n[$cat] ($((Get-ChildItem $dir -Directory).Count) skills)" -ForegroundColor Cyan
                Get-ChildItem $dir -Directory | ForEach-Object {
                    $abstract = Join-Path $_.FullName ".abstract"
                    $desc = if (Test-Path $abstract) { " - $(Get-Content $abstract -Raw)" } else { "" }
                    Write-Host "  $($_.Name)$desc"
                }
            }
        }
    }

    "sync" {
        Write-Host "Syncing skills from source locations..." -ForegroundColor Yellow
        $synced = 0
        foreach ($cat in $Categories) {
            $catDir = Join-Path $SkillsRoot $cat
            Get-ChildItem $catDir -Directory | ForEach-Object {
                $name = $_.Name
                $src = Find-SourceSkill $name
                if ($src) {
                    # For custom skills, only sync SKILL.md (preserve examples/learnings)
                    if ($cat -eq "custom") {
                        $srcSkill = Join-Path $src "SKILL.md"
                        # Don't overwrite custom SKILL.md - it has local modifications
                        Write-Host "  [skip] $name (custom - manage manually)" -ForegroundColor DarkGray
                    } else {
                        Copy-Item -Recurse -Force $src $catDir
                        Write-Host "  [sync] $name" -ForegroundColor Green
                        $synced++
                    }
                } else {
                    Write-Host "  [miss] $name (no source found)" -ForegroundColor Red
                }
            }
        }
        Write-Host "`nSynced $synced skills." -ForegroundColor Yellow
    }

    "status" {
        Write-Host "Comparing local skills to source..." -ForegroundColor Yellow
        foreach ($cat in $Categories) {
            $catDir = Join-Path $SkillsRoot $cat
            Get-ChildItem $catDir -Directory | ForEach-Object {
                $name = $_.Name
                $localSkill = Join-Path $_.FullName "SKILL.md"
                $src = Find-SourceSkill $name
                if ($src -and (Test-Path $localSkill)) {
                    $srcSkill = Join-Path $src "SKILL.md"
                    if (Test-Path $srcSkill) {
                        $localHash = (Get-FileHash $localSkill).Hash
                        $srcHash = (Get-FileHash $srcSkill).Hash
                        if ($localHash -ne $srcHash) {
                            Write-Host "  [modified] $cat/$name" -ForegroundColor Yellow
                        }
                    }
                }
            }
        }
        # Show custom skills example counts
        Write-Host "`nCustom skill examples:" -ForegroundColor Cyan
        Get-ChildItem (Join-Path $SkillsRoot "custom") -Directory | ForEach-Object {
            $exDir = Join-Path $_.FullName "examples"
            $count = if (Test-Path $exDir) { (Get-ChildItem $exDir -File | Where-Object { $_.Name -ne ".gitkeep" }).Count } else { 0 }
            Write-Host "  $($_.Name): $count examples"
        }
    }

    "add-example" {
        if (-not $Arg1 -or -not $Arg2) {
            Write-Host "Usage: .\skill-manager.ps1 add-example <skill-name> <example-name>" -ForegroundColor Red
            Write-Host "  e.g.: .\skill-manager.ps1 add-example jet-pi-troubleshooter pi-33288"
            Write-Host "  e.g.: .\skill-manager.ps1 add-example ticket-reviewer AIPL-1234"
            exit 1
        }
        $skillDir = Join-Path $SkillsRoot "custom\$Arg1\examples"
        if (-not (Test-Path $skillDir)) {
            Write-Host "Skill '$Arg1' not found in custom/" -ForegroundColor Red
            exit 1
        }
        $file = Join-Path $skillDir "$Arg2.md"
        if (Test-Path $file) {
            Write-Host "Example '$Arg2' already exists at $file" -ForegroundColor Yellow
        } else {
            $template = @"
# $Arg2

## Date
$(Get-Date -Format "yyyy-MM-dd")

## Summary
<!-- Brief description of what happened / what was reviewed -->

## Key Details
<!-- Symptoms, affected services, ticket details, etc. -->

## Resolution / Outcome
<!-- What was the root cause / review result -->

## Learnings
<!-- Patterns to apply in future investigations/reviews -->

"@
            Set-Content -Path $file -Value $template
            Write-Host "Created example template: $file" -ForegroundColor Green
            Write-Host "Edit the file to fill in details, then update learnings.md with any new patterns."
        }
    }

    default {
        Write-Host @"
Skill Manager - Local skill repository management

Usage:
  .\skill-manager.ps1 list [category]          List skills (all|anthropic|jet|custom)
  .\skill-manager.ps1 sync                     Pull latest from source locations
  .\skill-manager.ps1 status                   Show modified skills and example counts
  .\skill-manager.ps1 add-example <skill> <name>  Create example template

Categories: anthropic, jet, custom

Conversational triggers (in OpenCode):
  "new pi example"      -> Captures a PI investigation as a reference
  "new review example"  -> Captures a ticket review as a reference
"@ -ForegroundColor Cyan
    }
}
