#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import nibabel as nib
import numpy as np
import pandas as pd


LOW_SLICE = (slice(5, 60), slice(15, 134), slice(15, 102))
HIGH_SLICE = (slice(60, 115), slice(15, 134), slice(15, 102))
ANAT_RIGHT_SLICE = LOW_SLICE
ANAT_LEFT_SLICE = HIGH_SLICE


def json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")


def strip_nii_ext(path: str | Path) -> str:
    name = Path(path).name
    if name.endswith(".nii.gz"):
        return name[:-7]
    if name.endswith(".nii"):
        return name[:-4]
    return Path(name).stem


def make_generator():
    import torch.nn as nn

    class Down3d(nn.Module):
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv3d(in_channels, out_channels, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm3d(out_channels),
                nn.ReLU(inplace=True),
            )

        def forward(self, x):
            return self.conv(x)

    class Up3d(nn.Module):
        def __init__(self, in_channels: int, out_channels: int, stride: int, padding: int, output_padding: int):
            super().__init__()
            self.dcov = nn.Sequential(
                nn.ConvTranspose3d(
                    in_channels,
                    out_channels,
                    kernel_size=3,
                    stride=stride,
                    padding=padding,
                    output_padding=output_padding,
                ),
                nn.BatchNorm3d(out_channels),
                nn.LeakyReLU(inplace=True),
            )

        def forward(self, x):
            return self.dcov(x)

    class Generator(nn.Module):
        def __init__(self):
            super().__init__()
            self.down1 = Down3d(1, 64)
            self.down2 = Down3d(64, 64)
            self.down3 = Down3d(64, 128)
            self.down4 = Down3d(128, 256)
            self.bottle = nn.Conv3d(256, 5000, 1)
            self.up1 = Up3d(5000, 256, 2, 1, 0)
            self.up2 = Up3d(256, 128, 2, 1, 1)
            self.up3 = Up3d(128, 64, 2, 1, 1)
            self.up4 = Up3d(64, 64, 2, 1, 1)
            self.out = nn.Sequential(
                nn.Conv3d(64, 1, 2, 1, 0),
                nn.Sigmoid(),
            )

        def forward(self, inp):
            x = self.down1(inp)
            x = self.down2(x)
            x = self.down3(x)
            x = self.down4(x)
            x = self.bottle(x)
            x = self.up1(x)
            x = self.up2(x)
            x = self.up3(x)
            x = self.up4(x)
            return self.out(x)

    return Generator()


def load_generator(checkpoint: Path, device: str):
    import torch

    model = make_generator().to(device)
    try:
        payload = torch.load(str(checkpoint), map_location=device, weights_only=True)
    except TypeError:
        payload = torch.load(str(checkpoint), map_location=device)
    state = payload.get("state_dict", payload) if isinstance(payload, dict) else payload
    if state and all(str(k).startswith("module.") for k in state.keys()):
        state = {str(k)[7:]: v for k, v in state.items()}
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def resolve_device(requested: str) -> str:
    import torch

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false.")
    return requested


def load_subject_rows(args) -> pd.DataFrame:
    if args.manifest_csv:
        df = pd.read_csv(args.manifest_csv)
        if args.gm_col not in df.columns:
            raise ValueError(f"Manifest is missing gm column {args.gm_col!r}")
        if args.subject_col not in df.columns:
            raise ValueError(f"Manifest is missing subject column {args.subject_col!r}")
        out = df[[args.subject_col, args.gm_col]].rename(columns={args.subject_col: "subject", args.gm_col: "gm_path"})
    else:
        paths = sorted(glob.glob(args.input_glob))
        if not paths:
            raise RuntimeError(f"No input files matched {args.input_glob!r}")
        out = pd.DataFrame({"subject": [strip_nii_ext(p) for p in paths], "gm_path": paths})
    out = out.drop_duplicates(subset=["subject"]).reset_index(drop=True)
    if args.limit and args.limit > 0:
        out = out.iloc[: args.limit].copy()
    return out


