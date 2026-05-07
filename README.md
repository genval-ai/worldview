# worldview.genval.ai

A public Kanonak Protocol publisher offering an ontology and tooling for **falsifiable, evidence-backed worldview snapshots**.

## What this is

`worldview.genval.ai` defines a domain-general vocabulary for recording "what we believe and why" at a moment in time:

- **`WorldviewSnapshot`** — a point-in-time package with a narrative summary
- **`WorldviewThesis`** — a falsifiable claim with an explicit invalidation condition, supporting evidence, and a calibrated confidence
- **`Evidence`** (and typed subclasses) — primary-source observations that support or weaken theses

The ontology is split across two packages:

- **`worldview.genval.ai/core`** — abstract vocabulary (Snapshot/Thesis/Evidence base, generic Evidence subclasses, condition DSL, status/strength enums)
- **`worldview.genval.ai/finance`** — finance-specific Evidence subclasses (MarketData, Corporate, Analyst, CentralBank, InstitutionalFlow), Security class, finance-domain typed-instance vocabularies (indicators, event types)

## Why

The classic problem with research / market commentary / strategy memos is that the underlying claims are unfalsifiable prose. "Oil will stay elevated as long as the Strait of Hormuz is contested" doesn't tell you when to update your view; "WTI sustainably below \$80 for 30+ days following durable Hormuz reopening" does — but only if both sides of that condition are typed entities a rules engine can evaluate.

This publisher provides:

1. The vocabulary for writing falsifiable theses
2. A structured `invalidationCondition` expression DSL so a rules engine can flag when a thesis is approaching invalidation
3. A `snapshot-to-html` transformation that renders any worldview snapshot to a single-page HTML report
4. (Planned) Worked example skills and reference implementations

## Status

**Pre-release.** The vocabulary is being extracted from a working private implementation (`portfolio-ops.kanonak.com`) where it has shipped three snapshot versions. See [docs/ROADMAP.md](docs/ROADMAP.md) for current state.

## Using this ontology

Once published, importing in your own Kanonak package:

```yaml
my-worldview:
  type: Package
  publisher: example.com
  version: 1.0.0
  imports:
    - publisher: worldview.genval.ai
      packages:
        - package: core
          match: ^
          version: 1.0.0
          alias: wv
        - package: finance      # only if your domain is financial
          match: ^
          version: 1.0.0
          alias: fin
```

Then author snapshots, theses, and evidence using the imported classes.

## License

Apache 2.0 — see [LICENSE](LICENSE).

## The Kanonak Protocol

This repo is one of the first non-trivial public Kanonak Protocol publishers — a real-world example of how a versioned, distributed ontology can be authored, published, and consumed. See [kanonak.org](https://kanonak.org) for the protocol spec.
