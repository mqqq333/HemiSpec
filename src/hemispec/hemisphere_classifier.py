from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class HemisphereClassifierRun:
    predictions: pd.DataFrame
    summary: pd.DataFrame
    predictions_csv: Path | None = None
    summary_csv: Path | None = None
    message: str = ""


def run_hemisphere_classifier(
    roi_csv: Path,
    model_path: Path,
    out_dir: Path | None = None,
    metrics: tuple[str, ...] = ("ANS", "RNS"),
) -> HemisphereClassifierRun:
    model_specs = discover_classifier_models(model_path, metrics)
    if not model_specs:
        raise RuntimeError(f"No hemisphere classifier model bundles found under {model_path}")

    df = pd.read_csv(roi_csv)
    all_predictions: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []

    for metric, bundle_path in model_specs:
        bundle = _load_joblib_bundle(bundle_path)
        feature_names = list(bundle.get("feature_names") or _read_feature_names(bundle_path.parent))
        if not feature_names:
            raise RuntimeError(f"No feature_names found for classifier bundle: {bundle_path}")
        train_sklearn = str(bundle.get("sklearn_version", ""))
        feature_transform = _bundle_feature_transform(bundle)
        pipeline = bundle.get("pipeline", bundle)
        metric_df = build_classifier_feature_table(df, metric, feature_names)
        metric_df = apply_classifier_feature_transform(metric_df, feature_names, feature_transform)
        X = metric_df[feature_names].to_numpy(dtype=np.float32, copy=True)

        proba = _predict_right_probability(pipeline, X)
        pred = (proba >= 0.5).astype(int)
        pred_df = pd.DataFrame(
            {
                "model_metric": metric,
                "subject": metric_df["subject"].astype(str),
                "hemi": metric_df["hemi"].astype(str),
                "y_true": metric_df["y_true"].astype(int),
                "p_hat_RH": proba.astype(float),
                "y_pred": pred.astype(int),
                "correct": (pred == metric_df["y_true"].to_numpy(dtype=int)).astype(int),
                "model_bundle": str(bundle_path),
                "train_sklearn_version": train_sklearn,
                "feature_transform": feature_transform,
            }
        )
        all_predictions.append(pred_df)
        summaries.append(_summarize_predictions(metric, pred_df, bundle_path, train_sklearn, bundle))

    predictions = pd.concat(all_predictions, ignore_index=True)
    summary = pd.DataFrame(summaries)

    predictions_csv = None
    summary_csv = None
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        predictions_csv = out_dir / "hemisphere_classification_predictions.csv"
        summary_csv = out_dir / "hemisphere_classification_summary.csv"
        predictions.to_csv(predictions_csv, index=False)
        summary.to_csv(summary_csv, index=False)

        provenance = _load_json(model_path / "run_info.json" if model_path.is_dir() else model_path.parent.parent / "run_info.json")
        if provenance:
            (out_dir / "hemisphere_classifier_provenance.json").write_text(
                json.dumps(provenance, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    return HemisphereClassifierRun(
        predictions=predictions,
        summary=summary,
        predictions_csv=predictions_csv,
        summary_csv=summary_csv,
        message=f"hemisphere classification complete for {len(summary)} model(s)",
    )


def discover_classifier_models(model_path: Path, metrics: tuple[str, ...]) -> list[tuple[str, Path]]:
    path = Path(model_path)
    if path.is_file():
        metric = _metric_from_path(path) or _normalize_classifier_metric(metrics[0])
        return [(metric, path)]

    out: list[tuple[str, Path]] = []
    for metric in metrics:
        normalized = _normalize_classifier_metric(metric)
        metric_dir = path / normalized
        candidates = [
            metric_dir / f"{normalized}_noICBM_train_ICBM_test_model_bundle.joblib",
            metric_dir / f"{normalized}_final_pipeline.joblib",
        ]
        found = next((candidate for candidate in candidates if candidate.exists()), None)
        if found is not None:
            out.append((normalized, found))
    return out


def build_classifier_feature_table(df: pd.DataFrame, metric: str, feature_names: Iterable[str]) -> pd.DataFrame:
    metric = _normalize_classifier_metric(metric)
    features = list(feature_names)
    wide = _as_wide_roi_table(df)
    id_col = _infer_id_col(wide)
    subjects = wide[id_col].astype(str).to_numpy()
    left_cols = [_side_feature_to_wide_col(name, metric, "L") for name in features]
    right_cols = [_side_feature_to_wide_col(name, metric, "R") for name in features]

    missing_cols = [col for col in [*left_cols, *right_cols] if col not in wide.columns]
    if missing_cols:
        wide = pd.concat(
            [wide, pd.DataFrame(np.nan, index=wide.index, columns=missing_cols)],
            axis=1,
        )

    left = wide[left_cols].copy()
    right = wide[right_cols].copy()
    left.columns = features
    right.columns = features
    rows = pd.concat([left, right], ignore_index=True)
    rows.insert(0, "y_true", [0] * len(subjects) + [1] * len(subjects))
    rows.insert(0, "hemi", ["L"] * len(subjects) + ["R"] * len(subjects))
    rows.insert(0, "subject", list(subjects) + list(subjects))
    return rows


def apply_classifier_feature_transform(
    metric_df: pd.DataFrame,
    feature_names: Iterable[str],
    transform: str | None,
) -> pd.DataFrame:
    """Apply bundle-declared hemisphere-classifier feature transforms.

    The sklearn pipeline still handles feature-wise train-set scaling. These
    transforms remove per-subject/per-hemisphere intensity shifts before that
    pipeline is called, matching how newer bundles were trained.
    """

    mode = _normalize_feature_transform(transform)
    if mode in {"none", "raw"}:
        return metric_df

    features = list(feature_names)
    out = metric_df.copy()
    values = out[features].to_numpy(dtype=np.float64, copy=True)

    if mode == "hemi_center":
        values = values - _nanmean(values, axis=1)[:, None]
    elif mode == "hemi_zscore":
        values = _zscore(values, axis=1)
    elif mode in {"subject_pair_center", "subject_pair_zscore"}:
        for _, idx in out.groupby("subject", sort=False).groups.items():
            idx = list(idx)
            block = values[idx, :]
            mean = np.nanmean(block.reshape(-1))
            if np.isfinite(mean):
                block = block - mean
            if mode == "subject_pair_zscore":
                scale = np.nanstd(block.reshape(-1))
                if np.isfinite(scale) and scale > 0:
                    block = block / scale
            values[idx, :] = block
    elif mode in {"subject_lr_residual", "subject_lr_residual_zscore"}:
        values = _subject_lr_residual_transform(out, values, zscore=mode.endswith("_zscore"))
    else:
        raise ValueError(f"Unknown hemisphere classifier feature_transform: {transform!r}")

    out.loc[:, features] = values
    return out


def _as_wide_roi_table(df: pd.DataFrame) -> pd.DataFrame:
    if {"kind", "roi_label", "value"}.issubset(df.columns):
        subject_col = _infer_id_col(df)
        work = df.copy()
        work["metric"] = work["kind"].map(_normalize_classifier_metric)
        work["hemi"] = work["roi_label"].map(_label_to_hemi)
        work["roi_k"] = work["roi_label"].map(_label_to_compact_roi)
        work = work[work["hemi"].isin(["L", "R"]) & work["roi_k"].notna()]
        work["feature"] = work["metric"] + "_" + work["hemi"] + "_roi_" + work["roi_k"].astype(int).astype(str)
        wide = work.pivot_table(index=subject_col, columns="feature", values="value", aggfunc="mean", dropna=False)
        wide = wide.reset_index().rename(columns={subject_col: "subject"})
        wide.columns.name = None
        return wide
    return df.copy()


def _bundle_feature_transform(bundle) -> str:
    if not isinstance(bundle, dict):
        return "none"
    value = bundle.get("feature_transform")
    if value is None and isinstance(bundle.get("preprocessing"), dict):
        value = bundle["preprocessing"].get("feature_transform")
    return _normalize_feature_transform(value)


def _normalize_feature_transform(transform: str | None) -> str:
    if transform is None:
        return "none"
    value = str(transform).strip().lower().replace("-", "_")
    return value or "none"


def _nanmean(values: np.ndarray, axis: int) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        counts = np.sum(np.isfinite(values), axis=axis)
        sums = np.nansum(values, axis=axis)
    out = sums / np.maximum(counts, 1)
    out[counts == 0] = np.nan
    return out


def _zscore(values: np.ndarray, axis: int) -> np.ndarray:
    mean = _nanmean(values, axis=axis)
    centered = values - np.expand_dims(mean, axis=axis)
    with np.errstate(invalid="ignore", divide="ignore"):
        scale = np.nanstd(values, axis=axis)
    scale = np.where(np.isfinite(scale) & (scale > 0), scale, 1.0)
    return centered / np.expand_dims(scale, axis=axis)


def _subject_lr_residual_transform(metric_df: pd.DataFrame, values: np.ndarray, zscore: bool) -> np.ndarray:
    out = values.copy()
    for subject, idx in metric_df.groupby("subject", sort=False).groups.items():
        idx = list(idx)
        hemis = metric_df.loc[idx, "hemi"].astype(str).str.upper().to_numpy()
        left_idx = [idx[i] for i, hemi in enumerate(hemis) if hemi == "L"]
        right_idx = [idx[i] for i, hemi in enumerate(hemis) if hemi == "R"]
        if len(left_idx) != 1 or len(right_idx) != 1:
            raise ValueError(
                "feature_transform=subject_lr_residual_zscore requires exactly one L and one R row "
                f"per subject; got subject {subject!r} with hemispheres {list(hemis)!r}."
            )

        pair_idx = [left_idx[0], right_idx[0]]
        pair = out[pair_idx, :]
        finite_counts = np.sum(np.isfinite(pair), axis=1)
        if np.any(finite_counts == 0):
            raise ValueError(
                "feature_transform=subject_lr_residual_zscore requires finite ROI values for both L and R rows "
                f"per subject; got subject {subject!r} with finite feature counts {finite_counts.tolist()}."
            )
        lr_mean = _nanmean(pair, axis=0)
        residual = pair - lr_mean[None, :]
        if zscore:
            scale = np.nanstd(residual.reshape(-1))
            if np.isfinite(scale) and scale > 0:
                residual = residual / scale
        out[pair_idx, :] = residual
    return out


def _normalize_classifier_metric(metric: str) -> str:
    value = metric.strip().upper()
    if value in {"ANS", "GLS_ANS"}:
        return "GLS_ANS"
    if value in {"RNS", "GLS_RNS"}:
        return "GLS_RNS"
    return value


def _label_to_hemi(label: object) -> str:
    value = int(label)
    if 1 <= value <= 180:
        return "L"
    if 1001 <= value <= 1180:
        return "R"
    return ""


def _label_to_compact_roi(label: object) -> int | None:
    value = int(label)
    if 1 <= value <= 180:
        return value
    if 1001 <= value <= 1180:
        return value - 1000
    return None


def _side_feature_to_wide_col(feature: str, metric: str, hemi: str) -> str:
    prefix = f"{metric}_roi_"
    if not feature.startswith(prefix):
        raise ValueError(f"Unexpected classifier feature name {feature!r}; expected prefix {prefix!r}")
    return f"{metric}_{hemi}_roi_{feature[len(prefix):]}"


def _infer_id_col(df: pd.DataFrame) -> str:
    for column in ("subject", "subject_id", "id"):
        if column in df.columns:
            return column
    raise ValueError("ROI CSV must contain a subject, subject_id, or id column.")


def _load_joblib_bundle(path: Path):
    try:
        import joblib
    except ImportError as exc:
        raise ImportError(
            "Hemisphere classification requires joblib and scikit-learn. "
            "Install the classifier extra with `python -m pip install hemispec-toolkit[classifier]`."
        ) from exc

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        return joblib.load(path)


def _predict_right_probability(pipeline, X: np.ndarray) -> np.ndarray:
    if hasattr(pipeline, "predict_proba"):
        proba = pipeline.predict_proba(X)
        if proba.shape[1] < 2:
            raise RuntimeError("Classifier predict_proba returned fewer than two columns.")
        return proba[:, 1]
    decision = pipeline.decision_function(X)
    return 1.0 / (1.0 + np.exp(-decision))


def _summarize_predictions(metric: str, pred_df: pd.DataFrame, bundle_path: Path, train_sklearn: str, bundle) -> dict[str, object]:
    y_true = pred_df["y_true"].to_numpy(dtype=int)
    y_pred = pred_df["y_pred"].to_numpy(dtype=int)
    cm = _confusion_matrix_2x2(y_true, y_pred)
    row: dict[str, object] = {
        "metric": metric,
        "n_samples": int(len(pred_df)),
        "n_subjects": int(pred_df["subject"].nunique()),
        "accuracy": float((y_true == y_pred).mean()),
        "paired_rank_accuracy": _paired_rank_accuracy(pred_df),
        "confusion_0LH_1RH": json.dumps(cm),
        "model_bundle": str(bundle_path),
        "train_sklearn_version": train_sklearn,
    }
    if "feature_transform" in pred_df.columns:
        row["feature_transform"] = str(pred_df["feature_transform"].iloc[0])
    for key in ("best_inner_cv_roc_auc", "icbm_external_auc", "icbm_external_acc", "best_params"):
        if isinstance(bundle, dict) and key in bundle:
            value = bundle[key]
            row[key] = json.dumps(value) if isinstance(value, (dict, list)) else value
    return row


def _paired_rank_accuracy(pred_df: pd.DataFrame) -> float:
    correct: list[bool] = []
    for _, group in pred_df.groupby("subject", sort=False):
        rows = {str(row["hemi"]).upper(): float(row["p_hat_RH"]) for _, row in group.iterrows()}
        if "L" in rows and "R" in rows:
            correct.append(rows["R"] > rows["L"])
    return float(np.mean(correct)) if correct else float("nan")


def _confusion_matrix_2x2(y_true: np.ndarray, y_pred: np.ndarray) -> list[list[int]]:
    out = [[0, 0], [0, 0]]
    for true, pred in zip(y_true, y_pred):
        if true in (0, 1) and pred in (0, 1):
            out[int(true)][int(pred)] += 1
    return out


def _read_feature_names(metric_dir: Path) -> list[str]:
    path = metric_dir / "feature_names.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    if "feature" not in df.columns:
        return []
    return [str(value) for value in df["feature"]]


def _metric_from_path(path: Path) -> str | None:
    upper = path.name.upper()
    if "GLS_ANS" in upper:
        return "GLS_ANS"
    if "GLS_RNS" in upper:
        return "GLS_RNS"
    return None


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
