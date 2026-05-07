# InvalidationCondition expression DSL — design spec

**Status:** draft, pending review
**Issue:** [#34](https://github.com/genval-ai/kanonak/issues/34)
**Owner:** the next person who picks up the worldview ontology refactor

---

## Goal

Replace the prose `invalidationCondition: xsd.string` on `cp.WorldviewThesis` with a structured expression tree that:

1. A rules engine can evaluate against live market data + an event log to determine whether each thesis is `satisfied` (invalidated), `partially-satisfied` (invalidation in progress), or `unsatisfied` (thesis intact).
2. Tooling can statically inspect to answer questions like "what indicators do my active theses depend on?" and "what events would invalidate this thesis?"
3. Stays human-readable in YAML — authors should be able to write a condition without a code generator.
4. Mirrors the proven tagged-union shape of `kanonak.org/transformations@2.0.0`'s Expression so anyone who already learned that pattern can read this immediately.

The prose form does NOT go away — it stays in `thesisStatement` (which is the human-readable claim summary). The structured `invalidationCondition` IS the machine-evaluable form. Both are first-class.

---

## Approach — tagged-union Condition

A single `Condition` class with a `kind` discriminator. Each `kind` uses a subset of optional properties relevant to it. The runner dispatches on the resolved `kind` URI.

This is the same pattern as `kanonak.org/transformations@2.0.0/Expression`. The reason: it lets deeply-nested condition trees be authored in YAML without bumping into the `EmbeddedKanonakNoExplicitType` validator rule (embedded objects can't carry `type:`, but a `kind:` discriminator on a single tagged-union class works fine).

```yaml
Condition:
  type: rdfs.Class
  comment: A boolean condition tree node. The `kind` property
    discriminates which concrete behavior this instance represents.

ConditionKind:
  type: rdfs.Class
  comment: The discriminator vocabulary for Condition.

kind:
  type: owl.ObjectProperty
  domain: Condition
  range: ConditionKind
```

---

## Vocabulary — v1

### Boolean composition

| Kind | Properties | Semantics |
|---|---|---|
| `and-condition` | `operands: [Condition]` | All operands must be `satisfied` for AND to be `satisfied`. Any `unsatisfied` makes AND `unsatisfied`. Any `unknown` propagates `unknown`. Otherwise `partially-satisfied`. |
| `or-condition` | `operands: [Condition]` | Any operand `satisfied` makes OR `satisfied`. All `unsatisfied` makes OR `unsatisfied`. Otherwise `partially-satisfied` or `unknown`. |
| `not-condition` | `operand: Condition` | Inverts: satisfied↔unsatisfied; partial stays partial; unknown stays unknown. |

### Threshold (numeric observable comparison)

| Kind | Properties | Semantics |
|---|---|---|
| `threshold-condition` | `observable: Indicator`, `comparator: Comparator`, `threshold: xsd.decimal`, `unit: Unit?`, `persistence: PersistenceWindow?` | Evaluate the indicator's most recent value against the threshold using the comparator. If `persistence` is set, condition requires the comparator to hold for that window before being `satisfied`; partial within the window. |

`Comparator` is a named-instance vocabulary: `cp.lt`, `cp.lte`, `cp.gt`, `cp.gte`, `cp.eq`, `cp.between` (range form: `between` takes `threshold` + `thresholdHigh`).

`PersistenceWindow` is a small composite:

```yaml
PersistenceWindow:
  duration: xsd.integer
  unit: TimeUnit  # cp.trading-days, cp.calendar-days, cp.hours, cp.minutes
```

### Cross-indicator comparison

| Kind | Properties | Semantics |
|---|---|---|
| `indicator-comparison` | `left: Observable`, `comparator: Comparator`, `right: Observable`, `persistence: PersistenceWindow?` | Same as threshold-condition but right-hand side is another observable (possibly a derived one). |

`Observable` is a union: an `Indicator` reference, OR a `DerivedIndicator` definition (e.g. moving average).

```yaml
DerivedIndicator:
  type: rdfs.Class
  # subclass of Observable via a kind discriminator on Observable

DerivedIndicatorKind:
  type: rdfs.Class
  # named instances: moving-average, rolling-stdev, percent-change, etc.
```

For v1, ship `DerivedIndicatorKind: moving-average` only. Others as needed.

```yaml
left:
  type: cp.DerivedIndicator
  kind: cp.moving-average
  of: ind.spy-close
  period: 50
  unit: cp.trading-days
```

### Event-based

| Kind | Properties | Semantics |
|---|---|---|
| `event-condition` | `eventType: EventType`, `durability: Durability?`, `withinWindow: TimeWindow?` | Satisfied when an event of the given type has been recorded in the event log. `durability` (`cp.durable`, `cp.transient`, `cp.unspecified`) optionally requires the event to be classified as such. `withinWindow` optionally requires the event to be within the past N units of time. |

`EventType` is a domain-specific vocabulary (e.g. `ev-types.hormuz-reopened`, `ev-types.opec-supply-increase-material`, `ev-types.fomc-statement-released`). Generic event types live in `worldview.genval.ai/core`; finance event types in `worldview.genval.ai/finance`.

The event log itself is out of scope for the ontology — it's runtime infrastructure. The ontology defines the event-type vocabulary; the runtime maintains the log.

### Temporal sequencing

| Kind | Properties | Semantics |
|---|---|---|
| `sequenced-condition` | `after: Condition`, `then: Condition`, `withinWindow: TimeWindow?` | Satisfied when `after` first became satisfied at some time T, and `then` is satisfied at time T+ (optionally within `withinWindow`). |
| `before-condition` | `before: Condition`, `mustOccur: Condition` | Inverse: `mustOccur` must become satisfied before `before` does. Used to express "X must happen before Y otherwise the thesis is invalidated". |

Most "after Hormuz reopens" / "following durable peace" statements are sequenced-condition.

### Indicator presence (data-availability check)

| Kind | Properties | Semantics |
|---|---|---|
| `indicator-available` | `indicator: Indicator`, `withinWindow: TimeWindow?` | Satisfied if the indicator has a recent observation. Used as a guard — if data is stale, return `unknown` rather than evaluating downstream comparisons against possibly-stale values. |

### Constants

| Kind | Properties | Semantics |
|---|---|---|
| `always-satisfied` | none | Always returns `satisfied`. Useful for testing. |
| `always-unsatisfied` | none | Always returns `unsatisfied`. |

---

## Evaluation semantics

Each `Condition.evaluate(now, dataSource)` returns:

```typescript
type ConditionResult = {
  state: 'satisfied' | 'partially-satisfied' | 'unsatisfied' | 'unknown'
  trace: ConditionTrace   // structured explanation
  evaluatedAt: ISO-8601
}
```

The `trace` is itself a structured tree mirroring the condition tree, with each leaf carrying the observed values (or "unknown — indicator stale since 2026-04-15") and each node carrying its propagated state. This is what a UI would display when surfacing a thesis status to a human reviewer.

Propagation rules:

- **AND**: max-pessimism. unsatisfied if any operand unsatisfied; satisfied only if all satisfied; unknown if any unknown (and no unsatisfied); partial otherwise.
- **OR**: max-optimism. satisfied if any operand satisfied; unsatisfied only if all unsatisfied; unknown if any unknown (and no satisfied); partial otherwise.
- **NOT**: satisfied↔unsatisfied; partial→partial; unknown→unknown.
- **Persistence**: tracks the time the underlying comparison first became true. partial while inside the window, satisfied once duration elapsed.
- **Sequenced**: depends on event log having a record of the prior condition's first-satisfied time. unknown until `after` is satisfied; then evaluates `then` from that timestamp forward.

The runtime is responsible for calling `evaluate()` periodically per active thesis (e.g., once per market close + once per material event). When state transitions to `satisfied`, the runtime can auto-suggest the thesis status flip to `cp.invalidated` — a human still confirms before committing a new worldview snapshot.

---

## Worked examples — the 7 current invalidations from `worldview@1.0.2`

Each shows the prose followed by the structured form. The mappings are illustrative — actual indicator/event-type names will be locked when those vocabularies are drafted.

### 1. iran-war-rearmament

**Prose:** "A durable peace agreement signed and implemented before munitions stockpiles are replenished, COMBINED with an actual reduction in DoD outlays."

```yaml
invalidationCondition:
  kind: cp.and-condition
  operands:
    - kind: cp.event-condition
      eventType: ev-types.us-iran-peace-agreement-implemented
      durability: cp.durable
    - kind: cp.threshold-condition
      observable: ind.dod-outlays-yoy-change
      comparator: cp.lt
      threshold: 0
      persistence:
        duration: 2     # two consecutive quarterly readings
        unit: cp.fiscal-quarters
```

Note: the prose mentions stockpile-replenishment as the deadline. That's a more sophisticated condition (event-must-occur-before-other-event). In v1 we model just the AND of (peace) + (DoD-cut); the deadline is implicit in the `evaluatedAt` reading.

### 2. persistent-energy-shock

**Prose:** "WTI sustainably below $80 for 30+ days following durable Hormuz reopening, OR material OPEC+ supply increase that closes the supply gap."

```yaml
invalidationCondition:
  kind: cp.or-condition
  operands:
    - kind: cp.sequenced-condition
      after:
        kind: cp.event-condition
        eventType: ev-types.hormuz-reopened
        durability: cp.durable
      then:
        kind: cp.threshold-condition
        observable: ind.wti-close
        comparator: cp.lt
        threshold: 80
        unit: cp.usd-per-bbl
        persistence:
          duration: 30
          unit: cp.calendar-days
    - kind: cp.event-condition
      eventType: ev-types.opec-supply-increase-material
```

### 3. stagflation-risk

**Prose:** "Sustained drop in core PCE below 2.5% combined with stable employment, OR resolution of Iran conflict with rapid oil normalization."

```yaml
invalidationCondition:
  kind: cp.or-condition
  operands:
    - kind: cp.and-condition
      operands:
        - kind: cp.threshold-condition
          observable: ind.core-pce-yoy
          comparator: cp.lt
          threshold: 2.5
          persistence:
            duration: 3      # three monthly readings ≈ "sustained"
            unit: cp.months
        - kind: cp.threshold-condition
          observable: ind.unemployment-rate
          comparator: cp.between
          threshold: 4.0
          thresholdHigh: 4.5
          persistence:
            duration: 3
            unit: cp.months
    - kind: cp.and-condition
      operands:
        - kind: cp.event-condition
          eventType: ev-types.us-iran-conflict-resolution
          durability: cp.durable
        - kind: cp.threshold-condition
          observable: ind.wti-close
          comparator: cp.lt
          threshold: 80
          unit: cp.usd-per-bbl
          persistence:
            duration: 30
            unit: cp.calendar-days
```

### 4. gold-debasement-bid

**Prose:** "Resolution of all three drivers simultaneously — durable peace, Fed credibility restored under Warsh, and US fiscal deficit on declining trajectory."

```yaml
invalidationCondition:
  kind: cp.and-condition
  operands:
    - kind: cp.event-condition
      eventType: ev-types.us-iran-peace-agreement-implemented
      durability: cp.durable
    - kind: cp.event-condition
      eventType: ev-types.fed-credibility-restored-under-warsh
      # this is a soft event — needs a heuristic definition
    - kind: cp.threshold-condition
      observable: ind.us-fiscal-deficit-trailing-12m-trend
      comparator: cp.lt
      threshold: 0       # i.e. trending down (negative slope)
      persistence:
        duration: 6
        unit: cp.months
```

The "Fed credibility restored" leaf is a soft, qualitative event that doesn't have a clean quantitative definition. v1: model it as an event-type whose recording requires a human curator to log. v2 may define a structured composite (no 8-4 dissent + Warsh continuity speech delivered + market-implied Fed credibility metric improved).

### 5. ai-capex-cycle-with-china-tail

**Prose:** "AMD Q1 2026 data center revenue under $5.4B AND Q2 guide below $10.3B midpoint = thesis softens. NVDA China revenue worse than zero (export retaliation extending to other chips) = thesis breaks."

This thesis has TWO conditions: a "soften" and a "break". The current ontology only models invalidation. **v1 decision: only the breaking condition goes into invalidationCondition; the softening condition stays in thesisStatement.** v2 may add `softeningCondition` as a sibling property.

```yaml
invalidationCondition:
  kind: cp.event-condition
  eventType: ev-types.us-export-controls-extended-beyond-h20
```

NOTE: this is a thin model. The prose has more nuance ("worse than zero" implies negative china-revenue, which is the export-retaliation event). The event-type `us-export-controls-extended-beyond-h20` captures it as a discrete observable event.

### 6. equity-melt-up-vs-recession-risk

**Prose:** "Either VIX sustained above 25 with SPY breaking 50d MA = transition to vol expansion, OR clean break above SPX 7,300 with VIX falling below 15 = melt-up continues unimpeded."

This thesis has TWO sides — the "vol expansion" branch invalidates the "melt-up coexists with risk" framing in one direction; the "melt-up continues unimpeded" branch invalidates it in the other direction. Either firing means the coexistence framing has resolved.

```yaml
invalidationCondition:
  kind: cp.or-condition
  operands:
    - kind: cp.and-condition
      operands:
        - kind: cp.threshold-condition
          observable: ind.vix-close
          comparator: cp.gt
          threshold: 25
          persistence:
            duration: 5
            unit: cp.trading-days
        - kind: cp.indicator-comparison
          left: ind.spy-close
          comparator: cp.lt
          right:
            kind: cp.derived-indicator
            of: ind.spy-close
            derivedKind: cp.moving-average
            period: 50
            unit: cp.trading-days
    - kind: cp.and-condition
      operands:
        - kind: cp.threshold-condition
          observable: ind.spx-close
          comparator: cp.gt
          threshold: 7300
          persistence:
            duration: 5
            unit: cp.trading-days
        - kind: cp.threshold-condition
          observable: ind.vix-close
          comparator: cp.lt
          threshold: 15
          persistence:
            duration: 5
            unit: cp.trading-days
```

This is the most complex example and it exercises every primitive in the v1 vocabulary. If this maps cleanly, the schema is sufficient.

### 7. powell-warsh-transition-risk

**Prose:** "Warsh delivers continuity-signaling first speech and FOMC vote returns to majority/minority pattern (not 8-4 dissent). Transition risk premium fades within 30 days post-confirmation."

```yaml
invalidationCondition:
  kind: cp.and-condition
  operands:
    - kind: cp.event-condition
      eventType: ev-types.warsh-continuity-speech-delivered
    - kind: cp.threshold-condition
      observable: ind.fomc-dissent-count
      comparator: cp.lte
      threshold: 2     # majority/minority is ≤2 dissents
      persistence:
        duration: 1
        unit: cp.fomc-meetings   # i.e., happens at next meeting
```

The "30 days post-confirmation" framing is captured in the `persistence`/sequencing — the condition becomes evaluatable starting at confirmation time.

---

## Open questions / v2

1. **Severity gradient.** Several theses have natural soften/break thresholds. v1: only invalidation. v2: introduce `softeningCondition` as a separate property, or a generalized `signalCondition` list with severity tags.

2. **Cross-thesis dependencies.** Some thesis invalidations depend on the state of OTHER theses ("if `iran-war-rearmament` is invalidated AND `persistent-energy-shock` is invalidated, then `stagflation-risk` is also invalidated"). v1: don't support; expect the human curator to handle. v2: a `thesis-state-condition` kind that takes a thesis URI and a state.

3. **Soft events without quantitative definition.** "Fed credibility restored", "durable peace" — these aren't auto-detectable from data alone. v1: model as event-types whose recording requires human entry. v2: composite definitions.

4. **Indicator vocabulary scope.** Some indicators are general (CPI, unemployment). Others are derived/computed (5Y breakeven, SPY 50d MA). The Indicator class in `worldview.genval.ai/core` should distinguish raw vs derived. Probably v1 just allows both with a `isDerived: bool` flag.

5. **Backtesting.** Once invalidationCondition is structured, we can replay historical data through the condition tree to ask "would this thesis have been invalidated three months earlier?" That's a v2 capability — out of scope for the schema.

6. **Connection to skill content.** The skill content currently describes invalidationCondition as prose. After the DSL ships, the skill needs a new section on "structuring invalidation conditions" with worked examples. Probably a v1.1.0 of the skill.

---

## Where it lives

```
worldview.genval.ai/core@1.0.0
    Condition, ConditionKind (the tagged-union machinery)
    Comparator (named instances: lt, gt, lte, gte, eq, between)
    TimeUnit (named instances: hours, trading-days, calendar-days, months, fiscal-quarters)
    Durability (named instances: durable, transient, unspecified)
    PersistenceWindow, TimeWindow (composites)
    Indicator (abstract class; subclassable per domain)
    EventType (abstract class; subclassable per domain)
    DerivedIndicator + DerivedIndicatorKind (named: moving-average)
    All Condition kinds (and-condition through indicator-available)
    Result types (ConditionResult, ConditionTrace, EvaluationState)
    ALL generic event types and indicator instances (none in v1; deferred to domain-specific packages)

worldview.genval.ai/finance@1.0.0
    Finance Indicator instances:
        ind.wti-close, ind.brent-close, ind.gld-close, ind.spy-close, ind.spx-close,
        ind.vix-close, ind.10y-yield, ind.30y-yield, ind.core-pce-yoy,
        ind.unemployment-rate, ind.fomc-dissent-count, ...
    Finance EventType instances:
        ev-types.hormuz-reopened, ev-types.opec-supply-increase-material,
        ev-types.fomc-statement-released, ev-types.us-export-controls-extended-beyond-h20,
        ev-types.warsh-continuity-speech-delivered, ...
```

When a non-finance worldview shows up (climate, geopolitical), it imports `worldview.genval.ai/core` and either reuses the Indicator/EventType instances from `finance` (unlikely) or defines its own (`climate.example/indicators`).

---

## v1 scope summary

In:

- `Condition` tagged-union class + 9 kinds (and, or, not, threshold, indicator-comparison, event, sequenced, before, indicator-available, constants)
- `Indicator`, `DerivedIndicator`, `EventType` abstract classes
- `Comparator`, `TimeUnit`, `Durability` named-instance vocabularies
- `PersistenceWindow`, `TimeWindow`, `ConditionResult`, `ConditionTrace` composites
- All 7 current worldview invalidations re-expressible

Out (deferred):

- Severity gradient (`softeningCondition`)
- Cross-thesis state dependencies
- Auto-detection of "soft" events
- Backtesting tooling
- Indicator/EventType libraries beyond what the 7 worked examples need
- Skill content rewrite (separate task once schema lands)
