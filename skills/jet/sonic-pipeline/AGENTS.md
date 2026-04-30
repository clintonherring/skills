# sonic-pipeline skill

## Conventions
- Keep SKILL.md runtime-agnostic. Runtime-specific details (how tests are executed, scripts, flags, dependency managers, IAM configuration) belong in the corresponding file under `references/`.
- SKILL.md should only contain information that is actionable by an agent — configuration options, schema structure, and valid values. Do not include pipeline internals, architectural explanations, or implementation details that the user does not configure.
- SKILL.md should document the schema, structure, and concepts that apply across all runtimes. The runtime reference table points agents to the right file.
