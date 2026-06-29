from __future__ import annotations

import contextlib
from concurrent.futures import CancelledError
import importlib.util
import io
import re
import subprocess
import sys
import threading
import traceback
import tkinter as tk
from dataclasses import dataclass, replace
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

from .api import (
    default_input_glob,
    discover_local_dgn_bundles,
    resolve_classifier_model_dir,
    resolve_dgn_model_root,
    resolve_glasser_atlas_path,
    resolve_glasser_label_table,
)
from .hemisphere_classifier import discover_classifier_models
from .workflow import BilateralWorkflowConfig, BilateralWorkflowResult, run_bilateral_workflow

try:  # optional dependency: installed with hemispec-toolkit[gui]
    import customtkinter as ctk
except ImportError:  # pragma: no cover - exercised only on machines without GUI extra
    ctk = None  # type: ignore[assignment]


APP_TITLE = "HemiSpec"
APP_SUBTITLE = "ANS/RNS Generation Workbench"
SCROLL_INCREMENT_PX = 12
APP_DESCRIPTION = (
    "Generate voxel-wise reconstruction-derived hemispheric specificity maps from "
    "preprocessed GM inputs using the packaged HemiSpec workflow."
)
PREPROCESS_NOTE = (
    "Input files should be preprocessed grey-matter maps, typically ending with "
    "*_GM_masked.nii.gz. Run the packaged preprocessing script before this step."
)
ROI_NOTE = (
    "Voxel-wise ANS/RNS maps are the primary output. ROI tables are optional and can "
    "use the default Glasser atlas or a user-provided atlas/label table."
)
VALIDATION_NOTE = (
    "Classifier validation uses ROI features, so enabling it also enables ROI table export. "
    "TRT reliability uses the default paired-session settings. Advanced settings remain "
    "available through the CLI/API."
)

DEFAULT_INPUT_GLOB = default_input_glob()
DEFAULT_DGN_MODEL_ROOT = str(resolve_dgn_model_root())
DEFAULT_GLASSER_ATLAS = str(resolve_glasser_atlas_path())
DEFAULT_GLASSER_LABEL_TABLE = str(resolve_glasser_label_table())
DEFAULT_CLASSIFIER_MODEL_DIR = str(resolve_classifier_model_dir())
_TORCH_AVAILABLE_CACHE: bool | None = None

WORKFLOW_VISIBLE_FIELDS = (
    "input_glob",
    "out_dir",
    "export_roi_table",
    "roi_atlas",
    "roi_label_table",
    "run_classifier",
    "run_trt",
    "keep_intermediate",
)
WORKFLOW_ENCAPSULATED_FIELDS = (
    "model_root",
    "device",
    "roi_stat",
    "classifier_model_dir",
    "classifier_mode",
    "export_voxelwise",
    "write_nan_outside",
    "trt_file_regex",
    "trt_session_a",
    "trt_session_b",
    "gm_thresh",
    "eps",
    "pred_suffix",
    "actual_suffix",
    "clip_low",
    "clip_high",
    "verbose_every",
)
WORKFLOW_REQUIRED_FIELDS = WORKFLOW_VISIBLE_FIELDS + WORKFLOW_ENCAPSULATED_FIELDS

ENCAPSULATED_DEFAULTS = {
    "model_root": DEFAULT_DGN_MODEL_ROOT,
    "device": "auto",
    "roi_stat": "mean",
    "classifier_model_dir": DEFAULT_CLASSIFIER_MODEL_DIR,
    "classifier_mode": "single",
    "export_voxelwise": True,
    "write_nan_outside": True,
    "trt_file_regex": r"(sub-MSC\d+).*?(run-\d+)",
    "trt_session_a": "run-01",
    "trt_session_b": "run-02",
    "gm_thresh": 0.15,
    "eps": 1e-6,
    "pred_suffix": "_PRED_LR_full",
    "actual_suffix": "",
    "clip_low": None,
    "clip_high": None,
    "verbose_every": 50,
}


@dataclass(frozen=True)
class RuntimeAssetStatus:
    """Readiness record for GUI-visible runtime dependencies/assets."""

    key: str
    label: str
    ok: bool
    path: Path | None
    message: str
    guidance: str


def _is_torch_available() -> bool:
    """Return per-process torch availability without importing the heavy package."""

    global _TORCH_AVAILABLE_CACHE
    if _TORCH_AVAILABLE_CACHE is None:
        _TORCH_AVAILABLE_CACHE = importlib.util.find_spec("torch") is not None
    return _TORCH_AVAILABLE_CACHE


