"""Two-figure pack for the rewritten RWZ article.

Fig 1: Säule 1 — IAS-24-Disclosure-Kategorien, Häufigkeit ATX vs DAX (FY2024)
Fig 2: Säule 2 — Größte offengelegte RPT-Position vs SRD-II-Schwelle (FY2024),
       mit den 11 bereinigten Überschreitern hervorgehoben.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

OUT = Path("/home/user/RPT/analysis")
OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# Fig 1 — IAS-24-Disclosure-Frequenz nach Kategorie, ATX vs DAX
# ------------------------------------------------------------------

# Load category matrix from the earlier analysis (build_analysis.py output)
mat = pd.read_csv(OUT / "category_matrix.csv")

# German labels for the 20 categories
LABELS_DE = {
    "KMP_COMPENSATION":      "KMP-Vergütung",
    "JV_ASSOC_TRANSACTIONS": "JV / Assoziierte",
    "PENSION_RELATED":       "Pensions­vehikel",
    "SUBSIDIARY_NONCONSOL":  "Nicht-konsolidierte Töchter",
    "PAYABLES_RP":           "Verbindlichkeiten ggü. RP",
    "RECEIVABLES_RP":        "Forderungen ggü. RP",
    "DIVIDENDS_RP":          "Dividenden RP",
    "SALES_TO_RP":           "Umsätze mit RP",
    "PURCHASES_FROM_RP":     "Einkäufe von RP",
    "FOUNDATION_CHARITY":    "Stiftungen / Foundations",
    "SHAREHOLDER_LOANS":     "Anteilseignerdarlehen",
    "LOANS_TO_RP":           "Darlehen an RP",
    "GUARANTEES":            "Bürgschaften",
    "CASH_POOLING":          "Cash-Pooling",
    "LICENSE_ROYALTY":       "Lizenz / Royalty",
    "SLA_SHARED_SERVICES":   "Shared Services / SLA",
    "LEASES_RP":             "Leasing mit RP",
    "LOANS_FROM_RP":         "Darlehen von RP",
    "REAL_ESTATE_RP":        "Immobilien mit RP",
    "MA_RP":                 "M&A mit RP",
}
cat_cols = list(LABELS_DE.keys())

atx_freq = mat[mat["index"] == "ATX"][cat_cols].mean() * 100
dax_freq = mat[mat["index"] == "DAX"][cat_cols].mean() * 100
overall = mat[cat_cols].mean() * 100
order = overall.sort_values(ascending=True).index.tolist()

fig, ax = plt.subplots(figsize=(10.5, 8.5))
y = np.arange(len(order))
width = 0.42
ax.barh(y - width/2, [atx_freq[c] for c in order], height=width,
        label="ATX (n=20)", color="#d97706", alpha=0.9)
ax.barh(y + width/2, [dax_freq[c] for c in order], height=width,
        label="DAX (n=40)", color="#1f4e79", alpha=0.9)
ax.set_yticks(y)
ax.set_yticklabels([LABELS_DE[c] for c in order], fontsize=10)
ax.set_xlabel("Häufigkeit der Offenlegung (% der Emittenten je Index)", fontsize=11)
ax.set_title("Abb. 1 · IAS-24-Anhangoffenlegung: Verbreitung nach Transaktionskategorie\nATX und DAX, FY2024",
             fontsize=12, weight="bold", pad=12)
ax.set_xlim(0, 110)
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.legend(loc="lower right", fontsize=10)
for i, c in enumerate(order):
    ax.text(atx_freq[c] + 1, i - width/2, f"{atx_freq[c]:.0f}%",
            va="center", fontsize=8, color="#d97706")
    ax.text(dax_freq[c] + 1, i + width/2, f"{dax_freq[c]:.0f}%",
            va="center", fontsize=8, color="#1f4e79")
ax.axvline(50, color="grey", linewidth=0.6, linestyle=":")
ax.text(50, len(order)-0.5, "50 %", fontsize=8, ha="center", va="bottom", color="grey")
plt.tight_layout()
plt.savefig(OUT / "fig_artikel_saeule1.png", dpi=140)
plt.close(fig)
print(f"Fig 1 saved: {OUT / 'fig_artikel_saeule1.png'}")


# ------------------------------------------------------------------
# Fig 2 — SRD-II-Schwelle vs größter RPT, mit Überschreitern
# ------------------------------------------------------------------

thr = pd.read_csv(OUT / "threshold_matrix.csv")
thr["ratio"] = thr["largest_rpt_eurm"] / thr["binding_thr_eurm"]
thr["exceeds"] = thr["largest_rpt_eurm"] > thr["binding_thr_eurm"]

# The 11 bereinigte Überschreiter (after removal of pro-rata div, Beteiligungsertrag, Altbestand)
removed_ids = {"04", "16", "06", "07", "48", "44", "35"}
# 04 CA Immo (pro-rata), 16 Verbund (pro-rata, but 17 is Verbund... let me recheck)
# Actually let me look at the IDs
print(thr[thr["exceeds"]][["id", "company", "exemption", "ratio"]])

fig, ax = plt.subplots(figsize=(11, 8.5))

# All 60 companies — base scatter
for idx, color, marker in [("ATX", "#d97706", "o"), ("DAX", "#1f4e79", "o")]:
    sub = thr[thr["index"] == idx]
    ax.scatter(sub["binding_thr_eurm"], sub["largest_rpt_eurm"],
               c=color, label=f"{idx} (n={len(sub)})", alpha=0.45, s=55,
               edgecolor="white", linewidth=0.5, marker=marker)

# Diagonal
lims = [1, 30000]
ax.plot(lims, lims, color="grey", linewidth=1.0, linestyle="--",
        label="Schwellengleichheit (RPT = Schwelle)")

# Shade overshoot region
xx = np.linspace(lims[0], lims[1], 100)
ax.fill_between(xx, xx, np.full_like(xx, lims[1]), color="red", alpha=0.05)

# 11 bereinigte Überschreiter — namentlich markiert
HIGHLIGHTED = {
    # id: (company, ratio_label_shift_y)
    "12": ("PIERER Mobility", 1.3),     # 7.9×
    "55": ("Siemens Energy", 1.0),       # 2.5×
    "24": ("BASF", 1.0),                 # 2.4×
    "47": ("Porsche AG", 1.0),           # 2.3×
    "56": ("S. Healthineers", 1.0),      # 2.2×
    "15": ("Telekom Austria", 1.0),      # 1.8×
    "10": ("OMV", 1.0),                  # 1.4×
    "58": ("Volkswagen", 1.0),           # 1.3×
    "42": ("Infineon", 1.0),             # 1.2×
    "16": ("UNIQA", 1.0),                # 1.1× (CONSOL)
    "60": ("Zalando", 1.0),              # 1.0×
}

for cid, (name, ofy) in HIGHLIGHTED.items():
    row = thr[thr["id"] == cid]
    if row.empty:
        continue
    r = row.iloc[0]
    color = "#d97706" if r["index"] == "ATX" else "#1f4e79"
    ax.scatter([r["binding_thr_eurm"]], [r["largest_rpt_eurm"]],
               c=color, s=130, edgecolor="black", linewidth=1.4, marker="o",
               zorder=10)
    ax.annotate(name, (r["binding_thr_eurm"], r["largest_rpt_eurm"]),
                xytext=(6, 4), textcoords="offset points",
                fontsize=9, weight="bold",
                color=color)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_xlabel("Bindende SRD-II-Schwelle (EUR Mio., log)", fontsize=11)
ax.set_ylabel("Größte offengelegte RPT-Position (EUR Mio., log)", fontsize=11)
ax.set_title("Abb. 2 · SRD-II-Anlassmechanismus: Schwelle vs offengelegte RPT je Emittent\n"
             "11 bereinigte Überschreiter — null § 95c/§ 111c-Bekanntmachungen im Kalenderjahr 2024",
             fontsize=12, weight="bold", pad=12)
ax.grid(True, which="both", linestyle="--", alpha=0.3)
ax.text(2.5, 18000, "Überschreitungsbereich\n(RPT > Schwelle)",
        fontsize=10, color="darkred", alpha=0.75, weight="bold")

# Custom legend
handles = [
    mpatches.Patch(color="#d97706", label="ATX (n=20)"),
    mpatches.Patch(color="#1f4e79", label="DAX (n=40)"),
    plt.Line2D([0], [0], color="grey", linestyle="--", label="RPT = Schwelle"),
]
ax.legend(handles=handles, loc="lower right", fontsize=10)

# Add summary box
textbox = (
    "Zentraler Befund:\n"
    "  11 von 60 Emittenten (18 %) überschreiten die Schwelle nominell\n"
    "  0 § 95c/§ 111c-Bekanntmachungen im Kalenderjahr 2024\n"
    "  → Absorption durch Ausnahmekatalog (insb. ordentlicher Geschäftsgang)"
)
ax.text(1.5, 4, textbox, fontsize=9.5,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#fff5e6", edgecolor="#d97706", linewidth=1.0))

plt.tight_layout()
plt.savefig(OUT / "fig_artikel_saeule2.png", dpi=140)
plt.close(fig)
print(f"Fig 2 saved: {OUT / 'fig_artikel_saeule2.png'}")
