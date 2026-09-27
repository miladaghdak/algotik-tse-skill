# Changelog

## 1.0.0 — 2026-09-27

Initial release, written against `algotik-tse==1.8.0` and cross-validated
one-to-one with the upstream package and live providers.

- `SKILL.md`: package facts, ten enforced contracts, settings, API map
  with routing, behavioral rules for agents.
- `references/`: 14 domain references — price/flow, instrument identity,
  live market, market stream, local history, market analytics,
  industries, ownership, options, fixed income, funds/ETFs/bonds,
  energy/commodity, TGJU assets, HTTP client.
- `examples/`: 12 runnable scripts, all executed against live
  TSETMC/TGJU/IME during verification.
- `tests/`: machine-checked one-to-one inventory of all 167 exported
  names, snippet compilation + keyword validation against real
  signatures, deterministic math pins, and a live smoke suite with
  documented provider-window handling.
- `AUDIT.md`: full audit of the previous (1.0.x-era) skill text and the
  live-behavior findings, including the InstrumentInfo status window,
  publication-window emptiness, the watcher fast-view incompatibility
  and the snapshot-save scale pathology.
