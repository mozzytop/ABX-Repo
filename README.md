🚀 Key Features
Interactive Spectrum of Activity: A visual "Sanford-style" heatmap of antibacterials, antifungals, and antivirals color-coded by clinical reliability.

Dynamic US Sensitivity Data: Live-queried resistance trends powered by the NCBI Pathogen Detection database, filtered for US-specific isolates.

MDR "Deep Dive" Mode: Targeted guidance for niche organisms, including resistance mechanisms (via CARD) and high-exposure dosing.

Standardized Dosing Logic: Integrated dosing recommendations and renal adjustments based on the latest EUCAST clinical breakpoints.

Point-of-Care Exports: One-click PDF generation of currently filtered tables for offline use during clinical rotations.

📊 Data Sources & Interpretation
This tool synthesizes data from high-authority open-source medical references:

NCBI MicroBIGG-E: Provides the genomic and phenotypic data for real-world US resistance tracking.

CARD (Comprehensive Antibiotic Resistance Database): Used to map specific genes (e.g., blaCTX-M-15) to their clinical resistance phenotypes.

EUCAST: The gold standard for clinical breakpoint tables and dosage recommendations.

🛠️ Installation & Local Development

If you wish to run the app locally or contribute to the code:
Clone the repository:

Bash
git clone https://github.com/mozzytop/ABX-Repo.git
cd ABX-Repo
Install dependencies:

Bash
pip install -r requirements.txt
Run the app:

Bash
streamlit run app.py

Disclaimer
This tool is intended for educational and reference purposes for medical professionals and students. It is not a substitute for local hospital antibiograms or professional clinical judgment. Always verify dosing and sensitivities against institutional guidelines.
