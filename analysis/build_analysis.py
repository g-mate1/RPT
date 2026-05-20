"""Empirical analysis of Related Party Transaction disclosures across 60 ATX/DAX companies.

Reads each per-company markdown file in /home/user/RPT/disclosures/, classifies the
disclosure into 20 transaction-category flags using keyword pattern matching against
both the verbatim disclosure and the agent's "Categories disclosed" section, then
produces summary statistics, a frequency matrix, and visualisations.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DISCLOSURES = Path("/home/user/RPT/disclosures")
OUT = Path("/home/user/RPT/analysis")
OUT.mkdir(exist_ok=True)


# 60 companies in original index order
COMPANIES = [
    ("01_andritz", "Andritz", "ATX"),
    ("02_ats", "AT&S", "ATX"),
    ("03_bawag", "BAWAG Group", "ATX"),
    ("04_ca_immo", "CA Immobilien Anlagen", "ATX"),
    ("05_doco", "DO & CO", "ATX"),
    ("06_erste_group", "Erste Group Bank", "ATX"),
    ("07_evn", "EVN", "ATX"),
    ("08_lenzing", "Lenzing", "ATX"),
    ("09_mayr_melnhof", "Mayr-Melnhof Karton", "ATX"),
    ("10_omv", "OMV", "ATX"),
    ("11_oesterreichische_post", "Österreichische Post", "ATX"),
    ("12_pierer_mobility", "PIERER Mobility", "ATX"),
    ("13_rbi", "Raiffeisen Bank International", "ATX"),
    ("14_sbo", "Schoeller-Bleckmann", "ATX"),
    ("15_telekom_austria", "Telekom Austria / A1 Group", "ATX"),
    ("16_uniqa", "UNIQA Insurance Group", "ATX"),
    ("17_verbund", "Verbund", "ATX"),
    ("18_vig", "Vienna Insurance Group", "ATX"),
    ("19_voestalpine", "voestalpine", "ATX"),
    ("20_wienerberger", "Wienerberger", "ATX"),
    ("21_adidas", "Adidas", "DAX"),
    ("22_airbus", "Airbus", "DAX"),
    ("23_allianz", "Allianz", "DAX"),
    ("24_basf", "BASF", "DAX"),
    ("25_bayer", "Bayer", "DAX"),
    ("26_beiersdorf", "Beiersdorf", "DAX"),
    ("27_bmw", "BMW", "DAX"),
    ("28_brenntag", "Brenntag", "DAX"),
    ("29_commerzbank", "Commerzbank", "DAX"),
    ("30_continental", "Continental", "DAX"),
    ("31_daimler_truck", "Daimler Truck", "DAX"),
    ("32_deutsche_bank", "Deutsche Bank", "DAX"),
    ("33_deutsche_boerse", "Deutsche Börse", "DAX"),
    ("34_dhl_group", "DHL Group", "DAX"),
    ("35_deutsche_telekom", "Deutsche Telekom", "DAX"),
    ("36_eon", "E.ON", "DAX"),
    ("37_fresenius_se", "Fresenius SE", "DAX"),
    ("38_fmc", "Fresenius Medical Care", "DAX"),
    ("39_hannover_rueck", "Hannover Rück", "DAX"),
    ("40_heidelberg_materials", "Heidelberg Materials", "DAX"),
    ("41_henkel", "Henkel", "DAX"),
    ("42_infineon", "Infineon Technologies", "DAX"),
    ("43_mercedes_benz", "Mercedes-Benz Group", "DAX"),
    ("44_merck_kgaa", "Merck KGaA", "DAX"),
    ("45_mtu", "MTU Aero Engines", "DAX"),
    ("46_munich_re", "Munich Re", "DAX"),
    ("47_porsche_ag", "Porsche AG", "DAX"),
    ("48_porsche_se", "Porsche SE", "DAX"),
    ("49_qiagen", "Qiagen", "DAX"),
    ("50_rheinmetall", "Rheinmetall", "DAX"),
    ("51_rwe", "RWE", "DAX"),
    ("52_sap", "SAP", "DAX"),
    ("53_sartorius", "Sartorius", "DAX"),
    ("54_siemens", "Siemens", "DAX"),
    ("55_siemens_energy", "Siemens Energy", "DAX"),
    ("56_siemens_healthineers", "Siemens Healthineers", "DAX"),
    ("57_symrise", "Symrise", "DAX"),
    ("58_volkswagen", "Volkswagen", "DAX"),
    ("59_vonovia", "Vonovia", "DAX"),
    ("60_zalando", "Zalando", "DAX"),
]


# Category → list of regex patterns. Hits anywhere in the file (case-insensitive).
# These patterns are calibrated to RPT/IAS 24 disclosure language and not generic.
PATTERNS: dict[str, list[str]] = {
    "SALES_TO_RP": [
        r"sales? to (?:joint ventures|associates|related parti|other related)",
        r"revenues? (?:from|generated with|with) (?:joint ventures|associates|related parti)",
        r"goods (?:and services )?sold to (?:joint ventures|associates|related)",
        r"income from (?:related parties|joint ventures|associates)",
        r"premium income from .*(?:associates|joint ventures)",
        r"\bSALES_TO_RP[: ]*Y\b",
    ],
    "PURCHASES_FROM_RP": [
        r"purchases? from (?:joint ventures|associates|related parti|other related)",
        r"goods (?:and services )?(?:procured|purchased) from (?:joint ventures|associates|related)",
        r"expenses? to (?:joint ventures|associates|related parti)",
        r"deliveries (?:and services )?from",
        r"raw materials? from (?:joint ventures|associates|related|family)",
        r"services? (?:procured|received) from (?:joint ventures|associates|related)",
        r"\bPURCHASES_FROM_RP[: ]*Y\b",
    ],
    "RECEIVABLES_RP": [
        r"(?:trade )?receivables? (?:from|due from) (?:joint ventures|associates|related parti)",
        r"outstanding receivables? from",
        r"affiliate receivables",
        r"\bRECEIVABLES_RP[: ]*Y\b",
    ],
    "PAYABLES_RP": [
        r"(?:trade )?(?:payables?|liabilities) (?:to|due to) (?:joint ventures|associates|related parti)",
        r"trade liabilities? to",
        r"affiliate liabilities",
        r"\bPAYABLES_RP[: ]*Y\b",
    ],
    "LOANS_TO_RP": [
        r"loans? (?:granted )?to (?:joint ventures|associates|related parti|non-consolidated)",
        r"loans? to (?:joint ventures|associates|non-consolidated)",
        r"advances? to (?:joint ventures|associates|related)",
        r"loan receivable",
        r"\bLOANS_TO_RP[: ]*Y\b",
    ],
    "LOANS_FROM_RP": [
        r"loans? from (?:related parties|joint ventures|associates|shareholders?)",
        r"borrowings? from (?:related|shareholders?)",
        r"financial liabilit(?:y|ies) to .*(?:Pensionskasse|Pension Trust|shareholder)",
        r"shareholder loans? (?:granted|received|to)",
        r"\bLOANS_FROM_RP[: ]*Y\b",
    ],
    "GUARANTEES": [
        r"guarantees? (?:given|provided|received|to) ",
        r"counter-guarantee",
        r"\bBürgschaft",
        r"unutilised credit lines",
        r"contingent liabilit.*guarantee",
        r"\bGUARANTEES[: ]*Y\b",
    ],
    "KMP_COMPENSATION": [
        r"key management personnel",
        r"\bKMP\b",
        r"compensation of (?:the )?(?:management|executive|managing) board",
        r"remuneration of (?:the )?(?:management|executive|managing|supervisory) board",
        r"\bKMP_COMPENSATION[: ]*Y\b",
    ],
    "PENSION_RELATED": [
        r"pension trust",
        r"Pensionskasse",
        r"post-employment",
        r"contractual trust arrangement",
        r"\bCTA\b",
        r"pension fund (?:as|treated as) (?:a )?related",
        r"\bPENSION_RELATED[: ]*Y\b",
    ],
    "LEASES_RP": [
        r"lease (?:payment|liability|liabilities)",
        r"rent (?:payment|paid)",
        r"sale[- ]and[- ]leaseback",
        r"master lease agreement",
        r"office .*(?:rent|leas)",
        r"Mietzahlung",
        r"\bLEASES_RP[: ]*Y\b",
    ],
    "DIVIDENDS_RP": [
        r"dividends? (?:paid|distributed) to ",
        r"dividends? (?:received|from) (?:associates|joint ventures|equity-method|the (?:foundation|Stiftung))",
        r"dividend income (?:from )?(?:associates|equity-method|RBI|core shareholders?)",
        r"dividend(?:s)? .*(?:Stiftung|foundation|Republic of|ÖBAG|KfW|Bajaj|Bestseller|family pool)",
        r"\bDIVIDENDS_RP[: ]*Y\b",
    ],
    "SHAREHOLDER_LOANS": [
        r"shareholder loans?",
        r"loans? (?:to|from) (?:the )?(?:parent|controlling shareholder|principal shareholder|major shareholder)",
        r"intragroup loans?",
        r"intra[- ]group financing",
        r"cash pooling with (?:VW|parent|Mercedes|Siemens)",
        r"Bajaj.*(?:funding|loan)",
        r"\bSHAREHOLDER_LOANS[: ]*Y\b",
    ],
    "JV_ASSOC_TRANSACTIONS": [
        r"joint ventures?",
        r"associates? (?:as (?:a )?related|disclosed)",
        r"equity[- ]method",
        r"equity[- ]accounted",
        r"\bJV_ASSOC_TRANSACTIONS[: ]*Y\b",
    ],
    "SUBSIDIARY_NONCONSOL": [
        r"non[- ]consolidated subsidiaries",
        r"unconsolidated subsidiaries",
        r"non[- ]consolidated affiliated",
        r"\bSUBSIDIARY_NONCONSOL[: ]*Y\b",
    ],
    "CASH_POOLING": [
        r"cash[- ]pool",
        r"in[- ]house bank",
        r"group treasury .*pool",
        r"\bCASH_POOLING[: ]*Y\b",
    ],
    "SLA_SHARED_SERVICES": [
        r"shared services",
        r"service[- ]level agreement",
        r"\bSLA\b",
        r"management services .*(?:provided|received) (?:to|from) ",
        r"IT services? (?:to|from|provided to) (?:joint ventures|associates|Tchibo|Mercedes|Siemens|parent|group)",
        r"central(?:ly provided)? .*support services",
        r"global business services",
        r"\bSLA_SHARED_SERVICES[: ]*Y\b",
    ],
    "LICENSE_ROYALTY": [
        r"royalt(?:y|ies)",
        r"license fees? (?:to|from)",
        r"licensing (?:agreement|to) (?:joint ventures|associates|related)",
        r"trademark (?:license|fee)",
        r"technology licenses? to",
        r"\bLICENSE_ROYALTY[: ]*Y\b",
    ],
    "FOUNDATION_CHARITY": [
        r"Privatstiftung",
        r"\bStiftung\b",
        r"foundation .*(?:related|controlling|principal shareholder)",
        r"adidas Stiftung",
        r"Siemens Stiftung",
        r"ERSTE Foundation",
        r"\bFOUNDATION_CHARITY[: ]*Y\b",
    ],
    "REAL_ESTATE_RP": [
        r"real estate .*(?:related|Pension Trust|Privatstiftung|Stiftung|JV|joint venture|associate)",
        r"property .*(?:from|to) (?:related|joint venture|associate|foundation|Privatstiftung)",
        r"office .*(?:rented|leased) from (?:related|Pension Trust|Tchibo|joint venture)",
        r"Haas[- ]Haus",
        r"\bREAL_ESTATE_RP[: ]*Y\b",
    ],
    "MA_RP": [
        r"(?:stake|share) sale to .*(?:joint venture|associate|related|parent)",
        r"acquisition of .*(?:from )?(?:joint venture|associate|related|parent)",
        r"divestment .*(?:to|from) (?:related|parent|associate)",
        r"sale .*to .*(?:Siemens AG|Mercedes-Benz Group|VW AG|Bajaj|parent)",
        r"transfer of .*from .*Mubadala|ADNOC",
        r"\bMA_RP[: ]*Y\b",
    ],
}


COUNTRY = {"ATX": "Austria", "DAX": "Germany"}


def classify(text: str) -> dict[str, bool]:
    hits: dict[str, bool] = {}
    for cat, patterns in PATTERNS.items():
        hit = False
        # Negative override: explicit "X: N" tag from an agent-style summary.
        if re.search(rf"\b{cat}[: ]*N\b", text):
            # Still allow positive override if the agent contradicts with Y elsewhere
            for p in patterns:
                if re.search(p, text, flags=re.IGNORECASE):
                    hit = True
                    break
            # If only N tag and no other evidence, keep N
            if not hit:
                hits[cat] = False
                continue
        for p in patterns:
            if re.search(p, text, flags=re.IGNORECASE):
                hit = True
                break
        hits[cat] = hit
    return hits


def auditor_of(text: str) -> str:
    text_lower = text.lower()
    candidates = [
        ("KPMG", "KPMG"),
        ("PricewaterhouseCoopers", "PwC"),
        ("PwC", "PwC"),
        ("Deloitte", "Deloitte"),
        ("Ernst & Young", "EY"),
        ("EY ", "EY"),
        ("\bEY\b", "EY"),
        ("BDO", "BDO"),
        ("Mazars", "Mazars"),
        ("Grant Thornton", "Grant Thornton"),
        ("Sparkassen-Prüfungsverband", "Sparkassen-Prüfungsverband"),
    ]
    # Look in the **Auditor:** line first
    m = re.search(r"\*\*Auditor:\*\*\s*([^\n]+)", text)
    section = m.group(1) if m else text[:3000]
    for key, label in candidates:
        if re.search(key, section, flags=re.IGNORECASE):
            return label
    return "Unknown"


def arms_length(text: str) -> bool:
    return bool(
        re.search(
            r"arm['’]s[- ]length|at arm['’]s length|on arm['’]s length|normal market conditions|customary market conditions|standard market|"
            r"market terms|usual market conditions",
            text,
            flags=re.IGNORECASE,
        )
    )


def main() -> None:
    rows: list[dict] = []
    for slug, name, index in COMPANIES:
        path = DISCLOSURES / f"{slug}.md"
        if not path.exists():
            print(f"MISSING: {slug}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        flags = classify(text)
        rows.append(
            {
                "id": slug.split("_")[0],
                "company": name,
                "index": index,
                "country": COUNTRY[index],
                "auditor": auditor_of(text),
                "arms_length_stmt": arms_length(text),
                **flags,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "category_matrix.csv", index=False)

    # ---------- Aggregate statistics ----------
    cat_cols = list(PATTERNS.keys())

    overall = df[cat_cols].mean().sort_values(ascending=False) * 100
    by_index = df.groupby("index")[cat_cols].mean() * 100
    by_index_t = by_index.T
    by_index_t["delta_DAX_minus_ATX"] = by_index_t["DAX"] - by_index_t["ATX"]
    by_index_t = by_index_t.sort_values("delta_DAX_minus_ATX", ascending=False)

    auditor_counts = df["auditor"].value_counts()
    by_auditor_index = df.groupby(["index", "auditor"]).size().unstack(fill_value=0)
    arm_count = df["arms_length_stmt"].sum()

    # ---------- Tables ----------
    overall_md = overall.round(1).to_frame("freq_%_n60").to_markdown()
    by_index_md = by_index_t.round(1).to_markdown()
    auditor_md = auditor_counts.to_frame("companies").to_markdown()
    by_audit_idx_md = by_auditor_index.to_markdown()

    company_breadth = df[cat_cols].sum(axis=1)
    df_b = df.assign(categories_disclosed=company_breadth)
    breadth_table = (
        df_b[["id", "company", "index", "categories_disclosed"]]
        .sort_values(["index", "categories_disclosed"], ascending=[True, False])
        .to_markdown(index=False)
    )

    # ---------- Plots ----------
    plt.rcParams["figure.dpi"] = 110
    plt.rcParams["axes.titlesize"] = 11
    plt.rcParams["axes.labelsize"] = 9

    # 1. Overall frequency bar
    fig, ax = plt.subplots(figsize=(10, 7))
    overall.sort_values().plot(kind="barh", ax=ax, color="#3a6ea5")
    ax.set_xlabel("Disclosure frequency (% of 60 companies)")
    ax.set_title("Frequency of RPT disclosure categories — ATX 20 + DAX 40, FY2024")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    for i, v in enumerate(overall.sort_values()):
        ax.text(v + 0.7, i, f"{v:.0f}%", va="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT / "fig_overall_frequency.png")
    plt.close(fig)

    # 2. ATX vs DAX side-by-side
    fig, ax = plt.subplots(figsize=(11, 7))
    plot_df = by_index_t[["ATX", "DAX"]].sort_values("DAX")
    plot_df.plot(kind="barh", ax=ax, color=["#d97706", "#1f4e79"])
    ax.set_xlabel("Disclosure frequency (% within index)")
    ax.set_title("ATX (20) vs DAX (40) — RPT category disclosure frequency, FY2024")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(OUT / "fig_atx_vs_dax.png")
    plt.close(fig)

    # 3. Heatmap of company × category
    cat_short = [c.replace("_RP", "").replace("_FROM", "").replace("_TO", "") for c in cat_cols]
    matrix = df.set_index(["index", "company"])[cat_cols].astype(int)
    matrix = matrix.sort_index(level=0)
    fig, ax = plt.subplots(figsize=(13, 14))
    im = ax.imshow(matrix.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(cat_cols)))
    ax.set_xticklabels(cat_short, rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(matrix)))
    ax.set_yticklabels([f"[{ix}] {c}" for ix, c in matrix.index], fontsize=7)
    ax.set_title("RPT disclosure heatmap (1 = category disclosed)", fontsize=12)
    # gridlines between ATX/DAX
    atx_n = sum(1 for r in matrix.index if r[0] == "ATX")
    ax.axhline(atx_n - 0.5, color="red", linewidth=1.5)
    plt.tight_layout()
    plt.savefig(OUT / "fig_heatmap.png")
    plt.close(fig)

    # 4. Auditor distribution
    fig, ax = plt.subplots(figsize=(8, 4.5))
    auditor_counts.plot(kind="bar", ax=ax, color="#2e7d32")
    ax.set_ylabel("Companies (of 60)")
    ax.set_title("FY2024 Group Auditor — ATX + DAX")
    for i, v in enumerate(auditor_counts):
        ax.text(i, v + 0.2, str(v), ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT / "fig_auditor_distribution.png")
    plt.close(fig)

    # ---------- Findings summary ----------
    findings: list[str] = []
    findings.append(
        f"Population: {len(df)} companies (ATX = {(df['index']=='ATX').sum()}, DAX = {(df['index']=='DAX').sum()})."
    )
    findings.append(
        f"Companies with explicit arm's-length / market-conditions statement: "
        f"{arm_count} / {len(df)} ({arm_count/len(df)*100:.0f}%)."
    )
    top5 = overall.head(5)
    findings.append("Most frequently disclosed categories (n=60):")
    for cat, v in top5.items():
        findings.append(f"  - {cat}: {v:.0f}%")
    bot5 = overall.tail(5)
    findings.append("Least frequently disclosed categories:")
    for cat, v in bot5.items():
        findings.append(f"  - {cat}: {v:.0f}%")

    biggest_diff = by_index_t.head(3)
    findings.append("Categories where DAX disclosure exceeds ATX the most (pp):")
    for cat in biggest_diff.index:
        findings.append(
            f"  - {cat}: DAX {biggest_diff.loc[cat, 'DAX']:.0f}% vs ATX {biggest_diff.loc[cat, 'ATX']:.0f}%"
            f"  (Δ {biggest_diff.loc[cat, 'delta_DAX_minus_ATX']:+.0f}pp)"
        )
    atx_lead = by_index_t.tail(3).iloc[::-1]
    findings.append("Categories where ATX disclosure exceeds DAX the most (pp):")
    for cat in atx_lead.index:
        findings.append(
            f"  - {cat}: ATX {atx_lead.loc[cat, 'ATX']:.0f}% vs DAX {atx_lead.loc[cat, 'DAX']:.0f}%"
            f"  (Δ {atx_lead.loc[cat, 'delta_DAX_minus_ATX']:+.0f}pp)"
        )

    findings.append(
        f"Average category breadth (categories disclosed per company): "
        f"{company_breadth.mean():.1f} of {len(cat_cols)} ({company_breadth.mean()/len(cat_cols)*100:.0f}%)."
    )
    findings.append(
        f"  ATX mean: {df_b[df_b['index']=='ATX']['categories_disclosed'].mean():.1f}; "
        f"DAX mean: {df_b[df_b['index']=='DAX']['categories_disclosed'].mean():.1f}."
    )

    findings.append("Auditor concentration (Group auditor identified):")
    for a, n in auditor_counts.items():
        findings.append(f"  - {a}: {n} ({n/len(df)*100:.0f}%)")

    findings_text = "\n".join(findings)

    # Persist
    (OUT / "findings.txt").write_text(findings_text, encoding="utf-8")
    (OUT / "overall_frequency.md").write_text(
        "# Overall disclosure frequency (n=60)\n\n" + overall_md, encoding="utf-8"
    )
    (OUT / "atx_vs_dax.md").write_text(
        "# ATX vs DAX disclosure frequency (within-index %)\n\n" + by_index_md, encoding="utf-8"
    )
    (OUT / "auditor_counts.md").write_text(
        "# Group auditor — counts (n=60)\n\n" + auditor_md
        + "\n\n## By index\n\n" + by_audit_idx_md,
        encoding="utf-8",
    )
    (OUT / "company_breadth.md").write_text(
        "# Categories disclosed per company (out of 20)\n\n" + breadth_table, encoding="utf-8"
    )

    print(findings_text)


if __name__ == "__main__":
    main()
