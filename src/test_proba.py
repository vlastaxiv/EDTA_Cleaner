from pathlib import Path

import numpy as np

from utils import get_training_data, load_pipeline


ROOT = Path(__file__).resolve().parent.parent
PIPELINE_PATH = ROOT / "models" / "final_pipeline_v1_2025-12-09.joblib"

pipeline = load_pipeline(str(PIPELINE_PATH))
expected_cols = list(pipeline.feature_names_in_)

assert expected_cols == ["BTG3", "CD69", "CXCR1", "CXCR2", "FCGR3A", "JUN", "STEAP4"], (
    f"Unexpected feature columns: {expected_cols}"
)

df_train = get_training_data()
scores = pipeline.decision_function(df_train[expected_cols])

assert scores.shape == (len(df_train),), f"Unexpected score shape: {scores.shape}"
assert np.isfinite(scores).all(), "Non-finite scores in training data"

print("Pipeline smoke test passed.")
