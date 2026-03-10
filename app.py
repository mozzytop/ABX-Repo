"""
Dynamic Antibiogram & Antimicrobial Stewardship Tool
=====================================================
A Streamlit-based clinical reference tool for US clinical practice.
Covers bacteria, fungi, and viruses with MDR organism focus.

DATA SWAP INSTRUCTIONS:
  - All organism data lives in the `ORGANISM_DATA` list near the top of this file.
  - Each entry is a dict. Add/remove fields freely — the table will adapt.
  - To load from an external source (PostgreSQL, CSV, API), replace the
    `load_data()` function body. Keep the same return type: pd.DataFrame.
  - For EUCAST/CLSI breakpoint integration, fetch from their REST APIs and
    populate the "susceptibility" sub-keys before building the DataFrame.

Requirements: see requirements.txt
Run: streamlit run app.py
"""

import io
import pandas as pd
import streamlit as st
from fpdf import FPDF

# ─────────────────────────────────────────────────────────────────────────────
# 1. MOCK DATASET  (swap this list for a DB call in load_data() later)
# ─────────────────────────────────────────────────────────────────────────────
ORGANISM_DATA = [
    # ── BACTERIA ─────────────────────────────────────────────────────────────
    {
        "Category": "Bacteria",
        "Organism": "Staphylococcus aureus (MSSA)",
        "Gram / Morphology": "Gram+ Cocci",
        "First-Line Therapy": "Nafcillin / Oxacillin",
        "First-Line Dosing (US)": "Nafcillin 2 g IV q4h; Oxacillin 2 g IV q4h",
        "Alternative Therapy": "Cefazolin, Clindamycin",
        "Alternative Dosing": "Cefazolin 2 g IV q8h; Clindamycin 600 mg IV/PO q8h",
        "MDR Therapy": "Vancomycin (PCN allergy)",
        "MDR Dosing": "Vancomycin 25–30 mg/kg IV load, then AUC-guided (target 400–600)",
        "Resistance Mechanisms": "mecA negative (MSSA); beta-lactamase",
        "Key Notes": "Cefazolin preferred for bacteremia; avoid vancomycin if susceptible",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Staphylococcus aureus (HA-MRSA)",
        "Gram / Morphology": "Gram+ Cocci",
        "First-Line Therapy": "Vancomycin",
        "First-Line Dosing (US)": "Vancomycin AUC/MIC-guided (target AUC 400–600 mg·h/L)",
        "Alternative Therapy": "Daptomycin, Linezolid",
        "Alternative Dosing": "Daptomycin 6–10 mg/kg IV q24h; Linezolid 600 mg PO/IV q12h",
        "MDR Therapy": "Ceftaroline, Dalbavancin, Oritavancin",
        "MDR Dosing": "Ceftaroline 600 mg IV q8h; Dalbavancin 1500 mg IV × 1 dose",
        "Resistance Mechanisms": "mecA (PBP2a), VRSA rare (vanA/vanB)",
        "Key Notes": "Do NOT use daptomycin for pneumonia; rifampin only in combination",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Staphylococcus aureus (CA-MRSA)",
        "Gram / Morphology": "Gram+ Cocci",
        "First-Line Therapy": "TMP-SMX / Doxycycline",
        "First-Line Dosing (US)": "TMP-SMX 1–2 DS tabs PO q12h; Doxycycline 100 mg PO q12h",
        "Alternative Therapy": "Clindamycin, Linezolid",
        "Alternative Dosing": "Clindamycin 300–450 mg PO q8h; Linezolid 600 mg PO q12h",
        "MDR Therapy": "Vancomycin (severe/bacteremia)",
        "MDR Dosing": "Vancomycin AUC-guided IV (same as HA-MRSA above)",
        "Resistance Mechanisms": "mecA, PVL toxin (skin/soft tissue virulence)",
        "Key Notes": "PVL-positive strains cause necrotizing pneumonia/skin infections",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Streptococcus pneumoniae",
        "Gram / Morphology": "Gram+ Cocci",
        "First-Line Therapy": "Penicillin G / Amoxicillin",
        "First-Line Dosing (US)": "Penicillin G 3–4 MU IV q4h; Amoxicillin 500–875 mg PO q8h",
        "Alternative Therapy": "Ceftriaxone, Levofloxacin",
        "Alternative Dosing": "Ceftriaxone 2 g IV q24h; Levofloxacin 750 mg PO/IV q24h",
        "MDR Therapy": "Vancomycin + Rifampin (meningitis MDR)",
        "MDR Dosing": "Vancomycin 60 mg/kg/day IV ÷ q6h + Rifampin 600 mg q24h",
        "Resistance Mechanisms": "PBP mutations (PCN-R), ESBL rare, efflux (FQ-R)",
        "Key Notes": "Adjust based on MIC; high-dose PCN overcomes intermediate resistance",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Enterococcus faecalis (susceptible)",
        "Gram / Morphology": "Gram+ Cocci",
        "First-Line Therapy": "Ampicillin ± Gentamicin",
        "First-Line Dosing (US)": "Ampicillin 2 g IV q4h; Gentamicin 1 mg/kg IV q8h (synergy)",
        "Alternative Therapy": "Vancomycin, Linezolid",
        "Alternative Dosing": "Vancomycin AUC-guided IV; Linezolid 600 mg PO/IV q12h",
        "MDR Therapy": "Daptomycin (high-dose 8–12 mg/kg) + Ampicillin",
        "MDR Dosing": "Daptomycin 8–12 mg/kg IV q24h + Ampicillin 2 g IV q4h",
        "Resistance Mechanisms": "Intrinsic low-level AG resistance; high-level AG resistance (HLAR)",
        "Key Notes": "HLAR eliminates synergy; use ceftriaxone + ampicillin for endocarditis",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Enterococcus faecium (VRE)",
        "Gram / Morphology": "Gram+ Cocci",
        "First-Line Therapy": "Linezolid / Daptomycin",
        "First-Line Dosing (US)": "Linezolid 600 mg PO/IV q12h; Daptomycin 8–12 mg/kg IV q24h",
        "Alternative Therapy": "Tedizolid, Oritavancin",
        "Alternative Dosing": "Tedizolid 200 mg PO/IV q24h; Oritavancin 1200 mg IV × 1 dose",
        "MDR Therapy": "Quinupristin-dalfopristin (E. faecium ONLY)",
        "MDR Dosing": "Quinupristin-dalfopristin 7.5 mg/kg IV q8h",
        "Resistance Mechanisms": "vanA / vanB operons; intrinsically resistant to many beta-lactams",
        "Key Notes": "Consult ID; source control critical; linezolid myelosuppression risk >2 wks",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Bacteria",
        "Organism": "Escherichia coli (susceptible)",
        "Gram / Morphology": "Gram- Bacilli (Enteric)",
        "First-Line Therapy": "TMP-SMX / Fluoroquinolone",
        "First-Line Dosing (US)": "TMP-SMX 1 DS PO q12h; Ciprofloxacin 500 mg PO q12h",
        "Alternative Therapy": "Nitrofurantoin (UTI only), Fosfomycin",
        "Alternative Dosing": "Nitrofurantoin 100 mg ER PO q12h × 5d; Fosfomycin 3 g PO × 1",
        "MDR Therapy": "Ceftriaxone (moderate); Pip-Tazo (complicated)",
        "MDR Dosing": "Ceftriaxone 2 g IV q24h; Pip-Tazo 4.5 g IV q6h (ext. infusion)",
        "Resistance Mechanisms": "AmpC, ESBL, fluoroquinolone target mutations (gyrA/parC)",
        "Key Notes": "Always check local antibiogram; resistance rates highly variable",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "E. coli / Klebsiella (ESBL)",
        "Gram / Morphology": "Gram- Bacilli (Enteric)",
        "First-Line Therapy": "Ertapenem / Meropenem",
        "First-Line Dosing (US)": "Ertapenem 1 g IV q24h; Meropenem 1–2 g IV q8h",
        "Alternative Therapy": "Ceftolozane-tazobactam, Ceftazidime-avibactam",
        "Alternative Dosing": "CTZ/AVI 2.5 g IV q8h (ext. infusion over 3h)",
        "MDR Therapy": "Fosfomycin (UTI), Colistin (last resort)",
        "MDR Dosing": "Fosfomycin 6 g IV q6–8h; Colistin per PK/PD modeling",
        "Resistance Mechanisms": "CTX-M (dominant), SHV, TEM beta-lactamases",
        "Key Notes": "Step-down to oral after clinical improvement if susceptible; avoid pip-tazo for ESBL bacteremia",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Bacteria",
        "Organism": "Klebsiella pneumoniae (KPC-CRE)",
        "Gram / Morphology": "Gram- Bacilli (Enteric)",
        "First-Line Therapy": "Ceftazidime-avibactam",
        "First-Line Dosing (US)": "Ceftazidime-avibactam 2.5 g IV q8h (3-h ext. infusion)",
        "Alternative Therapy": "Meropenem-vaborbactam, Imipenem-relebactam",
        "Alternative Dosing": "Meropenem-vaborbactam 4 g IV q8h (3h); Imipenem-cilastatin-relebactam 1.25 g IV q6h",
        "MDR Therapy": "Cefiderocol, Aztreonam-avibactam (SAP), Tigecycline (combo)",
        "MDR Dosing": "Cefiderocol 2 g IV q8h (3h ext.); Tigecycline 200 mg load then 100 mg q12h",
        "Resistance Mechanisms": "KPC (serine carbapenemase), OXA-48 variants",
        "Key Notes": "ALWAYS consult ID; combination therapy often required; source control paramount",
        "Efficacy_FL": "yellow",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Bacteria",
        "Organism": "Klebsiella pneumoniae (MBL/NDM)",
        "Gram / Morphology": "Gram- Bacilli (Enteric)",
        "First-Line Therapy": "Aztreonam-avibactam (combo)",
        "First-Line Dosing (US)": "Aztreonam 6 g/day + Avibactam 0.375 g/day IV (investigational)",
        "Alternative Therapy": "Cefiderocol, Colistin + Meropenem",
        "Alternative Dosing": "Cefiderocol 2 g IV q8h (3h); Colistin CBA 5 mg/kg load then 2.5 mg/kg q12h",
        "MDR Therapy": "Tigecycline + Colistin + Meropenem (triple therapy)",
        "MDR Dosing": "Based on PK/PD modeling and ID consultation",
        "Resistance Mechanisms": "NDM, VIM, IMP metallo-beta-lactamases; hydrolysis of all carbapenems and most beta-lactams",
        "Key Notes": "Aztreonam NOT hydrolyzed by MBLs; ceftaz-AVI alone ineffective for MBL",
        "Efficacy_FL": "red",
        "Efficacy_Alt": "red",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Bacteria",
        "Organism": "Pseudomonas aeruginosa (susceptible)",
        "Gram / Morphology": "Gram- Bacilli (Non-fermenter)",
        "First-Line Therapy": "Pip-Tazo / Cefepime / Meropenem",
        "First-Line Dosing (US)": "Pip-Tazo 4.5 g IV q6h (ext. inf.); Cefepime 2 g IV q8h; Meropenem 2 g IV q8h",
        "Alternative Therapy": "Ciprofloxacin, Aztreonam, Aminoglycosides",
        "Alternative Dosing": "Ciprofloxacin 400 mg IV q8h; Aztreonam 2 g IV q6h; Amikacin 15–20 mg/kg IV q24h",
        "MDR Therapy": "Ceftolozane-tazobactam, Ceftazidime-avibactam",
        "MDR Dosing": "Ceftolozane-tazobactam 3 g IV q8h (1-h inf.); CTZ-AVI 2.5 g IV q8h",
        "Resistance Mechanisms": "AmpC derepression, OprD loss (carbapenem), MexAB efflux, PBP3 mutations",
        "Key Notes": "Avoid monotherapy for serious infections; combination for VAP/bacteremia controversial",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Pseudomonas aeruginosa (MDR/DTR)",
        "Gram / Morphology": "Gram- Bacilli (Non-fermenter)",
        "First-Line Therapy": "Cefiderocol",
        "First-Line Dosing (US)": "Cefiderocol 2 g IV q8h (3-h extended infusion)",
        "Alternative Therapy": "Imipenem-cilastatin-relebactam",
        "Alternative Dosing": "Imipenem-cilastatin-relebactam 1.25 g IV q6h (based on renal function)",
        "MDR Therapy": "Colistin + Meropenem (high-dose) + Fosfomycin",
        "MDR Dosing": "Colistin CBA 5 mg/kg load + Meropenem 2 g IV q8h (3-h) + Fosfomycin 6 g IV q6h",
        "Resistance Mechanisms": "Multiple mechanisms: MBL (VIM, IMP), AmpC, efflux, porin loss",
        "Key Notes": "DTR-PA = difficult-to-treat resistance; strict ID + pharmacy involvement required",
        "Efficacy_FL": "yellow",
        "Efficacy_Alt": "red",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Bacteria",
        "Organism": "Acinetobacter baumannii (MDR/XDR)",
        "Gram / Morphology": "Gram- Bacilli (Non-fermenter)",
        "First-Line Therapy": "Ampicillin-sulbactam (sulbactam component)",
        "First-Line Dosing (US)": "Sulbactam 9 g/day IV (as AMP-SUL 3 g IV q4h) — based on sulbactam MIC",
        "Alternative Therapy": "Colistin, Polymyxin B",
        "Alternative Dosing": "Colistin CBA load 5 mg/kg then 2.5 mg/kg q12h IV; Polymyxin B 1.25–1.5 mg/kg q12h IV",
        "MDR Therapy": "Cefiderocol, Tigecycline + Colistin, Sulbactam-durlobactam (investigational)",
        "MDR Dosing": "Cefiderocol 2 g IV q8h (3h); Tigecycline 200 mg load then 100 mg q12h",
        "Resistance Mechanisms": "OXA-23/24/48 carbapenemases, MBL (NDM), efflux, porin loss",
        "Key Notes": "Tigecycline FDA: use only if NO other option; combination preferred; monotherapy failure high",
        "Efficacy_FL": "red",
        "Efficacy_Alt": "red",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Bacteria",
        "Organism": "Haemophilus influenzae",
        "Gram / Morphology": "Gram- Coccobacilli",
        "First-Line Therapy": "Amoxicillin-clavulanate / Azithromycin",
        "First-Line Dosing (US)": "Amox-clav 875/125 mg PO q12h; Azithromycin 500 mg PO day 1 then 250 mg q24h",
        "Alternative Therapy": "Cefuroxime, Levofloxacin, Doxycycline",
        "Alternative Dosing": "Cefuroxime 250–500 mg PO q12h; Levofloxacin 750 mg PO q24h",
        "MDR Therapy": "Ceftriaxone (beta-lactamase positive, IV required)",
        "MDR Dosing": "Ceftriaxone 1–2 g IV q24h",
        "Resistance Mechanisms": "TEM-1 beta-lactamase; BLNAR (beta-lactamase negative, ampicillin resistant)",
        "Key Notes": "BLNAR strains: use fluoroquinolone or ceftriaxone; avoid trimethoprim monotherapy",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Neisseria gonorrhoeae",
        "Gram / Morphology": "Gram- Diplococci",
        "First-Line Therapy": "Ceftriaxone (single dose)",
        "First-Line Dosing (US)": "Ceftriaxone 500 mg IM × 1 dose (or 1 g if weight ≥150 kg)",
        "Alternative Therapy": "Gentamicin + Azithromycin (PCN/cephalosporin allergy)",
        "Alternative Dosing": "Gentamicin 240 mg IM × 1 + Azithromycin 2 g PO × 1",
        "MDR Therapy": "Ceftriaxone + Azithromycin 2g (cephalosporin-resistant strains)",
        "MDR Dosing": "Ceftriaxone 500 mg IM + Azithromycin 2 g PO simultaneously",
        "Resistance Mechanisms": "PPNG (TEM beta-lactamase), TRNG, CMRNG; emerging cephalosporin resistance (mosaic PBP2)",
        "Key Notes": "Always treat for chlamydia co-infection with doxycycline; test-of-cure 1–2 wks after treatment",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Bacteria",
        "Organism": "Clostridioides difficile",
        "Gram / Morphology": "Gram+ Bacilli (Anaerobe)",
        "First-Line Therapy": "Fidaxomicin / Vancomycin (PO)",
        "First-Line Dosing (US)": "Fidaxomicin 200 mg PO q12h × 10d; Vancomycin 125 mg PO q6h × 10d",
        "Alternative Therapy": "Metronidazole (mild, non-severe only)",
        "Alternative Dosing": "Metronidazole 500 mg PO q8h × 10–14d (only if fidaxomicin/vanco not available)",
        "MDR Therapy": "Bezlotoxumab (recurrence prevention) + Fidaxomicin",
        "MDR Dosing": "Bezlotoxumab 10 mg/kg IV × 1 infusion; Fidaxomicin extended-pulse regimen",
        "Resistance Mechanisms": "Fecal dysbiosis; spore persistence; toxin A/B production; ribotypes (027, 078)",
        "Key Notes": "Discontinue offending antibiotic ASAP; vancomycin/fidaxomicin NOT absorbed (intraluminal action); FMT for multiple recurrences",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Bacteria",
        "Organism": "Mycoplasma pneumoniae",
        "Gram / Morphology": "Cell Wall-Deficient",
        "First-Line Therapy": "Azithromycin / Doxycycline",
        "First-Line Dosing (US)": "Azithromycin 500 mg PO day 1 then 250 mg q24h × 4d; Doxycycline 100 mg PO q12h × 5–7d",
        "Alternative Therapy": "Levofloxacin, Moxifloxacin",
        "Alternative Dosing": "Levofloxacin 750 mg PO q24h × 5d; Moxifloxacin 400 mg PO q24h × 5d",
        "MDR Therapy": "Fluoroquinolone (if macrolide-resistant — emerging Asia/US)",
        "MDR Dosing": "Levofloxacin 750 mg PO q24h × 5d",
        "Resistance Mechanisms": "23S rRNA mutations (macrolide resistance — increasing US prevalence)",
        "Key Notes": "No cell wall → beta-lactams INEFFECTIVE; treat community-acquired pneumonia empirically",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },

    # ── FUNGI ────────────────────────────────────────────────────────────────
    {
        "Category": "Fungi",
        "Organism": "Candida albicans (susceptible)",
        "Gram / Morphology": "Yeast",
        "First-Line Therapy": "Fluconazole",
        "First-Line Dosing (US)": "Fluconazole 800 mg PO/IV load, then 400 mg q24h",
        "Alternative Therapy": "Micafungin / Caspofungin (candidemia/ICU)",
        "Alternative Dosing": "Micafungin 100–150 mg IV q24h; Caspofungin 70 mg load then 50 mg IV q24h",
        "MDR Therapy": "Amphotericin B liposomal (fluconazole-R)",
        "MDR Dosing": "Liposomal Amphotericin B 3–5 mg/kg IV q24h",
        "Resistance Mechanisms": "ERG11 mutations (azole resistance), FKS mutations (echinocandin resistance rare)",
        "Key Notes": "Echinocandin preferred for candidemia (IDSA 2016); de-escalate to fluconazole after 5–7d if susceptible & stable",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "green",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Fungi",
        "Organism": "Candida glabrata (C. glabrata / C. nivariensis)",
        "Gram / Morphology": "Yeast",
        "First-Line Therapy": "Echinocandin (Micafungin / Caspofungin)",
        "First-Line Dosing (US)": "Micafungin 100 mg IV q24h; Caspofungin 70 mg load then 50 mg IV q24h",
        "Alternative Therapy": "Voriconazole (if susceptible)",
        "Alternative Dosing": "Voriconazole 6 mg/kg IV q12h × 2 doses, then 4 mg/kg q12h",
        "MDR Therapy": "Liposomal Amphotericin B (FKS mutant/echinocandin-R)",
        "MDR Dosing": "Liposomal Amphotericin B 3–5 mg/kg IV q24h",
        "Resistance Mechanisms": "Intrinsically reduced fluconazole susceptibility; FKS1/FKS2 mutations (echinocandin-R)",
        "Key Notes": "Fluconazole: variable activity — AVOID empirically; always perform susceptibility testing",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Fungi",
        "Organism": "Candida auris (MDR)",
        "Gram / Morphology": "Yeast",
        "First-Line Therapy": "Echinocandin (Micafungin preferred)",
        "First-Line Dosing (US)": "Micafungin 100–150 mg IV q24h; Caspofungin 70 mg load then 50 mg q24h",
        "Alternative Therapy": "Ibrexafungerp (novel triterpenoid)",
        "Alternative Dosing": "Ibrexafungerp 300 mg PO q12h × 1d (or 150 mg PO q12h × 2d for mucosal)",
        "MDR Therapy": "Liposomal Amphotericin B + Echinocandin (combination)",
        "MDR Dosing": "L-AmB 5 mg/kg IV q24h + Micafungin 150 mg IV q24h",
        "Resistance Mechanisms": "Multi-drug resistant (simultaneous azole, polyene, echinocandin resistance possible via FKS, ERG11 mutations)",
        "Key Notes": "CDC Priority Pathogen; mandatory reporting; strict contact precautions; consult ID immediately",
        "Efficacy_FL": "yellow",
        "Efficacy_Alt": "red",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Fungi",
        "Organism": "Aspergillus fumigatus",
        "Gram / Morphology": "Mold (Hyaline)",
        "First-Line Therapy": "Voriconazole",
        "First-Line Dosing (US)": "Voriconazole 6 mg/kg IV q12h × 2 doses, then 4 mg/kg IV q12h (TDM target: 1–5.5 mg/L)",
        "Alternative Therapy": "Isavuconazole, Liposomal Amphotericin B",
        "Alternative Dosing": "Isavuconazole 372 mg IV/PO q8h × 6 doses (load) then 372 mg q24h; L-AmB 3–5 mg/kg IV q24h",
        "MDR Therapy": "Combination voriconazole + echinocandin (angioinvasive, azole-R)",
        "MDR Dosing": "Voriconazole + Micafungin/Caspofungin (standard doses above in combination)",
        "Resistance Mechanisms": "CYP51A mutations (TR34/L98H, TR46); azole resistance rising in environment",
        "Key Notes": "Echinocandins have NO reliable activity as monotherapy; TDM mandatory for voriconazole; posaconazole prophylaxis for high-risk hematology patients",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "red",
    },
    {
        "Category": "Fungi",
        "Organism": "Cryptococcus neoformans",
        "Gram / Morphology": "Yeast (Encapsulated)",
        "First-Line Therapy": "Liposomal Amphotericin B + Flucytosine",
        "First-Line Dosing (US)": "L-AmB 3–4 mg/kg IV q24h + Flucytosine 25 mg/kg PO q6h (induction 2 wks)",
        "Alternative Therapy": "Fluconazole (consolidation/maintenance phase)",
        "Alternative Dosing": "Fluconazole 400 mg PO q24h × 8 wks, then 200 mg q24h maintenance",
        "MDR Therapy": "AmBisome high-dose (5–6 mg/kg) + Flucytosine",
        "MDR Dosing": "L-AmB 5 mg/kg IV q24h + Flucytosine 25 mg/kg PO q6h × 2 wks (ID consultation)",
        "Resistance Mechanisms": "ERG11 mutations, overexpression of efflux pumps (azole-R); primary flucytosine resistance rare",
        "Key Notes": "Always check opening pressure — LP for pressure relief critical in CNS disease; monitor flucytosine levels (target 30–80 mcg/mL)",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Fungi",
        "Organism": "Mucormycosis (Mucor / Rhizopus spp.)",
        "Gram / Morphology": "Mold (Mucorales)",
        "First-Line Therapy": "Liposomal Amphotericin B",
        "First-Line Dosing (US)": "L-AmB 5–10 mg/kg IV q24h",
        "Alternative Therapy": "Isavuconazole (step-down), Posaconazole (step-down)",
        "Alternative Dosing": "Isavuconazole 372 mg PO/IV q24h (after AmB induction); Posaconazole 300 mg PO q24h",
        "MDR Therapy": "Combination surgery + antifungal (no truly salvage systemic option)",
        "MDR Dosing": "Debridement + L-AmB 10 mg/kg IV q24h ± Deferasirox 10 mg/kg/day PO (iron chelation — investigational)",
        "Resistance Mechanisms": "Intrinsically resistant to voriconazole, echinocandins, and fluconazole",
        "Key Notes": "SURGICAL DEBRIDEMENT is cornerstone of therapy; reverse underlying immunosuppression/DKA; voriconazole DOES NOT COVER Mucor",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "red",
    },

    # ── VIRUSES ──────────────────────────────────────────────────────────────
    {
        "Category": "Viruses",
        "Organism": "Influenza A & B",
        "Gram / Morphology": "RNA Virus (Orthomyxovirus)",
        "First-Line Therapy": "Oseltamivir / Zanamivir",
        "First-Line Dosing (US)": "Oseltamivir 75 mg PO q12h × 5d; Zanamivir 10 mg inhaled q12h × 5d",
        "Alternative Therapy": "Baloxavir marboxil (single dose)",
        "Alternative Dosing": "Baloxavir 40 mg PO × 1 dose (<80 kg); 80 mg PO × 1 dose (≥80 kg)",
        "MDR Therapy": "Peramivir (IV for hospitalized patients unable to take oral)",
        "MDR Dosing": "Peramivir 600 mg IV × 1 dose (can extend to 5–10 days for severe illness)",
        "Resistance Mechanisms": "H275Y (oseltamivir resistance in H1N1); PA I38T (baloxavir resistance)",
        "Key Notes": "Start within 48h of symptom onset for optimal effect; amantadine/rimantadine: HIGH resistance, NOT recommended",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "green",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Viruses",
        "Organism": "Herpes Simplex Virus (HSV-1/2)",
        "Gram / Morphology": "DNA Virus (Herpesviridae)",
        "First-Line Therapy": "Acyclovir / Valacyclovir",
        "First-Line Dosing (US)": "Valacyclovir 500–1000 mg PO q12h × 7–10d; Acyclovir 5–10 mg/kg IV q8h (severe)",
        "Alternative Therapy": "Famciclovir",
        "Alternative Dosing": "Famciclovir 500 mg PO q12h × 7–10d",
        "MDR Therapy": "Foscarnet (acyclovir-resistant), Cidofovir",
        "MDR Dosing": "Foscarnet 40 mg/kg IV q8h; Cidofovir 5 mg/kg IV weekly (+ probenecid + IV hydration)",
        "Resistance Mechanisms": "TK mutations (UL23) — acyclovir/valacyclovir resistance; DNA polymerase mutations (UL30) — foscarnet resistance",
        "Key Notes": "Foscarnet for TK-deficient strains; cidofovir as last resort (nephrotoxic); monitor renal function",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "green",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Viruses",
        "Organism": "Cytomegalovirus (CMV)",
        "Gram / Morphology": "DNA Virus (Herpesviridae)",
        "First-Line Therapy": "Valganciclovir / Ganciclovir",
        "First-Line Dosing (US)": "Valganciclovir 900 mg PO q12h (induction) then 900 mg q24h; Ganciclovir 5 mg/kg IV q12h (severe)",
        "Alternative Therapy": "Foscarnet (second-line or ganciclovir-R)",
        "Alternative Dosing": "Foscarnet 60 mg/kg IV q8h or 90 mg/kg IV q12h (induction)",
        "MDR Therapy": "Letermovir (prophylaxis in transplant), Maribavir (refractory/resistant CMV)",
        "MDR Dosing": "Letermovir 480 mg IV/PO q24h (prophylaxis); Maribavir 400 mg PO q12h × 8 wks (refractory)",
        "Resistance Mechanisms": "UL97 mutations (ganciclovir-R); UL54 mutations (multi-drug R — ganciclovir + foscarnet + cidofovir)",
        "Key Notes": "Maribavir FDA-approved 2021 for refractory/resistant CMV in transplant; monitor CBC weekly (ganciclovir myelosuppression)",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Viruses",
        "Organism": "Hepatitis C Virus (HCV) — Pan-genotypic",
        "Gram / Morphology": "RNA Virus (Flaviviridae)",
        "First-Line Therapy": "Sofosbuvir/Velpatasvir or Glecaprevir/Pibrentasvir",
        "First-Line Dosing (US)": "SOF/VEL 1 tablet PO q24h × 12 wks; GLE/PIB 3 tabs PO q24h × 8 wks (non-cirrhotic)",
        "Alternative Therapy": "Sofosbuvir/Velpatasvir/Voxilaprevir (NS5A-experienced)",
        "Alternative Dosing": "SOF/VEL/VOX 1 tablet PO q24h × 12 wks",
        "MDR Therapy": "Retreatment regimens per AASLD guidelines (based on prior regimen + resistance testing)",
        "MDR Dosing": "Individualized — consult hepatology/ID",
        "Resistance Mechanisms": "NS5A RASs (L31M, Y93H), NS5B mutations — resistance testing guides retreatment",
        "Key Notes": "Cure rates (SVR12) >95%; check drug interactions (acid-suppression, antiretrovirals); ribavirin no longer standard backbone",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "green",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Viruses",
        "Organism": "SARS-CoV-2 (COVID-19)",
        "Gram / Morphology": "RNA Virus (Betacoronavirus)",
        "First-Line Therapy": "Nirmatrelvir-ritonavir (Paxlovid) / Remdesivir",
        "First-Line Dosing (US)": "Nirmatrelvir-ritonavir 300/100 mg PO q12h × 5d (check DDIs); Remdesivir 200 mg IV day 1 then 100 mg q24h × 4d",
        "Alternative Therapy": "Molnupiravir (if Paxlovid not feasible)",
        "Alternative Dosing": "Molnupiravir 800 mg PO q12h × 5d",
        "MDR Therapy": "Remdesivir + Dexamethasone (hospitalized, O2-requiring)",
        "MDR Dosing": "Dexamethasone 6 mg PO/IV q24h × 10d; Remdesivir 200 mg IV day 1 then 100 mg q24h × 4d",
        "Resistance Mechanisms": "NSP5 (protease) mutations affecting nirmatrelvir; spike mutations affecting monoclonal antibodies",
        "Key Notes": "Ritonavir boosting causes significant drug interactions (check prescribing tool); monoclonal antibodies largely inactive against current variants",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "yellow",
        "Efficacy_MDR": "yellow",
    },
    {
        "Category": "Viruses",
        "Organism": "HIV-1 (ART-Naïve, Initial Regimen)",
        "Gram / Morphology": "RNA Virus (Retrovirus)",
        "First-Line Therapy": "Bictegravir/TAF/FTC (Biktarvy) or DTG + TAF/FTC",
        "First-Line Dosing (US)": "Bictegravir 50/TAF 25/FTC 200 mg PO q24h; DTG 50 mg + TAF/FTC 25/200 mg PO q24h",
        "Alternative Therapy": "Cabotegravir LA + Rilpivirine LA (injection-based, suppressed patients)",
        "Alternative Dosing": "CAB-LA 600 mg IM + RPV-LA 900 mg IM q4 wks (month 1 & 2), then q8 wks",
        "MDR Therapy": "Ibalizumab + optimized background (MDR HIV)",
        "MDR Dosing": "Ibalizumab 2000 mg IV load, then 800 mg IV q2 wks + OBR",
        "Resistance Mechanisms": "INSTI mutations (G140S, Q148H), NNRTI mutations (K103N, E138K), TAM (thymidine analog mutations)",
        "Key Notes": "Genotypic resistance testing before initiation; treat all patients regardless of CD4 count; TDM for select regimens",
        "Efficacy_FL": "green",
        "Efficacy_Alt": "green",
        "Efficacy_MDR": "yellow",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA LOADING FUNCTION  (swap this for DB/API call)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load organism data into a DataFrame.
    ── TO SWAP FOR REAL DATA ──────────────────────────────────────────────────
    Replace the body with something like:
        import sqlalchemy, json, requests
        # Option A – PostgreSQL:
        engine = sqlalchemy.create_engine(os.environ["DB_URL"])
        return pd.read_sql("SELECT * FROM organisms", engine)
        # Option B – REST API (EUCAST, etc.):
        r = requests.get("https://your-api/organisms")
        return pd.DataFrame(r.json())
        # Option C – CSV file:
        return pd.read_csv("organisms.csv")
    ──────────────────────────────────────────────────────────────────────────
    """
    return pd.DataFrame(ORGANISM_DATA)


# ─────────────────────────────────────────────────────────────────────────────
# 3. STYLING HELPERS
# ─────────────────────────────────────────────────────────────────────────────
EFFICACY_BG = {
    "green":  "#d4edda",   # First-line / reliable
    "yellow": "#fff3cd",   # Alternative / variable
    "red":    "#f8d7da",   # Not recommended / resistant
}
EFFICACY_TXT = {
    "green":  "#155724",
    "yellow": "#856404",
    "red":    "#721c24",
}

# Columns that carry efficacy codes (internal, hidden from display)
EFFICACY_COLS = ["Efficacy_FL", "Efficacy_Alt", "Efficacy_MDR"]

# Mapping: display column → efficacy code column
DISPLAY_TO_EFFICACY = {
    "First-Line Therapy": "Efficacy_FL",
    "Alternative Therapy": "Efficacy_Alt",
    "MDR Therapy": "Efficacy_MDR",
}

STANDARD_COLS = [
    "Category", "Organism", "Gram / Morphology",
    "First-Line Therapy", "First-Line Dosing (US)",
    "Alternative Therapy", "Alternative Dosing",
    "MDR Therapy", "MDR Dosing",
    "Resistance Mechanisms", "Key Notes",
]

MDR_COLS = [
    "Organism", "Gram / Morphology",
    "MDR Therapy", "MDR Dosing",
    "Resistance Mechanisms", "Key Notes",
]


def style_row(row: pd.Series) -> list:
    """Return CSS background/color strings for each cell in the display row."""
    styles = []
    for col in row.index:
        if col in DISPLAY_TO_EFFICACY:
            code = row[DISPLAY_TO_EFFICACY[col]]
            bg = EFFICACY_BG.get(code, "")
            fg = EFFICACY_TXT.get(code, "")
            styles.append(f"background-color: {bg}; color: {fg}; font-weight: bold;")
        else:
            styles.append("")
    return styles


def build_styled_df(df: pd.DataFrame, mdr_focus: bool):
    """Build and return a Pandas Styler object for the main table."""
    display_cols = MDR_COLS if mdr_focus else STANDARD_COLS

    # Keep only display columns that exist, plus the hidden efficacy cols
    available = [c for c in display_cols if c in df.columns]
    hidden_eff = [c for c in EFFICACY_COLS if c in df.columns]
    working = df[available + hidden_eff].copy()

    styler = (
        working.style
        .apply(style_row, axis=1)
        .set_properties(**{"font-size": "12px", "text-align": "left"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#1a3a5c"),
                ("color", "white"),
                ("font-size", "12px"),
                ("padding", "6px"),
            ]},
            {"selector": "td", "props": [
                ("padding", "6px 10px"),
                ("border-bottom", "1px solid #dee2e6"),
                ("vertical-align", "top"),
            ]},
        ])
        .hide(axis="columns", subset=hidden_eff)   # hide internal efficacy cols
        .hide(axis="index")
    )
    return styler


# ─────────────────────────────────────────────────────────────────────────────
# 4. PDF EXPORT ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def generate_pdf(filtered_df: pd.DataFrame, mdr_focus: bool) -> bytes:
    """
    Generate a landscape-oriented PDF from the currently filtered DataFrame.
    Returns raw PDF bytes for st.download_button.
    """
    display_cols = MDR_COLS if mdr_focus else STANDARD_COLS
    cols = [c for c in display_cols if c in filtered_df.columns]
    df_print = filtered_df[cols].copy()

    pdf = FPDF(orientation="L", unit="mm", format="A3")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    # ── Header ────────────────────────────────────────────────────────────
    pdf.set_font("Times", "B", 16)
    pdf.set_fill_color(26, 58, 92)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "Dynamic Antibiogram & Antimicrobial Stewardship Tool", ln=True,
             align="C", fill=True)

    pdf.set_font("Times", "", 9)
    pdf.set_text_color(100, 100, 100)
    mode_label = "MDR FOCUS MODE" if mdr_focus else "Standard Mode"
    pdf.cell(0, 6,
             f"  Mode: {mode_label}   |   Rows: {len(df_print)}   |   Generated: US Clinical Practice Reference",
             ln=True, align="L")
    pdf.ln(2)

    # ── Legend ────────────────────────────────────────────────────────────
    pdf.set_font("Times", "B", 8)
    pdf.set_text_color(0, 0, 0)
    for label, (r, g, b) in [
        ("First-Line / Reliable", (212, 237, 218)),
        ("Alternative / Variable", (255, 243, 205)),
        ("Not Recommended / Resistant", (248, 215, 218)),
    ]:
        pdf.set_fill_color(r, g, b)
        pdf.cell(5, 5, " ", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(70, 5, f" {label}", ln=False)
    pdf.ln(7)

    # ── Column widths (auto-scale to page width) ──────────────────────────
    PAGE_W = pdf.w - pdf.l_margin - pdf.r_margin
    col_weights = {
        "Category": 1,
        "Organism": 2.5,
        "Gram / Morphology": 1.5,
        "First-Line Therapy": 2,
        "First-Line Dosing (US)": 3.5,
        "Alternative Therapy": 2,
        "Alternative Dosing": 3.5,
        "MDR Therapy": 2,
        "MDR Dosing": 3.5,
        "Resistance Mechanisms": 2.5,
        "Key Notes": 3,
    }
    weights = [col_weights.get(c, 2) for c in cols]
    total_w = sum(weights)
    col_widths = [PAGE_W * (w / total_w) for w in weights]
    ROW_H = 6

    # ── Table header ──────────────────────────────────────────────────────
    pdf.set_font("Times", "B", 7)
    pdf.set_fill_color(26, 58, 92)
    pdf.set_text_color(255, 255, 255)
    for col, cw in zip(cols, col_widths):
        pdf.cell(cw, ROW_H, col, border=1, fill=True, align="C")
    pdf.ln()

    # ── Table rows ────────────────────────────────────────────────────────
    eff_map = filtered_df.set_index("Organism") if "Organism" in filtered_df.columns else None

    for _, row in df_print.iterrows():
        pdf.set_font("Times", "", 6.5)
        pdf.set_text_color(0, 0, 0)

        # Determine row height from content
        cell_heights = []
        for col, cw in zip(cols, col_widths):
            txt = str(row[col]) if pd.notna(row[col]) else ""
            n_lines = max(1, len(pdf.multi_cell(cw, ROW_H - 1, txt,
                                                 split_only=True)))
            cell_heights.append(n_lines * (ROW_H - 1))
        row_h = max(cell_heights)

        # Check page break
        if pdf.get_y() + row_h > pdf.h - pdf.b_margin:
            pdf.add_page()
            # Repeat header
            pdf.set_font("Times", "B", 7)
            pdf.set_fill_color(26, 58, 92)
            pdf.set_text_color(255, 255, 255)
            for col, cw in zip(cols, col_widths):
                pdf.cell(cw, ROW_H, col, border=1, fill=True, align="C")
            pdf.ln()
            pdf.set_font("Times", "", 6.5)
            pdf.set_text_color(0, 0, 0)

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for i, (col, cw) in enumerate(zip(cols, col_widths)):
            txt = str(row[col]) if pd.notna(row[col]) else ""
            # Efficacy colouring
            fill = False
            if col in DISPLAY_TO_EFFICACY and eff_map is not None:
                org = row.get("Organism", "")
                try:
                    eff_code = filtered_df.loc[
                        filtered_df["Organism"] == org, DISPLAY_TO_EFFICACY[col]
                    ].values[0]
                except Exception:
                    eff_code = ""
                color_map = {
                    "green": (212, 237, 218),
                    "yellow": (255, 243, 205),
                    "red": (248, 215, 218),
                }
                if eff_code in color_map:
                    pdf.set_fill_color(*color_map[eff_code])
                    fill = True
                else:
                    pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(255, 255, 255)

            pdf.set_xy(x_start + sum(col_widths[:i]), y_start)
            pdf.multi_cell(cw, row_h / max(1, len(
                pdf.multi_cell(cw, row_h - 1, txt, split_only=True)
            )), txt, border=1, fill=fill, align="L")

        pdf.set_xy(x_start, y_start + row_h)

    # ── Footer ────────────────────────────────────────────────────────────
    pdf.set_font("Times", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5,
             "Data derived from Sanford Guide, IDSA Guidelines, CDC, and US clinical practice. "
             "For clinical decision support only. Always correlate with local antibiogram and patient factors.",
             ln=True, align="C")

    return bytes(pdf.output())


# ─────────────────────────────────────────────────────────────────────────────
# 5. STREAMLIT APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Antimicrobial Stewardship Tool",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── Header banner ─────────────────────────────────────────────────────
    st.markdown("""
    <div style="background: linear-gradient(135deg,#1a3a5c,#0d6efd);
                padding:18px 24px; border-radius:8px; margin-bottom:16px;">
        <h2 style="color:white;margin:0;">Infectious Disease + Antimicrobial Stewardship</h2>
        <p style="color:#cce5ff;margin:4px 0 0 0;font-size:13px;">
            US Clinical Practice Reference · Bacteria · Fungi · Viruses · MDR Organisms
        </p>
    </div>
    """, unsafe_allow_html=True)

    df_full = load_data()

    # ── SIDEBAR ───────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## Filters & Settings")
        st.divider()

        # MDR Focus toggle
        mdr_focus = st.toggle(
            "MDR Focus Mode",
            value=False,
            help="Highlights salvage therapies and high-exposure dosing for resistant organisms",
        )
        if mdr_focus:
            st.warning("MDR Therapies: showing salvage/high-dose regimens")
        st.divider()

        # Category filter
        categories = ["All"] + sorted(df_full["Category"].unique().tolist())
        cat_sel = st.selectbox("Pathogen Category", categories)

        # Gram / Morphology filter (bacteria-centric)
        morph_options = sorted(df_full["Gram / Morphology"].unique().tolist())
        morph_sel = st.multiselect(
            "Gram Stain / Morphology",
            morph_options,
            default=[],
            help="Leave blank to include all morphologies",
        )

        # Search bar
        search_term = st.text_input(
            "Search Organism",
            placeholder="e.g. Pseudomonas, Candida, Influenza",
        )

        st.divider()

        # Legend
        st.markdown("### Efficacy Legend")
        st.markdown("""
        <div style="font-size:13px;line-height:1.9;">
          <span style="background:#d4edda;padding:2px 8px;border-radius:4px;">■</span>
          <b>First-Line</b> / Reliably active<br>
          <span style="background:#fff3cd;padding:2px 8px;border-radius:4px;">■</span>
          <b>Alternative</b> / Variable activity<br>
          <span style="background:#f8d7da;padding:2px 8px;border-radius:4px;">■</span>
          <b>Not Recommended</b> / Resistant<br>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("""
        <div style="font-size:11px;color:#888;">
        Data sources: Sanford Guide 2024, IDSA Guidelines, CDC, 
        EUCAST/CLSI Breakpoints<br><br>
        <b>Clinical decision support only.</b><br>
        Always correlate with local antibiogram and patient factors.
        </div>
        """, unsafe_allow_html=True)

    # ── FILTERING ─────────────────────────────────────────────────────────
    df = df_full.copy()

    if cat_sel != "All":
        df = df[df["Category"] == cat_sel]

    if morph_sel:
        df = df[df["Gram / Morphology"].isin(morph_sel)]

    if search_term.strip():
        mask = df["Organism"].str.contains(search_term.strip(), case=False, na=False)
        df = df[mask]

    # ── MAIN TABLE ────────────────────────────────────────────────────────
    if df.empty:
        st.info("No organisms match your current filters. Try broadening your search.")
    else:
        mode_label = "MDR Salvage Reference" if mdr_focus else "Standard Antibiogram"
        st.subheader(mode_label)

        styler = build_styled_df(df, mdr_focus)
        st.dataframe(
            styler,
            use_container_width=True,
            height=600,
        )

        # ── DETAIL EXPANDER ───────────────────────────────────────────────
        st.divider()
        with st.expander("Full Detail View (click to expand)", expanded=False):
            org_names = df["Organism"].tolist()
            selected_org = st.selectbox("Select Organism for Full Detail", org_names)
            if selected_org:
                row = df[df["Organism"] == selected_org].iloc[0]
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### {row['Organism']}")
                    st.markdown(f"**Category:** {row['Category']}")
                    st.markdown(f"**Gram/Morphology:** {row['Gram / Morphology']}")
                    st.markdown("---")
                    st.markdown("#### 🟢 First-Line Therapy")
                    st.info(f"**Agent:** {row['First-Line Therapy']}")
                    st.markdown(f"**US Dosing:** `{row['First-Line Dosing (US)']}`")
                    st.markdown("#### 🟡 Alternative Therapy")
                    st.warning(f"**Agent:** {row['Alternative Therapy']}")
                    st.markdown(f"**US Dosing:** `{row['Alternative Dosing']}`")
                with c2:
                    eff_code = row.get("Efficacy_MDR", "yellow")
                    eff_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(eff_code, "🟡")
                    st.markdown(f"#### {eff_emoji} MDR Therapy")
                    if eff_code == "red":
                        st.error(f"**Agent:** {row['MDR Therapy']}")
                    else:
                        st.warning(f"**Agent:** {row['MDR Therapy']}")
                    st.markdown(f"**US Dosing:** `{row['MDR Dosing']}`")
                    st.markdown("---")
                    st.markdown("#### Resistance Mechanisms")
                    st.markdown(f"_{row['Resistance Mechanisms']}_")
                    st.markdown("#### Key Notes")
                    st.markdown(f"> {row['Key Notes']}")

        # ── PDF EXPORT ────────────────────────────────────────────────────
        st.divider()
        st.subheader("Export")
        st.markdown("Download the currently filtered table as a **landscape-format PDF** point-of-care reference sheet.")

        export_col1, export_col2 = st.columns([2, 5])
        with export_col1:
            if st.button("Generate PDF", use_container_width=True, type="primary"):
                with st.spinner("Building PDF..."):
                    pdf_bytes = generate_pdf(df, mdr_focus)
                filename = f"antibiogram_{'MDR' if mdr_focus else 'standard'}_{cat_sel.replace(' ', '_')}.pdf"
                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["pdf_filename"] = filename
                st.success("PDF ready — click Download below!")

        if "pdf_bytes" in st.session_state:
            with export_col1:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=st.session_state["pdf_bytes"],
                    file_name=st.session_state.get("pdf_filename", "antibiogram.pdf"),
                    mime="application/pdf",
                    use_container_width=True,
                )

    # ── FOOTER ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("""
    <div style="text-align:center;font-size:11px;color:#888;padding:8px;">
    Data derived from <b>Sanford Guide 2024</b>, IDSA/ASHP Guidelines, CDC, and standard US clinical practice.<br>
    <b>For clinical decision support and educational use only.</b> 
    Always verify with local antibiogram, patient-specific factors, and current pharmacy/ID consultation.<br>
    <i>To integrate live breakpoint data: connect EUCAST API, NCBI Pathogen Detection, or CARD database — see load_data() in app.py.</i>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
