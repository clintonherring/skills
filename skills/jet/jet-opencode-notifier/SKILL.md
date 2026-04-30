---
name: jet-opencode-notifier
description: Set up and configure opencode-notifier for native desktop notifications in OpenCode. Use this skill when the user wants notification setup, OpenCode alerts, opencode-notifier config, Ghostty notifications, or to get notified on task completion, permission requests, errors, or questions.
metadata:
  owner: ai-platform
---

# OpenCode Notifier Setup

Help users install and configure opencode-notifier. Always ask which notification system they want to use before writing config. If they already mention Ghostty or a preference, confirm it in one line before proceeding.

## Start by asking

Ask this first:

"Which notification system do you want to use? I can set up Ghostty (recommended if you use Ghostty), macOS osascript (default, reliable), node-notifier (shows OpenCode icon but can miss alerts), or the standard Linux/Windows setup."

If they are unsure, recommend Ghostty for Ghostty users on macOS, otherwise osascript.

## Install the plugin (beta for Ghostty support)

Use the npm beta tag for now:

Update `~/.config/opencode/opencode.jsonc` to include:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["@mohak34/opencode-notifier@beta"]
}
```

Note: When Ghostty support is in stable, the user can switch to `@mohak34/opencode-notifier@latest`.

## Create the notifier config

Create `~/.config/opencode/opencode-notifier.json` with working defaults plus the chosen notification system.

Minimal example:

```json
{
  "notificationSystem": "ghostty"
}
```

If the user wants defaults explicitly set, use the full default template from the plugin README and set `notificationSystem` accordingly (macOS only).

## Notification system choices

### Ghostty (macOS)

Set in `opencode-notifier.json`:

```json
{
  "notificationSystem": "ghostty"
}
```

Then: System Settings -> Notifications -> Ghostty -> Alert style = Alerts (not Banners). This keeps notifications visible until clicked and allows jump-to-window behavior.

### macOS osascript (default)

```json
{
  "notificationSystem": "osascript"
}
```

If notifications do not appear: System Settings -> Notifications -> Script Editor.

### macOS node-notifier

```json
{
  "notificationSystem": "node-notifier"
}
```

Use only if the user wants the OpenCode icon and accepts occasional missed alerts.

### Linux

Do not set `notificationSystem` on Linux. Use the default config and ensure libnotify is installed.

```bash
sudo apt install libnotify-bin
```

For sounds, install one of: `paplay`, `aplay`, `mpv`, `ffplay`.

### Windows

Do not set `notificationSystem` on Windows. Works out of the box. For custom sounds, use `.wav` and full Windows paths.

## Validate install

Always validate the setup after configuration.

- Restart OpenCode
- Trigger a notification event (ask a question or wait for a completion)
- Confirm the notification appears

If the user is on Linux, suggest `notify-send "OpenCode" "Notifier test"` to confirm the system notification daemon is working.

## Remove after setup

Suggest removing this skill from their environment after the setup is done to avoid unnecessary triggering in future sessions.

## Configuration reference (quick)

Only expand if the user asks for customization.

- Global toggles: `sound`, `notification`, `timeout`, `showProjectName`, `showSessionTitle`, `showIcon`, `notificationSystem` (macOS only)
- Per-event control: `events.permission`, `events.complete`, `events.error`, `events.question`, `events.subagent_complete`, `events.user_cancelled`
- Custom messages: `messages.*` supports `{sessionTitle}`, `{projectName}`, `{timestamp}`, `{turn}`
- Custom sounds: `sounds.*` (macOS/Linux: wav/mp3, Windows: wav)
- Volumes: `volumes.*` in range `0..1`
- Custom command hooks: `command.enabled`, `command.path`, `command.args`, `command.minDuration`

## Troubleshooting

- macOS: If no notifications, check System Settings -> Notifications for Script Editor or Ghostty.
- Plugin not loading: Check `opencode.jsonc` syntax, clear cache `~/.cache/opencode/node_modules/@mohak34/opencode-notifier`, restart OpenCode.
- Linux: If no notifications, verify `notify-send "Test" "Hello"` works.
