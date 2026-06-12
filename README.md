# EDTA Blood RNA QC

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20665116.svg)](https://doi.org/10.5281/zenodo.20665116)

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

This project is released under the MIT License.

Copyright (c) 2026 Vlasta Korenková.

See the [LICENSE](LICENSE) file for details.

---

# B. Application usage

## Download the Repository

All commands shown in grey boxes below should be typed into a command-line window:

- **Windows:** open **PowerShell** or **Command Prompt** from the Start menu.
- **macOS:** open **Terminal** from Applications > Utilities.
- **Linux:** open your usual terminal application.

You can also use the built-in terminal in Visual Studio Code: open the project folder in VS Code, then choose **Terminal > New Terminal**.

The archived software release used in the manuscript is available on Zenodo:

```text
git clone https://doi.org/10.5281/zenodo.20665116
```
Alternatively, the repository can be downloaded from GitHub:

```text
git clone https://github.com/vlastaxiv/EDTA_Cleaner.git
```

Then go into the downloaded folder:

```text
cd EDTA_Cleaner
```
To use the archived release corresponding to Zenodo version v1.0.1, switch to that release:

git checkout v1.0.1

Keep the EDTA_Cleaner folder in one stable location on your computer after setup. If you move or rename the folder later, open a new terminal and run cd into the new location before starting the app again.


## Installation

The app needs its own Python environment. Create and activate the environment before starting the app.

The environment only needs to be created once. After it has been created, you do not need to repeat the creation step every time. However, you must activate the environment each time before starting the app.

**Requirements**

- Python 3.10.18
- Python packages listed in src/requirements.txt or src/environment.yml
- Conda (recommended) or Python venv

Choose **one** of the installation options below.

The Conda environment in this guide is called **edta_cleaner**.

The Python venv folder in this guide is called **edta_cleaner_venv**.

If you are a beginner, keep these names exactly as written. If you choose a different name, you must use your own name in all later activation commands too.

### Option 1: Conda environment (recommended)

Create the environment from the included Conda file. This command creates a Conda environment named **edta_cleaner**:

```text
conda env create -n edta_cleaner -f src/environment.yml
```

Run this creation command only once.

The app is now installed. To start it, continue to the Usage section below.

### Option 2: Python venv + pip

Create a virtual environment inside the project folder. This command creates a folder named **edta_cleaner_venv**.

On Windows:

```text
py -3.10 -m venv edta_cleaner_venv
```

On macOS / Linux:

```text
python3.10 -m venv edta_cleaner_venv
```

Run this creation command only once.

Activate the environment now so that the required packages are installed into it.

On Windows:

```text
edta_cleaner_venv\Scripts\activate
```

On macOS / Linux:

```text
source edta_cleaner_venv/bin/activate
```

Install the required packages:

```text
pip install -r src/requirements.txt
```

The app is now installed. To start it, continue to the Usage section below.


## Usage

### Quick start

Use these steps when you simply want to start the app.

1. Open a terminal in the EDTA_Cleaner folder.

2. Activate the environment according to the installation option you used.

   If you installed the app with Conda:

   ```text
   conda activate edta_cleaner
   ```

   If you installed the app with Python venv on Windows:

   ```text
   edta_cleaner_venv\Scripts\activate
   ```

   If you installed the app with Python venv on macOS / Linux:

   ```text
   source edta_cleaner_venv/bin/activate
   ```

3. Start the app from the project folder:

   ```text
   python run_streamlit.py
   ```

4. The Streamlit app should open automatically in a new browser window or tab.
   If it does not open automatically, copy the local URL printed in the
   terminal into your browser. It usually looks like this:

   ```text
   http://localhost:8501
   ```

### Why not run Streamlit directly?

Use `python run_streamlit.py` as the standard start command.

On some Windows Conda installations, the direct command below may fail before
the app is loaded:

```text
streamlit run src/app.py
```

The error can look like this:

```text
ssl.SSLError: [ASN1: NOT_ENOUGH_DATA] not enough data
```

This is caused by Python reading a malformed certificate from the Windows
certificate store while Streamlit is starting. It is not an error in the EDTA
Cleaner app or in the SVM model. The included `run_streamlit.py` launcher avoids
that startup problem and then runs the same Streamlit app.

### Optional next steps inside the app

After the app is open, choose what you want to do.

- **Try the demo dataset**

  The built-in example dataset is optional. It is only a demo dataset for testing that the app works. You do not need to use it before uploading your own data.

  To use the demo data, select **Built-in example dataset** in the sidebar.

- **Upload your own data**

  To analyze your own samples, click **Browse files** and select a CSV or Excel (.xlsx) file.

  Your file must follow the input format described in the **Input Data & Data Format** section below.

- **Adjust the False Negative Rate (FNR)**

  False Negative Rate (FNR) controls how strict the app is when deciding whether a sample is OK according to the pipeline.

  At **FNR = 0%**, the app uses the most conservative validated operating threshold, called the safe threshold. Only samples above this threshold are classified as OK.

  Increasing FNR shifts the operating threshold, so more borderline samples may be classified as OK according to the pipeline.

- **Run prediction and export results**

  Click **Run Prediction** to calculate the quality assessment. The app will show the SVM decision-boundary plot and the results table. You can then download the Excel report.


## 📁 Repository Structure

The repository contains the following key components:

- src/ — Streamlit app and utility scripts
- models/ — saved trained model pipeline (final_pipeline_v1_2025-12-09.joblib), PCA object (pca2.joblib), and safe threshold (safe_threshold.json)
- notebooks/ — Jupyter notebooks used for model development and evaluation
- data/ — input dataset used for model training (train_165_data.csv)
- data_for_testing/ — example files for user testing and upload validation
- src/requirements.txt — list of required Python packages
- src/environment.yml — conda environment specification
- README.md — project documentation (this file)

   
## 📊 Input Data & Data Format

###  Input file format for prediction

- File format: **CSV** or **Excel (.xlsx)**
- Each row corresponds to one sample.
- The first column must be named **sample** and should contain sample names or sample IDs.
- All gene columns must contain raw Cq values as directly exported from the qPCR machine.
- Do not upload already normalized data; normalization is performed automatically in the app.
- Required columns:
sample, BTG3, CD69, CXCR1, CXCR2, FCGR3A, GAPDH, GUSB, JUN, PPIB, STEAP4
- No missing values allowed.
- Decimal commas will be automatically converted to dots.

### Reference genes used for normalization

- GAPDH, GUSB, PPIB

### ΔCq normalization (performed automatically in the Streamlit app)

1. Compute mean Cq of reference genes for each sample.
2. ΔCq = (Cq_gene – Cq_ref_mean)

### Data included in repository

- data/train_165_data.csv — processed input data (ΔCq values) used for model training.
- data_for_testing/ — example files for user testing and error handling demonstration.


## ❌ Error Handling

- The app validates input files before processing.
- File-format or validation errors display a friendly warning in the main panel.
- Common errors handled:
  - Missing required columns
  - Non-numeric or invalid Cq values
  - Missing values
  - Incorrect file format (only CSV or XLSX accepted)


## Contributions

This repository is not open for external contributions. For any issues or questions, please contact the author directly.


## 📑 Citation

If you use EDTA Cleaner, please cite the archived software release:

Korenková V. (2026). EDTA Cleaner (v1.0.1). Zenodo. https://doi.org/10.5281/zenodo.20665116

If you use this code or parts of this pipeline in your own work or publication, please cite the associated article:

[Full citation will be added here once published]

## ✉️ Contact

For questions or support, please contact: ctrnacta@yahoo.com.  

_Last updated: 2026-06-11_

----

# C. Model Development

## 🔬 Model Development in Jupyter Notebooks

The SVM model was developed using blood RNA profiles obtained from EDTA tubes.

### 1️⃣ 1_SVM_model_kernel_20260126.ipynb 

- kernel screening (polynomial vs RBF) on donor-disjoint folds using threshold-free evaluation ROC/AUC
- selection of final hyperparameters

### 2️⃣ 2_SVM_model_development_20260126.ipynb 

- final model development: training of the fixed pipeline (StandardScaler + polynomial-kernel SVM)
- validation on TEST2-R23
- definition of the safe threshold (FNR = 0) as the maximum decision score observed among poor-quality samples in the reference data (DEV-165 + TEST2-R23)

### 3️⃣ 3_SVM_decision_boundary_20260611.ipynb

- model application and threshold exploration:
- uses the unchanged final model (final_pipeline_v1_2025-12-09.joblib) together with the predefined thresholds (no retraining or recalibration)
- computes decision scores for DEV-165, TEST1-23, TEST2-R23, and UNKNOWNS-69 and converts them to QC calls using fixed operating thresholds
- visualizes the decision boundary in PCA space by evaluating the full-space classifier on a PCA grid mapped back to the original feature space (PCA is used for plotting only; classification is performed in the 7D marker space)

### 4️⃣ 4_tumour_marker_case_study_silhouette_20260611.ipynb

- reproduces the tumour-marker case-study analysis for UNKNOWNS-69
- computes shared PC1-PC2 PCA projections for Fig. 6 and full-space silhouette scores for the manuscript and Supplementary Table S13
- performs stratified random-removal analysis to test whether the EDTA Cleaner-filtered improvement exceeds arbitrary sample removal
- uses the case-study CSV files stored in data/

## 📦 Model files

The pipelines are stored in the models/ directory:

   - final_pipeline_v1_2025-12-09.joblib — deployed classification pipeline
   - pca2.joblib - PCA model used only for 2D visualization
   - safe_threshold.json - stored safe-threshold value used as the strictest operating point (FNR = 0)

This file is automatically loaded by the Streamlit app to perform predictions on new data.

---
