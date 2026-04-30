# JET OpenCode Notifier Skill

This skill helps users install and configure [opencode-notifier](https://www.npmjs.com/package/@mohak34/opencode-notifier) for native desktop notifications in OpenCode. It supports Ghostty, macOS osascript, node-notifier, Linux, and Windows notification systems.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Prerequisites

### Required Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| `npm` | Install the OpenCode notifier plugin | Included with Node.js |

### Platform-specific

| Platform | Requirement |
|----------|-------------|
| macOS (Ghostty) | Ghostty terminal with alert-style notifications enabled |
| macOS (osascript) | Script Editor allowed in System Settings > Notifications |
| Linux | `libnotify-bin` installed (`sudo apt install libnotify-bin`) |
| Windows | Works out of the box |

## Usage

Once installed, the skill is automatically triggered when you:

- Want to set up desktop notifications for OpenCode
- Ask about opencode-notifier configuration
- Need help with Ghostty notification setup
- Want to be notified on task completion, permission requests, errors, or questions

## Skill Contents

| File | Description |
|------|-------------|
| `SKILL.md` | Main skill instructions, configuration guide, and troubleshooting |
| `evals/evals.json` | Skill evaluation tests |
