"""
Bulk-rewrite reference renders into label+tooltip resource spans
inside snapshot-to-html@1.0.0.kan.yml.

Three patterns are handled:

A) Depth-3 nested in And/Or operands (cond as VarRef):
     tx.stringLiteral: '...<code class="cond-X">'
     tx.UriName(tx.PropertyRead(VarRef(cond), <prop>))
     tx.stringLiteral: '</code>...'

B) Depth-1 reading via thesisRefMain through invalidationCondition:
     tx.stringLiteral: '...<code class="cond-X">'
     tx.UriName(tx.PropertyRead(tx.PropertyRead(ResolveRef(VarRef(thesisRefMain)),
                                                wv.invalidationCondition),
                                <prop>))
     tx.stringLiteral: '</code>...'

C) Evidence ev-fact-value (bare PropertyRead, evRef-based):
     tx.stringLiteral: '...<span class="ev-fact-value">'
     tx.PropertyRead(ResolveRef(VarRef(evRef)), <prop>)
     tx.stringLiteral: '</span>...'

The transformation in each case wraps the inner reference body in
ResolveRef and appends rdfs.label / rdfs.comment to produce both a
visible label and a hover tooltip. Only properties in ALLOWED_PROPS
are transformed (so comparators, durabilities, dates, etc. are left
untouched).
"""

import re
import sys
from pathlib import Path

ALLOWED_PROPS = {
    "wv.observable",
    "wv.event",
    "wv.left",
    "wv.right",
    "wv.indicator",
    "wv.indicatorName",
    "wv.aboutSecurity",
    "wv.policy",
    "wv.speaker",
    "wv.eventLocation",
    "wv.speakerRole",
    "wv.statementVenue",
    "wv.issuingBody",
    "fin.aboutSecurity",
    "fin.centralBank",
    "fin.analystInstitution",
    "fin.flowInstitution",
    "fin.flowDirection",
    "fin.marketMetric",
    "fin.corporateMetric",
    "fin.forecastTarget",
    "fin.forecastHorizon",
    "fin.reportingPeriod",
}


# Pattern A: simple inline VarRef inside UriName
PATTERN_A = re.compile(
    r"(?P<pre>[ \t]+)tx\.stringLiteral: '(?P<prefix>[^']*)<code class=\"(?P<klass>[a-zA-Z][a-zA-Z0-9_-]*)\">'[ \t]*\n"
    r"(?P<dash>[ \t]+)- type: tx\.UriName[ \t]*\n"
    r"[ \t]+tx\.uriNameOf:[ \t]*\n"
    r"[ \t]+type: tx\.PropertyRead[ \t]*\n"
    r"[ \t]+tx\.readSource: \{ type: tx\.VarRef, tx\.varName: (?P<var>[a-zA-Z_][a-zA-Z0-9_]*) \}[ \t]*\n"
    r"[ \t]+tx\.readProp: (?P<prop>\S+)[ \t]*\n"
    r"[ \t]+- type: tx\.StringLiteral[ \t]*\n"
    r"[ \t]+tx\.stringLiteral: '</code>(?P<suffix>[^']*)'"
)

def replace_a(m: re.Match) -> str:
    prop = m.group("prop")
    if prop not in ALLOWED_PROPS:
        return m.group(0)

    pre = m.group("pre")
    dash = m.group("dash")
    inner = " " * (len(dash) + 2)
    klass = m.group("klass")
    var = m.group("var")
    prefix = m.group("prefix")
    suffix = m.group("suffix")

    def chain(read_prop: str) -> str:
        return (
            f"{dash}- type: tx.PropertyRead\n"
            f"{inner}tx.readSource:\n"
            f"{inner}  type: tx.ResolveRef\n"
            f"{inner}  tx.resolveSource:\n"
            f"{inner}    type: tx.PropertyRead\n"
            f"{inner}    tx.readSource: {{ type: tx.VarRef, tx.varName: {var} }}\n"
            f"{inner}    tx.readProp: {prop}\n"
            f"{inner}tx.readProp: {read_prop}"
        )

    return (
        f"{pre}tx.stringLiteral: '{prefix}<span class=\"resource\"><code class=\"{klass}\">'\n"
        f"{chain('rdfs.label')}\n"
        f"{dash}- type: tx.StringLiteral\n"
        f"{inner}tx.stringLiteral: '</code><span class=\"resource-tip\">'\n"
        f"{chain('rdfs.comment')}\n"
        f"{dash}- type: tx.StringLiteral\n"
        f"{inner}tx.stringLiteral: '</span></span>{suffix}'"
    )


