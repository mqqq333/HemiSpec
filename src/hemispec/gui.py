from __future__ import annotations

import contextlib
import io
import re
import subprocess
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

from .api import (
    default_input_glob,
    resolve_classifier_model_dir,
    resolve_dgn_model_root,
    resolve_glasser_atlas_path,
    resolve_glasser_label_table,
)
from .workflow import BilateralWorkflowConfig, BilateralWorkflowResult, run_bilateral_workflow

try:  # optional dependency: installed with hemispec-toolkit[gui]
    import customtkinter as ctk
except ImportError:  # pragma: no cover - exercised only on machines without GUI extra
    ctk = None  # type: ignore[assignment]


APP_TITLE = "HemiSpec"
APP_SUBTITLE = "ANS/RNS Generation Workbench"
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

WORKFLOW_VISIBLE_FIELDS = (
    "input_glob",
    "out_dir",
    "export_roi_table",
    "roi_atlas",
    "roi_label_table",
    "run_classifier",
    "run_trt",
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


def _path_exists_or_empty(value: str) -> bool:
    text = value.strip()
    return not text or Path(text).exists()


def default_output_dir() -> str:
    return str(Path.cwd() / "hemispec_outputs" / "gui_run")


def make_workflow_config(state: dict[str, object]) -> BilateralWorkflowConfig:
    """Convert GUI state into the single workflow config used by CLI/API.

    This is deliberately separate from widgets so tests can enforce the same
    validation rules even when GUI controls are refactored.
    """

    input_glob = str(state["input_glob"]).strip()
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
        trt_file_regex=str(state.get("trt_file_regex", ENCAPSULATED_DEFAULTS["trt_file_regex"])),
        trt_session_a=str(state.get("trt_session_a", ENCAPSULATED_DEFAULTS["trt_session_a"])),
        trt_session_b=str(state.get("trt_session_b", ENCAPSULATED_DEFAULTS["trt_session_b"])),
        verbose_every=int(state.get("verbose_every", ENCAPSULATED_DEFAULTS["verbose_every"])),
    )