def build_runtime_asset_status(state: dict[str, object] | None = None) -> tuple[RuntimeAssetStatus, ...]:
    """Return GUI-ready status rows for optional runtime assets.

    The GUI keeps these checks shallow: it verifies paths, expected bundle
    layouts, and Python-package availability without loading large models or
    neuroimaging payloads.
    """

    values: dict[str, object] = dict(ENCAPSULATED_DEFAULTS)
    if state:
        values.update(state)

    model_root = _optional_path(str(values.get("model_root", DEFAULT_DGN_MODEL_ROOT)))
    classifier_dir = _optional_path(str(values.get("classifier_model_dir", DEFAULT_CLASSIFIER_MODEL_DIR)))
    classifier_mode = str(values.get("classifier_mode", ENCAPSULATED_DEFAULTS["classifier_mode"]))
    roi_atlas = _optional_path(str(values.get("roi_atlas", DEFAULT_GLASSER_ATLAS)))
    roi_label_table = _optional_path(str(values.get("roi_label_table", DEFAULT_GLASSER_LABEL_TABLE)))

    statuses = [
        _dgn_status(model_root),
        _atlas_status(roi_atlas, roi_label_table),
        _classifier_status(classifier_dir, classifier_mode),
        _torch_status(),
    ]
    return tuple(statuses)


def runtime_mode_label(statuses: tuple[RuntimeAssetStatus, ...]) -> str:
    """Return the GUI mode badge; classifier assets are intentionally optional."""

    by_key = {item.key: item for item in statuses}
    required = ("torch", "dgn", "atlas")
    if all(by_key.get(key) is not None and by_key[key].ok for key in required):
        return "Model-enabled"
    return "Lightweight"


def _dgn_status(model_root: Path | None) -> RuntimeAssetStatus:
    if model_root is None:
        return RuntimeAssetStatus(
            key="dgn",
            label="DGN model",
            ok=False,
            path=None,
            message="missing model root",
            guidance="Use the default released DGN bundle, or set HEMISPEC_DGN_MODEL_ROOT for a custom bundle.",
        )
    resolved_root = resolve_dgn_model_root(model_root)
    bundles = discover_local_dgn_bundles(model_root)
    missing = [direction for direction in ("L_to_R", "R_to_L") if direction not in bundles]
    if not missing:
        checkpoints = ", ".join(f"{direction}: {bundle.checkpoint.name}" for direction, bundle in sorted(bundles.items()))
        return RuntimeAssetStatus(
            key="dgn",
            label="DGN model",
            ok=True,
            path=resolved_root,
            message=f"found bilateral checkpoints ({checkpoints})",
            guidance="Ready for DGN inference.",
        )
    if model_root.exists():
        message = f"partial/missing checkpoints ({', '.join(missing)} missing)"
    else:
        message = "missing/not downloaded model root path"
    return RuntimeAssetStatus(
        key="dgn",
        label="DGN model",
        ok=False,
        path=resolved_root,
        message=message,
        guidance="Default installs auto-download released checkpoints on first model run; use --model-root only for custom bundles.",
    )


def _atlas_status(roi_atlas: Path | None, roi_label_table: Path | None) -> RuntimeAssetStatus:
    atlas_ok = roi_atlas is not None and roi_atlas.exists()
    label_ok = roi_label_table is not None and roi_label_table.exists()
    if atlas_ok and label_ok:
        return RuntimeAssetStatus(
            key="atlas",
            label="Glasser atlas",
            ok=True,
            path=roi_atlas,
            message="found atlas and label table",
            guidance="Ready for optional ROI export.",
        )
    missing = []
    if not atlas_ok:
        missing.append("atlas NIfTI")
    if not label_ok:
        missing.append("label table")
    return RuntimeAssetStatus(
        key="atlas",
        label="Glasser atlas",
        ok=False,
        path=roi_atlas or roi_label_table,
        message=f"missing {', '.join(missing)}",
        guidance="Set HEMISPEC_GLASSER_ATLAS / HEMISPEC_GLASSER_LABEL_TABLE or browse custom ROI files.",
    )


def _classifier_status(classifier_dir: Path | None, classifier_mode: str) -> RuntimeAssetStatus:
    if classifier_dir is None:
        return RuntimeAssetStatus(
            key="classifier",
            label="Classifier bundle",
            ok=False,
            path=None,
            message="missing classifier path",
            guidance="Default installs auto-download the released classifier when validation is enabled.",
        )
    try:
        models = discover_classifier_models(classifier_dir, ("ANS", "RNS"))
    except Exception as exc:
        return RuntimeAssetStatus(
            key="classifier",
            label="Classifier bundle",
            ok=False,
            path=classifier_dir,
            message=f"cannot inspect bundle ({exc})",
            guidance="Check classifier mode and bundle layout.",
        )
    if models:
        metrics = ", ".join(metric for metric, _path in models)
        return RuntimeAssetStatus(
            key="classifier",
            label="Classifier bundle",
            ok=True,
            path=classifier_dir,
            message=f"found {metrics} model(s) for mode {classifier_mode}",
            guidance="Ready when classifier validation is enabled.",
        )
    message = "missing classifier model files" if classifier_dir.exists() else "missing/not downloaded classifier directory"
    return RuntimeAssetStatus(
        key="classifier",
        label="Classifier bundle",
        ok=False,
        path=classifier_dir,
        message=message,
        guidance="Classifier validation is optional; the released bundle can auto-download when validation is enabled.",
    )


