# algotik-tse skill

An agent skill for the [algotik-tse](https://github.com/mohsenalipour/algotik_tse)
Python package (v1.8.0) — Tehran Stock Exchange (TSETMC), Iran Fara Bourse,
Iran Energy Exchange, IME commodity market and TGJU market data.

Everything in this skill was cross-validated one-to-one against the package
and against live providers:

- all 167 exported names in `algotik_tse.__all__` are documented
  (`tests/test_api_inventory.py` fails on any gap),
- every code snippet parses and its keyword arguments are validated
  against the real signatures (`tests/test_snippets.py`),
- the deterministic math layer is pinned by exact-value tests
  (`tests/test_offline_math.py`),
- representative live calls per API family run against TSETMC/TGJU/IME
  (`tests/test_live_smoke.py`, `pytest -m online`),
- upstream's own suite (501 offline + 118 online tests) was run against
  the installed 1.8.0 during the audit — all green.

The audit findings, including live provider behaviors the package docs
don't mention, are in `AUDIT.md`.

## Layout

```
SKILL.md               the skill itself: package facts, ten contracts,
                       API map, behavioral rules
references/            deep per-domain docs (14 files)
examples/              12 runnable, live-tested scripts
tests/                 offline validation + online smoke suite
AUDIT.md               audit report and verification evidence
```

## Installing the skill

The skill is a self-contained directory: a `SKILL.md` plus `references/`
(with `examples/` alongside). Clone it once, then link or copy it into
whichever agent you use.

### Claude Code

```bash
git clone https://github.com/miladaghdak/algotik-tse-skill
mkdir -p ~/.claude/skills
ln -s "$(pwd)/algotik-tse-skill" ~/.claude/skills/algotik-tse
```

If you prefer an isolated copy instead of a link:

```bash
cp -r algotik-tse-skill ~/.claude/skills/algotik-tse
```

### Other agents

Any agent that loads skills from a directory accepts it. Symlinks keep
every install in sync — one `git pull` updates them all at once:

| Agent | Skills directory |
|---|---|
| pi | `~/.pi/agent/skills/` |
| Codex | `~/.codex/skills/` |
| Cline | `~/.cline/skills/` |
| omp | `~/.omp/skills/` |
| Hermes | `~/.hermes/skills/` |
| ECC hub (shared across tools) | `~/.agents/skills/` |

```bash
ln -s "$(pwd)/algotik-tse-skill" ~/.pi/agent/skills/algotik-tse
ln -s "$(pwd)/algotik-tse-skill" ~/.codex/skills/algotik-tse
ln -s "$(pwd)/algotik-tse-skill" ~/.cline/skills/algotik-tse
ln -s "$(pwd)/algotik-tse-skill" ~/.omp/skills/algotik-tse
ln -s "$(pwd)/algotik-tse-skill" ~/.hermes/skills/algotik-tse
```

Hermes alternative: instead of per-skill links, list the directory that
holds your skills under `skills.external_dirs` in `~/.hermes/config.yaml`
and it picks up everything there.

The skill activates on Iranian-market data tasks: Persian tickers,
TSETMC/TGJU/IME data, options chains, اخزا, industry analytics,
shareholder data and the rest of the package surface.

## Running the tests

```bash
pip install --upgrade algotik-tse pytest

pytest                 # offline: inventory, snippets, math (no network)
pytest -m online       # live smoke: TSETMC / TGJU / IME calls
```

The online suite treats documented provider schedule states (empty bulk
payloads outside publication windows, the InstrumentInfo status window)
as skips, not failures — see the module docstring of
`tests/test_live_smoke.py` and `AUDIT.md` for what each state means.

## Requirements

- Python 3.8+ (verified on 3.11)
- `algotik-tse==1.8.0` (the skill pins this version; the inventory test
  fails on a different version by design)

## License

MIT for this repository. The `algotik_tse` package itself is GPL-3.0,
by Mohsen Alipour — this skill documents that package and replaces none
of its code.