def tensor_from_patch(patch: np.ndarray, device: str):
    import torch

    return torch.from_numpy(patch[np.newaxis, np.newaxis].astype(np.float32, copy=False)).to(device)


def run_two_direction_prediction(gm: np.ndarray, model_l2r, model_r2l, device: str, input_mask_threshold: float) -> np.ndarray:
    masked = np.where(gm > float(input_mask_threshold), gm, 0).astype(np.float32, copy=False)
    pred_full = np.zeros(gm.shape, dtype=np.float32)
    with __import__("torch").inference_mode():
        left_src = masked[ANAT_LEFT_SLICE].astype(np.float32, copy=False)
        right_src = masked[ANAT_RIGHT_SLICE].astype(np.float32, copy=False)
        pred_right = model_l2r(tensor_from_patch(left_src, device)).detach().cpu().numpy()[0, 0]
        pred_left = model_r2l(tensor_from_patch(right_src, device)).detach().cpu().numpy()[0, 0]
    pred_full[ANAT_RIGHT_SLICE] = pred_right.astype(np.float32, copy=False)
    pred_full[ANAT_LEFT_SLICE] = pred_left.astype(np.float32, copy=False)
    return pred_full


def mean_by_labels(
    values: np.ndarray,
    atlas: np.ndarray,
    valid: np.ndarray,
    labels: list[int],
    max_label: int,
    ignore_zero_values: bool,
) -> np.ndarray:
    flat_a = atlas.reshape(-1)
    flat_v = values.reshape(-1)
    flat_valid = valid.reshape(-1) & (flat_a > 0) & np.isfinite(flat_v)
    if ignore_zero_values:
        flat_valid &= flat_v != 0
    if not np.any(flat_valid):
        return np.full(len(labels), np.nan, dtype=np.float32)
    labs = flat_a[flat_valid].astype(np.int32, copy=False)
    vals = flat_v[flat_valid].astype(np.float32, copy=False)
    sums = np.bincount(labs, weights=vals, minlength=max_label + 1).astype(np.float64)
    cnts = np.bincount(labs, minlength=max_label + 1).astype(np.int64)
    out = []
    for lab in labels:
        out.append(float(sums[lab] / cnts[lab]) if lab <= max_label and cnts[lab] > 0 else np.nan)
    return np.asarray(out, dtype=np.float32)


def append_metric_columns(rec: dict[str, object], tag: str, left: np.ndarray, right: np.ndarray, eps: float) -> None:
    asym = (left - right) / (left + right + float(eps))
    for k, value in enumerate(left, start=1):
        rec[f"{tag}_L_roi_{k}"] = float(value)
    for k, value in enumerate(right, start=1):
        rec[f"{tag}_R_roi_{k}"] = float(value)
    for k, value in enumerate(asym, start=1):
        rec[f"{tag}_asym_roi_{k}"] = float(value)


def roi_wide_header(n_roi: int) -> list[str]:
    header = ["subject"]
    for tag in ("GLS_ANS", "GLS_RNS"):
        for side in ("L", "R", "asym"):
            for k in range(1, n_roi + 1):
                header.append(f"{tag}_{side}_roi_{k}")
    return header


