---
description: Run CodeBurn token/cost reports for this project (dashboard, web, optimize, today, month, overview, compare, yield, doctor).
agent: general
---

Run CodeBurn for Hey-Olivia. It reads opencode session data from `%USERPROFILE%\.local\share\opencode\opencode.db` automatically — fully local, no API keys, no upload.

Binary (installed `npm -g`): `C:\Users\toshi\AppData\Roaming\npm\codeburn.cmd`
Use the `.cmd` shim — the `.ps1` shim is blocked by the PowerShell execution policy.

Request/args: $ARGUMENTS

- No args → run the interactive TUI dashboard (last 7 days).
- Common subcommands: `today`, `month`, `overview`, `web`, `doctor`, `optimize`, `compare`, `yield`, `export`.
- `--provider opencode` filters to opencode sessions only; works on most subcommands.
- Interactive/TUI commands may hang in this shell — prefer non-interactive ones (`overview`, `today`, `month`, `doctor`, `optimize`, `compare`, `yield`, `export`) or `web` for the browser dashboard.
- If a command would block, run it detached in a new window: `Start-Process -FilePath "C:\Users\toshi\AppData\Roaming\npm\codeburn.cmd" -ArgumentList "<subcommand>"`.

Run `codeburn --help` if unsure. Summarize the key findings (tokens, cost, top models/projects, waste) to the user.
