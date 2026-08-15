# xander-plugins

A personal [Claude Code](https://claude.com/claude-code) plugin marketplace — workflow
skills for planning, orchestrating, and verifying agent work.

## Install

```
/plugin marketplace add Xander-git/xander-plugins
/plugin install execute-plan-orchestration@xander-plugins
/plugin install xander-workflow@xander-plugins
```

Browse everything with `/plugin marketplace browse xander-plugins`.

## Plugins

| Plugin | What it does |
|---|---|
| [`execute-plan-orchestration`](plugins/execute-plan-orchestration) | Turns a multi-task implementation plan into right-sized subagent clusters — tag tasks by shape, group them, assign model tier and reasoning effort, place review gates. Ships the `plan-reviewer` and `implementation-test-reviewer` agents that staff those gates. |
| [`xander-workflow`](plugins/xander-workflow) | Four workflow skills: `present-solutions`, `porting-a-reference-algorithm`, `dedupe-scanner`, `summarize-session`. |

## Repository layout

```
.claude-plugin/
  marketplace.json          # marketplace manifest (lists every plugin)
plugins/
  <plugin-name>/
    .claude-plugin/
      plugin.json           # plugin manifest (required)
    skills/                 # skills (optional)
    commands/               # slash commands (optional)
    agents/                 # subagent definitions (optional)
    hooks/hooks.json        # hooks (optional)
    .mcp.json               # MCP servers (optional)
```

## Adding a plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with at least `name`,
   `version`, and `description`.
2. Drop the plugin's content into `skills/`, `commands/`, `agents/`, etc.
3. Add a matching entry to the `plugins` array in
   [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json), pointing
   `source` at `./plugins/<name>`.
4. Bump the plugin's `version` in both manifests whenever its content changes —
   Claude Code uses it to decide when to update an installed copy.

Validate locally before pushing:

```
claude plugin validate .
```

## Local development

To try a plugin straight from a checkout without going through GitHub:

```
/plugin marketplace add /path/to/xander-plugins
```

Note that a plugin skill and a personal skill in `~/.claude/skills/` with the same
name will both be offered. Keep only one of the two installed.

## License

MIT — see [LICENSE](LICENSE).