def run_roi(args) -> None:
    device = resolve_device(args.device)
    print(f"[roi] device={device}")
    rows = load_subject_rows(args)
    print(f"[roi] subjects={len(rows)}")

    atlas_img = nib.load(str(args.atlas_path))
    atlas = np.squeeze(atlas_img.get_fdata()).astype(np.int32)
    max_label = int(np.nanmax(atlas))
    left_labels = list(range(args.lh_start, args.lh_start + args.n_roi))
    right_labels = list(range(args.rh_start, args.rh_start + args.n_roi))
    model_l2r = load_generator(args.ckpt_l2r, device)
    model_r2l = load_generator(args.ckpt_r2l, device)

    skipped: list[dict[str, object]] = []
    n_written = 0
    header = roi_wide_header(args.n_roi)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    partial_csv = args.out_csv.with_suffix(".partial.csv")
    with partial_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        f.flush()
        for idx, row in rows.iterrows():
            subject = str(row["subject"])
            gm_path = Path(str(row["gm_path"]))
            if not gm_path.exists():
                skipped.append({"subject": subject, "reason": "missing_gm", "gm_path": str(gm_path)})
                continue
            try:
                gm_img = nib.load(str(gm_path))
                gm = np.squeeze(gm_img.get_fdata(dtype=np.float32))
                if gm.shape != atlas.shape:
                    raise ValueError(f"shape mismatch gm={gm.shape} atlas={atlas.shape}")
                pred = run_two_direction_prediction(gm, model_l2r, model_r2l, device, args.input_mask_threshold)
                if args.clip_pred_0_1:
                    pred = np.clip(pred, 0.0, 1.0)
                valid = np.isfinite(gm) & np.isfinite(pred) & (gm >= float(args.gm_thresh))
                if args.restrict_to_prediction_mask:
                    valid &= pred != 0
                if not np.any(valid):
                    skipped.append({"subject": subject, "reason": "no_valid_voxels", "gm_path": str(gm_path)})
                    continue
                diff = np.zeros(gm.shape, dtype=np.float32)
                rns = np.zeros(gm.shape, dtype=np.float32)
                d = np.abs(gm - pred).astype(np.float32, copy=False)
                denom = (np.abs(gm) + np.abs(pred) + float(args.eps)).astype(np.float32, copy=False)
                diff[valid] = d[valid]
                rns[valid] = (d[valid] / denom[valid]).astype(np.float32, copy=False)

                rec: dict[str, object] = {"subject": subject}
                for tag, arr in (("GLS_ANS", diff), ("GLS_RNS", rns)):
                    left = mean_by_labels(arr, atlas, valid, left_labels, max_label, args.ignore_zero_roi_values)
                    right = mean_by_labels(arr, atlas, valid, right_labels, max_label, args.ignore_zero_roi_values)
                    append_metric_columns(rec, tag, left, right, args.eps)
                writer.writerow(rec)
                n_written += 1
                if args.flush_every > 0 and (n_written % args.flush_every) == 0:
                    f.flush()
                    os.fsync(f.fileno())
            except Exception as exc:
                skipped.append({"subject": subject, "reason": str(exc), "gm_path": str(gm_path)})
            if (idx + 1) % args.verbose_every == 0 or (idx + 1) == len(rows):
                print(f"[roi] processed={idx + 1}/{len(rows)} written={n_written} skipped={len(skipped)}", flush=True)

    if n_written == 0:
        raise RuntimeError("No ROI rows were written.")
    partial_csv.replace(args.out_csv)
    write_json(
        args.out_csv.with_suffix(".metadata.json"),
        {
            "out_csv": str(args.out_csv),
            "partial_csv": str(partial_csv),
            "n_input_subjects": int(len(rows)),
            "n_written_subjects": int(n_written),
            "n_skipped": int(len(skipped)),
            "skipped_first50": skipped[:50],
            "atlas_path": str(args.atlas_path),
            "ckpt_l2r": str(args.ckpt_l2r),
            "ckpt_r2l": str(args.ckpt_r2l),
            "slice_convention": {
                "low_slice": "5:60,15:134,15:102",
                "high_slice": "60:115,15:134,15:102",
                "anatomical_right_slice": "low_slice",
                "anatomical_left_slice": "high_slice",
                "L2R_checkpoint": "anatomical left high_slice -> anatomical right low_slice",
                "R2L_checkpoint": "anatomical right low_slice -> anatomical left high_slice",
                "roi_L_columns": f"atlas labels {left_labels[0]}..{left_labels[-1]}",
                "roi_R_columns": f"atlas labels {right_labels[0]}..{right_labels[-1]}",
            },
            "gm_thresh": float(args.gm_thresh),
            "input_mask_threshold": float(args.input_mask_threshold),
            "restrict_to_prediction_mask": bool(args.restrict_to_prediction_mask),
            "ignore_zero_roi_values": bool(args.ignore_zero_roi_values),
            "eps": float(args.eps),
        },
    )
    print(f"[roi] wrote {args.out_csv} shape=({n_written}, {len(header)})", flush=True)