# Pattern B: depth-1 via thesisRefMain.invalidationCondition.<prop>
PATTERN_B = re.compile(
    r"(?P<pre>[ \t]+)tx\.stringLiteral: '(?P<prefix>[^']*)<code class=\"(?P<klass>[a-zA-Z][a-zA-Z0-9_-]*)\">'[ \t]*\n"
    r"(?P<dash>[ \t]+)- type: tx\.UriName[ \t]*\n"
    r"[ \t]+tx\.uriNameOf:[ \t]*\n"
    r"[ \t]+type: tx\.PropertyRead[ \t]*\n"
    r"[ \t]+tx\.readSource:[ \t]*\n"
    r"[ \t]+type: tx\.PropertyRead[ \t]*\n"
    r"[ \t]+tx\.readSource:[ \t]*\n"
    r"[ \t]+type: tx\.ResolveRef[ \t]*\n"
    r"[ \t]+tx\.resolveSource: \{ type: tx\.VarRef, tx\.varName: (?P<var>[a-zA-Z_][a-zA-Z0-9_]*) \}[ \t]*\n"
    r"[ \t]+tx\.readProp: (?P<intermed>\S+)[ \t]*\n"
    r"[ \t]+tx\.readProp: (?P<prop>\S+)[ \t]*\n"
    r"[ \t]+- type: tx\.StringLiteral[ \t]*\n"
    r"[ \t]+tx\.stringLiteral: '</code>(?P<suffix>[^']*)'"
)

def replace_b(m: re.Match) -> str:
    prop = m.group("prop")
    if prop not in ALLOWED_PROPS:
        return m.group(0)

    pre = m.group("pre")
    dash = m.group("dash")
    inner = " " * (len(dash) + 2)
    klass = m.group("klass")
    var = m.group("var")
    intermed = m.group("intermed")
    prefix = m.group("prefix")
    suffix = m.group("suffix")

    def chain(read_prop: str) -> str:
        return (
            f"{dash}- type: tx.PropertyRead\n"
            f"{inner}tx.readSource:\n"
            f"{inner}  type: tx.ResolveRef\n"
            f"{inner}  tx.resolveSource:\n"
            f"{inner}    type: tx.PropertyRead\n"
            f"{inner}    tx.readSource:\n"
            f"{inner}      type: tx.PropertyRead\n"
            f"{inner}      tx.readSource:\n"
            f"{inner}        type: tx.ResolveRef\n"
            f"{inner}        tx.resolveSource: {{ type: tx.VarRef, tx.varName: {var} }}\n"
            f"{inner}      tx.readProp: {intermed}\n"
            f"{inner}    tx.readProp: {prop}\n"
            f"{inner}tx.readProp: {read_prop}"
        )

    return (
        f"{pre}tx.stringLiteral: '{prefix}<span class=\"resource\"><code class=\"{klass}\">'\n"
        f"{chain('rdfs.label')}\n"
        f"{dash}- type: tx.StringLiteral\n"
        f"{inner}tx.stringLiteral: '</code><span class=\"resource-tip\">'\n"
        f"{chain('rdfs.comment')}\n"
        f"{dash}- type: tx.StringLiteral\n"
        f"{inner}tx.stringLiteral: '</span></span>{suffix}'"
    )


