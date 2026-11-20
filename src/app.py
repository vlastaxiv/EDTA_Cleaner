import streamlit as st

from pathlib import Path

# Core helpers: pipeline, data loading & validation, charting
from utils import (
    validate_data,
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
    get_fnr_explanation,
    highlight_pred,
    UPLOAD_COLUMNS,
)


# Data & plotting
import pandas as pd
import matplotlib.pyplot as plt
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

st.set_page_config(page_title="EDTA Cleaner · codex oprava")

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
st.caption("codex oprava")
st.write(
    "Screen EDTA blood RNA expression profiles for handling-related changes. "
    "A FLAG calls for a review of the sample."
)

# Load the released model and the technical repeat used for threshold calibration.
try:
    pipeline_calc = load_pipeline(str(CALC_PIPELINE_PATH))  # klasifikace (sklearn Pipeline)
    pca2 = load_pipeline(str(PLOT_PIPELINE_PATH))           # grafy (PCA objekt z pca2.joblib)
    df_train = get_training_data()
    test2 = pd.read_csv(DATA_DIR / "test2_data.csv")
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
    value=True,
    key="use_example_dataset",
)
if use_example:
    st.sidebar.info("Using the built-in example dataset. Any uploaded file is ignored while the demo is selected.")

# Sidebar: operating-threshold adjustment
st.sidebar.markdown("---")
st.sidebar.header("Operating preset")
with st.sidebar.expander("How are the presets defined?"):
    for line in get_fnr_explanation():
        st.caption(line)
fnr = st.sidebar.selectbox(
    "Select a preset",
    list(FNR_TO_THRESHOLD.keys()),
    index=0,
    format_func=lambda preset: f"FNR{preset}",
    key="fnr_selectbox"
)
threshold = FNR_TO_THRESHOLD[fnr]

# Sidebar: about link
st.sidebar.markdown("---")
st.sidebar.header("About This Application")
with st.sidebar.expander("Model and reference data"):
    st.write(
        "The archived polynomial SVM uses seven markers and was fitted on 165 profiles. "
        "TEST2-R23 is a technical remeasurement of the 23 TEST1 specimens and contributed "
        "to threshold calibration. DEV and TEST1 share one complete record."
    )
st.sidebar.markdown("[Notebook documentation](https://github.com/vlastaxiv/EDTA_Cleaner/tree/v1.0.3-rc.1#readme)")

# Report calibration agreement against measured reference classes at the selected threshold.
reference_scores = pipeline_calc.decision_function(test2[expected_cols])
reference_pass = reference_scores > threshold
affected = test2["groups"].eq(0)
intact = test2["groups"].eq(1)
missed = int((affected & reference_pass).sum())
false_flags = int((intact & ~reference_pass).sum())

st.subheader(f"FNR{fnr} · reference results")
st.write(
    f"**{missed}/{affected.sum()} affected samples passed** ({missed / affected.sum():.1%} missed). "
    f"**{false_flags}/{intact.sum()} intact samples were flagged.**"
)
st.caption(
    f"Observed on TEST2-R23, the 23 technical repeats used in calibration. "
    f"A sample passes when its decision score is greater than {threshold!r}."
)

# Load and prepare data
if use_example:
    # Built-in example dataset
    df_new = get_example_data()
    # Validate against model features 
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


# Drop any 'group' or 'groups' columns if present
df_display = df_new.drop(columns=["group", "groups"], errors="ignore").copy()

# Round float values and reset index
float_cols = df_display.select_dtypes(include=["float"]).columns
df_display[float_cols] = df_display[float_cols].round(1)
df_display.index = range(1, len(df_display) + 1)


# PCA Projection: Training vs. New Samples
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names*",
    category=UserWarning,
    module="sklearn.utils.validation",
)

with st.expander("Normalized inputs and PCA projection"):
    st.dataframe(df_display, use_container_width=True)
    chart = create_pca_chart(pipeline_calc, pca2, df_train, df_new, expected_cols)
    st.altair_chart(chart, use_container_width=True)

# Example results update directly when the preset changes.
if use_example or st.button("Run Prediction"):
    # Identify the first column name
    first_col = df_new.columns[0]

    # Preprocess input data
    X_input_df = pd.DataFrame(df_new[expected_cols], columns=expected_cols)
    decision_scores = pipeline_calc.decision_function(X_input_df)
   
    # Apply threshold: class 1 if score > threshold, otherwise class 0
    preds = (decision_scores > threshold).astype(int)

    pred_labels = ["PASS" if p == 1 else "FLAG" for p in preds]
    total = len(preds)
    flagged = int((preds == 0).sum())
    st.subheader(f"FNR{fnr} · sample results")
    if use_example:
        is_unknown = ~df_new["sample"].isin(test2["sample"])
        flagged_unknown = int((is_unknown & (preds == 0)).sum())
        st.write(
            f"**{flagged_unknown}/{is_unknown.sum()} unknown samples flagged for review.** "
            "Their handling status is unknown."
        )
        boundary = df_new["sample"].eq("EDTA T24 3")
        boundary_score = float(decision_scores[boundary].item())
        boundary_call = "PASS" if boundary_score > threshold else "FLAG"
        st.write(
            f"**EDTA T24 3: {boundary_call}.** This affected reference sample scores "
            f"{boundary_score!r}, exactly the FNR0 threshold in the released data. "
            "Equality gives a FLAG."
        )
        st.caption(f"The example includes {total} samples: {is_unknown.sum()} unknowns and {len(test2)} references.")
    else:
        st.write(f"**{flagged}/{total} samples flagged for review.** {total - flagged} passed.")

    # Create results DataFrame
    sample_values = df_new["sample"].values if "sample" in df_new.columns else df_new[first_col].values
    df_result = pd.DataFrame({
        'sample': sample_values,
        'decision_score': decision_scores,
        'prediction': pred_labels
    })

    # Reset index to start from 1 (for display consistency)
    df_result.index = range(1, len(df_result) + 1)

    # Style the results table
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
            "decision_score": st.column_config.NumberColumn("Decision score", format="%.8f"),
            "prediction": st.column_config.TextColumn("prediction", width="large"),
        },
    )

    with st.expander("Decision boundary in PCA space"):
        fig = create_matplotlib_decision_plot(
            pipeline_calc, pca2, df_train, df_new, expected_cols, threshold, fnr
        )
        st.pyplot(fig)
        plt.close(fig)

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
            'num_format': '0.00000000',
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
            row_format = ok_format if prediction == "PASS" else altered_format
            worksheet.write_string(row_num, 0, str(row['sample']), default_format)
            worksheet.write_number(row_num, 1, float(row['decision_score']), score_format)
            worksheet.write(row_num, 2, prediction, row_format)

    excel_buffer.seek(0)
    st.download_button(
        "Download Results (.xlsx)",
        data=excel_buffer,
        file_name = f"EDTA_Cleaner_codex_oprava_FNR{fnr}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