def detect_sep(path: Path, user_sep: str = "") -> str:
    if user_sep:
        return user_sep
    header = path.open("r", encoding="utf-8", errors="ignore").readline()
    return "\t" if header.count("\t") > header.count(",") else ","


def infer_id_col(df: pd.DataFrame) -> str:
    for col in ("subject", "subject_id", "id"):
        if col in df.columns:
            return col
    raise ValueError("CSV must contain subject, subject_id, or id.")


def make_cols(metric: str, hemi: str, ids: Iterable[int]) -> list[str]:
    return [f"{metric}_{hemi}_roi_{i}" for i in ids]


def metric_cols(df: pd.DataFrame, metric: str, lh_start: int, n_roi: int, rh_start: int):
    left_ids = list(range(lh_start, lh_start + n_roi))
    left_cols = make_cols(metric, "L", left_ids)
    missing_left = [col for col in left_cols if col not in df.columns]
    if missing_left:
        raise ValueError(f"{metric}: missing left columns, first={missing_left[:5]}")
    schemes = [
        ("absolute", list(range(rh_start, rh_start + n_roi))),
        ("compact_1..n", list(range(1, n_roi + 1))),
        ("sequential_after_LH", list(range(n_roi + 1, n_roi + n_roi + 1))),
    ]
    for scheme, ids in schemes:
        right_cols = make_cols(metric, "R", ids)
        if all(col in df.columns for col in right_cols):
            return left_cols, right_cols, {"metric": metric, "rh_scheme": scheme, "rh_ids_range": [ids[0], ids[-1]]}
    examples = [col for col in df.columns if col.startswith(f"{metric}_R_roi_")][:20]
    raise ValueError(f"{metric}: cannot find complete right columns. Examples: {examples}")


def build_hemi_dataset(df: pd.DataFrame, metric: str, lh_start: int, n_roi: int, rh_start: int):
    id_col = infer_id_col(df)
    df = df.drop_duplicates(subset=[id_col]).copy()
    subjects = df[id_col].astype(str).to_numpy()
    left_cols, right_cols, meta = metric_cols(df, metric, lh_start, n_roi, rh_start)
    x_left = df[left_cols].to_numpy(dtype=np.float32, copy=True)
    x_right = df[right_cols].to_numpy(dtype=np.float32, copy=True)
    x_left[np.isinf(x_left)] = np.nan
    x_right[np.isinf(x_right)] = np.nan
    X = np.vstack([x_left, x_right]).astype(np.float32, copy=False)
    y = np.array([0] * len(subjects) + [1] * len(subjects), dtype=int)
    groups = np.array(list(subjects) + list(subjects), dtype=object)
    sample_subjects = np.array(list(subjects) + list(subjects), dtype=object)
    sample_hemi = np.array(["L"] * len(subjects) + ["R"] * len(subjects), dtype=object)
    feature_names = [f"{metric}_roi_{idx}" for idx in range(1, n_roi + 1)]
    meta.update(
        {
            "id_col": id_col,
            "n_subjects": int(len(subjects)),
            "n_samples": int(len(y)),
            "n_features": int(X.shape[1]),
            "label_definition": {"0": "LH atlas labels", "1": "RH atlas labels"},
        }
    )
    return X, y, groups, feature_names, sample_subjects, sample_hemi, meta