def _torch_status() -> RuntimeAssetStatus:
    if _is_torch_available():
        return RuntimeAssetStatus(
            key="torch",
            label="PyTorch",
            ok=True,
            path=None,
            message="available",
            guidance="DGN inference can use the installed torch runtime.",
        )
    return RuntimeAssetStatus(
        key="torch",
        label="PyTorch",
        ok=False,
        path=None,
        message="missing",
        guidance="Start the GUI from an environment with torch, e.g. conda activate d2l, or install hemispec-toolkit[model].",
    )


class MissingGuiDependency(RuntimeError):
    """Raised when the optional customtkinter GUI dependency is not installed."""


def ensure_gui_dependency() -> None:
    if ctk is None:
        raise MissingGuiDependency(
            "The HemiSpec GUI requires customtkinter. Install it with:\n"
            "  pip install hemispec-toolkit[gui]\n"
            "or from the repository with:\n"
            "  py -3.12 -m pip install -e .[gui]"
        )


def _optional_path(value: str) -> Path | None:
    text = value.strip()
    return Path(text) if text else None


def _normalize_input_glob(value: str) -> str:
    text = value.strip().strip('"').strip("'")
    path = Path(text)
    return str(path / "*_GM_masked.nii.gz") if path.is_dir() else text


def _path_exists_or_empty(value: str) -> bool:
    text = value.strip()
    return not text or Path(text).exists()


def default_output_dir() -> str:
    return str(Path.cwd() / "hemispec_outputs" / "gui_run")


def _speed_up_scroll(scrollable: object) -> None:
    canvas = getattr(scrollable, "_parent_canvas", None)
    if canvas is not None:
        canvas.configure(yscrollincrement=SCROLL_INCREMENT_PX)


def make_workflow_config(state: dict[str, object]) -> BilateralWorkflowConfig:
    """Convert GUI state into the single workflow config used by CLI/API.

    This is deliberately separate from widgets so tests can enforce the same
    validation rules even when GUI controls are refactored.
    """

    input_glob = _normalize_input_glob(str(state["input_glob"]))
    out_dir = str(state["out_dir"]).strip()
    export_roi_table = bool(state.get("export_roi_table", True))
    run_classifier = bool(state.get("run_classifier", False))
    run_trt = bool(state.get("run_trt", False))

    if not input_glob:
        raise ValueError("GM input glob is required.")
    if not out_dir:
        raise ValueError("Output workspace is required.")

    if run_classifier:
        export_roi_table = True

    roi_atlas = _optional_path(str(state.get("roi_atlas", ""))) if export_roi_table or run_classifier else None
    roi_label_table = _optional_path(str(state.get("roi_label_table", ""))) if export_roi_table or run_classifier else None
    if run_classifier and roi_atlas is not None and not roi_atlas.exists():
        raise ValueError(f"Classifier validation requires an existing ROI atlas: {roi_atlas}")

    clip_low = state.get("clip_low", ENCAPSULATED_DEFAULTS["clip_low"])
    clip_high = state.get("clip_high", ENCAPSULATED_DEFAULTS["clip_high"])
    clip_recon = None
    if clip_low is not None and clip_high is not None:
        clip_recon = (float(clip_low), float(clip_high))

    return BilateralWorkflowConfig(
        input_glob=input_glob,
        out_dir=Path(out_dir),
        model_root=_optional_path(str(state.get("model_root", ENCAPSULATED_DEFAULTS["model_root"]))),
        device=str(state.get("device", ENCAPSULATED_DEFAULTS["device"])),  # type: ignore[arg-type]
        gm_thresh=float(state.get("gm_thresh", ENCAPSULATED_DEFAULTS["gm_thresh"])),
        eps=float(state.get("eps", ENCAPSULATED_DEFAULTS["eps"])),
        clip_recon=clip_recon,
        reconstructed_suffix_to_strip=str(state.get("pred_suffix", ENCAPSULATED_DEFAULTS["pred_suffix"])),
        actual_suffix_to_strip=str(state.get("actual_suffix", ENCAPSULATED_DEFAULTS["actual_suffix"])),
        export_voxelwise=bool(state.get("export_voxelwise", ENCAPSULATED_DEFAULTS["export_voxelwise"])),
        write_nan_outside=bool(state.get("write_nan_outside", ENCAPSULATED_DEFAULTS["write_nan_outside"])),
        export_roi_table=export_roi_table,
        roi_atlas=roi_atlas,
        roi_label_table=roi_label_table,
        roi_stat=str(state.get("roi_stat", ENCAPSULATED_DEFAULTS["roi_stat"])),  # type: ignore[arg-type]
        run_classifier=run_classifier,
        classifier_model_dir=_optional_path(
            str(state.get("classifier_model_dir", ENCAPSULATED_DEFAULTS["classifier_model_dir"]))
        ),
        classifier_mode=str(state.get("classifier_mode", ENCAPSULATED_DEFAULTS["classifier_mode"])),
        run_trt=run_trt,
        keep_intermediate=bool(state.get("keep_intermediate", False)),
        trt_file_regex=str(state.get("trt_file_regex", ENCAPSULATED_DEFAULTS["trt_file_regex"])),
        trt_session_a=str(state.get("trt_session_a", ENCAPSULATED_DEFAULTS["trt_session_a"])),
        trt_session_b=str(state.get("trt_session_b", ENCAPSULATED_DEFAULTS["trt_session_b"])),
        verbose_every=int(state.get("verbose_every", ENCAPSULATED_DEFAULTS["verbose_every"])),
    )


