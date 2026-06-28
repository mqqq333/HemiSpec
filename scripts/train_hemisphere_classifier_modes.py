#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from hemispec.hemisphere_classifier import (
    apply_classifier_feature_transform,
    build_classifier_feature_table,
    run_hemisphere_classifier,
)


MODE_TRANSFORMS = {
    "single": "hemi_zscore",
    "paired_residual": "subject_lr_residual_zscore",
}


def json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")


def backup_existing(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    backup_root.mkdir(parents=True, exist_ok=True)
    target = backup_root / path.name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(path, target)


def feature_names(metric: str, n_roi: int) -> list[str]:
    return [f"{metric}_roi_{idx}" for idx in range(1, n_roi + 1)]


def confusion_matrix_2x2(y_true: np.ndarray, y_pred: np.ndarray) -> list[list[int]]:
    out = [[0, 0], [0, 0]]
    for true, pred in zip(y_true, y_pred):
        out[int(true)][int(pred)] += 1
    return out


def paired_rank_accuracy(pred_df: pd.DataFrame) -> float:
    correct: list[bool] = []
    for _, group in pred_df.groupby("subject", sort=False):
        rows = {str(row["hemi"]).upper(): float(row["p_hat_RH"]) for _, row in group.iterrows()}
        if "L" in rows and "R" in rows:
            correct.append(rows["R"] > rows["L"])
    return float(np.mean(correct)) if correct else float("nan")


def recall_for_label(y_true: np.ndarray, y_pred: np.ndarray, label: int) -> float:
    mask = y_true == label
    return float(np.mean(y_pred[mask] == label)) if np.any(mask) else float("nan")


def auc_score(y_true: np.ndarray, proba: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score(y_true, proba)) if len(np.unique(y_true)) == 2 else float("nan")


def evaluate_pipeline(pipeline, table: pd.DataFrame, metric: str, names: list[str], transform: str, label: str) -> dict[str, object]:
    from sklearn.metrics import accuracy_score

    df = build_classifier_feature_table(table, metric, names)
    df = apply_classifier_feature_transform(df, names, transform)
    X = df[names].to_numpy(dtype=np.float32, copy=True)
    y_true = df["y_true"].to_numpy(dtype=int)
    proba = pipeline.predict_proba(X)[:, 1]
    y_pred = (proba >= 0.5).astype(int)
    pred_df = pd.DataFrame(
        {
            "metric": metric,
            "subject": df["subject"].astype(str),
            "hemi": df["hemi"].astype(str),
            "y_true": y_true,
            "p_hat_RH": proba.astype(float),
            "y_pred": y_pred.astype(int),
            "correct": (y_true == y_pred).astype(int),
        }
    )
    return {
        "label": label,
        "n_samples": int(len(y_true)),
        "n_subjects": int(df["subject"].nunique()),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "auc": auc_score(y_true, proba),
        "left_recall": recall_for_label(y_true, y_pred, 0),
        "right_recall": recall_for_label(y_true, y_pred, 1),
        "paired_rank_accuracy": paired_rank_accuracy(pred_df),
        "confusion_0LH_1RH": confusion_matrix_2x2(y_true, y_pred),
    }


def train_one_metric(
    train_table: pd.DataFrame,
    icbm_table: pd.DataFrame,
    sch_table: pd.DataFrame | None,
    out_root: Path,
    mode: str,
    metric: str,
    n_roi: int,
    inner_splits: int,
    n_jobs: int,
    seed: int,
    max_iter: int,
) -> dict[str, object]:
    from sklearn import __version__ as sklearn_version
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import GridSearchCV, GroupKFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    transform = MODE_TRANSFORMS[mode]
    names = feature_names(metric, n_roi)
    train_df = build_classifier_feature_table(train_table, metric, names)
    train_df = apply_classifier_feature_transform(train_df, names, transform)
    X_train = train_df[names].to_numpy(dtype=np.float32, copy=True)
    y_train = train_df["y_true"].to_numpy(dtype=int)
    groups_train = train_df["subject"].astype(str).to_numpy()

    pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    solver="saga",
                    class_weight="balanced",
                    max_iter=max_iter,
                    random_state=seed,
                    n_jobs=1,
                ),
            ),
        ]
    )
    search = GridSearchCV(
        pipe,
        {"model__C": np.logspace(-4, 4, 30), "model__penalty": ["l2", "l1"]},
        scoring="roc_auc",
        cv=list(GroupKFold(n_splits=inner_splits).split(X_train, y_train, groups=groups_train)),
        refit=True,
        n_jobs=n_jobs,
    )
    search.fit(X_train, y_train)
    best = search.best_estimator_
    p_train = best.predict_proba(X_train)[:, 1]
    y_train_pred = (p_train >= 0.5).astype(int)

    evals = [
        evaluate_pipeline(best, icbm_table, metric, names, transform, "ICBM_external"),
    ]
    if sch_table is not None:
        evals.append(evaluate_pipeline(best, sch_table, metric, names, transform, "SCH_external"))

    metric_dir = out_root / metric
    metric_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"feature": names}).to_csv(metric_dir / "feature_names.csv", index=False)

    summary: dict[str, object] = {
        "metric": metric,
        "classifier_mode": mode,
        "feature_transform": transform,
        "model": "LogisticRegression(saga, class_weight=balanced) + median impute + standard scaler",
        "train_subjects_noICBM": int(train_df["subject"].nunique()),
        "train_samples": int(len(y_train)),
        "n_features": int(len(names)),
        "inner_cv_scoring": "roc_auc",
        "inner_splits": int(inner_splits),
        "best_params": search.best_params_,
        "best_inner_cv_roc_auc": float(search.best_score_),
        "train_auc": auc_score(y_train, p_train),
        "train_accuracy_0p5": float(accuracy_score(y_train, y_train_pred)),
        "train_confusion_0LH_1RH": confusion_matrix_2x2(y_train, y_train_pred),
        "sklearn_version": sklearn_version,
        "label_definition": {"0": "LH atlas labels", "1": "RH atlas labels"},
        "train_meta": {
            "id_col": "subject",
            "n_subjects": int(train_df["subject"].nunique()),
            "n_samples": int(len(y_train)),
            "n_features": int(len(names)),
        },
        "external_evaluations": evals,
    }
    for item in evals:
        if item["label"] == "ICBM_external":
            summary["icbm_external_auc"] = item["auc"]
            summary["icbm_external_acc"] = item["accuracy"]
            summary["icbm_external_paired_rank_acc"] = item["paired_rank_accuracy"]
            summary["test_meta"] = {
                "n_subjects": item["n_subjects"],
                "n_samples": item["n_samples"],
                "n_features": int(len(names)),
            }
        if item["label"] == "SCH_external":
            summary["sch_external_auc"] = item["auc"]
            summary["sch_external_acc"] = item["accuracy"]
            summary["sch_external_paired_rank_acc"] = item["paired_rank_accuracy"]
            summary["sch_external_right_recall"] = item["right_recall"]

    bundle = {
        "pipeline": best,
        "feature_names": names,
        "metric": metric,
        "classifier_mode": mode,
        "feature_transform": transform,
        **summary,
    }
    joblib.dump(bundle, metric_dir / f"{metric}_noICBM_train_ICBM_test_model_bundle.joblib")
    joblib.dump(best, metric_dir / f"{metric}_final_pipeline.joblib")
    write_json(metric_dir / "summary.json", summary)
    (metric_dir / "summary.txt").write_text(
        "\n".join(
            [
                f"metric: {metric}",
                f"classifier_mode: {mode}",
                f"feature_transform: {transform}",
                f"best_inner_cv_roc_auc: {summary['best_inner_cv_roc_auc']}",
                f"icbm_external_acc: {summary.get('icbm_external_acc')}",
                f"sch_external_acc: {summary.get('sch_external_acc')}",
                f"sch_external_right_recall: {summary.get('sch_external_right_recall')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def train_mode(
    train_table: pd.DataFrame,
    icbm_table: pd.DataFrame,
    sch_table: pd.DataFrame | None,
    out_dir: Path,
    mode: str,
    metrics: Iterable[str],
    args: argparse.Namespace,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = [
        train_one_metric(
            train_table=train_table,
            icbm_table=icbm_table,
            sch_table=sch_table,
            out_root=out_dir,
            mode=mode,
            metric=metric,
            n_roi=args.n_roi,
            inner_splits=args.inner_splits,
            n_jobs=args.n_jobs,
            seed=args.seed,
            max_iter=args.max_iter,
        )
        for metric in metrics
    ]
    rows = []
    for summary in summaries:
        icbm = next(item for item in summary["external_evaluations"] if item["label"] == "ICBM_external")
        sch = next((item for item in summary["external_evaluations"] if item["label"] == "SCH_external"), {})
        rows.append(
            {
                "metric": summary["metric"],
                "classifier_mode": mode,
                "feature_transform": summary["feature_transform"],
                "model": summary["model"],
                "train_subjects_noICBM": summary["train_subjects_noICBM"],
                "train_samples": summary["train_samples"],
                "test_subjects_ICBM": icbm["n_subjects"],
                "test_samples": icbm["n_samples"],
                "n_features": summary["n_features"],
                "inner_cv_scoring": summary["inner_cv_scoring"],
                "inner_splits": summary["inner_splits"],
                "best_params": summary["best_params"],
                "best_inner_cv_roc_auc": summary["best_inner_cv_roc_auc"],
                "icbm_external_auc": icbm["auc"],
                "icbm_external_acc": icbm["accuracy"],
                "icbm_external_paired_rank_acc": icbm["paired_rank_accuracy"],
                "sch_external_auc": sch.get("auc", float("nan")),
                "sch_external_acc": sch.get("accuracy", float("nan")),
                "sch_external_right_recall": sch.get("right_recall", float("nan")),
                "sch_external_paired_rank_acc": sch.get("paired_rank_accuracy", float("nan")),
                "confusion_matrix_labels_0LH_1RH": icbm["confusion_0LH_1RH"],
            }
        )
    pd.DataFrame(rows).to_csv(out_dir / "all_model_summaries.csv", index=False)
    write_json(out_dir / "all_model_summaries.json", summaries)
    write_json(
        out_dir / "run_info.json",
        {
            "train_csv": str(args.train_csv),
            "icbm_csv": str(args.icbm_csv),
            "sch_csv": str(args.sch_csv) if args.sch_csv else None,
            "out_dir": str(out_dir),
            "classifier_mode": mode,
            "feature_transform": MODE_TRANSFORMS[mode],
            "metrics": list(metrics),
            "inner_splits": int(args.inner_splits),
            "n_jobs": int(args.n_jobs),
            "seed": int(args.seed),
            "n_roi": int(args.n_roi),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train saved hemisphere classifier modes.")
    parser.add_argument("--train-csv", type=Path, required=True)
    parser.add_argument("--icbm-csv", type=Path, required=True)
    parser.add_argument("--sch-csv", type=Path, default=None)
    parser.add_argument("--single-out-dir", type=Path, required=True)
    parser.add_argument("--paired-out-dir", type=Path, required=True)
    parser.add_argument("--backup-root", type=Path, default=None)
    parser.add_argument("--metrics", default="GLS_ANS,GLS_RNS")
    parser.add_argument("--n-roi", type=int, default=180)
    parser.add_argument("--inner-splits", type=int, default=5)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iter", type=int, default=50000)
    args = parser.parse_args()

    if args.backup_root is not None:
        backup_existing(args.single_out_dir, args.backup_root)
        backup_existing(args.paired_out_dir, args.backup_root)

    train_table = pd.read_csv(args.train_csv)
    icbm_table = pd.read_csv(args.icbm_csv)
    sch_table = pd.read_csv(args.sch_csv) if args.sch_csv else None
    metrics = [part.strip().upper() for part in args.metrics.split(",") if part.strip()]
    train_mode(train_table, icbm_table, sch_table, args.single_out_dir, "single", metrics, args)
    train_mode(train_table, icbm_table, sch_table, args.paired_out_dir, "paired_residual", metrics, args)

    print(f"wrote single classifier: {args.single_out_dir}")
    print(f"wrote paired-residual classifier: {args.paired_out_dir}")


if __name__ == "__main__":
    main()