def paired_ranking_accuracy(predictions: pd.DataFrame) -> float:
    ok = []
    for _, group in predictions.groupby("subject"):
        rows = {str(row["hemi"]): float(row["p_hat_RH"]) for _, row in group.iterrows()}
        if "L" in rows and "R" in rows:
            ok.append(rows["R"] > rows["L"])
    return float(np.mean(ok)) if ok else float("nan")


def run_train_eval(args) -> None:
    from sklearn import __version__ as sklearn_version
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
    from sklearn.model_selection import GridSearchCV, GroupKFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    args.out_dir.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(args.train_csv, sep=detect_sep(args.train_csv, args.sep))
    test = pd.read_csv(args.test_csv, sep=detect_sep(args.test_csv, args.sep))
    metrics = [m.strip() for m in re.split(r"[,+]", args.metrics) if m.strip()]
    summaries: list[dict[str, object]] = []
    all_predictions: list[pd.DataFrame] = []

    for metric in metrics:
        metric_dir = args.out_dir / metric
        metric_dir.mkdir(parents=True, exist_ok=True)
        X_train, y_train, groups_train, feature_names, subj_train, hemi_train, train_meta = build_hemi_dataset(
            train, metric, args.lh_start, args.n_roi, args.rh_start
        )
        X_test, y_test, groups_test, feature_names_test, subj_test, hemi_test, test_meta = build_hemi_dataset(
            test, metric, args.lh_start, args.n_roi, args.rh_start
        )
        if feature_names != feature_names_test:
            raise RuntimeError(f"{metric}: train/test feature mismatch")

        pipe = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        solver="saga",
                        class_weight="balanced",
                        max_iter=args.max_iter,
                        random_state=args.seed,
                        n_jobs=1,
                    ),
                ),
            ]
        )
        inner = GroupKFold(n_splits=args.inner_splits)
        search = GridSearchCV(
            pipe,
            {"model__C": np.logspace(-4, 4, 30), "model__penalty": ["l2", "l1"]},
            scoring="roc_auc",
            cv=list(inner.split(X_train, y_train, groups=groups_train)),
            refit=True,
            n_jobs=args.n_jobs,
            verbose=args.verbose_search,
        )
        search.fit(X_train, y_train)
        best = search.best_estimator_
        p_train = best.predict_proba(X_train)[:, 1]
        p_test = best.predict_proba(X_test)[:, 1]
        y_pred = (p_test >= 0.5).astype(int)
        pred_df = pd.DataFrame(
            {
                "metric": metric,
                "subject": subj_test.astype(str),
                "hemi": hemi_test.astype(str),
                "y_true": y_test.astype(int),
                "p_hat_RH": p_test.astype(float),
                "y_pred": y_pred.astype(int),
                "correct": (y_pred == y_test).astype(int),
            }
        )
        pred_df.to_csv(metric_dir / "test_predictions.csv", index=False)
        all_predictions.append(pred_df)

        test_auc = float(roc_auc_score(y_test, p_test)) if len(np.unique(y_test)) == 2 else float("nan")
        train_auc = float(roc_auc_score(y_train, p_train)) if len(np.unique(y_train)) == 2 else float("nan")
        summary = {
            "metric": metric,
            "train_subjects": int(len(np.unique(groups_train))),
            "test_subjects": int(len(np.unique(groups_test))),
            "train_samples": int(len(y_train)),
            "test_samples": int(len(y_test)),
            "best_inner_cv_roc_auc": float(search.best_score_),
            "train_auc": train_auc,
            "test_auc": test_auc,
            "test_accuracy_0p5": float(accuracy_score(y_test, y_pred)),
            "test_paired_ranking_accuracy": paired_ranking_accuracy(pred_df),
            "confusion_0LH_1RH": confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist(),
            "best_params": search.best_params_,
            "sklearn_version": sklearn_version,
            "train_meta": train_meta,
            "test_meta": test_meta,
        }
        summaries.append(summary)
        pd.DataFrame({"feature": feature_names}).to_csv(metric_dir / "feature_names.csv", index=False)
        joblib.dump(
            {
                "pipeline": best,
                "feature_names": feature_names,
                "metric": metric,
                "sklearn_version": sklearn_version,
                **summary,
            },
            metric_dir / f"{metric}_icbmval_gan_noICBM_train_model_bundle.joblib",
        )
        write_json(metric_dir / "summary.json", summary)
        print(
            f"[train-eval] {metric} inner_auc={search.best_score_:.4f} "
            f"test_acc={summary['test_accuracy_0p5']:.4f} paired={summary['test_paired_ranking_accuracy']:.4f}"
        )

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(args.out_dir / "summary.csv", index=False)
    if all_predictions:
        pd.concat(all_predictions, ignore_index=True).to_csv(args.out_dir / "all_test_predictions.csv", index=False)
    write_json(
        args.out_dir / "run_info.json",
        {
            "train_csv": str(args.train_csv),
            "test_csv": str(args.test_csv),
            "metrics": metrics,
            "inner_splits": int(args.inner_splits),
            "n_jobs": int(args.n_jobs),
            "seed": int(args.seed),
        },
    )
    print(f"[train-eval] wrote {args.out_dir}")


