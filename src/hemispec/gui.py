from __future__ import annotations

import contextlib
import io
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from .api import (
    DGNInferenceConfig,
    DGNModelBundle,
    HemisphereClassificationConfig,
    MetricComputeConfig,
    PipelineRunConfig,
    ValidationConfig,
    compute_metrics,
    default_classifier_output_path,
    default_input_glob,
    default_trt_output_path,
    discover_local_dgn_bundles,
    resolve_classifier_model_dir,
    resolve_dgn_model_root,
    resolve_glasser_atlas_path,
    resolve_glasser_label_table,
    run_dgn_inference,
    run_pipeline,
    validate_reliability,
    validate_hemisphere_classification,
    validate_specificity,
)
from .workflow import BilateralWorkflowConfig, run_bilateral_workflow


APP_TITLE = "HemiSpec"
APP_SUBTITLE = "Hemisphere Reconstruction Structural Specificity Toolkit"
PREPROCESS_NOTE = (
    "Preprocess T1 images with the packaged HemiSpec preprocessing script first. "
    "Runtime inputs should be preprocessed GM maps ending with *_GM_masked.nii.gz."
)
DGN_RUNTIME_HELP = (
    "DGN inference requires PyTorch. For full local model inference on this workstation, "
    "start the GUI with scripts\\hemispec_gui_d2l.cmd or run the source GUI from the d2l "
    "conda environment. The lightweight packaged EXE can still run compute, TRT, "
    "specificity, and classifier workflows that do not require torch."
)

COLORS = {
    "bg": "#f6f8fb",
    "panel": "#ffffff",
    "panel_alt": "#f9fafb",
    "sidebar": "#111827",
    "sidebar_muted": "#9ca3af",
    "sidebar_active": "#2563eb",
    "text": "#111827",
    "muted": "#6b7280",
    "border": "#d9e1ec",
    "accent": "#2563eb",
    "accent_dark": "#1d4ed8",
    "success": "#15803d",
    "log_bg": "#0f172a",
    "log_fg": "#e5e7eb",
}

PAGE_META = {
    "workflow": (
        "Full Workflow",
        "Run bilateral DGN, ANS/RNS maps, ROI features, classifier validation, and optional TRT.",
    ),
    "pipeline": (
        "Single Direction",
        "Run one trained DGN direction and metric computation for debugging or focused analyses.",
    ),
    "infer": (
        "DGN Inference",
        "Deploy trained DGN checkpoints to generate contralateral GM reconstructions.",
    ),
    "compute": (
        "Compute ANS/RNS",
        "Calculate voxel-wise maps, ROI-wise features, or both from actual and reconstructed GM.",
    ),
    "trt": (
        "TRT Reliability",
        "Estimate test-retest reliability from paired ANS/RNS sessions.",
    ),
    "hemi_classify": (
        "Hemisphere Classifier",
        "Validate ROI-level ANS/RNS features with saved hemisphere-classifier bundles.",
    ),
    "specificity": (
        "Structural Specificity",
        "Measure within-subject versus between-subject structural specificity.",
    ),
}

NAV_ORDER = ["workflow", "pipeline", "infer", "compute", "trt", "hemi_classify", "specificity"]

DEFAULT_FILE_REGEX = r"(sub-MSC\d+).*?(run-\d+)"
DEFAULT_DGN_MODEL_ROOT = str(resolve_dgn_model_root())
DEFAULT_INPUT_GLOB = default_input_glob()
DEFAULT_GLASSER_ATLAS = str(resolve_glasser_atlas_path())
DEFAULT_GLASSER_LABEL_TABLE = str(resolve_glasser_label_table())
DEFAULT_CLASSIFIER_MODEL_DIR = str(resolve_classifier_model_dir())


def _bool(value: tk.BooleanVar) -> bool:
    return bool(value.get())


def _csv_labels(value: str) -> tuple[str, ...]:
    return tuple(part.strip().upper() for part in value.split(",") if part.strip())


def _optional_path(value: str) -> Path | None:
    text = value.strip()
    return Path(text) if text else None


def _classifier_model_dir(value: str, mode: str) -> Path | None:
    path = _optional_path(value)
    if path is None:
        return None
    if mode != "single" and path == Path(DEFAULT_CLASSIFIER_MODEL_DIR):
        return None
    return path


