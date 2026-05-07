# Roadmap

## Pre-release (current state)

The vocabulary is being extracted from a working private implementation in [`genval-ai/kanonak`](https://github.com/genval-ai/kanonak), where it shipped three snapshot versions inside `portfolio-ops.kanonak.com`. This repo is the new public home for the domain-general parts.

Parent issue: [genval-ai/kanonak#34](https://github.com/genval-ai/kanonak/issues/34) — captures the publisher-extraction plan and magic-string audit.

## Workstreams

### 1. Invalidation condition expression DSL

**Status:** spec drafted ([docs/specs/invalidation-condition-dsl.md](specs/invalidation-condition-dsl.md)); awaiting review.

The single highest-leverage piece of the new ontology — turns prose `invalidationCondition` into a structured tree a rules engine can evaluate. v1 vocabulary covers all 7 invalidations from the existing private worldview snapshots.

### 2. Typed instance vocabularies (magic-string elimination)

**Status:** not started.

Audit identified ~12 `xsd.string` properties on Evidence subclasses with significant drift after only 3 snapshots (e.g. `Fed Chair` / `Fed Chair (outgoing)` / `Fed Chair nominee`). Replace with named-instance vocabularies for Indicator, Institution, GovernmentBody, Location, Party, Role, MarketMetric, CorporateMetric, EventType, Comparator, TimeUnit, Durability.

### 3. Package drafts

**Status:** scaffold only.

Two packages to author:

- `worldview.genval.ai/core@1.0.0` — domain-general vocabulary
- `worldview.genval.ai/finance@1.0.0` — finance-specific subclasses + Security + finance instance vocabularies

Files will live under [`kanonak-packages/worldview.genval.ai/`](../kanonak-packages/worldview.genval.ai/).

### 4. Snapshot-to-HTML transformation

**Status:** working version exists in `genval-ai/kanonak`, needs to move and retarget URIs.

Will live as `worldview.genval.ai/snapshot-to-html@1.0.0`. Generic to any worldview snapshot — the `core` package's WorldviewSnapshot class.

### 5. Static publishing at worldview.genval.ai

**Status:** not started.

The Kanonak Protocol expects a publisher to serve `index.txt` and `<package>/<version>.kan.yml` at its origin. GitHub Pages workflow will mirror this repo's `kanonak-packages/worldview.genval.ai/` tree to a static site at `https://worldview.genval.ai/`. `.well-known/kanonak.json` is already in place.

## Acceptance test

A new worldview snapshot in `genval-ai/kanonak/portfolio-ops.kanonak.com/worldview@2.0.0.kan.yml` that imports `worldview.genval.ai/core` + `worldview.genval.ai/finance`, uses the new structured invalidationCondition end-to-end, and renders cleanly via the moved snapshot-to-html transformation.

## Out of scope (for v1)

- Severity gradient on theses (`softeningCondition` separate from `invalidationCondition`)
- Cross-thesis state dependencies (a thesis's invalidation depending on another thesis's state)
- Skill content rewrite for the new vocabulary (separate task once schema lands)
- Backtesting / historical replay of condition trees
- Non-financial Evidence subclass libraries (climate, scientific, geopolitical-only) — anyone is welcome to subclass `core` for their domain
