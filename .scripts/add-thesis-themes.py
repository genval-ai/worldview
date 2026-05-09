"""
One-shot: add `visual` import and `vis.thesisTheme` field to each
WorldviewThesis in every snapshot YAML. Run once; the resulting YAML
is hand-maintained from there.
"""

import re
import sys
from pathlib import Path

THEME_MAP = {
    "iran-war-rearmament": "vis.theme-defense",
    "persistent-energy-shock": "vis.theme-energy",
    "stagflation-risk": "vis.theme-inflation",
    "gold-debasement-bid": "vis.theme-gold",
    "ai-capex-cycle-with-china-tail": "vis.theme-ai",
    "equity-melt-up-vs-recession-risk": "vis.theme-equity",
    "powell-warsh-transition-risk": "vis.theme-monetary",
}

VISUAL_IMPORT = (
    "        - package: finance\n"
    "          match: ^\n"
    "          version: 1.0.0\n"
    "          alias: fin\n"
    "        - package: visual\n"
    "          match: ^\n"
    "          version: 1.0.0\n"
    "          alias: vis\n"
)

VISUAL_IMPORT_BEFORE = (
    "        - package: finance\n"
    "          match: ^\n"
    "          version: 1.0.0\n"
    "          alias: fin\n"
)


def add_theme_line(content: str, thesis_name: str, theme: str) -> str:
    pattern = re.compile(
        rf"(^{re.escape(thesis_name)}:\n"
        rf"  type: wv\.WorldviewThesis\n"
        rf"  label: [^\n]+\n"
        rf"  thesisStatement: [^\n]+\n"
        rf"  confidence: [0-9.]+\n)",
        re.MULTILINE,
    )
    return pattern.sub(rf"\1  vis.thesisTheme: {theme}\n", content)


def process(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    if "alias: vis" in content:
        print(f"{path.name}: already updated, skipping")
        return False
    if VISUAL_IMPORT_BEFORE not in content:
        print(f"{path.name}: import block not in expected shape, skipping")
        return False
    new = content.replace(VISUAL_IMPORT_BEFORE, VISUAL_IMPORT, 1)
    added = 0
    for thesis_name, theme in THEME_MAP.items():
        before = new
        new = add_theme_line(new, thesis_name, theme)
        if new != before:
            added += 1
    path.write_text(new, encoding="utf-8")
    print(f"{path.name}: import added, {added} theme(s) tagged")
    return True


def main():
    target_dir = Path("kanonak-packages/worldview.genval.ai")
    for snap in sorted(target_dir.glob("snapshot@*.kan.yml")):
        process(snap)


if __name__ == "__main__":
    main()
