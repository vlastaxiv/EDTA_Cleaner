import streamlit as st

from pathlib import Path

# Core helpers: pipeline, data loading & validation, charting
from utils import (
    load_pipeline,
    get_training_data,
    get_example_data,
    read_and_unify,
    validate_columns_presence,
    check_missing,
    normalize_qpcr,
    create_pca_chart,
    create_matplotlib_decision_plot,
    FNR_TO_THRESHOLD,
    highlight_pred,
    get_fnr_explanation,
    UPLOAD_COLUMNS, 
    SAFE_THRESHOLD
)


# Data & plotting
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import warnings

# File I/O
import io

# Project root and data/model paths
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR   = ROOT / "data"
MODELS_DIR = ROOT / "models"

TRAIN_DATA_PATH   = DATA_DIR / "train_165_data.csv"
EXAMPLE_DATA_PATH = DATA_DIR / "example_new_samples.csv"  
CALC_PIPELINE_PATH = MODELS_DIR / "final_pipeline_v1_2025-12-09.joblib"
PLOT_PIPELINE_PATH = MODELS_DIR /"pca2.joblib"

# Global CSS adjustments
st.markdown(
    """
    <style>
    /* Left-align titles and markdown */
    h1, h2, h3, .stMarkdown {
        text-align: left !important;
    }
    /* Ensure DataFrame containers are full-width */
    .element-container {
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Application title
st.title("EDTA Cleaner")
st.markdown(
    "This application evaluates whether gene expression profiles, derived from RNA isolated from EDTA-tube blood,"
    " meet quality standards using a trained Support Vector Machine (SVM) model."
)

# Load pipeline and training dataset
# Load pipeline and training dataset
# Load pipelines and training dataset
try:
    pipeline_calc = load_pipeline(str(CALC_PIPELINE_PATH))  # klasifikace (sklearn Pipeline)
    pca2 = load_pipeline(str(PLOT_PIPELINE_PATH))           # grafy (PCA objekt z pca2.joblib)
    df_train = get_training_data()
    st.success("Model, PCA2 and training data loaded successfully.")
except Exception as e:
    st.error(f"Initialization error: {e}")
    st.stop()


# Expected feature columns
try:
    expected_cols = list(pipeline_calc.feature_names_in_)
except Exception:
    expected_cols = list(pipeline_calc.named_steps['model'].feature_names_in_)



# Sidebar: upload & settings
st.sidebar.header("Upload New Samples for EDTA QC")
with st.sidebar.expander("ℹ️ Detailed upload instructions"):
    st.caption(
        "- Upload either an Excel (*.xlsx) or CSV file\n"
        "- The first column must be named sample and should contain sample names or sample IDs\n"
        "- Upload raw Cq values as exported from the qPCR machine\n"
        "- Do not upload already normalized data; normalization is performed automatically by the app\n"
        "- Required columns: sample, BTG3, CD69, CXCR1, CXCR2, FCGR3A, GAPDH, GUSB, JUN, PPIB, STEAP4\n"
        "- Ensure no missing values are present"
    )
def turn_off_example_dataset():
    st.session_state.use_example_dataset = False


uploaded_file = st.sidebar.file_uploader(
    "Upload your samples (CSV or XLSX)",
    type=["csv", "xlsx"],
    label_visibility="visible",
    key="uploaded_samples_file",
    on_change=turn_off_example_dataset,
)
use_example = st.sidebar.checkbox(
    "Use built-in example dataset (demo only)",
    value=False,
    key="use_example_dataset",
)
if use_example:
    st.sidebar.info("Using the built-in example dataset. Any uploaded file is ignored while the demo is selected.")

# Sidebar: operating-threshold adjustment
st.sidebar.markdown("---")
st.sidebar.header("Optional Threshold Adjustment")
with st.sidebar.expander("ℹ️ Why to adjust FNR?"):
    for line in get_fnr_explanation():
        st.caption(line)
fnr = st.sidebar.selectbox(
    "Select false negative rate (FNR) %",
    list(FNR_TO_THRESHOLD.keys()),
    index=0,
    key="fnr_selectbox"
)
threshold = FNR_TO_THRESHOLD[fnr]

# Sidebar: about link
st.sidebar.markdown("---")
st.sidebar.header("About This Application")
with st.sidebar.expander("ℹ️ SVM parameters and performance"):
    st.caption(
        "- Kernel: Polynomial\n"
        "- Polynomial degree: 2\n"
        "- Regularization parameter (C): 0.1\n"
        "- Coef0: 0.5\n"
        "- Gamma: scale\n"
        "- Training samples: 165\n"
        "- Test samples: 23\n"
        "- SV (% of training data): 18%\n"
        "- Cross-validation AUC (5-fold): 1.0 ± 0"
    )
  
st.sidebar.markdown("[ℹ️ Full documentation](https://github.com/vlastaxiv/EDTA_Cleaner#readme)")

# Load and prepare data
if use_example:
    # Built-in example dataset
    df_new = get_example_data()
    # Validate against model features 
    from utils import validate_data  # ensure function is imported
    validate_data(df_new, expected_cols)

elif uploaded_file:
    try:
        df_raw = read_and_unify(uploaded_file)
        validate_columns_presence(df_raw, UPLOAD_COLUMNS)
        check_missing(df_raw)
        df_new = normalize_qpcr(df_raw, expected_cols)
    except ValueError as err:
        st.warning(f"⚠️ File error: {err} Please check your file and try again.")
        st.stop()

else:
    st.info("Please upload a file or select the example dataset.")
    st.stop()

# Data preview
st.write("## Normalized Data Using Reference Genes ")

# Drop any 'group' or 'groups' columns if present
df_display = df_new.drop(columns=["group", "groups"], errors="ignore").copy()

# Round float values and reset index
float_cols = df_display.select_dtypes(include=["float"]).columns
df_display[float_cols] = df_display[float_cols].round(1)
df_display.index = range(1, len(df_display) + 1)
st.dataframe(df_display, use_container_width=True)

# PCA Projection: Training vs. New Samples
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names*",
    category=UserWarning,
    module="sklearn.utils.validation",
)

chart = create_pca_chart(pipeline_calc, pca2, df_train, df_new, expected_cols)
st.altair_chart(chart, use_container_width=True)

# Display current operating threshold
st.markdown(
    f"**Current operating threshold:** {threshold:.2f} (FNR = {fnr}%). Samples with SVM decision score > operating threshold are classified as OK according to the pipeline."
)

# Prediction step
if st.button("Run Prediction"):
    # Identify the first column name
    first_col = df_new.columns[0]

    # Preprocess input data
    X_input_df = pd.DataFrame(df_new[expected_cols], columns=expected_cols)
    decision_scores = pipeline_calc.decision_function(X_input_df)
   
    # Apply threshold: class 1 if score > threshold, otherwise class 0
    preds = (decision_scores > threshold).astype(int)

    # generate prediction labels based on thresholded decision scores
    pred_labels = [
        "Sample quality is OK." if p == 1 else
        "Do not use this sample. Its gene expression has been altered in EDTA tube."
        for p in preds
    ]

    # Plot decision boundary
    fig = create_matplotlib_decision_plot(
    pipeline_calc, pca2, df_train, df_new, expected_cols, threshold, fnr
    )

    st.pyplot(fig)

    # Display results table
    st.write("## Quality Assessment")


    # Create results DataFrame
    sample_values = df_new["sample"].values if "sample" in df_new.columns else df_new[first_col].values
    df_result = pd.DataFrame({
        'sample': sample_values,
        'decision_score': [f"{score:.2f}".rstrip('0').rstrip('.') for score in decision_scores],
        'prediction': pred_labels
    })

    # Reset index to start from 1 (for display consistency)
    df_result.index = range(1, len(df_result) + 1)

    # Style the results table
    def highlight_pred(val):
        return 'background-color: white; color: black' if val == 'Sample quality is OK.' \
               else 'background-color: #eb9696; color: black'

    styled = (
        df_result.style
                 .map(highlight_pred, subset=['prediction'])
                 .set_properties(subset=['decision_score'], **{'text-align': 'left'})
                 .set_properties(
                     subset=['prediction'],
                     **{
                         'text-align': 'left',
                         'white-space': 'normal',
                         'word-wrap': 'break-word',
                         'min-width': '360px',
                     }
                 )
    )

    # Table visualization
    st.dataframe(
        styled,
        use_container_width=True,
        column_config={
            "sample": st.column_config.TextColumn("sample", width="small"),
            "decision_score": st.column_config.TextColumn("decision_score", width="small"),
            "prediction": st.column_config.TextColumn("prediction", width="large"),
        },
    )

    # Summary of predictions
    total = len(preds)
    ok_count = sum(preds)
    altered_count = total - ok_count
    st.markdown(f"**Support vector model prediction results with selected FNR = {fnr}%:**")
    st.markdown(f"{ok_count} samples OK ({ok_count/total*100:.1f}%), {altered_count} samples with altered gene expression ({altered_count/total*100:.1f}%)"
    )

    # Export results to Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Predictions')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFFF',
            'font_color': '#000000',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        ok_format = workbook.add_format({
            'bg_color': '#FFFFFF',
            'font_color': '#000000',
            'border': 1,
            'valign': 'top',
            'text_wrap': True,
        })
        altered_format = workbook.add_format({
            'bg_color': '#F4A3A3',
            'font_color': '#000000',
            'border': 1,
            'valign': 'top',
            'text_wrap': True,
        })
        default_format = workbook.add_format({
            'bg_color': '#FFFFFF',
            'font_color': '#000000',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        score_format = workbook.add_format({
            'bg_color': '#FFFFFF',
            'font_color': '#000000',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.00',
        })

        for col_num, column_name in enumerate(df_result.columns):
            worksheet.write(0, col_num, column_name, header_format)

        worksheet.set_column('A:A', 24)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 62)
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, len(df_result), len(df_result.columns) - 1)

        for row_num, (_, row) in enumerate(df_result.iterrows(), start=1):
            prediction = row['prediction']
            row_format = ok_format if prediction == "Sample quality is OK." else altered_format
            worksheet.write(row_num, 0, row['sample'], default_format)
            worksheet.write_number(row_num, 1, float(row['decision_score']), score_format)
            worksheet.write(row_num, 2, prediction, row_format)

    excel_buffer.seek(0)
    st.download_button(
        "Download Results (.xlsx)",
        data=excel_buffer,
        file_name = f"Predictions_FNR_{fnr}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