def workflow_cli_command(state: dict[str, object]) -> str:
    """Return a reproducible CLI command equivalent to the visible GUI choices."""

    return " ".join(_workflow_cli_parts(make_workflow_config(state)))


def workflow_cli_display_command(state: dict[str, object]) -> str:
    """Return the same command split over lines for the GUI preview."""

    parts = _workflow_cli_parts(make_workflow_config(state))
    lines = [" ".join(parts[:2])]
    idx = 2
    while idx < len(parts):
        flag = parts[idx]
        if idx + 1 < len(parts) and not parts[idx + 1].startswith("--"):
            lines.append(f"  {flag} {parts[idx + 1]}")
            idx += 2
        else:
            lines.append(f"  {flag}")
            idx += 1
    return " `\n".join(lines)


def _workflow_cli_parts(config: BilateralWorkflowConfig) -> list[str]:
    parts = [
        "hemispec",
        "workflow",
        "--input-glob",
        _quote(config.input_glob),
        "--out-dir",
        _quote(str(config.out_dir)),
    ]
    if not config.export_roi_table:
        parts.append("--no-roi-table")
    else:
        if config.roi_atlas is not None:
            parts.extend(["--roi-atlas", _quote(str(config.roi_atlas))])
        if config.roi_label_table is not None:
            parts.extend(["--roi-label-table", _quote(str(config.roi_label_table))])
    if config.run_classifier:
        parts.append("--run-classifier")
    if config.run_trt:
        parts.append("--run-trt")
    if config.keep_intermediate:
        parts.append("--keep-intermediate")
    return parts


def _quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    if not re.fullmatch(r"[A-Za-z0-9_./:\\-]+", escaped):
        return f'"{escaped}"'
    return escaped


def _open_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", str(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class _StdoutProxy(io.TextIOBase):
    def __init__(self, emit: Callable[[str], None]) -> None:
        self._emit = emit

    def write(self, text: str) -> int:
        if text:
            self._emit(text)
        return len(text)

    def flush(self) -> None:
        return None