def workflow_cli_command(state: dict[str, object]) -> str:
    """Return a reproducible CLI command equivalent to the visible GUI choices."""

    config = make_workflow_config(state)
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
    return " ".join(parts)


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
        self.last_out_dir: Path | None = None
        self.vars: dict[str, object] = {}
        self.status_var = ctk.StringVar(value="Ready")
        self.summary_var = ctk.StringVar(value="Primary output: voxel-wise ANS/RNS maps")

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

        content = ctk.CTkScrollableFrame(main, fg_color="#f6f8fb")
        content.grid(row=1, column=0, padx=22, pady=(0, 8), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        self._build_input_card(content, 0)
        self._build_output_card(content, 1)
        self._build_roi_card(content, 2)
        self._build_validation_card(content, 3)
        self._build_run_card(content, 4)

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
            text="Creates: recon/ | metrics/ | subject_maps/ | subject_hemi_maps/ | tables/",
            text_color="#64748b",
            font=ctk.CTkFont(size=12),
        ).grid(row=3, column=1, padx=(0, 16), pady=(0, 10), sticky="w")

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
        ctk.CTkCheckBox(card, text="Run TRT reliability", variable=self.vars["run_trt"]).grid(
            row=3, column=0, columnspan=3, padx=16, pady=(0, 12), sticky="w"
        )

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
        actions.grid_columnconfigure(4, weight=1)
        self.run_button = ctk.CTkButton(actions, text="Run HemiSpec", command=self._run_clicked, height=36)
        self.run_button.grid(row=0, column=0, padx=(0, 10), sticky="w")
        ctk.CTkButton(actions, text="Copy CLI Command", command=self._copy_cli, height=36, fg_color="#334155").grid(
            row=0, column=1, padx=(0, 10), sticky="w"
        )
        ctk.CTkButton(actions, text="Open Output Folder", command=self._open_output, height=36, fg_color="#475569").grid(
            row=0, column=2, padx=(0, 10), sticky="w"
        )
        ctk.CTkButton(actions, text="Clear Log", command=self._clear_log, height=36, fg_color="#64748b").grid(
            row=0, column=3, sticky="w"
        )

        self.cli_box = ctk.CTkTextbox(card, height=48, wrap="word", fg_color="#f8fafc", text_color="#0f172a")
        self.cli_box.grid(row=3, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="ew")
        self._refresh_cli_box()

        self.log_box = ctk.CTkTextbox(card, height=150, wrap="word", fg_color="#0f172a", text_color="#e5e7eb")
        self.log_box.grid(row=4, column=0, columnspan=3, padx=16, pady=(0, 14), sticky="ew")
        self._log("Ready. Configure inputs and click Run HemiSpec.\n")

    def _entry_row(self, parent: object, row: int, label: str, var_key: str, browse: Callable[[], None]) -> list[object]:
        label_widget = ctk.CTkLabel(parent, text=label, text_color="#111827")
        label_widget.grid(row=row, column=0, padx=16, pady=(0, 8), sticky="w")
        entry = ctk.CTkEntry(parent, textvariable=self.vars[var_key], height=34)
        entry.grid(row=row, column=1, padx=(0, 8), pady=(0, 8), sticky="ew")
        entry.bind("<KeyRelease>", lambda _event: self._refresh_cli_box())
        button = ctk.CTkButton(parent, text="Browse", width=88, command=browse, fg_color="#475569")
        button.grid(row=row, column=2, padx=(0, 16), pady=(0, 8), sticky="e")
        return [label_widget, entry, button]

    def _browse_input_file(self) -> None:
        path = filedialog.askopenfilename(title="Select one GM map to build a folder glob")
        if not path:
            return
        p = Path(path)
        suffix = "*_GM_masked.nii.gz" if p.name.endswith("_GM_masked.nii.gz") else f"*{''.join(p.suffixes)}"
        self.vars["input_glob"].set(str(p.parent / suffix))  # type: ignore[union-attr]
        self._refresh_cli_box()

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Select output workspace")
        if path:
            self.vars["out_dir"].set(path)  # type: ignore[union-attr]
            self._refresh_cli_box()

    def _browse_atlas_file(self) -> None:
        path = filedialog.askopenfilename(title="Select ROI atlas NIfTI", filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All", "*")])
        if path:
            self.vars["roi_atlas"].set(path)  # type: ignore[union-attr]
            self._refresh_cli_box()

    def _browse_label_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select ROI label table", filetypes=[("Tables", "*.xlsx *.csv *.tsv"), ("All", "*")]
        )
        if path:
            self.vars["roi_label_table"].set(path)  # type: ignore[union-attr]
            self._refresh_cli_box()

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
        self._refresh_cli_box()

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

    def _refresh_cli_box(self) -> None:
        if not hasattr(self, "cli_box"):
            return
        try:
            cli = workflow_cli_command(self._state_snapshot())
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

        self.is_running = True
        self.last_out_dir = config.out_dir
        self.run_button.configure(state="disabled", text="Running...")
        self.status_var.set("Running HemiSpec workflow")
        self._log("\n[run] Starting HemiSpec standard workflow\n")
        self._log(f"[run] output: {config.out_dir}\n")
        self._log(f"[run] CLI: {workflow_cli_command(state)}\n")

        thread = threading.Thread(target=self._run_worker, args=(config,), daemon=True)
        thread.start()

    def _run_worker(self, config: BilateralWorkflowConfig) -> None:
        try:
            with contextlib.redirect_stdout(_StdoutProxy(self._threadsafe_log)), contextlib.redirect_stderr(
                _StdoutProxy(self._threadsafe_log)
            ):
                result = run_bilateral_workflow(config)
            self.after(0, lambda: self._run_finished(result, None))
        except Exception as exc:  # pragma: no cover - GUI worker path
            detail = traceback.format_exc()
            self.after(0, lambda: self._run_finished(None, (exc, detail)))

    def _run_finished(self, result: BilateralWorkflowResult | None, error: tuple[BaseException, str] | None) -> None:
        self.is_running = False
        self.run_button.configure(state="normal", text="Run HemiSpec")
        if error is not None:
            exc, detail = error
            self.status_var.set("Failed")
            self._log(f"[error] {exc}\n{detail}\n")
            messagebox.showerror("HemiSpec workflow failed", str(exc))
            return
        assert result is not None
        self.status_var.set("Done")
        self.summary_var.set(f"Done: {result.combined_maps_dir}")
        self._log("[done] HemiSpec workflow complete\n")
        self._log(f"subject_maps: {result.combined_maps_dir}\n")
        self._log(f"subject_hemi_maps: {result.hemi_maps_dir}\n")
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