def add_roi_parser(sub) -> None:
    parser = sub.add_parser("roi", help="Recompute ANS/RNS Glasser ROI table with two DGN checkpoints.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest-csv", type=Path)
    source.add_argument("--input-glob", default="")
    parser.add_argument("--gm-col", default="gm_path")
    parser.add_argument("--subject-col", default="stem")
    parser.add_argument("--atlas-path", type=Path, required=True)
    parser.add_argument("--ckpt-l2r", type=Path, required=True)
    parser.add_argument("--ckpt-r2l", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--gm-thresh", type=float, default=0.15)
    parser.add_argument("--input-mask-threshold", type=float, default=0.05)
    parser.add_argument("--eps", type=float, default=1e-6)
    parser.set_defaults(restrict_to_prediction_mask=True, ignore_zero_roi_values=True)
    parser.add_argument("--restrict-to-prediction-mask", dest="restrict_to_prediction_mask", action="store_true")
    parser.add_argument("--no-restrict-to-prediction-mask", dest="restrict_to_prediction_mask", action="store_false")
    parser.add_argument("--ignore-zero-roi-values", dest="ignore_zero_roi_values", action="store_true")
    parser.add_argument("--include-zero-roi-values", dest="ignore_zero_roi_values", action="store_false")
    parser.add_argument("--clip-pred-0-1", action="store_true")
    parser.add_argument("--lh-start", type=int, default=1)
    parser.add_argument("--rh-start", type=int, default=1001)
    parser.add_argument("--n-roi", type=int, default=180)
    parser.add_argument("--verbose-every", type=int, default=25)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.set_defaults(func=run_roi)


def add_train_eval_parser(sub) -> None:
    parser = sub.add_parser("train-eval", help="Train original LR hemisphere classifier and test on a second ROI table.")
    parser.add_argument("--train-csv", type=Path, required=True)
    parser.add_argument("--test-csv", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--metrics", default="GLS_ANS,GLS_RNS")
    parser.add_argument("--sep", default="")
    parser.add_argument("--inner-splits", type=int, default=5)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iter", type=int, default=50000)
    parser.add_argument("--verbose-search", type=int, default=0)
    parser.add_argument("--lh-start", type=int, default=1)
    parser.add_argument("--rh-start", type=int, default=1001)
    parser.add_argument("--n-roi", type=int, default=180)
    parser.set_defaults(func=run_train_eval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Temporary ICBM-val GAN ROI recompute and classifier evaluation.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    add_roi_parser(sub)
    add_train_eval_parser(sub)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