def _torch_runtime_status() -> tuple[bool, str]:
    try:
        import torch
    except ImportError:
        return False, "DGN runtime: PyTorch not available"
    version = getattr(torch, "__version__", "unknown")
    cuda = "CUDA" if torch.cuda.is_available() else "CPU"
    return True, f"DGN runtime: torch {version} / {cuda}"


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, style="App.TFrame")
        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas, style="App.TFrame")

        self.window_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.body.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._sync_canvas_width)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _sync_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_canvas_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.winfo_ismapped():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class HemiSpecGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_TITLE} - {APP_SUBTITLE}")
        self.geometry("1180x780")
        self.minsize(1040, 700)
        self.configure(bg=COLORS["bg"])

        self.pages: dict[str, ScrollableFrame] = {}
        self.nav_buttons: dict[str, tk.Button] = {}
        self.run_buttons: list[ttk.Button] = []
        self.active_page = "pipeline"
        self.status_var = tk.StringVar(value="Ready")
        self.dgn_runtime_available, dgn_runtime_text = _torch_runtime_status()
        self.dgn_status_var = tk.StringVar(value=dgn_runtime_text)
        self.page_title_var = tk.StringVar()
        self.page_subtitle_var = tk.StringVar()

        self._configure_styles()
        self._build_shell()
        self._build_pages()
        self._show_page("workflow")

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        with contextlib.suppress(tk.TclError):
            style.theme_use("clam")

        default_font = ("Segoe UI", 10)
        heading_font = ("Segoe UI Semibold", 16)
        section_font = ("Segoe UI Semibold", 11)

        style.configure(".", font=default_font)
        style.configure("App.TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("Alt.TFrame", background=COLORS["panel_alt"])
        style.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=heading_font)
        style.configure("Subtitle.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=("Segoe UI", 10))
        style.configure("Section.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=section_font)
        style.configure("Hint.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("Field.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=default_font)
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=4)
        style.configure("TCheckbutton", background=COLORS["panel"], foreground=COLORS["text"], font=default_font)
        style.configure("Accent.TButton", padding=(14, 8), foreground="#ffffff", background=COLORS["accent"])
        style.map(
            "Accent.TButton",
            background=[("active", COLORS["accent_dark"]), ("disabled", "#93c5fd")],
            foreground=[("disabled", "#f8fafc")],
        )
        style.configure("Secondary.TButton", padding=(12, 7))

    def _build_shell(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=238)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        tk.Label(
            sidebar,
            text=APP_TITLE,
            bg=COLORS["sidebar"],
            fg="#ffffff",
            font=("Segoe UI Semibold", 22),
            anchor="w",
        ).pack(fill="x", padx=22, pady=(24, 2))
        tk.Label(
            sidebar,
            text="Structural specificity workbench",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_muted"],
            font=("Segoe UI", 9),
            anchor="w",
            wraplength=180,
            justify="left",
        ).pack(fill="x", padx=22, pady=(0, 24))

        for key in NAV_ORDER:
            title, _subtitle = PAGE_META[key]
            button = tk.Button(
                sidebar,
                text=title,
                command=lambda page=key: self._show_page(page),
                anchor="w",
                bd=0,
                padx=18,
                pady=10,
                relief="flat",
                cursor="hand2",
                font=("Segoe UI", 10),
            )
            button.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[key] = button

        tk.Frame(sidebar, bg=COLORS["sidebar"]).pack(fill="both", expand=True)
        tk.Label(
            sidebar,
            text="Runtime scope: trained model deployment, metric export, and validation.",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_muted"],
            wraplength=185,
            justify="left",
            font=("Segoe UI", 8),
        ).pack(fill="x", padx=22, pady=(8, 22))

        main = ttk.Frame(self, style="App.TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(main, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=26, pady=(22, 12))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, textvariable=self.page_title_var, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.page_subtitle_var, style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(3, 0)
        )
        status = tk.Label(
            header,
            textvariable=self.status_var,
            bg="#eaf1ff",
            fg=COLORS["accent_dark"],
            padx=12,
            pady=6,
            font=("Segoe UI Semibold", 9),
        )
        status.grid(row=0, column=1, rowspan=2, sticky="e")
        dgn_status = tk.Label(
            header,
            textvariable=self.dgn_status_var,
            bg="#e8f8ef" if self.dgn_runtime_available else "#fff4e5",
            fg=COLORS["success"] if self.dgn_runtime_available else "#9a3412",
            padx=12,
            pady=6,
            font=("Segoe UI Semibold", 9),
        )
        dgn_status.grid(row=0, column=2, rowspan=2, sticky="e", padx=(8, 0))

        self.content_stack = ttk.Frame(main, style="App.TFrame")
        self.content_stack.grid(row=1, column=0, sticky="nsew", padx=22)
        self.content_stack.grid_rowconfigure(0, weight=1)
        self.content_stack.grid_columnconfigure(0, weight=1)

        log_panel = tk.Frame(main, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        log_panel.grid(row=2, column=0, sticky="ew", padx=26, pady=(10, 20))
        log_panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            log_panel,
            text="Run log",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 6))
        ttk.Button(log_panel, text="Clear", style="Secondary.TButton", command=self._clear_log).grid(
            row=0, column=1, padx=12, pady=(8, 4), sticky="e"
        )
        self.log = tk.Text(
            log_panel,
            height=8,
            wrap="word",
            bg=COLORS["log_bg"],
            fg=COLORS["log_fg"],
            insertbackground=COLORS["log_fg"],
            relief="flat",
            padx=12,
            pady=10,
            font=("Consolas", 9),
        )
        self.log.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))

    def _build_pages(self) -> None:
        for key in NAV_ORDER:
            page = ScrollableFrame(self.content_stack)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

        self.workflow_vars = self._build_workflow_page(self.pages["workflow"].body)
        self.pipeline_vars = self._build_pipeline_page(self.pages["pipeline"].body)
        self.infer_vars = self._build_infer_page(self.pages["infer"].body)
        self.compute_vars = self._build_compute_page(self.pages["compute"].body)
        self.trt_vars = self._build_validation_page(self.pages["trt"].body, "trt")
        self.hemi_classify_vars = self._build_hemi_classify_page(self.pages["hemi_classify"].body)
        self.spec_vars = self._build_validation_page(self.pages["specificity"].body, "specificity")

    def _show_page(self, key: str) -> None:
        self.active_page = key
        title, subtitle = PAGE_META[key]
        self.page_title_var.set(title)
        self.page_subtitle_var.set(subtitle)
        self.pages[key].tkraise()
        for page, button in self.nav_buttons.items():
            active = page == key
            button.configure(
                bg=COLORS["sidebar_active"] if active else COLORS["sidebar"],
                fg="#ffffff" if active else "#d1d5db",
                activebackground=COLORS["sidebar_active"] if active else "#1f2937",
                activeforeground="#ffffff",
            )

    def _build_workflow_page(self, parent: tk.Misc) -> dict[str, object]:
        self._notice(parent, PREPROCESS_NOTE)
        vars_: dict[str, object] = {}

        inputs = self._section(parent, "Inputs and local model assets", "Use preprocessed GM maps; configured local DGN directions are discovered automatically.")
        vars_["input_glob"] = self._field(inputs, "Preprocessed GM glob", 0, DEFAULT_INPUT_GLOB)
        vars_["out_dir"] = self._field(inputs, "Workflow output directory", 1, str(default_trt_output_path("full_workflow")), browse="dir")
        vars_["model_root"] = self._field(inputs, "DGN model root", 2, DEFAULT_DGN_MODEL_ROOT, browse="dir")
        vars_["device"] = self._combo(inputs, "Device", 3, ["auto", "cpu", "cuda"], "auto")

        roi = self._section(parent, "ROI and classifier", "Export Glasser ROI features and validate left/right ROI features with the saved classifier.")
        vars_["roi_atlas"] = self._field(roi, "ROI atlas NIfTI", 0, DEFAULT_GLASSER_ATLAS, browse="file")
        vars_["roi_label_table"] = self._field(roi, "ROI label table", 1, DEFAULT_GLASSER_LABEL_TABLE, browse="file")
        vars_["roi_stat"] = self._combo(roi, "ROI statistic", 2, ["mean", "median"], "mean")
        vars_["run_classifier"] = self._check(roi, "Run hemisphere classifier", 3, True)
        vars_["classifier_model_dir"] = self._field(roi, "Classifier model directory", 4, DEFAULT_CLASSIFIER_MODEL_DIR, browse="dir")
        vars_["classifier_mode"] = self._combo(roi, "Classifier mode", 5, ["single", "paired_residual"], "single")

        outputs = self._section(parent, "Outputs and TRT", "Voxel-wise, ROI-wise, subject mean summaries, and optional test-retest reliability.")
        vars_["export_voxelwise"] = self._check(outputs, "Export direction-level group voxel-wise maps", 0, True)
        vars_["write_nan_outside"] = self._check(outputs, "Write NaN outside valid voxels", 1, True)
        vars_["run_trt"] = self._check(outputs, "Run TRT reliability for repeated sessions", 2, False)
        vars_["trt_file_regex"] = self._field(outputs, "TRT file regex", 3, DEFAULT_FILE_REGEX)
        vars_["trt_session_a"] = self._field(outputs, "TRT session A", 4, "run-01")
        vars_["trt_session_b"] = self._field(outputs, "TRT session B", 5, "run-02")

        params = self._section(parent, "Parameters", "Defaults match the current deployment contract.")
        vars_["gm_thresh"] = self._field(params, "GM threshold", 0, "0.15")
        vars_["eps"] = self._field(params, "RNS epsilon", 1, "1e-6")
        vars_["pred_suffix"] = self._field(params, "Pred suffix to strip", 2, "_PRED_LR_full")
        vars_["actual_suffix"] = self._field(params, "Actual suffix to strip", 3, "")
        vars_["clip_low"] = self._field(params, "Clip low", 4, "")
        vars_["clip_high"] = self._field(params, "Clip high", 5, "")
        vars_["verbose_every"] = self._field(params, "Verbose every", 6, "50")

        self._actions(parent, "Run full workflow", lambda: self._run_workflow(vars_))
        return vars_

    def _section(self, parent: tk.Misc, title: str, description: str = "") -> ttk.Frame:
        shell = tk.Frame(parent, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        shell.pack(fill="x", padx=4, pady=(0, 12))
        tk.Label(
            shell,
            text=title,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 12),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 2))
        if description:
            tk.Label(
                shell,
                text=description,
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 9),
                wraplength=820,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 10))
        body = ttk.Frame(shell, style="Panel.TFrame")
        body.pack(fill="x", padx=16, pady=(6, 16))
        body.grid_columnconfigure(1, weight=1)
        return body

    def _notice(self, parent: tk.Misc, text: str) -> None:
        box = tk.Frame(parent, bg="#eef5ff", highlightbackground="#bfdbfe", highlightthickness=1)
        box.pack(fill="x", padx=4, pady=(0, 12))
        tk.Label(
            box,
            text=text,
            bg="#eef5ff",
            fg="#1e3a8a",
            justify="left",
            wraplength=900,
            font=("Segoe UI", 9),
        ).pack(fill="x", padx=14, pady=10)

    def _field(
        self,
        parent: ttk.Frame,
        label: str,
        row: int,
        default: str = "",
        browse: str | None = None,
        width: int = 20,
    ) -> tk.StringVar:
        var = tk.StringVar(value=default)
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
        ttk.Entry(parent, textvariable=var, width=width).grid(row=row, column=1, sticky="ew", pady=5)
        if browse:
            ttk.Button(parent, text="Browse", style="Secondary.TButton", command=lambda: self._browse(var, browse)).grid(
                row=row, column=2, sticky="ew", padx=(8, 0), pady=5
            )
        return var

    def _combo(
        self,
        parent: ttk.Frame,
        label: str,
        row: int,
        values: list[str],
        default: str,
    ) -> tk.StringVar:
        var = tk.StringVar(value=default)
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
        box = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=18)
        box.grid(row=row, column=1, sticky="w", pady=5)
        return var

    def _check(self, parent: ttk.Frame, label: str, row: int, default: bool) -> tk.BooleanVar:
        var = tk.BooleanVar(value=default)
        ttk.Checkbutton(parent, text=label, variable=var).grid(row=row, column=1, sticky="w", pady=5)
        return var

    def _actions(self, parent: tk.Misc, label: str, command: Callable[[], None]) -> None:
        actions = ttk.Frame(parent, style="App.TFrame")
        actions.pack(fill="x", padx=4, pady=(0, 18))
        button = ttk.Button(actions, text=label, style="Accent.TButton", command=command)
        button.pack(side="right")
        self.run_buttons.append(button)

    def _browse(self, var: tk.StringVar, mode: str) -> None:
        if mode == "dir":
            value = filedialog.askdirectory()
        elif mode == "save_csv":
            value = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        else:
            value = filedialog.askopenfilename()
        if value:
            var.set(value)

    def _build_pipeline_page(self, parent: tk.Misc) -> dict[str, object]:
        self._notice(parent, PREPROCESS_NOTE)
        vars_: dict[str, object] = {}

        inputs = self._section(parent, "Input and trained DGN", "Select one deployed DGN direction and the preprocessed GM maps.")
        vars_["input_glob"] = self._field(inputs, "Preprocessed GM glob", 0, DEFAULT_INPUT_GLOB)
        vars_["direction"] = self._combo(inputs, "DGN direction", 1, ["L_to_R", "R_to_L"], "L_to_R")
        vars_["model_root"] = self._field(inputs, "DGN model root", 2, DEFAULT_DGN_MODEL_ROOT, browse="dir")
        vars_["checkpoint"] = self._field(inputs, "Checkpoint override", 3, "", browse="file")
        vars_["device"] = self._combo(inputs, "Device", 4, ["auto", "cpu", "cuda"], "auto")

        outputs = self._section(parent, "Outputs", "Choose where reconstructed GM and downstream ANS/RNS outputs are written.")
        vars_["recon_dir"] = self._field(outputs, "Reconstructed GM directory", 0, str(default_trt_output_path("recon_L_to_R")), browse="dir")
        vars_["metrics_dir"] = self._field(outputs, "ANS/RNS output directory", 1, str(default_trt_output_path("ANS_RNS_L_to_R")), browse="dir")
        vars_["output_suffix"] = self._field(outputs, "Reconstruction suffix", 2, "_PRED_LR_full.nii.gz")
        vars_["save_subject"] = self._check(outputs, "Save per-subject ANS/RNS maps", 3, True)
        vars_["export_voxelwise"] = self._check(outputs, "Export group voxel-wise NIfTI maps", 4, True)
        vars_["write_nan_outside"] = self._check(outputs, "Write NaN outside valid voxels", 5, False)

        roi = self._section(parent, "Optional ROI route", "Provide an atlas to add ROI-wise ANS/RNS CSV export.")
        vars_["roi_atlas"] = self._field(roi, "ROI atlas NIfTI", 0, DEFAULT_GLASSER_ATLAS, browse="file")
        vars_["roi_label_table"] = self._field(roi, "ROI label table", 1, DEFAULT_GLASSER_LABEL_TABLE, browse="file")
        vars_["roi_out_csv"] = self._field(roi, "ROI output CSV", 2, "", browse="save_csv")
        vars_["roi_stat"] = self._combo(roi, "ROI statistic", 3, ["mean", "median"], "mean")

        params = self._section(parent, "Parameters", "Defaults match the current ANS/RNS runtime contract.")
        vars_["gm_thresh"] = self._field(params, "GM threshold", 0, "0.15")
        vars_["eps"] = self._field(params, "RNS epsilon", 1, "1e-6")
        vars_["pred_suffix"] = self._field(params, "Pred suffix to strip", 2, "_PRED_LR_full")
        vars_["actual_suffix"] = self._field(params, "Actual suffix to strip", 3, "")
        vars_["clip_low"] = self._field(params, "Clip low", 4, "")
        vars_["clip_high"] = self._field(params, "Clip high", 5, "")
        vars_["verbose_every"] = self._field(params, "Verbose every", 6, "50")

        self._actions(parent, "Run DGN + ANS/RNS", lambda: self._run_pipeline(vars_))
        return vars_

    def _build_infer_page(self, parent: tk.Misc) -> dict[str, object]:
        self._notice(parent, PREPROCESS_NOTE)
        vars_: dict[str, object] = {}

        section = self._section(parent, "Inference setup", "Load a trained DGN model and generate contralateral GM maps.")
        vars_["input_glob"] = self._field(section, "Preprocessed GM glob", 0, DEFAULT_INPUT_GLOB)
        vars_["direction"] = self._combo(section, "Direction", 1, ["L_to_R", "R_to_L"], "L_to_R")
        vars_["model_root"] = self._field(section, "DGN model root", 2, DEFAULT_DGN_MODEL_ROOT, browse="dir")
        vars_["checkpoint"] = self._field(section, "Checkpoint override", 3, "", browse="file")
        vars_["device"] = self._combo(section, "Device", 4, ["auto", "cpu", "cuda"], "auto")

        out = self._section(parent, "Output", "Generated maps are pasted back into the full GM volume.")
        vars_["recon_dir"] = self._field(out, "Reconstructed GM directory", 0, str(default_trt_output_path("recon_L_to_R")), browse="dir")
        vars_["output_suffix"] = self._field(out, "Output suffix", 1, "_PRED_LR_full.nii.gz")
        vars_["clip_low"] = self._field(out, "Clip low", 2, "")
        vars_["clip_high"] = self._field(out, "Clip high", 3, "")

        self._actions(parent, "Run DGN inference", lambda: self._run_infer(vars_))
        return vars_

    def _build_compute_page(self, parent: tk.Misc) -> dict[str, object]:
        self._notice(parent, PREPROCESS_NOTE)
        vars_: dict[str, object] = {}

        inputs = self._section(parent, "Actual and reconstructed GM", "Compute ANS/RNS from matched actual and DGN-reconstructed GM maps.")
        vars_["actual_glob"] = self._field(inputs, "Preprocessed GM glob", 0, DEFAULT_INPUT_GLOB)
        vars_["predicted_glob"] = self._field(inputs, "DGN-reconstructed GM glob", 1, str(default_trt_output_path("recon_L_to_R", "*.nii.gz")))
        vars_["out_dir"] = self._field(inputs, "Output directory", 2, str(default_trt_output_path("ANS_RNS_L_to_R")), browse="dir")

        routes = self._section(parent, "Export routes", "Use voxel-wise maps, ROI-wise CSV features, or both.")
        vars_["export_voxelwise"] = self._check(routes, "Export group voxel-wise NIfTI maps", 0, True)
        vars_["save_subject"] = self._check(routes, "Save per-subject ANS/RNS maps", 1, True)
        vars_["write_nan_outside"] = self._check(routes, "Write NaN outside valid voxels", 2, False)
        vars_["roi_atlas"] = self._field(routes, "ROI atlas NIfTI", 3, DEFAULT_GLASSER_ATLAS, browse="file")
        vars_["roi_label_table"] = self._field(routes, "ROI label table", 4, DEFAULT_GLASSER_LABEL_TABLE, browse="file")
        vars_["roi_out_csv"] = self._field(routes, "ROI output CSV", 5, "", browse="save_csv")
        vars_["roi_stat"] = self._combo(routes, "ROI statistic", 6, ["mean", "median"], "mean")

        params = self._section(parent, "Metric parameters", "Defaults follow the published ANS/RNS preprocessing contract.")
        vars_["gm_thresh"] = self._field(params, "GM threshold", 0, "0.15")
        vars_["eps"] = self._field(params, "RNS epsilon", 1, "1e-6")
        vars_["pred_suffix"] = self._field(params, "Pred suffix to strip", 2, "_PRED_LR_full")
        vars_["actual_suffix"] = self._field(params, "Actual suffix to strip", 3, "")

        self._actions(parent, "Compute ANS/RNS", lambda: self._run_compute(vars_))
        return vars_

    def _build_validation_page(self, parent: tk.Misc, mode: str) -> dict[str, object]:
        vars_: dict[str, object] = {"mode": mode}
        default_out = (
            str(default_trt_output_path("trt_L_to_R_auto_hemi"))
            if mode == "trt"
            else str(default_trt_output_path("specificity_L_to_R_auto_hemi"))
        )

        inputs = self._section(parent, "ANS/RNS maps", "Point to per-subject ANS/RNS maps produced by the compute step.")
        vars_["maps_dir"] = self._field(inputs, "Maps directory", 0, str(default_trt_output_path("ANS_RNS_L_to_R", "subject_maps")), browse="dir")
        vars_["out_dir"] = self._field(inputs, "Output directory", 1, default_out, browse="dir")
        vars_["kinds"] = self._field(inputs, "Kinds", 2, "ANS,RNS")
        vars_["suffix_template"] = self._field(inputs, "Suffix template", 3, "_{kind}.nii.gz")
        vars_["file_regex"] = self._field(inputs, "File regex", 4, r"(sub-MSC\d+).*?(run-\d+)")
        vars_["session_a"] = self._field(inputs, "Session A", 5, "run-01")
        vars_["session_b"] = self._field(inputs, "Session B", 6, "run-02")

        settings = self._section(parent, "Validation settings", "Use auto/target hemispheres for one-direction DGN outputs.")
        vars_["hemis"] = self._field(settings, "Hemispheres / ROIs", 0, "auto")
        vars_["dgn_direction"] = self._combo(settings, "DGN direction", 1, ["auto", "L_to_R", "R_to_L", "bilateral"], "auto")
        vars_["metric"] = self._combo(settings, "Similarity metric", 2, ["pearson", "spearman"], "pearson")
        vars_["mask_type"] = self._combo(settings, "Mask type", 3, ["rate", "max"], "rate")
        vars_["thr"] = self._field(settings, "Mask threshold", 4, "0")
        vars_["rate_thr"] = self._field(settings, "Rate threshold", 5, "0.3")
        vars_["mask_mode"] = self._combo(settings, "Mask mode", 6, ["union", "intersect"], "union")
        vars_["hemi_slices"] = self._field(settings, "Custom hemi slices", 7, "")
        vars_["symmetrize"] = self._check(settings, "Symmetrize hemispheres", 8, True)
        vars_["write_plots"] = self._check(settings, "Write summary plots", 9, True)

        label = "Run TRT reliability" if mode == "trt" else "Run specificity validation"
        self._actions(parent, label, lambda: self._run_validation(vars_))
        return vars_

    def _build_hemi_classify_page(self, parent: tk.Misc) -> dict[str, object]:
        vars_: dict[str, object] = {}

        features = self._section(parent, "ROI-level features", "Use an existing ROI CSV, or provide an atlas to derive ROI features from maps.")
        vars_["maps_dir"] = self._field(features, "ANS/RNS maps directory", 0, str(default_trt_output_path("ANS_RNS_L_to_R", "subject_maps")), browse="dir")
        vars_["roi_csv"] = self._field(features, "ROI-wise ANS/RNS CSV", 1, "", browse="file")
        vars_["roi_atlas"] = self._field(features, "ROI atlas NIfTI", 2, DEFAULT_GLASSER_ATLAS, browse="file")
        vars_["roi_label_table"] = self._field(features, "ROI label table", 3, DEFAULT_GLASSER_LABEL_TABLE, browse="file")

        model = self._section(parent, "Saved classifier", "Runtime loads saved sklearn/joblib bundles only; training is out of scope.")
        vars_["classifier_model_dir"] = self._field(
            model,
            "Classifier model directory",
            0,
            DEFAULT_CLASSIFIER_MODEL_DIR,
            browse="dir",
        )
        vars_["classifier_mode"] = self._combo(model, "Classifier mode", 1, ["single", "paired_residual"], "single")
        vars_["checkpoint"] = self._field(model, "Single checkpoint override", 2, "", browse="file")
        vars_["out_dir"] = self._field(model, "Output directory", 3, str(default_classifier_output_path("gui_run")), browse="dir")
        vars_["kinds"] = self._field(model, "Kinds", 4, "ANS,RNS")
        vars_["suffix_template"] = self._field(model, "Suffix template", 5, "_{kind}.nii.gz")
        vars_["file_regex"] = self._field(model, "File regex", 6, r"(?P<subject>.+?)_{kind}\.nii(?:\.gz)?$")
        vars_["device"] = self._combo(model, "Device", 7, ["auto", "cpu", "cuda"], "auto")

        self._actions(parent, "Run hemisphere classifier", lambda: self._run_hemi_classify(vars_))
        return vars_

    def _append_log(self, text: str) -> None:
        self.log.insert("end", text)
        self.log.see("end")

    def _clear_log(self) -> None:
        self.log.delete("1.0", "end")

    def _set_running(self, is_running: bool) -> None:
        state = "disabled" if is_running else "normal"
        for button in self.run_buttons:
            button.configure(state=state)

    def _run_background(self, label: str, fn: Callable[[], None]) -> None:
        self.status_var.set(f"Running: {label}")
        self._set_running(True)
        self._append_log(f"\n[{label}] started\n")

        def worker() -> None:
            buf = io.StringIO()
            ok = True
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                try:
                    fn()
                except Exception:
                    ok = False
                    traceback.print_exc()
            self.after(0, lambda: self._finish(label, ok, buf.getvalue()))

        threading.Thread(target=worker, daemon=True).start()

    def _require_dgn_runtime(self) -> bool:
        if self.dgn_runtime_available:
            return True
        self._append_log(f"\n[DGN runtime] {DGN_RUNTIME_HELP}\n")
        messagebox.showerror(APP_TITLE, DGN_RUNTIME_HELP)
        return False

    def _finish(self, label: str, ok: bool, text: str) -> None:
        self._append_log(text)
        status = "finished" if ok else "failed"
        self._append_log(f"[{label}] {status}\n")
        self.status_var.set("Ready" if ok else f"Failed: {label}")
        self._set_running(False)
        if not ok:
            messagebox.showerror(APP_TITLE, "Task failed. Check the run log for details.")

    def _resolve_model(self, vars_: dict[str, object]) -> DGNModelBundle:
        direction = str(vars_["direction"].get())
        checkpoint = str(vars_["checkpoint"].get()).strip()
        if checkpoint:
            return DGNModelBundle(
                checkpoint=Path(checkpoint),
                direction=direction,  # type: ignore[arg-type]
                source_hemisphere="left" if direction == "L_to_R" else "right",
                target_hemisphere="right" if direction == "L_to_R" else "left",
            )
        model_root = str(vars_["model_root"].get()).strip() or None
        bundles = discover_local_dgn_bundles(model_root)
        if direction not in bundles:
            raise RuntimeError(
                f"No local DGN bundle found for {direction}. "
                "Set HEMISPEC_DGN_MODEL_ROOT, check local assets/models/dgn, or choose a checkpoint override."
            )
        return bundles[direction]

    def _parse_clip(self, vars_: dict[str, object]) -> tuple[float, float] | None:
        low = str(vars_["clip_low"].get()).strip()
        high = str(vars_["clip_high"].get()).strip()
        if not low and not high:
            return None
        if not low or not high:
            raise ValueError("Both clip low and clip high are required when clipping is enabled.")
        return float(low), float(high)

    def _metric_config(self, vars_: dict[str, object]) -> MetricComputeConfig:
        return MetricComputeConfig(
            actual_glob=str(vars_["actual_glob"].get()),
            reconstructed_glob=str(vars_["predicted_glob"].get()),
            out_dir=Path(str(vars_["out_dir"].get())),
            gm_thresh=float(str(vars_["gm_thresh"].get())),
            eps=float(str(vars_["eps"].get())),
            reconstructed_suffix_to_strip=str(vars_["pred_suffix"].get()),
            actual_suffix_to_strip=str(vars_["actual_suffix"].get()),
            export_voxelwise=_bool(vars_["export_voxelwise"]),
            save_subject_maps=_bool(vars_["save_subject"]),
            write_nan_outside=_bool(vars_["write_nan_outside"]),
            roi_atlas=_optional_path(str(vars_["roi_atlas"].get())),
            roi_out_csv=_optional_path(str(vars_["roi_out_csv"].get())),
            roi_label_table=_optional_path(str(vars_["roi_label_table"].get())),
            roi_stat=str(vars_["roi_stat"].get()),  # type: ignore[arg-type]
        )

    def _inference_config(self, vars_: dict[str, object]) -> DGNInferenceConfig:
        return DGNInferenceConfig(
            model=self._resolve_model(vars_),
            input_glob=str(vars_["input_glob"].get()),
            out_dir=Path(str(vars_["recon_dir"].get())),
            device=str(vars_["device"].get()),  # type: ignore[arg-type]
            direction=str(vars_["direction"].get()),  # type: ignore[arg-type]
            clip_recon=self._parse_clip(vars_),
            output_suffix=str(vars_["output_suffix"].get()),
        )

    def _pipeline_config(self, vars_: dict[str, object]) -> PipelineRunConfig:
        return PipelineRunConfig(
            inference=self._inference_config(vars_),
            metrics_out_dir=Path(str(vars_["metrics_dir"].get())),
            gm_thresh=float(str(vars_["gm_thresh"].get())),
            eps=float(str(vars_["eps"].get())),
            reconstructed_suffix_to_strip=str(vars_["pred_suffix"].get()),
            actual_suffix_to_strip=str(vars_["actual_suffix"].get()),
            save_subject_maps=_bool(vars_["save_subject"]),
            write_nan_outside=_bool(vars_["write_nan_outside"]),
            verbose_every=int(str(vars_["verbose_every"].get())),
            export_voxelwise=_bool(vars_["export_voxelwise"]),
            roi_atlas=_optional_path(str(vars_["roi_atlas"].get())),
            roi_out_csv=_optional_path(str(vars_["roi_out_csv"].get())),
            roi_label_table=_optional_path(str(vars_["roi_label_table"].get())),
            roi_stat=str(vars_["roi_stat"].get()),  # type: ignore[arg-type]
        )

    def _workflow_config(self, vars_: dict[str, object]) -> BilateralWorkflowConfig:
        classifier_mode = str(vars_["classifier_mode"].get())
        return BilateralWorkflowConfig(
            input_glob=str(vars_["input_glob"].get()),
            out_dir=Path(str(vars_["out_dir"].get())),
            model_root=_optional_path(str(vars_["model_root"].get())),
            device=str(vars_["device"].get()),
            gm_thresh=float(str(vars_["gm_thresh"].get())),
            eps=float(str(vars_["eps"].get())),
            clip_recon=self._parse_clip(vars_),
            reconstructed_suffix_to_strip=str(vars_["pred_suffix"].get()),
            actual_suffix_to_strip=str(vars_["actual_suffix"].get()),
            export_voxelwise=_bool(vars_["export_voxelwise"]),
            write_nan_outside=_bool(vars_["write_nan_outside"]),
            roi_atlas=_optional_path(str(vars_["roi_atlas"].get())),
            roi_label_table=_optional_path(str(vars_["roi_label_table"].get())),
            roi_stat=str(vars_["roi_stat"].get()),
            run_classifier=_bool(vars_["run_classifier"]),
            classifier_model_dir=_classifier_model_dir(str(vars_["classifier_model_dir"].get()), classifier_mode),
            classifier_mode=classifier_mode,
            run_trt=_bool(vars_["run_trt"]),
            trt_file_regex=str(vars_["trt_file_regex"].get()),
            trt_session_a=str(vars_["trt_session_a"].get()),
            trt_session_b=str(vars_["trt_session_b"].get()),
            verbose_every=int(str(vars_["verbose_every"].get())),
        )

    def _validation_config(self, vars_: dict[str, object]) -> ValidationConfig:
        return ValidationConfig(
            maps_dir=Path(str(vars_["maps_dir"].get())),
            out_dir=Path(str(vars_["out_dir"].get())),
            kinds=_csv_labels(str(vars_["kinds"].get())),
            suffix_template=str(vars_["suffix_template"].get()),
            file_regex=str(vars_["file_regex"].get()),
            session_a=str(vars_["session_a"].get()),
            session_b=str(vars_["session_b"].get()),
            hemis=_csv_labels(str(vars_["hemis"].get())),
            dgn_direction=str(vars_["dgn_direction"].get()),  # type: ignore[arg-type]
            hemi_slices=str(vars_["hemi_slices"].get()).strip() or None,
            metric=str(vars_["metric"].get()).lower(),  # type: ignore[arg-type]
            mask_type=str(vars_["mask_type"].get()).lower(),  # type: ignore[arg-type]
            thr=float(str(vars_["thr"].get())),
            rate_thr=float(str(vars_["rate_thr"].get())),
            mask_mode=str(vars_["mask_mode"].get()).lower(),  # type: ignore[arg-type]
            symmetrize=_bool(vars_["symmetrize"]),
            write_plots=_bool(vars_["write_plots"]),
        )

    def _hemi_classification_config(self, vars_: dict[str, object]) -> HemisphereClassificationConfig:
        classifier_mode = str(vars_["classifier_mode"].get())
        return HemisphereClassificationConfig(
            maps_dir=Path(str(vars_["maps_dir"].get())),
            roi_csv=_optional_path(str(vars_["roi_csv"].get())),
            atlas_path=_optional_path(str(vars_["roi_atlas"].get())),
            label_table=_optional_path(str(vars_["roi_label_table"].get())),
            classifier_checkpoint=_optional_path(str(vars_["checkpoint"].get())),
            classifier_model_dir=_classifier_model_dir(str(vars_["classifier_model_dir"].get()), classifier_mode),
            classifier_mode=classifier_mode,  # type: ignore[arg-type]
            out_dir=_optional_path(str(vars_["out_dir"].get())),
            kinds=_csv_labels(str(vars_["kinds"].get())),
            suffix_template=str(vars_["suffix_template"].get()),
            file_regex=str(vars_["file_regex"].get()),
            device=str(vars_["device"].get()),  # type: ignore[arg-type]
        )

    def _run_pipeline(self, vars_: dict[str, object]) -> None:
        if not self._require_dgn_runtime():
            return

        def job() -> None:
            result = run_pipeline(self._pipeline_config(vars_))
            print("[done] DGN inference + ANS/RNS compute complete")
            print(f"reconstructed: {len(result.reconstructed_paths)}")
            print(f"pairs: {result.metrics.n_pairs}")
            print(f"metrics: {result.metrics.out_dir}")
            if result.metrics.subject_maps_dir:
                print(f"subject_maps: {result.metrics.subject_maps_dir}")
            if result.metrics.roi_csv:
                print(f"roi_csv: {result.metrics.roi_csv}")

        self._run_background("pipeline", job)

    def _run_workflow(self, vars_: dict[str, object]) -> None:
        if not self._require_dgn_runtime():
            return

        def job() -> None:
            result = run_bilateral_workflow(self._workflow_config(vars_))
            print("[done] bilateral HemiSpec workflow complete")
            print(f"L_to_R reconstructed: {len(result.l_to_r.reconstructed_paths)}")
            print(f"R_to_L reconstructed: {len(result.r_to_l.reconstructed_paths)}")
            print(f"bilateral_subject_maps: {result.combined_maps_dir}")
            print(f"hemisphere_maps: {result.hemi_maps_dir}")
            print(f"roi_csv: {result.roi_csv}")
            print(f"roi_wide_csv: {result.roi_wide_csv}")
            print(f"subject_summary_csv: {result.subject_summary_csv}")
            if result.classifier:
                print(f"classifier_summary_csv: {result.classifier.summary_csv}")
                if result.classifier.accuracy is not None:
                    print(f"classifier_accuracy_mean: {result.classifier.accuracy:.6f}")
            if result.trt:
                print(f"trt_summary_csv: {result.trt.summary_csv}")

        self._run_background("workflow", job)

    def _run_infer(self, vars_: dict[str, object]) -> None:
        if not self._require_dgn_runtime():
            return

        def job() -> None:
            outputs = run_dgn_inference(self._inference_config(vars_))
            print("[done] DGN inference complete")
            print(f"outputs: {len(outputs)}")
            for path in outputs[:10]:
                print(path)

        self._run_background("infer", job)

    def _run_compute(self, vars_: dict[str, object]) -> None:
        def job() -> None:
            result = compute_metrics(self._metric_config(vars_))
            print("[done] ANS/RNS compute complete")
            print(f"pairs: {result.n_pairs}")
            print(f"out_dir: {result.out_dir}")
            if result.subject_maps_dir:
                print(f"subject_maps: {result.subject_maps_dir}")
            if result.roi_csv:
                print(f"roi_csv: {result.roi_csv}")

        self._run_background("compute", job)

    def _run_validation(self, vars_: dict[str, object]) -> None:
        mode = str(vars_["mode"])

        def job() -> None:
            config = self._validation_config(vars_)
            run = validate_reliability(config) if mode == "trt" else validate_specificity(config)
            for row in run.summary_rows:
                print(
                    f"[{row.kind}_{row.hemi}] N={row.n_subjects} vox={row.n_voxels} "
                    f"MR={row.match_rate:.1f}% SI={row.specificity_index:.4f} "
                    f"t={row.t_value:.2f} p={row.p_value:.2e}"
                )
            print(f"[done] outputs written to {run.out_dir}")

        self._run_background(mode, job)

    def _run_hemi_classify(self, vars_: dict[str, object]) -> None:
        def job() -> None:
            result = validate_hemisphere_classification(self._hemi_classification_config(vars_))
            print(result.message)
            if result.accuracy is not None:
                print(f"accuracy_mean: {result.accuracy:.6f}")
            print(f"n_samples: {result.n_samples}")
            if result.summary_csv:
                print(f"summary_csv: {result.summary_csv}")
            if result.predictions_csv:
                print(f"predictions_csv: {result.predictions_csv}")

        self._run_background("hemi-classify", job)


def main() -> None:
    app = HemiSpecGui()
    app.mainloop()


if __name__ == "__main__":
    main()
