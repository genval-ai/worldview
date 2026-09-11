# worldview.genval.ai

A public [Kanonak Protocol](https://kanonak.org) publisher for falsifiable,
evidence-backed worldview snapshots.

Live: [worldview.genval.ai](https://worldview.genval.ai)

A worldview snapshot is a point-in-time record of *what we believe and why*: a
set of falsifiable theses, each carrying a distributional confidence, a
machine-evaluable invalidation condition, and the typed evidence backing it. A
thesis without an invalidation condition is unfalsifiable belief, not analysis.

## Packages

Packages follow the protocol's schema-vs-data split — the model and the
instances version at their own pace, so a daily data refresh never forces a
schema bump.

### Schema

| Package | Latest | Defines |
| --- | --- | --- |
| `core` | 2.1.0 | Snapshot, Thesis, Evidence, the condition DSL, status/strength enumerations |
| `finance` | 3.0.0 | The Security class, five finance Evidence subclasses, Institution subclasses |
| `estimates` | 1.0.0 | Distributional-estimate primitives (Beta, Normal, LogNormal, Triangular, Uniform) |
| `factors` | 1.0.0 | Driver and the reified DriverLoading a thesis carries |
| `horizons` | 1.0.0 | `thesisHorizon` — when a thesis resolves, as a distributional duration |
| `sources` | 1.8.0 | Typed citation publishers with trust and reach estimates |
| `visual` | 2.0.0 | Theme and hue primitives keyed by thesis and by source |
| `derivatives` | 1.0.0 | OptionContract, identified the OCC-universal way |
| `alignment` | 1.0.0 | Alignment, ThesisAlignment, AlignedSecurity — theses to vehicles |
| `fund` | 1.0.0 | Fund, Holding, weighting methods — alignments to weights |

### Data

| Package | Latest | Holds |
| --- | --- | --- |
| `snapshots` | 4.0.2 | The worldview itself — one version per observation |
| `securities` | 2.4.0 | The tradable-instrument inventory |
| `drivers` | 1.0.0 | The current macro Driver instances |
| `regimes` | 1.0.0 | The public regime taxonomy |
| `indicators` | 2.0.0 | Indicator bands and their regime votes |
| `events` | 2.0.0 | The Event-subclass taxonomy and the public event log |
| `alignments` | 2.0.2 | Theses mapped to security baskets |
| `funds` | 1.1.4 | Baskets weighted into a book |

### Presentation

| Package | Latest | Does |
| --- | --- | --- |
| `worldview-look` | 2.1.0 | Brand tokens, per-type band stacks, and semantic-zoom SVG tiers |

Rendering is declarative: `worldview-look` adds `derivation.look` declarations
to the graph rather than shipping a renderer.

## The derivation chain

Each derived package pins its input exactly (`match: '='`), so a downstream
artifact can never drift to a different input than the one it was derived from:

```
snapshots@4.0.2
      |  derivedFromSnapshot
alignments@2.0.2      theses -> security baskets
      |  derivedFromAlignment
funds@1.1.4           baskets -> weighted holdings
```

## Importing

```yaml
imports:
  - publisher: worldview.genval.ai
    packages:
      - package: core
        match: ^
        version: 2.1.0
        alias: wv
```

Every resource is addressable at its canonical URL —
<https://worldview.genval.ai/core/2.1.0/WorldviewThesis> — and each package's
source is one file at `https://worldview.genval.ai/{package}/{version}.kan.yml`.

## Working on this repo

```bash
npm install -g @kanonak-protocol/cli

kanonak validate kanonak-packages/worldview.genval.ai   # resolves every import over HTTP
kanonak serve --watch --publisher worldview.genval.ai   # live preview at localhost:8080
```

Published versions are immutable — fix a mistake by publishing a new version,
never by editing one that is already out.

Pushing to `main` runs `.github/workflows/publish.yml`, which validates every
`.kan.yml`, renders the site with `kanonak publish`, and deploys it to GitHub
Pages.

## License

Apache 2.0 — see [LICENSE](LICENSE).
