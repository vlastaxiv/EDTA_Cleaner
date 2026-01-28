---
# EDTA Blood RNA QC

A Streamlit app for automated quality control of EDTA-tube blood RNA profiles using a custom-trained Support Vector Machine (SVM) model.
The model was developed on internally generated experimental data. The app performs ΔCq normalization (using internal reference genes) and evaluates each sample using a fixed preprocessing and classification pipeline. PCA is used only for visualization (2D projection); classification is computed in the full feature space. Features include interactive PCA plots, adjustable False Negative Rate (FNR) thresholds, and Excel report export.

---

## 📋 Table of Contents

**A. Licence**

**B. Application usage**

1. Clone the Repository  
2. Installation  
3. Usage  
4. Repository Structure  
5. Input Data & Data Format  
6. Error Handling  
7. Contributions  
8. Citation  
9. Contact

**C. Model Development**

10. Model Development & Jupyter Notebooks  
11. Model files

----

# A. Licence

⚠️ **Important notice** 

Copyright (c) 2026 Vlasta Korenková.  
All rights reserved.  

This code is provided for review purposes only.  
It may not be copied, modified, or used in any form until the associated manuscript is published.  
Upon publication, a permissive license will be attached.  

---

# B. Application usage

## 🔽 Clone the Repository

```bash
git clone https://github.com/vlastaxiv/EDTA_Cleaner.git
cd EDTA_Cleaner


## 🚀 Installation

**Requirements**

- Python 3.13.2
- Git
- Conda (recommended) or venv
- Python packages listed in requirements.txt (installed automatically during setup)

### Conda (recommended)

```bash
conda env create -f environment.yml
conda activate predikce_env
```

### pip + venv

```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```


## 🎬 Usage

1. **Start the app** 

```bash
streamlit run src/app.py
   ```

2. **Built-in example**  
   - Check **Built-in example dataset** in the sidebar to instantly load demo data.

3. **Upload your own data**  
   - Click **Browse files** and select a CSV or Excel (.xlsx) file containing these columns (any order):  
     ```
     sample, BTG3, CD69, CXCR1, CXCR2, FCGR3A, GAPDH, GUSB, JUN, PPIB, STEAP4
     ```
   - No missing values allowed. Decimal commas will be auto-converted to dots.

4. **Adjust the False Negative Rate (FNR)**  
   - Use the slider to shift the decision threshold:
     - **0 %** is strictest.
     - **Increasing FNR** permits more borderline samples to pass as OK samples.
     - **Max 10 %** keeps 100 % specificity on training data.

5. **Run Prediction**  
   - Click **Run Prediction**.  
   - View SVM decision-boundary plot.  
   - Inspect the styled results table (white = OK, red = altered).  
   - Download an Excel report.



## 📁 Repository Structure

The repository contains the following key components:

- `src/` — Streamlit app and utility scripts
- `models/` — saved trained model pipeline (`final_pipeline_prob.joblib`)
- `notebooks/` — Jupyter notebooks used for model development and evaluation
- `data/` — input dataset used for model training (`SVM_training_data.csv`)
- `data_for_testing/` — example files for user testing and upload validation
- `requirements.txt` — list of required Python packages
- `environment.yml` — conda environment specification
- `README.md` — project documentation (this file)

   
## 📊 Input Data & Data Format

###  Input file format for prediction

- File format: **CSV** or **Excel (.xlsx)**
- Each row corresponds to one sample.
- **⚠ All values must be raw Cq values as directly exported from the qPCR machine (unprocessed, not normalized).**
- Required columns:
sample, BTG3, CD69, CXCR1, CXCR2, FCGR3A, GAPDH, GUSB, JUN, PPIB, STEAP4
- No missing values allowed.
- Decimal commas will be automatically converted to dots.

### Reference genes used for normalization

- `GAPDH, GUSB, PPIB`

### ΔCq normalization (performed automatically in the Streamlit app)

1. Compute mean Cq of reference genes for each sample.
2. ΔCq = (Cq_gene – Cq_ref_mean)
3. Final value = –ΔCq

### Data included in repository

- data/SVM_training_data.csv — processed input data (-ΔCq values) used for model training.
- data_for_testing/ — example files for user testing and error handling demonstration.


## ❌ Error Handling

- The app validates input files before processing.
- File-format or validation errors display a friendly `⚠️` warning in the main panel.
- Common errors handled:
  - Missing required columns
  - Non-numeric or invalid Cq values
  - Missing values
  - Incorrect file format (only CSV or XLSX accepted)


## Contributions

This repository is not open for external contributions. For any issues or questions, please contact the author directly.


## 📑 Citation

If you use this code or parts of this pipeline in your own work or publication, please cite the associated article:

[Full citation will be added here once published]

Alternatively, you can refer to this repository as:

Korenková V. EDTA Cleaner – Streamlit app for EDTA blood RNA quality control using SVM classification. GitHub repository: https://github.com/vlastaxiv/EDTA_Cleaner


## ✉️ Contact

For questions or support, please contact: `ctrnacta@yahoo.com`.  

_Last updated: 2026-01-28_

----

# C. Model Development

## 🔬 Model Development in Jupyter Notebooks

The SVM model was developed using blood RNA profiles obtained from EDTA tubes.

### 1️⃣ 1_SVM_model_kernel_26012026.ipynb 

- kernel screening (polynomial vs RBF) on donor-disjoint folds using threshold-free evaluation ROC/AUC
- selection of final hyperparameters

### 2️⃣ 2_SVM_model_development_26012026.ipynb 

- final model development: training of the fixed pipeline (StandardScaler + polynomial-kernel SVM)
- validation on TEST2-R23
- definition of the safe threshold (FNR = 0) as the maximum decision score observed among poor-quality samples in the reference data (DEV-165 + TEST2-R23)

### 3️⃣ 3_SVM_decision_boundary_26012026.ipynb

- model application and threshold exploration:
- uses the unchanged final model (final_pipeline_v1_2025-12-09.joblib) together with the predefined thresholds (no retraining or recalibration)
- computes decision scores for DEV-165, TEST1-23, TEST2-R23, and UNKNOWNS-69 and converts them to QC calls using fixed operating thresholds
- visualizes the decision boundary in PCA space by evaluating the full-space classifier on a PCA grid mapped back to the original feature space (PCA is used for plotting only; classification is performed in the 7D marker space)

## 📦 Model files

The pipelines are stored in the models/ directory:

   - final_pipeline_v1_2025-12-09.joblib — complete pipeline containing StandardScaler, PCA transformation, and trained SVM classifier
   - pca2.joblib - PCA model used only for 2D visualization
   - safe_threshold.json - stored safe-threshold value used as the strictest operating point (FNR = 0)

This file is automatically loaded by the Streamlit app to perform predictions on new data.

---
