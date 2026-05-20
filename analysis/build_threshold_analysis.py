"""Threshold analysis — manually curated from the per-company agent reports.

Each row carries: BS (Bilanzsumme EUR m, FY2024), U (Umsatz / Operating Income / Prämien EUR m),
binding threshold (EUR m), largest disclosed RPT (EUR m), the SRD II exemption that applies,
and the count of § 95c (AT) / § 111c (DE) website notifications observed for calendar 2024.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

OUT = Path("/home/user/RPT/analysis")
OUT.mkdir(exist_ok=True)


# Hand-curated from the 60 per-company threshold files in /disclosures/thresholds/
# Columns:
#   id, company, index, bs_eurm, u_eurm (rev/OI/premium), binding_thr_eurm,
#   largest_rpt_eurm, exemption_applies (None/CONSOL/PRO_RATA_DIV/ORDINARY/LEGACY/HYBRID),
#   notices_2024
DATA = [
    # ----- ATX (binding threshold = MIN(5% BS, 2.5% U)) -----
    ("01", "Andritz",                   "ATX",     8163,    8314,  208,    14,      None,           0),
    ("02", "AT&S",                      "ATX",     4622,    1590,   40,     1,      None,           0),
    ("03", "BAWAG Group",               "ATX",    72300,    1628,   41,    35,      None,           0),  # OI proxy
    ("04", "CA Immobilien Anlagen",     "ATX",     6029,     239,    6,    60.5,    "PRO_RATA_DIV", 0),
    ("05", "DO & CO",                   "ATX",     1279,    2298,   57,     1,      None,           0),
    ("06", "Erste Group Bank",          "ATX",   353700,   11178,  279,   350,      "PRO_RATA_DIV", 0),  # OI proxy
    ("07", "EVN",                       "ATX",    10914,    3257,   81,   182,      "PRO_RATA_DIV", 0),  # Verbund associate-div
    ("08", "Lenzing",                   "ATX",     4977,    2663,   67,    30,      None,           0),
    ("09", "Mayr-Melnhof Karton",       "ATX",     4863,    4080,  102,    10,      None,           0),
    ("10", "OMV",                       "ATX",    45517,   33981,  850,  1228,      "ORDINARY",     0),  # Borouge 4 ECA guarantee
    ("11", "Österreichische Post",      "ATX",     6500,    3123,   78,    65,      None,           0),
    ("12", "PIERER Mobility",           "ATX",      950,    1873,   47,   372,      "POST_DECONS",  0),  # KTM AG receivable after Nov 2024 deconsolidation
    ("13", "Raiffeisen Bank Int.",      "ATX",   199900,    6400,  160,   100,      None,           0),  # OI proxy
    ("14", "Schoeller-Bleckmann",       "ATX",      986,     560,   14,     5.3,    None,           0),
    ("15", "Telekom Austria",           "ATX",     9854,    5410,  135,   243,      "ORDINARY",     0),  # ETS lease, master lease at arm's length
    ("16", "UNIQA Insurance Group",     "ATX",    28532,    7840,  196,   215,      "CONSOL",       0),  # UNIQA Re intragroup loan
    ("17", "Verbund",                   "ATX",    18718,    8225,  206,   682,      "PRO_RATA_DIV", 0),
    ("18", "Vienna Insurance Group",    "ATX",    56800,   14740,  368,   150,      None,           0),
    ("19", "voestalpine",               "ATX",    15734,   15744,  394,   192,      None,           0),
    ("20", "Wienerberger",              "ATX",     6380,    4513,  113,    21,      None,           0),

    # ----- DAX (threshold = 1.5% Bilanzsumme; uniform for all DE issuers) -----
    ("21", "Adidas",                    "DAX",    20655,   None,    310,   106,     None,           0),
    ("22", "Airbus (NL hybrid)",        "DAX",   129213,   None,   1938,   104,     None,           0),  # 1.5% proxy
    ("23", "Allianz",                   "DAX",  1130338,   None,  16955,    12,     None,           0),
    ("24", "BASF",                      "DAX",    80415,   None,   1206,  2943,     "ORDINARY",     0),  # JV multi-year purchase obligations
    ("25", "Bayer",                     "DAX",   110850,   None,   1663,    50,     None,           0),
    ("26", "Beiersdorf",                "DAX",    13011,   None,    195,    13,     None,           0),
    ("27", "BMW",                       "DAX",   267732,   None,   4016,   200,     None,           0),
    ("28", "Brenntag",                  "DAX",    11668,   None,    175,    13,     None,           0),
    ("29", "Commerzbank",               "DAX",   555000,   None,   8325,   100,     None,           0),
    ("30", "Continental",               "DAX",    36966,   None,    555,   300,     None,           0),
    ("31", "Daimler Truck",             "DAX",    73854,   None,   1108,   580,     "PRO_RATA_DIV", 0),
    ("32", "Deutsche Bank",             "DAX",  1395000,   None,  20925,    77,     None,           0),
    ("33", "Deutsche Börse",            "DAX",   232000,   None,   3480,    10,     None,           0),
    ("34", "DHL Group",                 "DAX",    72700,   None,   1091,   380,     "PRO_RATA_DIV", 0),  # KfW pro-rata
    ("35", "Deutsche Telekom",          "DAX",   304900,   None,   4574,  4600,     "LEGACY",       0),  # GD Tower lease stock balance, not new transaction
    ("36", "E.ON",                      "DAX",   111361,   None,   1670,   200,     None,           0),
    ("37", "Fresenius SE",              "DAX",    43550,   None,    653,   452,     None,           0),
    ("38", "Fresenius Medical Care",    "DAX",    33567,   None,    504,   200,     None,           0),
    ("39", "Hannover Rück",             "DAX",    87700,   None,   1315,   424,     "PRO_RATA_DIV", 0),
    ("40", "Heidelberg Materials",      "DAX",    37302,   None,    559,   157,     "PRO_RATA_DIV", 0),
    ("41", "Henkel",                    "DAX",    35250,   None,    529,   297,     "PRO_RATA_DIV", 0),
    ("42", "Infineon Technologies",     "DAX",    27978,   None,    420,   500,     "ORDINARY",     0),  # ESMC JV multi-year capital tranches
    ("43", "Mercedes-Benz Group",       "DAX",   260000,   None,   3900,   189,     None,           0),
    ("44", "Merck KGaA",                "DAX",    51567,   None,    774,   990,     "LEGACY",       0),  # E. Merck KG legacy financial liability
    ("45", "MTU Aero Engines",          "DAX",    12497,   None,    187,   150,     None,           0),
    ("46", "Munich Re",                 "DAX",   300000,   None,   4500,    35,     None,           0),
    ("47", "Porsche AG",                "DAX",    60500,   None,    908,  2062,     "CONSOL",       0),  # VW cash pool intragroup
    ("48", "Porsche SE",                "DAX",    42841,   None,    643,  1400,     "PRO_RATA_DIV", 0),  # VW dividend received pro-rata
    ("49", "Qiagen (NL hybrid)",        "DAX",     5477,   None,     82,     4,     None,           0),  # 1.5% proxy
    ("50", "Rheinmetall",               "DAX",    14344,   None,    215,   150,     None,           0),
    ("51", "RWE",                       "DAX",    91860,   None,   1378,    15,     None,           0),
    ("52", "SAP",                       "DAX",    75700,   None,   1136,    80,     None,           0),
    ("53", "Sartorius",                 "DAX",     9717,   None,    146,    10,     None,           0),
    ("54", "Siemens",                   "DAX",   147812,   None,   2217,   400,     None,           0),
    ("55", "Siemens Energy",            "DAX",    56058,   None,    841,  2081,     None,           1),  # India stake sale — 1 § 111c notice in FY (Dec 2023)
    ("56", "Siemens Healthineers",      "DAX",    46055,   None,    691,  1500,     "CONSOL",       0),  # Siemens Treasury intercompany
    ("57", "Symrise",                   "DAX",     8325,   None,    125,     3,     None,           0),
    ("58", "Volkswagen",                "DAX",   624000,   None,   9360, 11941,     "ORDINARY",     0),  # JV loans to FAW/SAIC/JAC
    ("59", "Vonovia",                   "DAX",    90236,   None,   1354,   522,     None,           0),
    ("60", "Zalando",                   "DAX",     7984,   None,    120,   122,     "ORDINARY",     0),  # Bestseller purchases ordinary supplier flow
]


def main() -> None:
    df = pd.DataFrame(
        DATA,
        columns=[
            "id", "company", "index", "bs_eurm", "u_eurm",
            "binding_thr_eurm", "largest_rpt_eurm", "exemption", "notices_2024",
        ],
    )
    df["exceeds_numerically"] = df["largest_rpt_eurm"] > df["binding_thr_eurm"]
    df["cushion_x"] = df["largest_rpt_eurm"] / df["binding_thr_eurm"]
    df.to_csv(OUT / "threshold_matrix.csv", index=False)

    # ============== Findings ==============
    findings: list[str] = []
    findings.append("Population: ATX 20, DAX 40, n=60.")
    total_notices = int(df["notices_2024"].sum())
    findings.append(f"Sum of § 95c (AT) / § 111c (DE) notices in calendar year 2024: {total_notices}.")
    findings.append("  → The Siemens Energy notice (India stake sale to Siemens AG) was dated 8 Dec 2023, "
                    "i.e. inside FY2023/24 but BEFORE calendar 2024. Calendar-year 2024 publications = 0 across all 60.")

    atx = df[df["index"] == "ATX"]
    dax = df[df["index"] == "DAX"]
    findings.append("")
    findings.append("Absolute binding threshold (EUR m):")
    findings.append(f"  ATX (5% BS or 2.5% U, lower binds): "
                    f"min {atx['binding_thr_eurm'].min():.0f}, "
                    f"25th {atx['binding_thr_eurm'].quantile(0.25):.0f}, "
                    f"median {atx['binding_thr_eurm'].median():.0f}, "
                    f"75th {atx['binding_thr_eurm'].quantile(0.75):.0f}, "
                    f"max {atx['binding_thr_eurm'].max():.0f}.")
    findings.append(f"  DAX (1.5% Bilanzsumme): "
                    f"min {dax['binding_thr_eurm'].min():.0f}, "
                    f"25th {dax['binding_thr_eurm'].quantile(0.25):.0f}, "
                    f"median {dax['binding_thr_eurm'].median():.0f}, "
                    f"75th {dax['binding_thr_eurm'].quantile(0.75):.0f}, "
                    f"max {dax['binding_thr_eurm'].max():.0f}.")
    findings.append(f"  Ratio of medians DAX / ATX = "
                    f"{dax['binding_thr_eurm'].median() / atx['binding_thr_eurm'].median():.1f}x.")
    findings.append("")
    findings.append("Companies whose largest *disclosed* RPT line item exceeds the binding threshold "
                    "(numerically, before applying SRD II exemptions):")
    exceeds = df[df["exceeds_numerically"]].sort_values("cushion_x", ascending=False)
    findings.append(f"  Total: {len(exceeds)} of 60 ({len(exceeds)/60*100:.0f}%) — "
                    f"ATX {(exceeds['index']=='ATX').sum()} / 20, "
                    f"DAX {(exceeds['index']=='DAX').sum()} / 40.")
    for _, r in exceeds.iterrows():
        ex = r["exemption"] if r["exemption"] else "—"
        findings.append(f"   {r['company']:35s} ({r['index']}): largest RPT EUR {r['largest_rpt_eurm']:6.0f} m vs "
                        f"threshold EUR {r['binding_thr_eurm']:5.0f} m → {r['cushion_x']:4.1f}x · Ausnahme: {ex}")

    # Exemption table
    findings.append("")
    findings.append("Distribution of applicable exemptions (only for the n_exceeds cases above):")
    ex_counts = exceeds["exemption"].fillna("(keine erkennbare)").value_counts()
    for k, v in ex_counts.items():
        findings.append(f"   {k}: {v}")

    findings_text = "\n".join(findings)
    (OUT / "threshold_findings.txt").write_text(findings_text, encoding="utf-8")
    print(findings_text)

    # ============== Plots ==============
    plt.rcParams["figure.dpi"] = 110

    # Fig 1: Boxplot of absolute thresholds
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(
        [atx["binding_thr_eurm"].values, dax["binding_thr_eurm"].values],
        tick_labels=["ATX (n=20)\nmin(5% BS, 2.5% U)", "DAX (n=40)\n1.5% × Bilanzsumme"],
        widths=0.5, patch_artist=True,
        boxprops=dict(facecolor="#cfe2f3"),
    )
    ax.set_yscale("log")
    ax.set_ylabel("Absolute Schwellenwert (EUR Mio., log-Skala)")
    ax.set_title("SRD-II-Wesentlichkeitsschwelle in absoluten Beträgen — ATX vs DAX, FY2024")
    for i, sub in enumerate([atx, dax], 1):
        ax.scatter([i] * len(sub), sub["binding_thr_eurm"], alpha=0.5,
                   color="#d97706" if i == 1 else "#1f4e79")
    ax.grid(axis="y", which="both", linestyle="--", alpha=0.4)
    ax.annotate(f"Median EUR {atx['binding_thr_eurm'].median():.0f} m",
                (1, atx['binding_thr_eurm'].median()),
                xytext=(1.15, atx['binding_thr_eurm'].median() * 1.5),
                fontsize=10, color="#d97706", weight="bold")
    ax.annotate(f"Median EUR {dax['binding_thr_eurm'].median():.0f} m",
                (2, dax['binding_thr_eurm'].median()),
                xytext=(2.15, dax['binding_thr_eurm'].median() * 1.5),
                fontsize=10, color="#1f4e79", weight="bold")
    plt.tight_layout()
    plt.savefig(OUT / "fig_threshold_boxplot.png")
    plt.close(fig)

    # Fig 2: Scatter — largest RPT vs threshold, log-log
    fig, ax = plt.subplots(figsize=(11, 8))
    for idx, color in [("ATX", "#d97706"), ("DAX", "#1f4e79")]:
        sub = df[df["index"] == idx]
        ax.scatter(sub["binding_thr_eurm"], sub["largest_rpt_eurm"],
                   c=color, label=f"{idx} (n={len(sub)})", alpha=0.75, s=70, edgecolor="white")
        # label the ones above the diagonal
        for _, r in sub.iterrows():
            if r["exceeds_numerically"]:
                ax.annotate(r["company"][:16], (r["binding_thr_eurm"], r["largest_rpt_eurm"]),
                            fontsize=8, alpha=0.85, xytext=(4, 3), textcoords="offset points")
    lims = [1, 30000]
    ax.plot(lims, lims, color="grey", linewidth=1.2, linestyle="--",
            label="Diagonale: RPT = Schwelle")
    # Shade the area above the diagonal
    ax.fill_between(lims, lims, [lims[1]] * 2, color="red", alpha=0.05)
    ax.text(2, 15000, "RPT > Schwelle\n(nominell; Ausnahmen prüfen)",
            fontsize=10, color="darkred", alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_xlabel("Bindende SRD-II-Schwelle (EUR Mio., log)")
    ax.set_ylabel("Größte offengelegte RPT-Einzelposition (EUR Mio., log)")
    ax.set_title("Größte offengelegte RPT-Einzelposition vs SRD-II-Schwelle — ATX + DAX, FY2024")
    ax.grid(True, which="both", linestyle="--", alpha=0.3)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(OUT / "fig_threshold_scatter.png")
    plt.close(fig)

    # Fig 3: Histogram of "cushion factors" (largest RPT / threshold), log scale
    fig, ax = plt.subplots(figsize=(10, 5.5))
    df_pos = df[df["cushion_x"] > 0].copy()
    bins = [0.001, 0.01, 0.1, 0.3, 1.0, 2.0, 5.0, 10.0, 30.0]
    ax.hist([df_pos[df_pos["index"]=="ATX"]["cushion_x"],
             df_pos[df_pos["index"]=="DAX"]["cushion_x"]],
            bins=bins, label=["ATX", "DAX"],
            color=["#d97706", "#1f4e79"], stacked=False)
    ax.axvline(1.0, color="grey", linestyle="--", label="Schwelle")
    ax.set_xscale("log")
    ax.set_xlabel("Größter RPT / Schwelle (log)")
    ax.set_ylabel("Anzahl Emittenten")
    ax.set_title("Distanz zwischen größter offengelegter RPT und SRD-II-Schwelle (FY2024)")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(OUT / "fig_cushion_histogram.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
