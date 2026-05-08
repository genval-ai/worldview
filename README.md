# worldview.genval.ai

A public [Kanonak Protocol](https://kanonak.org) publisher for falsifiable, evidence-backed worldview snapshots.

Live: [worldview.genval.ai](https://worldview.genval.ai)

## Packages

- `worldview.genval.ai/core` — abstract vocabulary (Snapshot, Thesis, Evidence, condition DSL)
- `worldview.genval.ai/finance` — finance-domain Evidence subclasses, Security class, typed-instance vocabularies
- `worldview.genval.ai/snapshot` — the worldview itself, one version per observation date
- `worldview.genval.ai/snapshot-to-html` — renders any snapshot to a single-page HTML report
- `worldview.genval.ai/landing-page` — renders the snapshots index

## Importing

```yaml
imports:
  - publisher: worldview.genval.ai
    packages:
      - package: core
        match: ^
        version: 1.0.0
        alias: wv
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