class HemiSpecGui(ctk.CTk if ctk is not None else tk.Tk):  # type: ignore[misc]
    def __init__(self) -> None:
        ensure_gui_dependency()
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_TITLE} - {APP_SUBTITLE}")
        self.geometry("1080x760")
        self.minsize(960, 680)

        self.is_running = False
        self.cancel_event = threading.Event()
        self.last_out_dir: Path | None = None
        self.vars: dict[str, object] = {}
        self.status_var = ctk.StringVar(value="Ready")
        self.runtime_mode_var = ctk.StringVar(value="Mode: checking")
        self.summary_var = ctk.StringVar(value="Primary output: voxel-wise ANS/RNS maps")
        self._status_refresh_after_id: str | None = None

        self._build_state()
        self._build_layout()
        self._sync_roi_state()

    def _build_state(self) -> None:
        self.vars = {
            "input_glob": ctk.StringVar(value=DEFAULT_INPUT_GLOB),
            "out_dir": ctk.StringVar(value=default_output_dir()),
            "export_roi_table": ctk.BooleanVar(value=True),
            "roi_atlas": ctk.StringVar(value=DEFAULT_GLASSER_ATLAS),
            "roi_label_table": ctk.StringVar(value=DEFAULT_GLASSER_LABEL_TABLE),
            "run_classifier": ctk.BooleanVar(value=False),
            "run_trt": ctk.BooleanVar(value=False),
            "keep_intermediate": ctk.BooleanVar(value=False),
        }
        for key, value in ENCAPSULATED_DEFAULTS.items():
            if key not in self.vars:
                self.vars[key] = value

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main = ctk.CTkFrame(self, corner_radius=0, fg_color="#f6f8fb")
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, padx=22, pady=(14, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="ew")
        title_block.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            title_block,
            text="HemiSpec",
            anchor="w",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color="#0f172a",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_block,
            text="Reconstruction-derived Hemispheric Specificity - ANS/RNS generation",
            anchor="w",
            font=ctk.CTkFont(size=13),
            text_color="#475569",
        ).grid(row=1, column=0, pady=(1, 0), sticky="w")
        ctk.CTkLabel(
            header,
            textvariable=self.status_var,
            anchor="e",
            text_color="#2563eb",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=1, padx=(18, 0), sticky="e")
        ctk.CTkLabel(
            header,
            textvariable=self.runtime_mode_var,
            anchor="e",
            text_color="#64748b",
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=1, padx=(18, 0), sticky="e")

        content = ctk.CTkScrollableFrame(main, fg_color="#f6f8fb")
        _speed_up_scroll(content)
        content.grid(row=1, column=0, padx=22, pady=(0, 8), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        self._build_input_card(content, 0)
        self._build_output_card(content, 1)
        self._build_status_card(content, 2)
        self._build_roi_card(content, 3)
        self._build_validation_card(content, 4)
        self._build_run_card(content, 5)

        footer = ctk.CTkFrame(main, height=28, corner_radius=0, fg_color="#f6f8fb")
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer, textvariable=self.summary_var, text_color="#64748b", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=22, pady=(0, 8), sticky="w"
        )

    def _card(
        self,
        parent: object,
        row: int,
        title: str,
        note: str,
        *,
        accent: str,
        bg: str,
        border: str,
    ) -> object:
        card = ctk.CTkFrame(parent, fg_color=bg, border_color=border, border_width=1, corner_radius=14)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(1, weight=1)

        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.grid(row=0, column=0, columnspan=3, padx=16, pady=(12, 1), sticky="ew")
        title_row.grid_columnconfigure(1, weight=1)
        accent_bar = ctk.CTkFrame(title_row, width=6, height=22, fg_color=accent, corner_radius=4)
        accent_bar.grid(row=0, column=0, padx=(0, 8), sticky="nsw")
        accent_bar.grid_propagate(False)
        ctk.CTkLabel(
            title_row,
            text=title,
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=accent,
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(card, text=note, wraplength=760, justify="left", text_color="#475569").grid(
            row=1, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="w"
        )
        return card

    def _build_input_card(self, parent: object, row: int) -> None:
        card = self._card(
            parent,
            row,
            "Input GM maps",
            PREPROCESS_NOTE,
            accent="#2563eb",
            bg="#eff6ff",
            border="#bfdbfe",
        )
        self._entry_row(card, 2, "GM input glob", "input_glob", self._browse_input_file)

    def _build_output_card(self, parent: object, row: int) -> None:
        card = self._card(
            parent,
            row,
            "Output workspace",
            "Choose where HemiSpec writes reconstructions, maps, tables, and logs.",
            accent="#15803d",
            bg="#f0fdf4",
            border="#bbf7d0",
        )
        self._entry_row(card, 2, "Output directory", "out_dir", self._browse_output_dir)
        ctk.CTkLabel(
            card,
            text="Creates: voxel_maps/ (ANS.L, ANS.R, RNS.L, RNS.R) | tables/ | validation/; recon is removed unless kept.",
            text_color="#64748b",
            font=ctk.CTkFont(size=12),
        ).grid(row=3, column=1, padx=(0, 16), pady=(0, 10), sticky="w")

    def _build_status_card(self, parent: object, row: int) -> None:
        card = self._card(
            parent,
            row,
            "Setup status",
            "Check runtime readiness before a long workflow run. DGN checkpoints are the released HemiSpec defaults and can auto-download into the user cache; PyTorch is still required in the active environment.",
            accent="#0891b2",
            bg="#ecfeff",
            border="#a5f3fc",
        )
        self.asset_status_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.asset_status_frame.grid(row=2, column=0, columnspan=3, padx=16, pady=(0, 12), sticky="ew")
        self.asset_status_frame.grid_columnconfigure(1, weight=1)
        self._refresh_runtime_status()

    def _build_roi_card(self, parent: object, row: int) -> None:
        card = self._card(
            parent,
            row,
            "Optional ROI table",
            ROI_NOTE,
            accent="#7c3aed",
            bg="#f5f3ff",
            border="#ddd6fe",
        )
        roi_check = ctk.CTkCheckBox(
            card,
            text="Export ROI table",
            variable=self.vars["export_roi_table"],
            command=self._sync_roi_state,
        )
        roi_check.grid(row=2, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="w")
        self.roi_widgets: list[object] = []
        self.roi_widgets.extend(self._entry_row(card, 3, "ROI atlas NIfTI", "roi_atlas", self._browse_atlas_file))
        self.roi_widgets.extend(self._entry_row(card, 4, "ROI label table", "roi_label_table", self._browse_label_file))

    def _build_validation_card(self, parent: object, row: int) -> None:
        card = self._card(
            parent,
            row,
            "Optional validation",
            VALIDATION_NOTE,
            accent="#c2410c",
            bg="#fff7ed",
            border="#fed7aa",
        )
        ctk.CTkCheckBox(
            card,
            text="Run hemisphere-classifier validation (requires ROI table)",
            variable=self.vars["run_classifier"],
            command=self._sync_classifier_state,
        ).grid(row=2, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="w")
        ctk.CTkCheckBox(card, text="Run TRT reliability", variable=self.vars["run_trt"], command=self._on_config_changed).grid(
            row=3, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="w"
        )
        ctk.CTkCheckBox(
            card,
            text="Keep intermediate reconstructions and one-direction metrics (debug/storage heavy)",
            variable=self.vars["keep_intermediate"],
            command=self._on_config_changed,
        ).grid(row=4, column=0, columnspan=3, padx=16, pady=(0, 12), sticky="w")

    def _build_run_card(self, parent: object, row: int) -> None:
        card = self._card(
            parent,
            row,
            "Run HemiSpec",
            "Review the equivalent CLI command, run the workflow, and inspect logs.",
            accent="#0f172a",
            bg="#f8fafc",
            border="#cbd5e1",
        )
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=2, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="ew")
        actions.grid_columnconfigure(5, weight=1)
        self.run_button = ctk.CTkButton(actions, text="Run HemiSpec", command=self._run_clicked, height=36)
        self.run_button.grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.stop_button = ctk.CTkButton(
            actions, text="Stop", command=self._stop_clicked, height=36, state="disabled", fg_color="#b91c1c"
        )
        self.stop_button.grid(row=0, column=1, padx=(0, 10), sticky="w")
        ctk.CTkButton(actions, text="Copy CLI Command", command=self._copy_cli, height=36, fg_color="#334155").grid(
            row=0, column=2, padx=(0, 10), sticky="w"
        )
        ctk.CTkButton(actions, text="Open Output Folder", command=self._open_output, height=36, fg_color="#475569").grid(
            row=0, column=3, padx=(0, 10), sticky="w"
        )
        ctk.CTkButton(actions, text="Clear Log", command=self._clear_log, height=36, fg_color="#64748b").grid(
            row=0, column=4, sticky="w"
        )

        ctk.CTkLabel(
            card,
            text=(
                "Equivalent CLI command for reproducibility. "
                "ROI atlas / label table are optional reference files for ROI table export; "
                "uncheck Export ROI table to omit them."
            ),
            text_color="#475569",
            font=ctk.CTkFont(size=12),
            wraplength=760,
            justify="left",
        ).grid(row=3, column=0, columnspan=3, padx=16, pady=(0, 4), sticky="w")
        self.cli_box = ctk.CTkTextbox(card, height=92, wrap="word", fg_color="#f8fafc", text_color="#0f172a")
        self.cli_box.grid(row=4, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="ew")
        self._refresh_cli_box()

        self.log_box = ctk.CTkTextbox(card, height=150, wrap="word", fg_color="#0f172a", text_color="#e5e7eb")
        self.log_box.grid(row=5, column=0, columnspan=3, padx=16, pady=(0, 14), sticky="ew")
        self._log("Ready. Configure inputs and click Run HemiSpec.\n")

    def _entry_row(self, parent: object, row: int, label: str, var_key: str, browse: Callable[[], None]) -> list[object]:
        label_widget = ctk.CTkLabel(parent, text=label, text_color="#111827")
        label_widget.grid(row=row, column=0, padx=16, pady=(0, 8), sticky="w")
        entry = ctk.CTkEntry(parent, textvariable=self.vars[var_key], height=34)
        entry.grid(row=row, column=1, padx=(0, 8), pady=(0, 8), sticky="ew")
        entry.bind("<KeyRelease>", lambda _event: self._on_config_changed())
        button = ctk.CTkButton(parent, text="Browse", width=88, command=browse, fg_color="#475569")
        button.grid(row=row, column=2, padx=(0, 16), pady=(0, 8), sticky="e")
        return [label_widget, entry, button]

    def _browse_input_file(self) -> None:
        path = filedialog.askdirectory(title="Select folder containing *_GM_masked.nii.gz files")
        if not path:
            return
        self.vars["input_glob"].set(str(Path(path) / "*_GM_masked.nii.gz"))  # type: ignore[union-attr]
        self._on_config_changed()

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Select output workspace")
        if path:
            self.vars["out_dir"].set(path)  # type: ignore[union-attr]
            self._on_config_changed()

    def _browse_atlas_file(self) -> None:
        path = filedialog.askopenfilename(title="Select ROI atlas NIfTI", filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All", "*")])
        if path:
            self.vars["roi_atlas"].set(path)  # type: ignore[union-attr]
            self._on_config_changed()

    def _browse_label_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select ROI label table", filetypes=[("Tables", "*.xlsx *.csv *.tsv"), ("All", "*")]
        )
        if path:
            self.vars["roi_label_table"].set(path)  # type: ignore[union-attr]
            self._on_config_changed()

    def _sync_classifier_state(self) -> None:
        if bool(self.vars["run_classifier"].get()):  # type: ignore[union-attr]
            self.vars["export_roi_table"].set(True)  # type: ignore[union-attr]
        self._sync_roi_state()

    def _sync_roi_state(self) -> None:
        roi_enabled = bool(self.vars["export_roi_table"].get()) or bool(self.vars["run_classifier"].get())  # type: ignore[union-attr]
        state = "normal" if roi_enabled else "disabled"
        warned = False
        for widget in getattr(self, "roi_widgets", []):
            try:
                widget.configure(state=state)
            except (tk.TclError, AttributeError, ValueError) as exc:
                if not warned:
                    self._log(f"[warning] Could not update ROI widget state: {exc}\n")
                    warned = True
        self._on_config_changed()

    def _state_snapshot(self) -> dict[str, object]:
        snapshot: dict[str, object] = {}
        for key in WORKFLOW_VISIBLE_FIELDS:
            value = self.vars[key]
            snapshot[key] = value.get() if hasattr(value, "get") else value
        snapshot.update(ENCAPSULATED_DEFAULTS)
        return snapshot

    def _validate_state(self) -> dict[str, object]:
        state = self._state_snapshot()
        make_workflow_config(state)
        if bool(state["export_roi_table"]):
            atlas = str(state.get("roi_atlas", ""))
            label_table = str(state.get("roi_label_table", ""))
            if atlas and not _path_exists_or_empty(atlas):
                self._log(f"[warning] ROI atlas not found; workflow will continue without ROI tables unless classifier validation requires ROI features: {atlas}\n")
            if label_table and not _path_exists_or_empty(label_table):
                self._log(f"[warning] ROI label table not found; labels will be skipped if ROI export runs: {label_table}\n")
        return state

    def _on_config_changed(self) -> None:
        self._refresh_cli_box()
        self._schedule_runtime_status_refresh()

    def _schedule_runtime_status_refresh(self, delay_ms: int = 300) -> None:
        if not hasattr(self, "asset_status_frame"):
            return
        if self._status_refresh_after_id is not None:
            try:
                self.after_cancel(self._status_refresh_after_id)
            except tk.TclError:
                pass
        self._status_refresh_after_id = self.after(delay_ms, self._refresh_runtime_status)

    def _refresh_runtime_status(self) -> None:
        self._status_refresh_after_id = None
        if not hasattr(self, "asset_status_frame"):
            return
        for child in self.asset_status_frame.winfo_children():
            child.destroy()

        statuses = build_runtime_asset_status(self._state_snapshot())
        self.runtime_mode_var.set(f"Mode: {runtime_mode_label(statuses)}")
        for row, item in enumerate(statuses):
            row_frame = ctk.CTkFrame(self.asset_status_frame, fg_color="transparent")
            row_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=3)
            row_frame.grid_columnconfigure(1, weight=1)

            color = "#15803d" if item.ok else "#b45309"
            badge_bg = "#dcfce7" if item.ok else "#fef3c7"
            badge_text = "found" if item.ok else "missing"
            ctk.CTkLabel(
                row_frame,
                text=badge_text,
                width=70,
                fg_color=badge_bg,
                text_color=color,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="nw")

            detail_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            detail_frame.grid(row=0, column=1, sticky="ew")
            detail_frame.grid_columnconfigure(0, weight=1)
            message = f"{item.label}: {item.message}"
            if item.path is not None:
                message += f" | {item.path}"
            ctk.CTkLabel(
                detail_frame,
                text=message,
                text_color="#0f172a",
                anchor="w",
                justify="left",
                wraplength=760,
            ).grid(row=0, column=0, sticky="ew")
            ctk.CTkLabel(
                detail_frame,
                text=item.guidance,
                text_color="#64748b",
                anchor="w",
                justify="left",
                wraplength=760,
                font=ctk.CTkFont(size=12),
            ).grid(row=1, column=0, sticky="ew", pady=(0, 4))

    def _refresh_cli_box(self) -> None:
        if not hasattr(self, "cli_box"):
            return
        try:
            cli = workflow_cli_display_command(self._state_snapshot())
        except Exception as exc:  # keep GUI responsive while fields are being edited
            cli = f"# incomplete configuration: {exc}"
        self.cli_box.configure(state="normal")
        self.cli_box.delete("1.0", "end")
        self.cli_box.insert("1.0", cli)
        self.cli_box.configure(state="disabled")

    def _copy_cli(self) -> None:
        try:
            cli = workflow_cli_command(self._state_snapshot())
        except Exception as exc:
            messagebox.showerror("Cannot build CLI command", str(exc))
            return
        self.clipboard_clear()
        self.clipboard_append(cli)
        self.status_var.set("CLI command copied")

    def _open_output(self) -> None:
        try:
            out = Path(str(self.vars["out_dir"].get()))  # type: ignore[union-attr]
            if not out.exists():
                messagebox.showinfo("Output folder not found", "Run the workflow first, or choose an existing output folder.")
                return
            _open_path(out)
        except Exception as exc:
            messagebox.showerror("Cannot open output folder", str(exc))

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _run_clicked(self) -> None:
        if self.is_running:
            return
        try:
            state = self._validate_state()
            config = make_workflow_config(state)
        except Exception as exc:
            messagebox.showerror("Invalid HemiSpec configuration", str(exc))
            return

        self.cancel_event.clear()
        config = replace(config, should_cancel=self.cancel_event.is_set)
        self.is_running = True
        self.last_out_dir = config.out_dir
        self.run_button.configure(state="disabled", text="Running...")
        self.stop_button.configure(state="normal", text="Stop")
        self.status_var.set("Running HemiSpec workflow")
        self._log("\n[run] Starting HemiSpec standard workflow\n")
        self._log(f"[run] output: {config.out_dir}\n")
        self._log(f"[run] CLI: {workflow_cli_command(state)}\n")

        thread = threading.Thread(target=self._run_worker, args=(config,), daemon=True)
        thread.start()

    def _stop_clicked(self) -> None:
        if not self.is_running:
            return
        self.cancel_event.set()
        self.stop_button.configure(state="disabled", text="Stopping...")
        self.status_var.set("Stopping after current file")
        self._log("[cancel] Stop requested; waiting for the current file to finish.\n")

    def _run_worker(self, config: BilateralWorkflowConfig) -> None:
        try:
            with contextlib.redirect_stdout(_StdoutProxy(self._threadsafe_log)), contextlib.redirect_stderr(
                _StdoutProxy(self._threadsafe_log)
            ):
                result = run_bilateral_workflow(config)
            self.after(0, lambda result=result: self._run_finished(result, None))
        except Exception as exc:  # pragma: no cover - GUI worker path
            detail = traceback.format_exc()
            self.after(0, lambda exc=exc, detail=detail: self._run_finished(None, (exc, detail)))

    def _run_finished(self, result: BilateralWorkflowResult | None, error: tuple[BaseException, str] | None) -> None:
        self.is_running = False
        self.cancel_event.clear()
        self.run_button.configure(state="normal", text="Run HemiSpec")
        self.stop_button.configure(state="disabled", text="Stop")
        if error is not None:
            exc, detail = error
            if isinstance(exc, CancelledError):
                self.status_var.set("Stopped")
                self._log("[stopped] HemiSpec workflow stopped by user.\n")
                return
            self.status_var.set("Failed")
            self._log(f"[error] {exc}\n{detail}\n")
            messagebox.showerror("HemiSpec workflow failed", str(exc))
            return
        assert result is not None
        self.status_var.set("Done")
        self.summary_var.set(f"Done: {result.hemi_maps_dir}")
        self._log("[done] HemiSpec workflow complete\n")
        self._log(f"voxel_maps: {result.hemi_maps_dir}\n")
        intermediate_status = result.combined_maps_dir if result.combined_maps_dir.exists() else "removed"
        self._log(f"intermediate_combined_maps: {intermediate_status}\n")
        self._log(f"subject_summary_csv: {result.subject_summary_csv}\n")
        self._log(f"roi_csv: {result.roi_csv if result.roi_csv else 'skipped'}\n")
        self._log(f"roi_wide_csv: {result.roi_wide_csv if result.roi_wide_csv else 'skipped'}\n")
        if result.classifier is not None:
            self._log(f"classifier_summary: {result.classifier.summary_csv}\n")
        if result.trt is not None:
            self._log(f"trt_summary: {result.trt.summary_csv}\n")

    def _threadsafe_log(self, text: str) -> None:
        self.after(0, lambda: self._log(text))

    def _log(self, text: str) -> None:
        if not hasattr(self, "log_box"):
            return
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")


def main() -> None:
    try:
        ensure_gui_dependency()
    except MissingGuiDependency as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing HemiSpec GUI dependency", str(exc))
        root.destroy()
        raise SystemExit(str(exc)) from exc
    app = HemiSpecGui()
    app.mainloop()


if __name__ == "__main__":
    main()
