# jet-datadog

Interact with Datadog's observability platform using the [pup CLI](https://github.com/datadog-labs/pup).

## Installation

### Homebrew (macOS/Linux)

```bash
brew tap datadog-labs/pack
brew install datadog-labs/pack/pup
```

### Windows

For Copilot/OpenCode-style agent workflows, use `pup` inside an interactive WSL2 terminal. Starting the assistant from PowerShell while relying on WSL for auth may not work correctly.

Install `pup` inside your WSL distro using the Linux instructions above, then verify with:

```bash
pup --version
```

If you need to run `pup` natively from PowerShell, use file-based token storage instead of the default Windows credential-store integration:

```powershell
[System.Environment]::SetEnvironmentVariable("DD_SITE", "datadoghq.eu", "User")
[System.Environment]::SetEnvironmentVariable("DD_TOKEN_STORAGE", "file", "User")
```

Then open a new PowerShell session and run `pup auth login` once. Tokens should then persist under `%APPDATA%\pup\`.

### Build from Source (macOS/Linux/WSL)

Requires [rustup](https://rustup.rs/) and the latest stable Rust toolchain.

```bash
git clone https://github.com/datadog-labs/pup.git && cd pup
rustup toolchain install stable
rustup default stable
cargo build --release
cp target/release/pup /usr/local/bin/pup
```

### Verify

```bash
pup --version
```

### Authenticate

```bash
export DD_SITE="datadoghq.eu"
pup auth login
```

On Windows, prefer running `pup auth login` from an interactive WSL terminal for agent workflows. If you need native PowerShell, set `DD_TOKEN_STORAGE=file` first as shown above.