# Pattern C: Evidence ev-fact-value, bare PropertyRead with evRef ResolveRef
PATTERN_C = re.compile(
    r"(?P<pre>[ \t]+)tx\.stringLiteral: '(?P<prefix>[^']*)<span class=\"ev-fact-value\">'[ \t]*\n"
    r"(?P<dash>[ \t]+)- type: tx\.PropertyRead[ \t]*\n"
    r"[ \t]+tx\.readSource:[ \t]*\n"
    r"[ \t]+type: tx\.ResolveRef[ \t]*\n"
    r"[ \t]+tx\.resolveSource:[ \t]*\n"
    r"[ \t]+type: tx\.VarRef[ \t]*\n"
    r"[ \t]+tx\.varName: (?P<var>[a-zA-Z_][a-zA-Z0-9_]*)[ \t]*\n"
    r"[ \t]+tx\.readProp: (?P<prop>\S+)[ \t]*\n"
    r"[ \t]+- type: tx\.StringLiteral[ \t]*\n"
    r"[ \t]+tx\.stringLiteral: '(?P<suffix>[^']*)</span>(?P<rest>[^']*)'"
)

def replace_c(m: re.Match) -> str:
    prop = m.group("prop")
    if prop not in ALLOWED_PROPS:
        return m.group(0)

    pre = m.group("pre")
    dash = m.group("dash")
    inner = " " * (len(dash) + 2)
    var = m.group("var")
    prefix = m.group("prefix")
    suffix = m.group("suffix")
    rest = m.group("rest")

    def chain(read_prop: str) -> str:
        return (
            f"{dash}- type: tx.PropertyRead\n"
            f"{inner}tx.readSource:\n"
            f"{inner}  type: tx.ResolveRef\n"
            f"{inner}  tx.resolveSource:\n"
            f"{inner}    type: tx.PropertyRead\n"
            f"{inner}    tx.readSource:\n"
            f"{inner}      type: tx.ResolveRef\n"
            f"{inner}      tx.resolveSource:\n"
            f"{inner}        type: tx.VarRef\n"
            f"{inner}        tx.varName: {var}\n"
            f"{inner}    tx.readProp: {prop}\n"
            f"{inner}tx.readProp: {read_prop}"
        )

    return (
        f"{pre}tx.stringLiteral: '{prefix}<span class=\"ev-fact-value resource\">'\n"
        f"{chain('rdfs.label')}\n"
        f"{dash}- type: tx.StringLiteral\n"
        f"{inner}tx.stringLiteral: '<span class=\"resource-tip\">'\n"
        f"{chain('rdfs.comment')}\n"
        f"{dash}- type: tx.StringLiteral\n"
        f"{inner}tx.stringLiteral: '{suffix}</span></span>{rest}'"
    )


def main():
    target = Path(sys.argv[1])
    content = target.read_text(encoding="utf-8")
    original = content

    counts = {"A": 0, "B": 0, "C": 0, "skipped_A": 0, "skipped_B": 0, "skipped_C": 0}

    def collect_a(m):
        prop = m.group("prop")
        if prop in ALLOWED_PROPS:
            counts["A"] += 1
            return replace_a(m)
        else:
            counts["skipped_A"] += 1
            return m.group(0)

    def collect_b(m):
        prop = m.group("prop")
        if prop in ALLOWED_PROPS:
            counts["B"] += 1
            return replace_b(m)
        else:
            counts["skipped_B"] += 1
            return m.group(0)

    def collect_c(m):
        prop = m.group("prop")
        if prop in ALLOWED_PROPS:
            counts["C"] += 1
            return replace_c(m)
        else:
            counts["skipped_C"] += 1
            return m.group(0)

    content = PATTERN_A.sub(collect_a, content)
    content = PATTERN_B.sub(collect_b, content)
    content = PATTERN_C.sub(collect_c, content)

    print(f"Pattern A (depth-3 nested):     transformed={counts['A']}  skipped={counts['skipped_A']}")
    print(f"Pattern B (depth-1 thesisRef):  transformed={counts['B']}  skipped={counts['skipped_B']}")
    print(f"Pattern C (Evidence ev-fact):   transformed={counts['C']}  skipped={counts['skipped_C']}")

    if content == original:
        print("No changes.")
        return

    target.write_text(content, encoding="utf-8")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
