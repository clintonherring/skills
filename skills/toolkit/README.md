# Toolkit - Windows Tool Locations & Setup

This folder contains Windows-specific configuration for tools used by custom skills.
When a skill references a tool (acli, wizcli, pup, gh, aws), check here for how to find and use it on this machine.

## How skills use this

Skills should reference `toolkit/` instead of hardcoding Windows paths. Before running any tool command, check here if the tool isn't on PATH.
