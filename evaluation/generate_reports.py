#!/usr/bin/env python3
"""
Generate PDF evaluation reports for the 9DATAV Data Visualisation Challenge 2026.
Reads evaluations.json, renders Jinja2 HTML templates, converts to PDF via WeasyPrint.
Outputs 12 team reports + 1 summary report to evaluation/output/.
"""

import json
import statistics
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
DATA_FILE = BASE_DIR / "evaluations.json"

# Grade mapping
GRADE_MAP = [
    (4.5, "A",  "A"),
    (4.0, "A-", "Am"),
    (3.5, "B+", "Bp"),
    (3.0, "B",  "B"),
    (2.5, "B-", "Bm"),
    (2.0, "C",  "C"),
    (0.0, "D",  "D"),
]

# Short names for heatmap columns
DIM_SHORT_NAMES = {
    "alignment":       "Align",
    "dataset_quality": "Data",
    "analytical_depth": "Depth",
    "decision_maker":  "DM",
    "feasibility":     "Feas",
    "differentiation": "Diff",
    "presentation":    "Pres",
}

# Per-team one-line verdicts
VERDICTS = {
    1:  "Strong foundation with authoritative datasets. Needs household impact layer and visual differentiation from generic oil analysis to stand out.",
    2:  "Excellent multi-indicator approach with robust CSO data. Composite stress index is novel. Needs transparent methodology and genuine inquiry framing.",
    3:  "Most comprehensive submission. Switched from Housing as advised. Strong KPI framework but must differentiate from Team 07 on waiting lists.",
    4:  "Highly distinctive topic with solid STOP dataset. Needs deeper exploration: cite specific counts and trends from the data. Define decision-maker.",
    5:  "Valid funding angle on AMR but lost the powerful mortality comparison hook. Needs dataset provenance and more specific quantitative findings.",
    6:  "Most analytically rigorous (r=-0.76). Outstanding for a 2-person team. Capacity is the key risk; must ruthlessly prioritise deliverables.",
    7:  "Strong Pareto analysis and EUR 420M budget accountability framing. Needs spend-per-specialty data to complete the argument. Overlaps Team 03.",
    8:  "Pivoted from Hormuz without explanation. The conflict-to-renewables angle is interesting but needs causation caveats and a specific decision-maker.",
    9:  "Top submission. Best decision-maker persona, strongest counter-trend finding (Ireland +28% vs EU -12.3%), three actionable policy recommendations.",
    10: "Major improvement from generic food prices to Ukraine wheat shock. Exceptional data exploration with specific FAO statistics. Near-exemplary work.",
    11: "Topic is strong but execution is weak. No exploratory analysis, no figures, copy-paste error, no decision-maker. Needs significant catch-up work.",
    12: "Weakest submission. Ignored AI Incidents recommendation, shortest document (253 words), no URLs, no decision-maker. Requires urgent remediation.",
}

OBSERVATIONS = [
    "Teams 03 and 07 both chose hospital waiting lists. Team 03 focuses on specialty bottleneck mechanics; Team 07 frames it as budget accountability (EUR 420M). Both must sharpen differentiation.",
    "Team 08 pivoted from the recommended Hormuz energy angle to conflict-renewables correlation without explanation. The new direction has merit but the departure should be acknowledged.",
    "Team 09 is the standout: best decision-maker persona (RSA Director), strongest counter-trend finding, and the only team with three implementation-ready policy recommendations.",
    "Team 12 diverged from the AI Incidents recommendation to pursue Oil/Conflict, the most saturated topic in the cohort. Shortest submission at 253 words.",
    "Team 06 (Flooded and Forgotten) achieves the strongest analytical rigour (Pearson r=-0.76, 5 figures) despite being the only 2-person team. Feasibility is their main constraint.",
    "Team 10 exemplifies 'evolution done right': narrowed from generic food prices to Ukraine wheat supply chain disruption with FAO data. A model for how to sharpen scope.",
    "Three teams (01, 08, 12) touch oil/conflict/geopolitics. Only Team 01 has a clear differentiation strategy (household impact layer).",
    "Copy-paste errors appear in Team 11 (repeated paragraph) and generic framing in Team 12. Both suggest insufficient review before submission.",
]


def compute_weighted_score(scores, dimensions):
    """Compute weighted average score from dimension scores and weights."""
    total = 0.0
    for dim in dimensions:
        total += scores[dim["id"]] * dim["weight"]
    return round(total, 2)


def assign_grade(score):
    """Return (grade_label, grade_class) for a weighted score."""
    for threshold, label, css_class in GRADE_MAP:
        if score >= threshold:
            return label, css_class
    return "D", "D"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    meta = data["meta"]
    dimensions = data["dimensions"]
    teams = data["teams"]

    # Add short names to dimensions
    for dim in dimensions:
        dim["short_name"] = DIM_SHORT_NAMES[dim["id"]]

    # Compute scores and grades
    for team in teams:
        team["weighted_score"] = compute_weighted_score(team["scores"], dimensions)
        team["grade"], team["grade_class"] = assign_grade(team["weighted_score"])
        team["verdict"] = VERDICTS.get(team["number"], "")

    # Set up Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    team_template = env.get_template("team_report.html")
    summary_template = env.get_template("summary_report.html")

    # Generate team reports
    for team in teams:
        html_str = team_template.render(
            team=team,
            dimensions=dimensions,
            meta=meta,
        )
        pdf_path = OUTPUT_DIR / f"team{team['number']:02d}-evaluation.pdf"
        HTML(string=html_str).write_pdf(str(pdf_path))
        print(f"  Generated {pdf_path.name}")

    # Compute cohort statistics
    scores = [t["weighted_score"] for t in teams]
    followed_count = sum(
        1 for t in teams if t["alignment"] in ("FOLLOWED", "EVOLVED")
    )

    stats = {
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "highest": max(scores),
        "lowest": min(scores),
        "followed": followed_count,
    }

    # Rank teams by score descending
    ranked_teams = sorted(teams, key=lambda t: t["weighted_score"], reverse=True)

    # Generate summary report
    html_str = summary_template.render(
        meta=meta,
        dimensions=dimensions,
        stats=stats,
        ranked_teams=ranked_teams,
        observations=OBSERVATIONS,
    )
    summary_path = OUTPUT_DIR / "summary-evaluation.pdf"
    HTML(string=html_str).write_pdf(str(summary_path))
    print(f"  Generated {summary_path.name}")

    print(f"\nDone. {len(teams) + 1} PDFs in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
