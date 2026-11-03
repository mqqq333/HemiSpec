from __future__ import annotations

import contextlib
import glob
import importlib.resources
import importlib.util
import io
import locale
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import traceback
from concurrent.futures import CancelledError
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
DEFAULT_WINDOW_SIZE = (1240, 800)
MIN_WINDOW_SIZE = (900, 560)
# Spec section 7.1: target = min(cap, fraction * logical work area); the minimum
# is min(cap, logical work area - 32). Both are computed in logical units.
WINDOW_TARGET_FRACTIONS = (0.94, 0.92)
MIN_WINDOW_INSET_PX = 32
APP_DESCRIPTION = (
    "Generate voxel-wise reconstruction-derived hemispheric specificity maps from "
    "preprocessed GM inputs using the packaged HemiSpec workflow."
)
PREPROCESS_NOTE = (
    "Input files should be preprocessed grey-matter maps, typically ending with "
    "*_GM_masked.nii.gz. Run the packaged preprocessing script before this step."
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

# Design tokens: design spec section 1 (light scheme only).
@dataclass(frozen=True)
class Theme:
    id: str
    name_en: str
    name_zh: str
    appearance: str
    paper_0: str
    paper_50: str
    paper_100: str
    paper_200: str
    line_200: str
    line_300: str
    line_400: str
    control_off: str
    ink_500: str
    ink_600: str
    ink_700: str
    ink_900: str
    teal_50: str
    teal_100: str
    teal_200: str
    teal_500: str
    teal_600: str
    teal_700: str
    verm_50: str
    verm_100: str
    verm_200: str
    verm_500: str
    verm_600: str
    verm_700: str
    success_fg: str
    success_accent: str
    success_bg: str
    warning_fg: str
    warning_accent: str
    warning_bg: str
    log_bg: str
    danger_text: str
    highlight: str


THEME_COOL_TEAL = Theme(
    id="cool_teal",
    name_en="Cool Teal",
    name_zh="冷白·青",
    appearance="light",
    paper_0="#FFFFFF",
    paper_50="#F6F8F8",
    paper_100="#EEF2F2",
    paper_200="#E4EAEA",
    line_200="#DDE4E4",
    line_300="#C9D3D3",
    line_400="#849091",
    control_off="#8A9697",
    ink_500="#5F6B6D",
    ink_600="#465153",
    ink_700="#323B3D",
    ink_900="#1C2526",
    teal_50="#EAF4F2",
    teal_100="#D3EAE6",
    teal_200="#A9D4CE",
    teal_500="#0F7A78",
    teal_600="#0D6F6D",
    teal_700="#0A5957",
    verm_50="#FBEEEB",
    verm_100="#F6DAD4",
    verm_200="#EDB5AB",
    verm_500="#B8352A",
    verm_600="#A02D23",
    verm_700="#84251D",
    success_fg="#276B43",
    success_accent="#2F7D4F",
    success_bg="#E9F3EC",
    warning_fg="#8A5508",
    warning_accent="#C98A1E",
    warning_bg="#FBF1DE",
    log_bg="#FAFBFB",
    danger_text="#A02D23",
    highlight="#0F7A78",
)

THEME_COOL_CYAN = Theme(
    id="cool_cyan",
    name_en="Cool Cyan",
    name_zh="冷白·电青",
    appearance="light",
    paper_0="#FFFFFF",
    paper_50="#F6F8F8",
    paper_100="#EEF2F2",
    paper_200="#E4EAEA",
    line_200="#DDE4E4",
    line_300="#C9D3D3",
    line_400="#849091",
    control_off="#8A9697",
    ink_500="#5F6B6D",
    ink_600="#465153",
    ink_700="#323B3D",
    ink_900="#1C2526",
    teal_50="#E6F4F8",
    teal_100="#CCE8F0",
    teal_200="#99D1E1",
    teal_500="#07819E",
    teal_600="#06718B",
    teal_700="#055F75",
    verm_50="#FCECE9",
    verm_100="#F8D5CF",
    verm_200="#F0AA9E",
    verm_500="#D93E24",
    verm_600="#B8321C",
    verm_700="#962816",
    success_fg="#276B43",
    success_accent="#2F7D4F",
    success_bg="#E9F3EC",
    warning_fg="#8A5508",
    warning_accent="#C98A1E",
    warning_bg="#FBF1DE",
    log_bg="#FAFBFB",
    danger_text="#B8321C",
    highlight="#07819E",
)

THEME_INK_NIGHT = Theme(
    id="ink_night",
    name_en="Ink Night",
    name_zh="墨夜·青朱",
    appearance="dark",
    paper_0="#121A21",
    paper_50="#0B1015",
    paper_100="#18222B",
    paper_200="#1F2B35",
    line_200="#22303B",
    line_300="#2C3C49",
    line_400="#5A6E7C",
    control_off="#5F7280",
    ink_500="#8395A1",
    ink_600="#A3B2BC",
    ink_700="#C2CED6",
    ink_900="#DCE6EC",
    teal_50="#153035",
    teal_100="#173F43",
    teal_200="#1B5B5C",
    teal_500="#2BD4CB",
    teal_600="#22BFB7",
    teal_700="#6BE3DC",
    verm_50="#2E2226",
    verm_100="#41272A",
    verm_200="#65302E",
    verm_500="#FF5A47",
    verm_600="#FF6B5A",
    verm_700="#FF8A7D",
    success_fg="#3DD68C",
    success_accent="#3DD68C",
    success_bg="#17312E",
    warning_fg="#F2B347",
    warning_accent="#F2B347",
    warning_bg="#2D2C26",
    log_bg="#0E151B",
    danger_text="#FF6B5A",
    highlight="#2BD4CB",
)

THEME_GRAPHITE_BRONZE = Theme(
    id="graphite_bronze",
    name_en="Graphite Bronze",
    name_zh="石墨·青铜",
    appearance="dark",
    paper_0="#191E1D",
    paper_50="#111414",
    paper_100="#1F2524",
    paper_200="#262D2C",
    line_200="#2B3331",
    line_300="#36403E",
    line_400="#68746F",
    control_off="#6B7673",
    ink_500="#9C998F",
    ink_600="#B5B2A8",
    ink_700="#CDCAC1",
    ink_900="#E6E3DA",
    teal_50="#1E302D",
    teal_100="#213C37",
    teal_200="#26534B",
    teal_500="#3FB5A0",
    teal_600="#37A391",
    teal_700="#6CCDBB",
    verm_50="#2E231F",
    verm_100="#3C2621",
    verm_200="#572B23",
    verm_500="#C9442F",
    verm_600="#E5694F",
    verm_700="#EE8A74",
    success_fg="#6FCF97",
    success_accent="#6FCF97",
    success_bg="#23332C",
    warning_fg="#E0A33A",
    warning_accent="#E0A33A",
    warning_bg="#312E21",
    log_bg="#151918",
    danger_text="#E5694F",
    highlight="#C8A15A",
)


PAPER_0 = THEME_COOL_TEAL.paper_0
PAPER_50 = THEME_COOL_TEAL.paper_50
PAPER_100 = THEME_COOL_TEAL.paper_100
PAPER_200 = THEME_COOL_TEAL.paper_200
LINE_200 = THEME_COOL_TEAL.line_200
LINE_300 = THEME_COOL_TEAL.line_300
LINE_400 = THEME_COOL_TEAL.line_400
CONTROL_OFF = THEME_COOL_TEAL.control_off
INK_500 = THEME_COOL_TEAL.ink_500
INK_600 = THEME_COOL_TEAL.ink_600
INK_700 = THEME_COOL_TEAL.ink_700
INK_900 = THEME_COOL_TEAL.ink_900

TEAL_50 = THEME_COOL_TEAL.teal_50
TEAL_100 = THEME_COOL_TEAL.teal_100
TEAL_200 = THEME_COOL_TEAL.teal_200
TEAL_500 = THEME_COOL_TEAL.teal_500
TEAL_600 = THEME_COOL_TEAL.teal_600
TEAL_700 = THEME_COOL_TEAL.teal_700

VERM_50 = THEME_COOL_TEAL.verm_50
VERM_100 = THEME_COOL_TEAL.verm_100
VERM_200 = THEME_COOL_TEAL.verm_200
VERM_500 = THEME_COOL_TEAL.verm_500
VERM_600 = THEME_COOL_TEAL.verm_600
VERM_700 = THEME_COOL_TEAL.verm_700

SUCCESS_FG = THEME_COOL_TEAL.success_fg
SUCCESS_ACCENT = THEME_COOL_TEAL.success_accent
SUCCESS_BG = THEME_COOL_TEAL.success_bg
WARNING_FG = THEME_COOL_TEAL.warning_fg
WARNING_ACCENT = THEME_COOL_TEAL.warning_accent
WARNING_BG = THEME_COOL_TEAL.warning_bg

# Spec section 7.2 gives this log-surface value explicitly; it is not in section 1.
LOG_BG = THEME_COOL_TEAL.log_bg

DANGER_TEXT = THEME_COOL_TEAL.danger_text
HIGHLIGHT = THEME_COOL_TEAL.highlight

THEMES: dict[str, Theme] = {
    theme.id: theme
    for theme in (THEME_COOL_TEAL, THEME_COOL_CYAN, THEME_INK_NIGHT, THEME_GRAPHITE_BRONZE)
}
DEFAULT_THEME = "cool_teal"

# Per-theme header marks (transparent 256x256 PNGs in resources/gui). The
# window/EXE icon is separate and stays hemispec.ico / hemispec.png.
THEME_MARK_FILES: dict[str, str] = {
    "cool_teal": "hemispec_mark_cool_teal.png",
    "cool_cyan": "hemispec_mark_cool_cyan.png",
    "ink_night": "hemispec_mark_ink_night.png",
    "graphite_bronze": "hemispec_mark_graphite_bronze.png",
}

_THEME_COLOR_FIELDS: tuple[str, ...] = (
    "paper_0",
    "paper_50",
    "paper_100",
    "paper_200",
    "line_200",
    "line_300",
    "line_400",
    "control_off",
    "ink_500",
    "ink_600",
    "ink_700",
    "ink_900",
    "teal_50",
    "teal_100",
    "teal_200",
    "teal_500",
    "teal_600",
    "teal_700",
    "verm_50",
    "verm_100",
    "verm_200",
    "verm_500",
    "verm_600",
    "verm_700",
    "success_fg",
    "success_accent",
    "success_bg",
    "warning_fg",
    "warning_accent",
    "warning_bg",
    "log_bg",
    "danger_text",
    "highlight",
)


def apply_theme_globals(theme_id: str) -> None:
    """Point every UPPERCASE color constant at ``THEMES[theme_id]``.

    Widgets read these module globals when they are built, so switching the
    globals and rebuilding the window re-skins the whole UI. This also selects
    the customtkinter appearance mode named by the theme.
    """

    theme = THEMES[theme_id]
    globals_ = globals()
    for name in _THEME_COLOR_FIELDS:
        globals_[name.upper()] = getattr(theme, name)
    ctk.set_appearance_mode(theme.appearance)

# Spec section 7.1/7.2: single-column layout below 1060 logical width, two columns
# with grid weights 10:11 and minsize 440/480 above it.
RESPONSIVE_BREAKPOINT = 1060
RESPONSIVE_DEBOUNCE_MS = 150
COLUMN_WEIGHTS = (10, 11)
COLUMN_MINSIZE = (440, 480)
COLUMN_GAP = 16

# Spec section 7.3: toggle capsule geometry in logical units.
TOGGLE_TRACK_W = 40
TOGGLE_TRACK_H = 22
TOGGLE_RADIUS = 11
TOGGLE_KNOB = 16
TOGGLE_INSET = 3
TOGGLE_FOCUS_RING = 2

# Spec section 7.2/7.3 timing and live-status constants.
MATCH_DEBOUNCE_MS = 300
COPY_FEEDBACK_MS = 1500
ELAPSED_TICK_MS = 1000
AUTOSCROLL_SLACK = 0.01

# Spec section 7.3: stepper nodes in display order.
STEPPER_NODES = ("l_to_r", "r_to_l", "merge", "roi", "summary")
STEPPER_STAGE_TO_NODE = {
    "l_to_r": "l_to_r",
    "r_to_l": "r_to_l",
    "merge": "merge",
    "roi": "roi",
    "summary": "summary",
    "classifier": "summary",
    "trt": "summary",
}

TRANSLATIONS: dict[str, tuple[str, str]] = {
    "subtitle": ("ANS/RNS Generation Workbench", "ANS/RNS 生成工作台"),
    "theme_label": ("Theme", "主题"),
    "status_ready": ("Ready", "就绪"),
    "status_running": ("Running HemiSpec workflow", "正在运行 HemiSpec 工作流"),
    "status_stopping": ("Stop requested — finishing current file", "已请求停止 — 正在完成当前文件"),
    "status_done": ("Completed", "已完成"),
    "status_failed": ("Failed", "运行失败"),
    "status_stopped": ("Stopped", "已停止"),
    "status_copied": ("CLI command copied", "CLI 命令已复制"),
    "status_closing": ("Closing after current file", "将在当前文件完成后关闭"),
    "mode_checking": ("checking", "检查中"),
    "mode_lightweight": ("Lightweight", "轻量模式"),
    "mode_model_enabled": ("Model-enabled", "完整模型"),
    "summary_default": (
        "Primary output: voxel-wise ANS/RNS maps",
        "主要输出：体素级 ANS/RNS 图",
    ),
    "summary_done": ("Completed: {path}", "已完成：{path}"),
    "input_output_title": ("Input & output", "输入与输出"),
    "optional_title": ("Optional analysis", "可选分析"),
    "cli_title": ("Equivalent CLI", "等效命令行"),
    "log_title": ("Log", "日志"),
    "chip_ready": ("Ready", "就绪"),
    "chip_partial": ("Partial", "部分缺失"),
    "chip_missing": ("Missing", "缺失"),
    "chip_optional": ("Optional", "可选"),
    "button_refresh": ("Refresh", "刷新"),
    "stepper_l_to_r": ("L→R", "左→右"),
    "stepper_r_to_l": ("R→L", "右→左"),
    "stepper_merge": ("Merge", "合并"),
    "stepper_roi": ("ROI", "ROI"),
    "stepper_summary": ("Summary", "汇总"),
    "stepper_skipped": ("skipped", "跳过"),
    "input_title": ("Input GM maps", "输入灰质图"),
    "input_placeholder": (
        r"Folder or glob, e.g. D:\data\*_GM_masked.nii.gz",
        r"文件夹或 glob，例如 D:\data\*_GM_masked.nii.gz",
    ),
    "note_preprocess": (
        PREPROCESS_NOTE,
        "输入应为预处理后的灰质图，通常以 *_GM_masked.nii.gz 结尾。请先运行随包提供的预处理脚本。",
    ),
    "output_title": ("Output folder", "输出文件夹"),
    "note_output": (
        "Choose where HemiSpec writes reconstructions, maps, tables, and logs.",
        "选择 HemiSpec 写入重建图、指标图、表格和日志的位置。",
    ),
    "output_hint": (
        "Results go to voxel_maps/, tables/ and validation/. intermediate/ is deleted after "
        'the run unless "Keep intermediate files" is on.',
        "结果写入 voxel_maps/、tables/ 和 validation/；除非开启「保留中间文件」，"
        "intermediate/ 会在运行结束后删除。",
    ),
    "status_title": ("Environment", "运行环境"),
    "note_status": (
        "Check Environment before a long run. DGN models are the released HemiSpec defaults "
        "and can auto-download into the user cache; PyTorch is still required in the active "
        "environment.",
        "长时间运行前请检查运行环境。DGN 模型使用 HemiSpec 发布的默认资产，可自动下载到用户缓存；"
        "当前 Python 环境仍需安装 PyTorch。",
    ),
    "roi_title": ("Optional ROI table", "可选 ROI 表"),
    "note_roi": (
        "Voxel-wise ANS/RNS maps are the primary output. Export ROI table is optional and can "
        "use the default Atlas or a custom atlas/label table.",
        "体素级 ANS/RNS 图是主要输出。导出 ROI 表为可选项，可使用默认脑区图谱或自定义脑区图谱/标签表。",
    ),
    "validation_title": ("Optional validation", "可选验证"),
    "note_validation": (
        "Hemisphere-classifier validation uses ROI features, so enabling it also enables ROI "
        "table export. Test–retest reliability (TRT) uses the default paired-session settings. "
        "Advanced settings remain available through the CLI/API.",
        "半球分类器验证使用 ROI 特征，因此启用它会同时启用 ROI 表导出。重测信度（TRT）使用默认配对会话设置；"
        "高级参数仍可通过 CLI/API 使用。",
    ),
    "note_trt": (
        "Runs the paired-session reliability check with the default settings.",
        "使用默认配对会话设置运行重测信度检查。",
    ),
    "note_keep": (
        "Keeps intermediate reconstructions, direction metrics, and combined maps.",
        "保留中间重建结果、方向指标与合并图。",
    ),
    "run_title": ("Run", "开始运行"),
    "note_run": (
        "Review the Equivalent CLI, run the workflow, and inspect the Log.",
        "检查等效命令行，运行工作流并查看日志。",
    ),
    "field_input": ("Input GM maps", "输入灰质图"),
    "field_output": ("Output folder", "输出文件夹"),
    "field_atlas": ("ROI atlas NIfTI", "ROI 脑区图谱 NIfTI"),
    "field_labels": ("Label table", "标签表"),
    "button_browse": ("Browse", "浏览"),
    "switch_roi": ("Export ROI table", "导出 ROI 表"),
    "switch_classifier": ("Hemisphere-classifier validation", "半球分类器验证"),
    "classifier_needs_roi": ("Requires the ROI table", "需要 ROI 表"),
    "switch_trt": ("Test–retest reliability (TRT)", "重测信度（TRT）"),
    "switch_keep": ("Keep intermediate files", "保留中间文件"),
    "on": ("On", "开"),
    "off": ("Off", "关"),
    "button_run": ("Run", "开始运行"),
    "button_running": ("Running…", "运行中…"),
    "button_stop": ("Stop", "停止"),
    "button_stop_requested": ("Stop requested…", "已请求停止…"),
    "button_copy": ("Copy", "复制"),
    "button_copied": ("Copied ✓", "已复制 ✓"),
    "button_copy_log": ("Copy log", "复制日志"),
    "button_open": ("Open output", "打开输出"),
    # Spec section 7.2/7.4: the output-row button reads "Open" / "打开"; the
    # log toolbar keeps "Open output" / "打开输出".
    "button_open_folder": ("Open", "打开"),
    "button_clear": ("Clear Log", "清空日志"),
    "status_log_copied": ("Log copied", "日志已复制"),
    "status_run_failed": ("Run failed — see log", "运行失败，请查看日志"),
    "status_validating_classifier": ("Validating classifier…", "正在验证分类器…"),
    "status_validating_trt": (
        "Validating test–retest reliability…",
        "正在验证重测信度…",
    ),
    "input_match_count": ("{n} files found", "找到 {n} 个文件"),
    "input_no_matches": ("No matching files", "没有匹配的文件"),
    "dialog_no_inputs_title": ("No input files", "没有输入文件"),
    "dialog_no_inputs_body": (
        "No input files match: {glob}",
        "没有找到匹配的输入文件：{glob}",
    ),
    "dialog_nonempty_output_title": ("Output folder not empty", "输出文件夹非空"),
    "dialog_nonempty_output_body": (
        "The output folder is not empty. Existing files may be overwritten. Continue?",
        "输出文件夹非空，已有文件可能被覆盖。继续吗？",
    ),
    "cli_hint": (
        "Equivalent CLI command for reproducibility. Atlas and label table are optional "
        "reference files for ROI table export; turn off Export ROI table to omit them.",
        "用于复现的等效命令行。脑区图谱与标签表是 ROI 表导出的可选参考文件；"
        "关闭「导出 ROI 表」即可省略它们。",
    ),
    "stage_idle": ("Idle", "空闲"),
    "stage_queued": ("Queued", "已排队"),
    "stage_l_to_r": ("L → R reconstruction", "左 → 右重建"),
    "stage_r_to_l": ("R → L reconstruction", "右 → 左重建"),
    "stage_merge": ("Merging bilateral maps", "合并双侧图"),
    "stage_roi": ("Exporting ROI table", "导出 ROI 表"),
    "stage_summary": ("Writing summary", "写入汇总"),
    "stage_classifier": ("Classifier validation", "分类器验证"),
    "stage_trt": ("TRT reliability", "TRT 可靠性"),
    "asset_dgn": ("DGN models", "DGN 模型"),
    "asset_atlas": ("Atlas", "脑区图谱"),
    "asset_classifier": ("Classifier", "分类器"),
    "asset_torch": ("PyTorch", "PyTorch"),
    "badge_found": ("found", "已找到"),
    "badge_missing": ("missing", "缺失"),
    "dialog_invalid_title": ("Invalid HemiSpec configuration", "HemiSpec 配置无效"),
    "dialog_cli_title": ("Cannot build CLI command", "无法生成 CLI 命令"),
    "dialog_output_missing_title": ("Output folder not found", "未找到输出文件夹"),
    "dialog_output_missing_body": (
        "Run the workflow first, or choose an existing output folder.",
        "请先运行工作流，或选择一个已存在的输出文件夹。",
    ),
    "dialog_open_title": ("Cannot open output folder", "无法打开输出文件夹"),
    "dialog_failed_title": ("HemiSpec workflow failed", "HemiSpec 工作流失败"),
    "dialog_missing_dep_title": ("Missing HemiSpec GUI dependency", "缺少 HemiSpec GUI 依赖"),
    "dialog_close_title": ("HemiSpec is running", "HemiSpec 正在运行"),
    "dialog_close_body": (
        "A run is still in progress. Stop it and exit?",
        "任务仍在运行。要停止并退出吗？",
    ),
}

_STAGE_KEYS = {
    "l_to_r": "stage_l_to_r",
    "r_to_l": "stage_r_to_l",
    "merge": "stage_merge",
    "roi": "stage_roi",
    "summary": "stage_summary",
    "classifier": "stage_classifier",
    "trt": "stage_trt",
}

_WORKFLOW_STAGE_PATTERNS = (
    (r"\[workflow\]\s+Running L_to_R inference and metrics", "l_to_r"),
    (r"\[workflow\]\s+Running R_to_L inference and metrics", "r_to_l"),
    (r"\[workflow\]\s+Merging bilateral subject maps", "merge"),
    (r"\[workflow\]\s+Exporting bilateral ROI table", "roi"),
    (r"\[workflow\]\s+Writing subject metric summary", "summary"),
    (r"\[workflow\]\s+Running hemisphere-classifier validation", "classifier"),
    (r"\[workflow\]\s+Running TRT reliability validation", "trt"),
)
_INFER_RE = re.compile(
    r"\[infer\]\s+(?P<direction>L_to_R|R_to_L)\s+(?P<current>\d+)/(?P<total>\d+)\s+"
    r"(?P<phase>start|done)\s+(?P<name>.+)"
)
_MERGE_RE = re.compile(r"\[merge\]\s+(?P<current>\d+)/(?P<total>\d+)\s*(?P<name>.*)")


@dataclass(frozen=True)
class ProgressUpdate:
    """Parsed stage/progress information from one workflow log line."""

    stage: str
    detail: str = ""
    current: int | None = None
    total: int | None = None

    @property
    def fraction(self) -> float | None:
        if self.current is None or not self.total:
            return None
        return max(0.0, min(1.0, self.current / self.total))


def parse_progress_line(line: str) -> ProgressUpdate | None:
    """Parse one HemiSpec workflow log line into a stage and optional progress.

    The parser is intentionally pure so it can be tested without Tk or a display.
    Logging itself remains English, as required by the CLI/log contract.
    """

    text = line.strip()
    if not text:
        return None

    infer = _INFER_RE.search(text)
    if infer:
        direction = infer.group("direction")
        stage = "l_to_r" if direction == "L_to_R" else "r_to_l"
        detail = f"{infer.group('phase')} {infer.group('name')}"
        return ProgressUpdate(
            stage=stage,
            detail=detail,
            current=int(infer.group("current")),
            total=int(infer.group("total")),
        )

    merge = _MERGE_RE.search(text)
    if merge:
        return ProgressUpdate(
            stage="merge",
            detail=merge.group("name").strip(),
            current=int(merge.group("current")),
            total=int(merge.group("total")),
        )

    for pattern, stage in _WORKFLOW_STAGE_PATTERNS:
        if re.search(pattern, text):
            return ProgressUpdate(stage=stage, detail="")

    return None


def parse_stage_line(line: str) -> ProgressUpdate | None:
    """Backward-friendly alias for callers that only need stage parsing."""

    return parse_progress_line(line)


def stage_display(stage: str, language: str = "en") -> str:
    """Return the localized display label for a parsed stage code."""

    key = _STAGE_KEYS.get(stage, "stage_idle")
    return translate(key, language)


def translate(key: str, language: str = "en") -> str:
    """Return one UI string in English or Chinese.

    Logs, filesystem paths, and the equivalent CLI command are always emitted in
    English and never pass through this function.
    """

    english, chinese = TRANSLATIONS.get(key, (key, key))
    return chinese if language.lower().startswith("zh") else english


_FONT_FAMILIES = {
    "en": ("Segoe UI", "Microsoft YaHei UI", "Helvetica Neue", "Arial"),
    "zh": ("Microsoft YaHei UI", "Segoe UI", "Helvetica Neue", "Arial"),
}
_FONT_FAMILIES_DARWIN = {
    "en": ("SF Pro Text", "Helvetica Neue", "Arial"),
    "zh": ("PingFang SC", "Hiragino Sans GB", "Helvetica Neue", "Arial"),
}
_MONO_FAMILIES = ("Cascadia Mono", "Consolas", "Courier New")


def _first_available_family(families: tuple[str, ...], available: set[str] | None) -> str:
    if not available:
        return families[0]
    lowered = {name.lower(): name for name in available}
    for family in families:
        if family.lower() in lowered:
            return lowered[family.lower()]
    return families[0]


def gui_font_families(language: str = "en", mono: bool = False, available: set[str] | None = None) -> str:
    """Return the spec's GUI font family for the current OS and language (section 2.2)."""

    if mono:
        return _first_available_family(_MONO_FAMILIES, available)
    zh = str(language).lower().startswith("zh")
    if sys.platform == "darwin":
        return _first_available_family(_FONT_FAMILIES_DARWIN["zh" if zh else "en"], available)
    return _first_available_family(_FONT_FAMILIES["zh" if zh else "en"], available)


def default_ui_language() -> str:
    """Return the spec's default UI language: Chinese for a zh system locale.

    Spec section 7.3: Chinese if the system UI locale starts with "zh",
    otherwise EN. Windows exposes the authoritative value through
    ``GetUserDefaultUILanguage``; other platforms fall back to ``locale``.
    """

    if sys.platform.startswith("win"):
        try:
            import ctypes

            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if (int(lang_id) & 0x3FF) == 0x04:  # LANG_CHINESE
                return "zh"
            return "en"
        except Exception:
            pass
    for getter in (locale.getlocale, getattr(locale, "getdefaultlocale", None)):
        if getter is None:
            continue
        try:
            name = getter()[0] or ""
        except Exception:
            continue
        if str(name).lower().startswith("zh"):
            return "zh"
    for env_name in ("LANG", "LC_ALL", "LC_MESSAGES"):
        if str(os.environ.get(env_name, "")).lower().startswith("zh"):
            return "zh"
    return "en"


def ellipsize(text: str, limit: int = 72) -> str:
    """Trim one status detail line to the spec's ellipsized single-line form."""

    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: max(0, limit - 1)] + "…"


def gui_resource_dir() -> Path | None:
    """Locate the packaged GUI resource directory in source and frozen builds."""

    candidates: list[Path] = []
    candidates.append(Path(__file__).resolve().parent / "resources" / "gui")
    if getattr(sys, "_MEIPASS", None):
        candidates.append(Path(sys._MEIPASS) / "hemispec" / "resources" / "gui")
    try:
        package_gui = importlib.resources.files("hemispec") / "resources" / "gui"
        candidates.append(Path(str(package_gui)))
    except (ImportError, ModuleNotFoundError, TypeError):
        pass
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def gui_icon_path(filename: str = "hemispec.png") -> Path | None:
    """Safely resolve a GUI icon, returning None when it is unavailable."""

    resource_dir = gui_resource_dir()
    if resource_dir is None:
        return None
    candidate = resource_dir / filename
    return candidate if candidate.is_file() else None


def gui_theme_mark_path(theme_id: str) -> Path | None:
    """Resolve the header mark PNG for ``theme_id``, or None when unavailable."""

    filename = THEME_MARK_FILES.get(theme_id)
    if filename is None:
        return None
    return gui_icon_path(filename)


def find_matching_inputs(input_glob: str) -> tuple[Path, ...]:
    """Return regular files matched by the normalized GM input glob."""

    pattern = _normalize_input_glob(input_glob)
    if not pattern:
        return ()
    matches = (Path(path) for path in glob.glob(pattern, recursive=True))
    return tuple(sorted(path for path in matches if path.is_file()))


def output_dir_is_nonempty(path: Path) -> bool:
    """Return True when an existing output path already contains entries."""

    return path.is_dir() and any(path.iterdir())


@dataclass(frozen=True)
class PreflightResult:
    """Outcome of run-time validation that the GUI can act on without dialogs."""

    matches: tuple[Path, ...]
    out_dir: Path | None = None
    requires_confirmation: bool = False


class NoInputFilesError(ValueError):
    """Raised when a glob is valid but matches no input files."""

    def __init__(self, input_glob: str) -> None:
        super().__init__(f"No input files matched: {input_glob}")
        self.input_glob = input_glob


def preflight_workflow_state(state: dict[str, object]) -> PreflightResult:
    """Validate run-time inputs that intentionally stay out of config previews.

    Blocking problems (missing or unmatched inputs, invalid output paths) raise.
    A non-empty output folder is *not* blocking: spec section 7.3 asks the user
    to confirm overwriting, so this returns ``requires_confirmation=True``.
    """

    values: dict[str, object] = dict(ENCAPSULATED_DEFAULTS)
    values.update(state)
    input_glob = _normalize_input_glob(str(values.get("input_glob", "")))
    if not input_glob:
        raise ValueError("GM input glob is required.")
    matches = find_matching_inputs(input_glob)
    if not matches:
        raise NoInputFilesError(input_glob)

    out_text = str(values.get("out_dir", "")).strip()
    if not out_text:
        raise ValueError("Output workspace is required.")
    out_dir = Path(out_text)
    if out_dir.exists() and not out_dir.is_dir():
        raise ValueError(f"Output workspace path is not a directory: {out_dir}")
    return PreflightResult(
        matches=matches,
        out_dir=out_dir,
        requires_confirmation=output_dir_is_nonempty(out_dir),
    )


def safe_match_count(input_glob: str) -> int | None:
    """Count matching input files without letting a bad glob break the UI."""

    try:
        return len(find_matching_inputs(input_glob))
    except (OSError, ValueError, re.error):
        return None


def match_count_display(count: int | None, language: str = "en") -> tuple[str, str]:
    """Return the spec section 7.2 live match text and its status color."""

    if count is None or count <= 0:
        return translate("input_no_matches", language), VERM_700
    return translate("input_match_count", language).format(n=count), SUCCESS_FG


_STATUS_STAGE_LABEL_KEYS = {
    "queued": "stage_queued",
    "l_to_r": "stepper_l_to_r",
    "r_to_l": "stepper_r_to_l",
    "merge": "stepper_merge",
    "roi": "stepper_roi",
    "summary": "stepper_summary",
}


def format_elapsed(seconds: float) -> str:
    """Format elapsed seconds as the spec's ``MM:SS`` clock."""

    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def format_percent(fraction: float | None) -> str:
    """Format a 0..1 fraction as the spec's integer percentage."""

    value = 0.0 if fraction is None else max(0.0, min(1.0, float(fraction)))
    return f"{int(value * 100 + 0.5)}%"


def status_stage_text(
    stage: str | None,
    current: int | None = None,
    total: int | None = None,
    language: str = "en",
) -> str:
    """Return the left side of the run status line, e.g. ``R→L 12/24``."""

    if stage == "classifier":
        return translate("status_validating_classifier", language)
    if stage == "trt":
        return translate("status_validating_trt", language)
    key = _STATUS_STAGE_LABEL_KEYS.get(stage or "")
    label = translate(key, language) if key else translate("stage_idle", language)
    if current is not None and total:
        return f"{label} {current}/{total}"
    return label


def status_line_text(
    stage: str | None,
    current: int | None,
    total: int | None,
    fraction: float | None,
    elapsed_seconds: float,
    language: str = "en",
) -> tuple[str, str]:
    """Return the spec section 7.2 status-line pair (left, right)."""

    left = status_stage_text(stage, current, total, language)
    right = f"{format_percent(fraction)} · {format_elapsed(elapsed_seconds)}"
    return left, right


def should_autoscroll(yview: tuple[float, float], slack: float = AUTOSCROLL_SLACK) -> bool:
    """Return True only when a text widget is already scrolled to the bottom."""

    try:
        _top, bottom = yview
    except (TypeError, ValueError):
        return True
    return float(bottom) >= 1.0 - slack


# Spec section 7.3 "Log tags": one Text tag per row of the table, plus the
# default ink-700 style for everything else.
LOG_TAG_DEFAULT = "log_default"
LOG_TAG_WORKFLOW = "log_workflow"
LOG_TAG_MODELS = "log_models"
LOG_TAG_WARNING = "log_warning"
LOG_TAG_ERROR = "log_error"
LOG_TAG_SUCCESS = "log_success"

LOG_TAG_ORDER = (
    LOG_TAG_WORKFLOW,
    LOG_TAG_MODELS,
    LOG_TAG_WARNING,
    LOG_TAG_ERROR,
    LOG_TAG_SUCCESS,
    LOG_TAG_DEFAULT,
)


def classify_log_line(line: str) -> str:
    """Return the spec section 7.3 log tag for one (possibly partial) line.

    Rows are matched top to bottom in the spec table's order, so the first row
    that matches wins: ``[workflow]``, ``[models]``, WARNING/warn,
    Error/Traceback/ERROR, the final success line, then the ink-700 default.
    """

    text = str(line)
    if "[workflow]" in text:
        return LOG_TAG_WORKFLOW
    if "[models]" in text:
        return LOG_TAG_MODELS
    lowered = text.lower()
    if "warning" in lowered or "warn" in lowered:
        return LOG_TAG_WARNING
    if "error" in lowered or "traceback" in lowered:
        return LOG_TAG_ERROR
    # The workflow's terminal success line is "[done] ... complete".
    if text.strip().startswith("[done]"):
        return LOG_TAG_SUCCESS
    return LOG_TAG_DEFAULT


def _apply_window_icon(window: tk.Misc) -> None:
    """Best-effort window icon loading that never blocks GUI startup."""

    ico_path = gui_icon_path("hemispec.ico")
    if sys.platform.startswith("win") and ico_path is not None:
        try:
            window.iconbitmap(str(ico_path))
            return
        except (tk.TclError, OSError):
            pass
    png_path = gui_icon_path("hemispec.png")
    if png_path is None:
        return
    try:
        image = tk.PhotoImage(master=window, file=str(png_path))
        window.iconphoto(True, image)
        setattr(window, "_hemispec_icon_image", image)
    except (tk.TclError, OSError):
        pass


def fit_window_geometry(
    work_area: tuple[int, int, int, int],
    scaling: float,
    preferred: tuple[int, int] = DEFAULT_WINDOW_SIZE,
    minimum: tuple[int, int] = MIN_WINDOW_SIZE,
    target_fractions: tuple[float, float] = WINDOW_TARGET_FRACTIONS,
    min_inset: int = MIN_WINDOW_INSET_PX,
) -> tuple[int, int, int, int, int, int]:
    """Fit a logical-size CTk window inside a physical monitor work area.

    Spec section 7.1: convert the physical work area to logical units by
    dividing by the window scaling factor ``s``, then target
    ``min(cap, fraction * logical work area)`` and set
    ``minsize = min(cap, logical work area - 32)``. CTk scales window
    width/height but leaves the ``+x+y`` part of the geometry string in
    physical pixels, so this returns logical dimensions plus physical
    placement. The pure helper is separate from Tk for headless tests.
    """

    area_left, area_top, area_width, area_height = (int(value) for value in work_area)
    scale = max(0.4, float(scaling))
    logical_width = max(320.0, area_width / scale)
    logical_height = max(240.0, area_height / scale)
    fraction_x, fraction_y = target_fractions
    target_width = min(int(preferred[0]), int(fraction_x * logical_width))
    target_height = min(int(preferred[1]), int(fraction_y * logical_height))
    # Spec section 7.1: minsize = min(cap, logical work area - 32). The result is
    # a floor for user resizing; raising the target to it only matters in
    # degenerate tiny work areas and keeps the window inside the work area.
    min_width = max(320, min(int(minimum[0]), int(logical_width) - int(min_inset)))
    min_height = max(240, min(int(minimum[1]), int(logical_height) - int(min_inset)))
    width = max(target_width, min_width)
    height = max(target_height, min_height)
    x = area_left + max(0, (area_width - round(width * scale)) // 2)
    y = area_top + max(0, (area_height - round(height * scale)) // 2)
    return width, height, x, y, min_width, min_height


def _windows_work_area(window: tk.Misc) -> tuple[int, int, int, int] | None:
    """Return the primary monitor work area in physical pixels on Windows."""

    if not sys.platform.startswith("win"):
        return None
    try:
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        if not ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return None
        return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
    except Exception:
        return None


def _window_scaling(window: tk.Misc) -> float:
    if ctk is None:
        return 1.0
    try:
        return float(ctk.ScalingTracker.get_window_dpi_scaling(window))
    except Exception:
        return 1.0


def apply_initial_window_geometry(window: tk.Misc) -> None:
    """Size and center the window inside the real DPI-scaled work area."""

    work_area = _windows_work_area(window)
    if work_area is None:
        width, height = DEFAULT_WINDOW_SIZE
        window.geometry(f"{width}x{height}")
        window.minsize(*MIN_WINDOW_SIZE)
        return
    width, height, x, y, min_width, min_height = fit_window_geometry(work_area, _window_scaling(window))
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(min_width, min_height)


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


def runtime_status_state(item: RuntimeAssetStatus, *, classifier_required: bool = False) -> str:
    """Classify one runtime asset row for the spec section 7.3 status chips."""

    if item.ok:
        return "ready"
    if item.key == "classifier" and not classifier_required:
        return "optional"
    if item.message.startswith("partial/") or item.message == "missing label table":
        return "partial"
    return "missing"


def runtime_mode_display(label: str, language: str = "en") -> str:
    """Translate the mode badge for display without changing the English contract."""

    key = {"Lightweight": "mode_lightweight", "Model-enabled": "mode_model_enabled"}.get(label)
    return translate(key, language) if key is not None else label


_RUNTIME_MESSAGE_ZH = {
    "missing model root": "模型根目录缺失",
    "missing/not downloaded model root path": "模型根目录缺失/未下载",
    "found atlas and label table": "已找到 atlas 与标签表",
    "missing atlas NIfTI": "缺少 atlas NIfTI",
    "missing label table": "缺少标签表",
    "missing atlas NIfTI, label table": "缺少 atlas NIfTI、标签表",
    "missing classifier path": "分类器路径缺失",
    "missing classifier model files": "分类器模型文件缺失",
    "missing/not downloaded classifier directory": "分类器目录缺失/未下载",
    "available": "可用",
    "missing": "缺失",
}

_RUNTIME_GUIDANCE_ZH = {
    "Use the default released DGN bundle, or set HEMISPEC_DGN_MODEL_ROOT for a custom bundle.": (
        "使用默认发布的 DGN 模型包，或通过 HEMISPEC_DGN_MODEL_ROOT 指定自定义模型包。"
    ),
    "Ready for DGN inference.": "已就绪，可进行 DGN 推理。",
    "Default installs auto-download released checkpoints on first model run; use --model-root only for custom bundles.": (
        "默认安装会在首次运行模型时自动下载已发布检查点；仅自定义模型包需要使用 --model-root。"
    ),
    "Ready for optional ROI export.": "已就绪，可进行可选 ROI 导出。",
    "Set HEMISPEC_GLASSER_ATLAS / HEMISPEC_GLASSER_LABEL_TABLE or browse custom ROI files.": (
        "设置 HEMISPEC_GLASSER_ATLAS / HEMISPEC_GLASSER_LABEL_TABLE，或浏览选择自定义 ROI 文件。"
    ),
    "Default installs auto-download the released classifier when validation is enabled.": (
        "默认安装会在启用验证时自动下载已发布分类器。"
    ),
    "Check classifier mode and bundle layout.": "请检查分类器模式与模型包目录结构。",
    "Ready when classifier validation is enabled.": "启用分类器验证后即可使用。",
    "Classifier validation is optional; the released bundle can auto-download when validation is enabled.": (
        "分类器验证为可选项；启用验证时已发布模型包可自动下载。"
    ),
    "DGN inference can use the installed torch runtime.": "DGN 推理可使用当前已安装的 torch 运行时。",
    "Start the GUI from an environment with torch, e.g. conda activate d2l, or install hemispec-toolkit[model].": (
        "请在已安装 torch 的环境中启动 GUI，例如 conda activate d2l，或安装 hemispec-toolkit[model]。"
    ),
}


def runtime_status_display(item: RuntimeAssetStatus, language: str = "en") -> tuple[str, str]:
    """Return localized display text for one English runtime-status record."""

    if not str(language).lower().startswith("zh"):
        return item.message, item.guidance

    message = _RUNTIME_MESSAGE_ZH.get(item.message)
    if message is None and item.message.startswith("found bilateral checkpoints ("):
        message = "已找到双侧检查点 (" + item.message[len("found bilateral checkpoints (") :]
    if message is None and item.message.startswith("partial/missing checkpoints ("):
        # Spec section 7.3 names this phrase exactly.
        message = "检查点不完整或缺失"
    if message is None and item.message.startswith("found ") and "model(s) for mode " in item.message:
        detail, _, mode = item.message[len("found ") :].partition(" model(s) for mode ")
        message = f"已找到 {detail} 模型（模式 {mode}）"
    if message is None and item.message.startswith("cannot inspect bundle ("):
        detail = item.message[len("cannot inspect bundle (") :].removesuffix(")")
        message = f"无法检查模型包（{detail}）"
    if message is None:
        message = item.message
    guidance = _RUNTIME_GUIDANCE_ZH.get(item.guidance, item.guidance)
    return message, guidance


def stage_detail_display(detail: str, language: str = "en") -> str:
    """Translate the GUI-owned prefix of a runtime stage detail, preserving filenames."""

    if str(language).lower().startswith("zh"):
        if detail.startswith("start "):
            return "开始 " + detail[len("start ") :]
        if detail.startswith("done "):
            return "完成 " + detail[len("done ") :]
    return detail


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


def _open_path(path: Path) -> bool:
    """Open an existing folder in the OS file manager; no-op when absent."""

    if not path.is_dir():
        return False
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])
    return True


class _StdoutProxy(io.TextIOBase):
    def __init__(self, emit: Callable[[str], None]) -> None:
        self._emit = emit

    def write(self, text: str) -> int:
        if text:
            self._emit(text)
        return len(text)

    def flush(self) -> None:
        return None


def _widget_scaling(widget: object) -> float:
    if ctk is None:
        return 1.0
    try:
        return max(0.4, float(ctk.ScalingTracker.get_widget_scaling(widget)))
    except Exception:
        return 1.0


def bind_button_keyboard(
    button: object,
    *,
    focus_color: str | None = None,
    ring_width: int = TOGGLE_FOCUS_RING,
) -> object:
    """Make a CTkButton Tab-reachable and Enter/Space activatable.

    Spec section 7.5: tab order follows visual order and every action is
    keyboard-reachable. CTkButton keeps focus on its internal canvas and does
    not take focus by default, so that canvas is the widget that receives keys.
    The focus ring follows the spec's 2px teal-500 rule (section 7.3); the ring
    color resolves to the current theme's teal-500 at call time so a rebuilt
    window tracks the active theme.
    Returns the invoke handler so tests can call it directly; an unmapped
    window cannot receive generated key events.
    """

    if focus_color is None:
        focus_color = TEAL_500

    canvas = getattr(button, "_canvas", None)
    if canvas is None:
        return None
    try:
        canvas.configure(takefocus=1)
    except tk.TclError:
        return None

    restore: dict[str, object] = {"width": None, "color": None}

    def _state(attribute: str, default: object) -> object:
        try:
            return button.cget(attribute)  # type: ignore[attr-defined]
        except (tk.TclError, AttributeError, ValueError):
            return default

    def invoke(_event: object = None) -> str:
        if str(_state("state", "normal")) == "disabled":
            return "break"
        try:
            button.invoke()  # type: ignore[attr-defined]
        except (tk.TclError, AttributeError):
            pass
        return "break"

    def focus_in(_event: object = None) -> None:
        if restore["width"] is None:
            restore["width"] = _state("border_width", 0)
            restore["color"] = _state("border_color", focus_color)
        try:
            button.configure(  # type: ignore[attr-defined]
                border_width=ring_width, border_color=focus_color
            )
        except (tk.TclError, AttributeError, ValueError):
            pass

    def focus_out(_event: object = None) -> None:
        width = 0 if restore["width"] is None else restore["width"]
        color = focus_color if restore["color"] is None else restore["color"]
        try:
            button.configure(border_width=width, border_color=color)  # type: ignore[attr-defined]
        except (tk.TclError, AttributeError, ValueError):
            pass

    for sequence in ("<Return>", "<KP_Enter>", "<space>"):
        try:
            canvas.bind(sequence, invoke)
        except tk.TclError:
            continue
    try:
        canvas.bind("<FocusIn>", focus_in)
        canvas.bind("<FocusOut>", focus_out)
    except tk.TclError:
        pass
    setattr(button, "_hemispec_keyboard_invoke", invoke)
    setattr(button, "_hemispec_keyboard_focus", (focus_in, focus_out))
    return invoke


class ToggleCapsule(ctk.CTkFrame if ctk is not None else tk.Frame):  # type: ignore[misc]
    """Spec section 7.3 toggle: a Canvas capsule, never CTkSwitch.

    The track is 40x22 logical with radius 11, a 16px knob inset 3, and it is
    reachable by Tab (Space/Enter toggle). The caller owns the BooleanVar.
    """

    def __init__(self, master: object, variable: object, command: Callable[[], None] | None = None) -> None:
        super().__init__(master, fg_color="transparent", width=0, height=0)
        self._variable = variable
        self._command = command
        self._enabled = True
        self._hover = False
        self._focused = False
        self._toggle_canvas = tk.Canvas(
            self, highlightthickness=0, bd=0, bg=PAPER_0, takefocus=1, cursor="hand2"
        )
        self._toggle_canvas.pack()
        self._toggle_canvas.bind("<Button-1>", lambda _event: self.toggle())
        self._toggle_canvas.bind("<space>", lambda _event: self.toggle())
        self._toggle_canvas.bind("<Return>", lambda _event: self.toggle())
        self._toggle_canvas.bind("<Enter>", self._on_enter)
        self._toggle_canvas.bind("<Leave>", self._on_leave)
        self._toggle_canvas.bind("<FocusIn>", self._on_focus_in)
        self._toggle_canvas.bind("<FocusOut>", self._on_focus_out)
        try:
            variable.trace_add("write", lambda *_args: self._redraw())  # type: ignore[union-attr]
        except AttributeError:
            pass
        self._redraw()

    def _on_enter(self, _event: object = None) -> None:
        if self._enabled:
            self._hover = True
            self._redraw()

    def _on_leave(self, _event: object = None) -> None:
        self._hover = False
        self._redraw()

    def _on_focus_in(self, _event: object = None) -> None:
        self._focused = True
        self._redraw()

    def _on_focus_out(self, _event: object = None) -> None:
        self._focused = False
        self._redraw()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        try:
            self._toggle_canvas.configure(takefocus=1 if self._enabled else 0, cursor="hand2" if self._enabled else "")
        except tk.TclError:
            pass
        self._redraw()

    def toggle(self) -> None:
        if not self._enabled:
            return
        try:
            self._variable.set(not bool(self._variable.get()))  # type: ignore[union-attr]
        except AttributeError:
            return
        self._redraw()
        if self._command is not None:
            self._command()

    def _set_scaling(self, *args: object, **kwargs: object) -> None:
        super()._set_scaling(*args, **kwargs)  # type: ignore[misc]
        if hasattr(self, "_canvas"):
            self._redraw()

    @staticmethod
    def _stadium_fill(canvas: tk.Canvas, x0: float, y0: float, x1: float, y1: float, radius: float, fill: str) -> None:
        canvas.create_oval(x0, y0, x0 + 2 * radius, y1, fill=fill, outline="")
        canvas.create_oval(x1 - 2 * radius, y0, x1, y1, fill=fill, outline="")
        canvas.create_rectangle(x0 + radius, y0, x1 - radius, y1, fill=fill, outline="")

    @staticmethod
    def _stadium_outline(
        canvas: tk.Canvas,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        radius: float,
        color: str,
        width: float,
    ) -> None:
        canvas.create_arc(
            x0, y0, x0 + 2 * radius, y1, start=90, extent=180, style="arc", outline=color, width=width
        )
        canvas.create_arc(
            x1 - 2 * radius, y0, x1, y1, start=270, extent=180, style="arc", outline=color, width=width
        )
        canvas.create_line(x0 + radius, y0 + width / 2, x1 - radius, y0 + width / 2, fill=color, width=width)
        canvas.create_line(x0 + radius, y1 - width / 2, x1 - radius, y1 - width / 2, fill=color, width=width)

    def _redraw(self) -> None:
        scale = _widget_scaling(self)
        ring = TOGGLE_FOCUS_RING
        width = int(round((TOGGLE_TRACK_W + 2 * ring) * scale))
        # Spec section 7.3: hit target is at least 28 logical units tall.
        height = int(round(max(TOGGLE_TRACK_H + 2 * ring, 28) * scale))
        canvas = self._toggle_canvas
        try:
            if int(canvas.cget("width") or 0) != width or int(canvas.cget("height") or 0) != height:
                canvas.configure(width=width, height=height)
        except (tk.TclError, ValueError):
            return
        canvas.delete("all")

        on = bool(self._variable.get())  # type: ignore[union-attr]
        if not self._enabled:
            track, border, knob = PAPER_100, LINE_300, LINE_300
        elif on:
            track, border, knob = (TEAL_600 if self._hover else TEAL_500), "", PAPER_0
        else:
            track, border, knob = PAPER_100, (INK_600 if self._hover else CONTROL_OFF), CONTROL_OFF

        x0 = ring * scale
        y0 = (height - TOGGLE_TRACK_H * scale) / 2
        x1 = x0 + TOGGLE_TRACK_W * scale
        y1 = y0 + TOGGLE_TRACK_H * scale
        radius = TOGGLE_RADIUS * scale

        if self._focused and self._enabled:
            self._stadium_outline(
                canvas,
                x0 - 1 * scale,
                y0 - 1 * scale,
                x1 + 1 * scale,
                y1 + 1 * scale,
                radius + 1 * scale,
                TEAL_200,
                2 * scale,
            )
        self._stadium_fill(canvas, x0, y0, x1, y1, radius, track)
        if border:
            self._stadium_outline(canvas, x0, y0, x1, y1, radius, border, 1.5 * scale)

        diameter = TOGGLE_KNOB * scale
        center_y = (y0 + y1) / 2
        if on:
            center_x = x1 - TOGGLE_INSET * scale - diameter / 2
        else:
            center_x = x0 + TOGGLE_INSET * scale + diameter / 2
        canvas.create_oval(
            center_x - diameter / 2,
            center_y - diameter / 2,
            center_x + diameter / 2,
            center_y + diameter / 2,
            fill=knob,
            outline="",
        )


class Stepper(ctk.CTkFrame if ctk is not None else tk.Frame):  # type: ignore[misc]
    """Spec section 7.3 five-node stepper drawn on a Canvas."""

    def __init__(self, master: object, font_factory: Callable[..., object]) -> None:
        super().__init__(master, fg_color="transparent")
        self._font = font_factory
        self._language = "en"
        self._states = {node: "pending" for node in STEPPER_NODES}
        self._sublabels: dict[str, str] = {}
        self._stepper_canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=PAPER_0)
        self._stepper_canvas.pack(fill="x", expand=True)
        self._stepper_canvas.bind("<Configure>", lambda _event: self._redraw())
        self._number_font = font_factory(11)
        self._number_bold = font_factory(11, "bold")
        self._label_font = font_factory(12)
        self._label_bold = font_factory(12, "bold")
        self._sub_font = font_factory(11, mono=True)
        self._redraw()

    def set_language(self, language: str) -> None:
        self._language = "zh" if str(language).lower().startswith("zh") else "en"
        self._redraw()

    def set_states(self, states: dict[str, str], sublabels: dict[str, str] | None = None) -> None:
        self._states.update(states)
        if sublabels is not None:
            self._sublabels = dict(sublabels)
        self._redraw()

    def reset(self, roi_enabled: bool) -> None:
        self._states = {node: "pending" for node in STEPPER_NODES}
        if not roi_enabled:
            self._states["roi"] = "skipped"
        self._sublabels = {}
        self._redraw()

    def node_state(self, node: str) -> str:
        return self._states.get(node, "pending")

    def _set_scaling(self, *args: object, **kwargs: object) -> None:
        super()._set_scaling(*args, **kwargs)  # type: ignore[misc]
        if hasattr(self, "_canvas"):
            self._redraw()

    def _redraw(self) -> None:
        scale = _widget_scaling(self)
        canvas = self._stepper_canvas
        width = max(int(canvas.winfo_width()), 320)
        height = int(round(58 * scale))
        try:
            if int(canvas.cget("height") or 0) != height:
                canvas.configure(height=height)
        except (tk.TclError, ValueError):
            return
        canvas.delete("all")

        pad = 2 * scale
        radius = 11 * scale
        center_y = pad + radius
        count = len(STEPPER_NODES)
        left = pad + radius
        right = width - pad - radius
        centers = [
            left + (index * (right - left) / (count - 1)) if count > 1 else left
            for index in range(count)
        ]

        for index in range(count - 1):
            node = STEPPER_NODES[index]
            color = TEAL_500 if self._states.get(node) == "done" else LINE_200
            canvas.create_line(
                centers[index] + radius,
                center_y,
                centers[index + 1] - radius,
                center_y,
                fill=color,
                width=max(1, int(round(2 * scale))),
            )

        for index, node in enumerate(STEPPER_NODES):
            state = self._states.get(node, "pending")
            cx = centers[index]
            fill, border, border_width, mark, mark_color = PAPER_0, LINE_300, 1.5, str(index + 1), INK_500
            mark_font = self._number_font
            label_color = INK_500
            label_font = self._label_font
            if state == "active":
                fill, border, border_width = TEAL_50, HIGHLIGHT, 2
                mark_color, mark_font = TEAL_700, self._number_bold
                label_color, label_font = INK_900, self._label_bold
            elif state == "done":
                fill, border, mark, mark_color = TEAL_500, "", "✓", PAPER_0
                mark_font = self._number_bold
                label_color = INK_700
            elif state == "error":
                fill, border, border_width = VERM_50, VERM_600, 2
                mark, mark_color, mark_font = "!", VERM_700, self._number_bold
                label_color = VERM_700
            elif state == "skipped":
                fill, border, border_width = PAPER_100, LINE_200, 1.5
                mark, mark_color = "–", INK_500
                label_color = INK_500

            canvas.create_oval(
                cx - radius,
                center_y - radius,
                cx + radius,
                center_y + radius,
                fill=fill,
                outline=border if border else fill,
                width=max(1, int(round(border_width * scale))) if border else 0,
            )
            canvas.create_text(
                cx,
                center_y,
                text=mark,
                fill=mark_color,
                font=mark_font,
                anchor="center",
            )
            canvas.create_text(
                cx,
                center_y + radius + 4 * scale,
                text=translate(f"stepper_{node}", self._language),
                fill=label_color,
                font=label_font,
                anchor="n",
            )
            sublabel = self._sublabels.get(node)
            if state == "skipped":
                sublabel = translate("stepper_skipped", self._language)
            if sublabel and state in ("active", "skipped"):
                canvas.create_text(
                    cx,
                    center_y + radius + 22 * scale,
                    text=sublabel,
                    fill=TEAL_700 if state == "active" else INK_500,
                    font=self._sub_font,
                    anchor="n",
                )


class HemiSpecGui(ctk.CTk if ctk is not None else tk.Tk):  # type: ignore[misc]
    """Two-pane HemiSpec desktop workbench.

    The left pane collects the input/output contract; the wider right pane holds
    optional analyses, the run controls, and the live English output log. All
    worker output reaches Tk through a queue polled on the main thread.
    """

    def __init__(self) -> None:
        ensure_gui_dependency()
        super().__init__()
        apply_theme_globals(DEFAULT_THEME)

        self.title(f"{APP_TITLE} — {APP_SUBTITLE}")
        self.configure(fg_color=PAPER_50)
        apply_initial_window_geometry(self)
        _apply_window_icon(self)

        self._available_fonts = self._detect_available_fonts()
        self._font_specs: list[tuple[object, int, str, bool]] = []
        self.is_running = False
        self.cancel_event = threading.Event()
        self.last_out_dir: Path | None = None
        self.vars: dict[str, object] = {}
        self.language_var = ctk.StringVar(value=default_ui_language())
        self.theme_var = ctk.StringVar(value=DEFAULT_THEME)
        self.status_var = ctk.StringVar(value="Ready")
        self.runtime_mode_var = ctk.StringVar(value="checking")
        self.summary_var = ctk.StringVar(value="Primary output: voxel-wise ANS/RNS maps")
        self.stage_var = ctk.StringVar(value="Idle")
        self._status_refresh_after_id: str | None = None
        self._status_key = "status_ready"
        self._status_args: dict[str, object] = {}
        self._summary_key = "summary_default"
        self._summary_args: dict[str, object] = {}
        self._stage_key = "stage_idle"
        self._stage_detail = ""
        self._i18n_labels: list[tuple[object, str]] = []
        self._language_refreshers: list[Callable[[], None]] = []
        self._language_buttons: dict[str, object] = {}
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._poll_after_id: str | None = None
        self._configure_bound = False
        self._close_when_done = False
        self._closing = False
        self._header_image: object | None = None

        # Phase 3 live feedback: debounced match count, run clock/status line,
        # copy-button feedback, and log autoscroll state.
        self._match_after_id: str | None = None
        self._run_started_at: float | None = None
        self._run_stage: str | None = None
        self._run_current: int | None = None
        self._run_total: int | None = None
        self._run_fraction: float | None = None
        self._elapsed_after_id: str | None = None
        self._copy_after_id: str | None = None
        self._copy_feedback_button: object | None = None
        self._status_line_key: str | None = None
        self._status_line_color = INK_700
        self._progress_indeterminate = False
        self._log_bold_font: object | None = None

        self._build_state()
        self._build_layout()
        self._sync_roi_state()
        self._set_status("status_ready")
        self._set_summary("summary_default")
        self._set_stage("stage_idle")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_after_id = self.after(80, self._poll_events)

    def _detect_available_fonts(self) -> set[str]:
        try:
            return set(tkfont.families(self))
        except (tk.TclError, AttributeError):
            return set()

    def _font(self, size: int, weight: str = "normal", mono: bool = False) -> object:
        font = ctk.CTkFont(
            family=gui_font_families(str(self.language_var.get()), mono, self._available_fonts),
            size=size,
            weight=weight,
        )
        self._font_specs.append((font, size, weight, mono))
        return font

    def _retune_fonts(self) -> None:
        language = str(self.language_var.get())
        for font, _size, _weight, mono in self._font_specs:
            try:
                font.configure(  # type: ignore[attr-defined]
                    family=gui_font_families(language, mono, self._available_fonts)
                )
            except (tk.TclError, AttributeError, ValueError):
                continue

    # ------------------------------------------------------------------ state
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

    # ------------------------------------------------------------------ i18n
    def _t(self, key: str) -> str:
        return translate(key, str(self.language_var.get()))

    def _register_label(self, widget: object, key: str) -> object:
        self._i18n_labels.append((widget, key))
        return widget

    def _label(self, parent: object, key: str, **kwargs: object) -> object:
        widget = ctk.CTkLabel(parent, text=self._t(key), **kwargs)
        return self._register_label(widget, key)

    def _set_status(self, key: str, **kwargs: object) -> None:
        self._status_key = key
        self._status_args = dict(kwargs)
        self.status_var.set(self._t(key).format(**kwargs))

    def _set_summary(self, key: str, **kwargs: object) -> None:
        self._summary_key = key
        self._summary_args = dict(kwargs)
        self.summary_var.set(self._t(key).format(**kwargs))

    def _set_stage(self, key: str, detail: str = "") -> None:
        self._stage_key = key
        self._stage_detail = detail
        label = self._t(key)
        display_detail = stage_detail_display(detail, str(self.language_var.get()))
        self.stage_var.set(f"{label} · {display_detail}" if display_detail else label)

    def _set_language(self, language: str) -> None:
        language = "zh" if str(language).lower().startswith("zh") else "en"
        previous = str(self.language_var.get())
        self.language_var.set(language)
        self._apply_language()
        if previous != language:
            self._log(
                "[ui] Language set to "
                f"{'Chinese' if language == 'zh' else 'English'} "
                "(workflow logs, paths, and CLI commands remain English).\n"
            )

    def _apply_language(self) -> None:
        for widget in list(self._i18n_labels):
            widget_obj, key = widget
            try:
                widget_obj.configure(text=self._t(key))  # type: ignore[attr-defined]
            except (tk.TclError, AttributeError, ValueError):
                continue
        for refresh in list(self._language_refreshers):
            try:
                refresh()
            except (tk.TclError, AttributeError, ValueError):
                continue
        self._set_status(self._status_key, **self._status_args)
        self._set_summary(self._summary_key, **self._summary_args)
        self._set_stage(self._stage_key, self._stage_detail)
        self._refresh_status_line()
        self._refresh_match_count()
        self._set_open_output_primary(self._status_line_key == "status_done")
        if hasattr(self, "stepper"):
            self.stepper.set_language(str(self.language_var.get()))
        self._refresh_language_buttons()
        self._retune_fonts()
        if hasattr(self, "asset_status_frame"):
            self._refresh_runtime_status()

    def _refresh_language_buttons(self) -> None:
        for code, button in self._language_buttons.items():
            active = code == str(self.language_var.get())
            try:
                button.configure(  # type: ignore[attr-defined]
                    fg_color=TEAL_50 if active else PAPER_0,
                    hover_color=TEAL_50 if active else PAPER_100,
                    text_color=TEAL_700 if active else INK_600,
                )
            except (tk.TclError, AttributeError):
                continue

    # --------------------------------------------------------------- theming
    def apply_theme(self, theme_id: str) -> bool:
        """Switch to ``THEMES[theme_id]`` and rebuild the window content.

        Refused (returns ``False``, no change) while a run is in progress. State
        in ``self.vars``, the language, and the log text survive the rebuild; the
        CLI box, environment status, layout mode, and stepper are re-rendered.
        """

        if theme_id not in THEMES:
            return False
        if self.is_running:
            # Keep the picker in sync with the run state; it is disabled now and
            # _refresh_action_buttons re-enables it when the run finishes.
            self._refresh_theme_control()
            return False
        if theme_id == str(self.theme_var.get()):
            return True

        pending = self._cancel_rebuild_after_jobs()

        # Log text and scroll position move to the rebuilt log box verbatim; the
        # per-line tags are re-applied through the normal _log path.
        log_text = ""
        log_scroll = None
        if hasattr(self, "log_box"):
            try:
                log_text = self.log_box.get("1.0", "end-1c")
                log_scroll = self.log_box.yview()
            except (tk.TclError, AttributeError):
                log_text, log_scroll = "", None

        self.theme_var.set(theme_id)
        apply_theme_globals(theme_id)
        self.configure(fg_color=PAPER_50)

        main = getattr(self, "_main_frame", None)
        if main is not None:
            main.destroy()

        self._i18n_labels = []
        self._language_refreshers = []
        self._font_specs = []
        self._build_layout()
        if self._header_image is not None:
            try:
                self._header_image.configure(size=(28, 28))
            except (AttributeError, tk.TclError):
                pass

        # _build_log_card seeds the fresh box with the "Ready" welcome line;
        # replace it with the captured content so nothing is duplicated.
        if log_text:
            self.log_box.configure(state="normal")
            self.log_box.delete("1.0", "end")
            for chunk in str(log_text).splitlines(keepends=True) or [str(log_text)]:
                start = self.log_box.index("end-1c")
                self.log_box.insert("end", chunk)
                self.log_box.tag_add(classify_log_line(chunk), start, "end-1c")
            self.log_box.configure(state="disabled")
            if log_scroll is not None:
                try:
                    self.log_box.yview_moveto(log_scroll[0])
                except (tk.TclError, AttributeError):
                    pass

        # Re-apply state that is not carried by widgets: language-dependent
        # strings, derived widget states, and cached environment status.
        self._sync_roi_state()
        self._set_status(self._status_key, **self._status_args)
        self._set_summary(self._summary_key, **self._summary_args)
        self._set_stage(self._stage_key, self._stage_detail)
        self._refresh_status_line()
        self._refresh_runtime_status()
        self._refresh_match_count()
        self._refresh_action_buttons()
        self._refresh_theme_control()
        if pending:
            self._schedule_match_count()
        self._evaluate_layout()
        return True

    def _cancel_rebuild_after_jobs(self) -> list[str]:
        """Cancel pending ``after()`` jobs that target the destroyed widgets."""

        cancelled: list[str] = []
        for attribute in (
            "_match_after_id",
            "_status_refresh_after_id",
            "_copy_after_id",
        ):
            after_id = getattr(self, attribute, None)
            if after_id is not None:
                try:
                    self.after_cancel(after_id)
                    cancelled.append(str(attribute))
                except tk.TclError:
                    pass
                setattr(self, attribute, None)
        return cancelled

    # --------------------------------------------------------------- layout
    def _build_layout(self) -> None:
        # Spec sections 7.1/7.2: two columns above 1060 logical width, a single
        # scroll column below it. Both containers live in the same body frame so
        # cards can be re-gridded without rebuilding their state.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main = ctk.CTkFrame(self, corner_radius=0, fg_color=PAPER_50)
        self._main_frame = main
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_header(main)

        body = ctk.CTkFrame(main, fg_color="transparent")
        body.grid(row=1, column=0, padx=16, pady=16, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=COLUMN_WEIGHTS[0], minsize=COLUMN_MINSIZE[0])
        body.grid_columnconfigure(1, weight=COLUMN_WEIGHTS[1], minsize=COLUMN_MINSIZE[1])
        self._body = body

        self._left_scroll = ctk.CTkScrollableFrame(
            body,
            fg_color=PAPER_50,
            width=COLUMN_MINSIZE[0],
            scrollbar_fg_color=PAPER_50,
            scrollbar_button_color=LINE_300,
            scrollbar_button_hover_color=LINE_400,
        )
        _speed_up_scroll(self._left_scroll)
        self._left_scroll.grid(row=0, column=0, padx=(0, COLUMN_GAP // 2), sticky="nsew")
        self._left_scroll.grid_columnconfigure(0, weight=1)

        self._right_column = ctk.CTkFrame(body, fg_color="transparent")
        self._right_column.grid(row=0, column=1, padx=(COLUMN_GAP // 2, 0), sticky="nsew")
        self._right_column.grid_columnconfigure(0, weight=1)
        self._right_column.grid_rowconfigure(2, weight=1)

        self._single_scroll = ctk.CTkScrollableFrame(
            body,
            fg_color=PAPER_50,
            width=COLUMN_MINSIZE[0],
            scrollbar_fg_color=PAPER_50,
            scrollbar_button_color=LINE_300,
            scrollbar_button_hover_color=LINE_400,
        )
        _speed_up_scroll(self._single_scroll)
        self._single_scroll.grid_columnconfigure(0, weight=1)

        # Cards are created as children of ``body`` and then gridded into whichever
        # container is active. Tk's grid -in only allows a container that descends
        # from the widget's master, so this keeps two-column/single-column
        # switching possible without rebuilding any widget or state.
        self._cards = {
            "input_output": self._build_input_output_card(body, 0),
            "optional": self._build_optional_card(body, 1),
            "cli": self._build_cli_card(body, 2),
            "environment": self._build_environment_card(body, 0),
            "run": self._build_run_card(body, 1),
            "log": self._build_log_card(body, 2),
        }
        self._layout_mode = ""
        self._apply_layout_mode("two")
        self._layout_after_id: str | None = None
        if not self._configure_bound:
            self.bind("<Configure>", self._on_window_configure, add="+")
            self._configure_bound = True

        footer = ctk.CTkFrame(main, height=28, corner_radius=0, fg_color=PAPER_50)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            footer,
            textvariable=self.summary_var,
            text_color=INK_500,
            font=self._font(12),
        ).grid(row=0, column=0, padx=22, pady=(0, 8), sticky="w")

    def _on_window_configure(self, event: object) -> None:
        # Spec section 7.1: re-evaluate layout on <Configure> with a 150ms debounce.
        if getattr(event, "widget", None) is not self:
            return
        if self._layout_after_id is not None:
            try:
                self.after_cancel(self._layout_after_id)
            except tk.TclError:
                pass
        self._layout_after_id = self.after(RESPONSIVE_DEBOUNCE_MS, self._evaluate_layout)

    def _evaluate_layout(self) -> None:
        self._layout_after_id = None
        try:
            physical_width = int(self.winfo_width())
        except tk.TclError:
            return
        scale = _window_scaling(self)
        logical_width = physical_width / scale if scale else physical_width
        self._apply_layout_mode(
            "single" if logical_width < RESPONSIVE_BREAKPOINT else "two"
        )

    def _apply_layout_mode(self, mode: str) -> None:
        if getattr(self, "_layout_mode", None) == mode:
            return
        self._layout_mode = mode
        if mode == "single":
            # One scroll frame holds every card; the two-column minimum widths
            # would otherwise force a wider window than the spec's minsize.
            self._body.grid_columnconfigure(0, weight=1, minsize=0)
            self._body.grid_columnconfigure(1, weight=0, minsize=0)
            self._hide_container(self._left_scroll)
            self._hide_container(self._right_column)
            self._show_container(self._single_scroll, row=0, column=0, columnspan=2, sticky="nsew")
            order = ("input_output", "optional", "cli", "environment", "run", "log")
            for row, name in enumerate(order):
                self._place_card(self._cards[name], self._single_scroll, row, expand=False)
            return

        self._body.grid_columnconfigure(0, weight=COLUMN_WEIGHTS[0], minsize=COLUMN_MINSIZE[0])
        self._body.grid_columnconfigure(1, weight=COLUMN_WEIGHTS[1], minsize=COLUMN_MINSIZE[1])
        self._hide_container(self._single_scroll)
        self._show_container(
            self._left_scroll, row=0, column=0, padx=(0, COLUMN_GAP // 2), sticky="nsew"
        )
        self._show_container(
            self._right_column, row=0, column=1, padx=(COLUMN_GAP // 2, 0), sticky="nsew"
        )
        self._place_card(self._cards["input_output"], self._left_scroll, 0, expand=False)
        self._place_card(self._cards["optional"], self._left_scroll, 1, expand=False)
        self._place_card(self._cards["cli"], self._left_scroll, 2, expand=False)
        self._place_card(self._cards["environment"], self._right_column, 0, expand=False)
        self._place_card(self._cards["run"], self._right_column, 1, expand=False)
        self._place_card(self._cards["log"], self._right_column, 2, expand=True)

    @staticmethod
    def _grid_target(container: object) -> object:
        # CTkScrollableFrame embeds itself in a canvas and forwards grid() to its
        # private parent frame; grid_remove is not forwarded, so hide that frame.
        return getattr(container, "_parent_frame", container)

    @classmethod
    def _show_container(cls, container: object, **grid_kwargs: object) -> None:
        cls._grid_target(container).grid(**grid_kwargs)  # type: ignore[attr-defined]

    @classmethod
    def _hide_container(cls, container: object) -> None:
        cls._grid_target(container).grid_remove()  # type: ignore[attr-defined]

    @classmethod
    def _place_card(cls, card: object, container: object, row: int, *, expand: bool) -> None:
        card.grid(  # type: ignore[attr-defined]
            in_=cls._grid_target(container),
            row=row,
            column=0,
            sticky="nsew" if expand else "ew",
            pady=(0, 12),
        )

    def _build_header(self, main: object) -> None:
        # Spec section 7.2: header height 56, paper-0, 1px line-200 border plus
        # the 3px hemisphere rule as its bottom edge.
        header = ctk.CTkFrame(main, fg_color=PAPER_0, corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_rowconfigure(0, weight=1)
        header.grid_propagate(False)

        logo = ctk.CTkFrame(header, fg_color="transparent")
        logo.grid(row=0, column=0, padx=(16, 0), pady=4, sticky="w")
        logo.grid_columnconfigure(1, weight=1)

        self._header_image = self._load_header_image()
        if self._header_image is not None:
            ctk.CTkLabel(logo, text="", image=self._header_image).grid(
                row=0, column=0, rowspan=2, padx=(0, 8), sticky="w"
            )
        else:
            ctk.CTkLabel(
                logo,
                text="H",
                width=28,
                height=28,
                corner_radius=6,
                fg_color=TEAL_500,
                text_color=PAPER_0,
                font=self._font(20, "bold"),
            ).grid(row=0, column=0, rowspan=2, padx=(0, 8), sticky="w")

        ctk.CTkLabel(
            logo,
            text=APP_TITLE,
            anchor="w",
            height=24,
            font=self._font(20, "bold"),
            text_color=INK_900,
        ).grid(row=0, column=1, sticky="w")
        self._label(
            logo,
            "subtitle",
            anchor="w",
            height=16,
            text_color=INK_500,
            font=self._font(12),
        ).grid(row=1, column=1, sticky="w")

        # Spec section 7.2: the header's right side is the mode badge, then the
        # language segmented control, then the theme picker (the run status line
        # lives in the Run card).
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=2, padx=16, pady=4, sticky="e")

        self.mode_badge = ctk.CTkLabel(
            controls,
            textvariable=self.runtime_mode_var,
            width=100,
            height=22,
            corner_radius=11,
            fg_color=PAPER_200,
            text_color=INK_600,
            font=self._font(11, "bold"),
            border_width=1,
            border_color=HIGHLIGHT,
        )
        self.mode_badge.grid(row=0, column=0, padx=(0, 12), sticky="e")

        language = ctk.CTkFrame(
            controls,
            fg_color=PAPER_0,
            border_color=LINE_300,
            border_width=1,
            corner_radius=6,
        )
        language.grid(row=0, column=1, sticky="e")
        active = str(self.language_var.get())
        # Spec section 7.3: segments are "中文" | "EN", 44x26 each.
        for column, (code, text) in enumerate((("zh", "中文"), ("en", "EN"))):
            is_active = code == active
            button = ctk.CTkButton(
                language,
                text=text,
                width=44,
                height=26,
                corner_radius=6,
                border_width=0,
                fg_color=TEAL_50 if is_active else PAPER_0,
                hover_color=TEAL_50 if is_active else PAPER_100,
                text_color=TEAL_700 if is_active else INK_600,
                text_color_disabled=INK_500,
                font=self._font(12, "bold"),
                command=lambda value=code: self._set_language(value),
            )
            button.grid(row=0, column=column, padx=2, pady=2)
            # Spec section 7.5: both language segments are keyboard-reachable.
            bind_button_keyboard(button)
            self._language_buttons[code] = button

        self._build_theme_control(controls)

        ctk.CTkFrame(header, height=1, corner_radius=0, fg_color=LINE_200).grid(
            row=1, column=0, columnspan=3, sticky="ew"
        )
        self._hemisphere_rule(header).grid(row=2, column=0, columnspan=3, sticky="ew")

    def _theme_names(self) -> list[str]:
        """Theme display names for the current UI language, in registry order."""

        language = str(self.language_var.get())
        return [
            theme.name_zh if language == "zh" else theme.name_en
            for theme in THEMES.values()
        ]

    def _refresh_theme_control(self) -> None:
        option = getattr(self, "theme_option", None)
        if option is None:
            return
        try:
            values = self._theme_names()
            option.configure(values=values)
            # The display shows the localized name; theme_var itself keeps the
            # registry id and is deliberately not bound to the OptionMenu.
            option.set(self._theme_names_for(str(self.theme_var.get())))
            option.configure(
                state="disabled" if self.is_running else "normal",
                fg_color=PAPER_0,
                button_color=PAPER_100,
                button_hover_color=PAPER_200,
                text_color=INK_900,
                text_color_disabled=INK_500,
                dropdown_fg_color=PAPER_0,
                dropdown_hover_color=TEAL_50,
                dropdown_text_color=INK_900,
            )
        except (tk.TclError, AttributeError, ValueError):
            return

    def _build_theme_control(self, controls: object) -> None:
        # Placed right after the language segmented control. The OptionMenu shows
        # the four theme names in the current UI language and rebuilds the window
        # on selection; disabled while a run is in progress.
        theme_frame = ctk.CTkFrame(controls, fg_color="transparent")
        theme_frame.grid(row=0, column=2, padx=(12, 0), sticky="e")
        self.theme_label = self._label(
            theme_frame,
            "theme_label",
            text_color=INK_600,
            font=self._font(12),
        )
        self.theme_label.grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.theme_option = ctk.CTkOptionMenu(
            theme_frame,
            values=self._theme_names(),
            width=132,
            height=26,
            corner_radius=6,
            fg_color=PAPER_0,
            button_color=PAPER_100,
            button_hover_color=PAPER_200,
            text_color=INK_900,
            text_color_disabled=INK_500,
            dropdown_fg_color=PAPER_0,
            dropdown_hover_color=TEAL_50,
            dropdown_text_color=INK_900,
            dropdown_font=self._font(12),
            font=self._font(12),
            command=self._on_theme_selected,
        )
        self.theme_option.grid(row=0, column=1, sticky="e")
        self._language_refreshers.append(self._refresh_theme_control)
        self._make_theme_option_keyboard_reachable(self.theme_option)
        self._refresh_theme_control()

    def _theme_names_for(self, theme_id: str) -> str:
        theme = THEMES.get(theme_id, THEMES[DEFAULT_THEME])
        language = str(self.language_var.get())
        return theme.name_zh if language == "zh" else theme.name_en

    def _on_theme_selected(self, choice: str) -> None:
        for theme_id, theme in THEMES.items():
            if choice in (theme.name_en, theme.name_zh):
                if theme_id != str(self.theme_var.get()):
                    self.apply_theme(theme_id)
                return

    def _make_theme_option_keyboard_reachable(self, option: object) -> None:
        # Spec section 7.5: the OptionMenu's internal canvas must take focus and
        # Return/Space open the dropdown (Return is also re-bound below because
        # CTkOptionMenu ships without a keyboard binding).
        canvas = getattr(option, "_canvas", None)
        if canvas is None:
            return
        try:
            canvas.configure(takefocus=1)
            canvas.bind("<Return>", self._invoke_theme_dropdown)
            canvas.bind("<KP_Enter>", self._invoke_theme_dropdown)
            canvas.bind("<space>", self._invoke_theme_dropdown)
        except (tk.TclError, AttributeError):
            return
        setattr(option, "_hemispec_theme_dropdown", self._invoke_theme_dropdown)

    def _invoke_theme_dropdown(self, _event: object = None) -> str:
        option = getattr(self, "theme_option", None)
        if option is None:
            return "break"
        if str(option.cget("state")) == "disabled":
            return "break"
        try:
            option._open_dropdown_menu()
        except (tk.TclError, AttributeError):
            pass
        return "break"

    def _hemisphere_rule(self, parent: object) -> object:
        """Spec section 1.6: left teal-500, 2px paper-0 gap, right verm-500."""

        strip = ctk.CTkFrame(parent, height=3, corner_radius=0, fg_color=PAPER_0)
        strip.grid_propagate(False)
        strip.grid_columnconfigure(0, weight=1)
        strip.grid_columnconfigure(2, weight=1)
        strip.grid_rowconfigure(0, weight=1, minsize=3)
        left = ctk.CTkFrame(strip, height=3, corner_radius=0, fg_color=TEAL_500)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        gap = ctk.CTkFrame(strip, width=2, height=3, corner_radius=0, fg_color=PAPER_0)
        gap.grid(row=0, column=1, sticky="nsew")
        gap.grid_propagate(False)
        right = ctk.CTkFrame(strip, height=3, corner_radius=0, fg_color=VERM_500)
        right.grid(row=0, column=2, sticky="nsew")
        right.grid_propagate(False)
        return strip

    def _load_header_image(self) -> object | None:
        self._header_mark_path = None
        theme_var = getattr(self, "theme_var", None)
        theme_id = str(theme_var.get()) if theme_var is not None else DEFAULT_THEME
        path = gui_theme_mark_path(theme_id) or gui_icon_path("hemispec.png")
        if path is None or ctk is None:
            return None
        try:
            from PIL import Image

            with Image.open(path) as opened:
                image = opened.convert("RGBA").copy()
            header_image = ctk.CTkImage(light_image=image, dark_image=image, size=(28, 28))
            self._header_mark_path = path
            return header_image
        except Exception:
            return None

    # ------------------------------------------------------------------ cards
    def _card(
        self,
        parent: object,
        row: int,
        title_key: str,
        *,
        accent: str,
        bg: str | None = None,
        border: str | None = None,
        expand: bool = False,
        ghost_button: tuple[str, Callable[[], None]] | None = None,
    ) -> object:
        # Spec section 7.2: paper-0 container, 1px line-200 border, corner 10,
        # inner padding 16; the title row leads with a 3x16 accent bar.
        bg = PAPER_0 if bg is None else bg
        border = LINE_200 if border is None else border
        card = ctk.CTkFrame(parent, fg_color=bg, border_color=border, border_width=1, corner_radius=10)
        card.grid(row=row, column=0, sticky="nsew" if expand else "ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        title_row.grid_columnconfigure(1, weight=1)
        accent_bar = ctk.CTkFrame(title_row, width=3, height=16, fg_color=accent, corner_radius=0)
        accent_bar.grid(row=0, column=0, padx=(0, 8), sticky="nsw")
        accent_bar.grid_propagate(False)
        self._label(
            title_row,
            title_key,
            font=self._font(15, "bold"),
            text_color=INK_900,
        ).grid(row=0, column=1, sticky="w")

        if ghost_button is not None:
            button_key, button_command = ghost_button
            ghost = ctk.CTkButton(
                title_row,
                text=self._t(button_key),
                command=button_command,
                height=28,
                width=72,
                corner_radius=6,
                fg_color="transparent",
                hover_color=TEAL_50,
                text_color=TEAL_600,
                text_color_disabled=INK_500,
                font=self._font(12),
            )
            ghost.grid(row=0, column=2, sticky="e")
            self._register_label(ghost, button_key)
            bind_button_keyboard(ghost)
            if button_key == "button_copy":
                self.copy_button = ghost
            elif button_key == "button_refresh":
                self.refresh_button = ghost
        return card

    def _build_input_output_card(self, parent: object, row: int) -> object:
        # Spec section 7.2 card 1: input field + Browse, live match count (debounced
        # 300ms, 12px), output field + Browse/Open, then the corrected output hint.
        card = self._card(parent, row, "input_output_title", accent=TEAL_500)
        input_row = ctk.CTkFrame(card, fg_color="transparent")
        input_row.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)
        self.input_entry = ctk.CTkEntry(
            input_row,
            textvariable=self.vars["input_glob"],
            height=34,
            corner_radius=6,
            border_width=1,
            border_color=LINE_400,
            fg_color=PAPER_0,
            text_color=INK_900,
            placeholder_text_color=INK_500,
            placeholder_text=self._t("input_placeholder"),
            font=self._font(13),
        )
        self.input_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.input_entry.bind("<KeyRelease>", lambda _event: self._on_config_changed())
        self.input_entry.bind("<FocusIn>", lambda _event: self.input_entry.configure(border_color=TEAL_500))
        self.input_entry.bind("<FocusOut>", lambda _event: self.input_entry.configure(border_color=LINE_400))

        def refresh_placeholder() -> None:
            self.input_entry.configure(placeholder_text=self._t("input_placeholder"))

        self._language_refreshers.append(refresh_placeholder)
        self.input_browse_button = self._browse_button(input_row, self._browse_input_file)
        self.input_browse_button.grid(row=0, column=1, sticky="e")

        # Spec section 7.2: live match count directly below the input field.
        self.match_count_label = ctk.CTkLabel(
            card,
            text="",
            anchor="w",
            justify="left",
            text_color=INK_500,
            font=self._font(12),
        )
        self.match_count_label.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="w")
        self._schedule_match_count()

        # The preprocessing hint is not named in spec section 7.2 but was existing
        # copy; it stays as a 12px ink-500 hint directly under the match count.
        self._label(
            card,
            "note_preprocess",
            wraplength=540,
            justify="left",
            text_color=INK_500,
            font=self._font(12),
        ).grid(row=3, column=0, padx=16, pady=(0, 8), sticky="w")

        output_row = ctk.CTkFrame(card, fg_color="transparent")
        output_row.grid(row=4, column=0, padx=16, pady=(0, 8), sticky="ew")
        output_row.grid_columnconfigure(0, weight=1)
        self.output_entry = ctk.CTkEntry(
            output_row,
            textvariable=self.vars["out_dir"],
            height=34,
            corner_radius=6,
            border_width=1,
            border_color=LINE_400,
            fg_color=PAPER_0,
            text_color=INK_900,
            placeholder_text_color=INK_500,
            font=self._font(13),
        )
        self.output_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.output_entry.bind("<KeyRelease>", lambda _event: self._on_config_changed())
        self.output_entry.bind("<FocusIn>", lambda _event: self.output_entry.configure(border_color=TEAL_500))
        self.output_entry.bind("<FocusOut>", lambda _event: self.output_entry.configure(border_color=LINE_400))
        output_actions = ctk.CTkFrame(output_row, fg_color="transparent")
        output_actions.grid(row=0, column=1, sticky="e")
        self.output_browse_button = self._browse_button(output_actions, self._browse_output_dir)
        self.output_browse_button.grid(row=0, column=0, padx=(0, 6))
        self.open_button = ctk.CTkButton(
            output_actions,
            text=self._t("button_open_folder"),
            command=self._open_output,
            height=32,
            width=110,
            corner_radius=6,
            fg_color=PAPER_0,
            hover_color=PAPER_100,
            border_width=1,
            border_color=LINE_300,
            text_color=INK_900,
            text_color_disabled=INK_500,
            font=self._font(13),
        )
        self.open_button.grid(row=0, column=1)
        self._register_label(self.open_button, "button_open_folder")
        bind_button_keyboard(self.open_button)

        self._label(
            card,
            "output_hint",
            wraplength=540,
            justify="left",
            text_color=INK_500,
            font=self._font(12),
        ).grid(row=5, column=0, padx=16, pady=(0, 16), sticky="w")
        return card

    def _build_optional_card(self, parent: object, row: int) -> object:
        # Spec section 7.2 card 2: four toggle rows. ROI on reveals the Atlas and
        # label-table pickers behind a 1px line-200 left rule, indented 16px.
        card = self._card(parent, row, "optional_title", accent=TEAL_500)
        next_row = 1
        self._toggle_row(card, next_row, "switch_roi", "export_roi_table", self._sync_roi_state, description_key="note_roi")
        next_row += 1
        self.roi_reveal = ctk.CTkFrame(card, fg_color="transparent")
        self.roi_reveal.grid(row=next_row, column=0, padx=(32, 16), pady=(0, 8), sticky="ew")
        self.roi_reveal.grid_columnconfigure(1, weight=1)
        rule = ctk.CTkFrame(self.roi_reveal, width=1, height=1, fg_color=LINE_200)
        rule.grid(row=0, column=0, rowspan=2, padx=(0, 15), sticky="ns")
        rule.grid_propagate(False)
        roi_fields = ctk.CTkFrame(self.roi_reveal, fg_color="transparent")
        roi_fields.grid(row=0, column=1, rowspan=2, sticky="ew")
        roi_fields.grid_columnconfigure(1, weight=1)
        self.roi_widgets: list[object] = []
        for field_row, (label_key, var_key, browse) in enumerate(
            (
                ("field_atlas", "roi_atlas", self._browse_atlas_file),
                ("field_labels", "roi_label_table", self._browse_label_file),
            )
        ):
            self.roi_widgets.extend(self._entry_row(roi_fields, field_row, label_key, var_key, browse))
        next_row += 1

        self._toggle_row(
            card, next_row, "switch_classifier", "run_classifier", self._sync_classifier_state,
            description_key="note_validation",
        )
        next_row += 1
        self.classifier_note = self._label(
            card,
            "classifier_needs_roi",
            anchor="w",
            text_color=VERM_700,
            font=self._font(12),
        )
        self.classifier_note.grid(row=next_row, column=0, padx=32, pady=(0, 8), sticky="w")
        next_row += 1
        self._toggle_row(card, next_row, "switch_trt", "run_trt", self._on_config_changed, description_key="note_trt")
        next_row += 1
        self._toggle_row(
            card, next_row, "switch_keep", "keep_intermediate", self._on_config_changed,
            description_key="note_keep",
        )
        self._sync_classifier_note()
        self.vars["run_classifier"].trace_add(  # type: ignore[union-attr]
            "write", lambda *_args: self._sync_classifier_note()
        )
        return card

    def _sync_classifier_note(self) -> None:
        if not hasattr(self, "classifier_note"):
            return
        if bool(self.vars["run_classifier"].get()):  # type: ignore[union-attr]
            self.classifier_note.grid()
        else:
            self.classifier_note.grid_remove()

    def _build_cli_card(self, parent: object, row: int) -> object:
        # Spec section 7.2 card 3: sunken read-only box with a ghost Copy button.
        card = self._card(
            parent,
            row,
            "cli_title",
            accent=TEAL_500,
            ghost_button=("button_copy", self._copy_cli),
        )
        self.cli_box = ctk.CTkTextbox(
            card,
            height=92,
            wrap="word",
            corner_radius=6,
            border_width=1,
            border_color=LINE_200,
            fg_color=PAPER_100,
            text_color=INK_700,
            scrollbar_button_color=LINE_300,
            scrollbar_button_hover_color=LINE_400,
            font=self._font(12, mono=True),
        )
        self.cli_box.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        self._refresh_cli_box()
        return card

    def _build_environment_card(self, parent: object, row: int) -> object:
        # Spec section 7.2 card 4: ghost Refresh plus four dot+word status rows.
        card = self._card(
            parent,
            row,
            "status_title",
            accent=VERM_500,
            ghost_button=("button_refresh", self._refresh_runtime_status),
        )
        self.asset_status_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.asset_status_frame.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.asset_status_frame.grid_columnconfigure(0, weight=1)
        self._refresh_runtime_status()
        return card

    def _build_run_card(self, parent: object, row: int) -> object:
        # Spec section 7.2 card 5: Run/Stop in a 2:1 row, stepper (margin-top 16),
        # progress bar, then the status line.
        card = self._card(parent, row, "run_title", accent=VERM_500)

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=1, column=0, padx=16, pady=(0, 0), sticky="ew")
        actions.grid_columnconfigure(0, weight=2, uniform="run")
        actions.grid_columnconfigure(1, weight=1, uniform="run")
        self.run_button = ctk.CTkButton(
            actions,
            text=self._t("button_run"),
            command=self._run_clicked,
            height=40,
            corner_radius=6,
            fg_color=TEAL_600,
            hover_color=TEAL_700,
            text_color=PAPER_0,
            text_color_disabled=INK_500,
            font=self._font(14, "bold"),
        )
        self.run_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        bind_button_keyboard(self.run_button)
        self.stop_button = ctk.CTkButton(
            actions,
            text=self._t("button_stop"),
            command=self._stop_clicked,
            height=40,
            corner_radius=6,
            state="disabled",
            fg_color=PAPER_0,
            hover_color=VERM_50,
            border_width=1,
            border_color=VERM_200,
            text_color=DANGER_TEXT,
            text_color_disabled=INK_500,
            font=self._font(14, "bold"),
        )
        self.stop_button.grid(row=0, column=1, sticky="ew")
        bind_button_keyboard(self.stop_button)
        self._register_label(self.run_button, "button_run")
        self._register_label(self.stop_button, "button_stop")
        self._language_refreshers.append(self._refresh_action_buttons)

        self.stepper = Stepper(card, self._font)
        self.stepper.grid(row=2, column=0, padx=16, pady=(16, 8), sticky="ew")
        self.stepper.set_language(str(self.language_var.get()))
        self.stepper.reset(bool(self.vars["export_roi_table"].get()))

        self.progress_bar = ctk.CTkProgressBar(
            card,
            height=8,
            corner_radius=4,
            progress_color=TEAL_500,
            fg_color=PAPER_200,
        )
        self.progress_bar.grid(row=3, column=0, padx=16, pady=(0, 8), sticky="ew")
        self.progress_bar.set(0)

        # Spec section 7.2: the status line follows the progress bar. Left shows
        # the stage plus counts ("R→L 12/24", mono 12, ink-700); right shows the
        # percentage and elapsed clock ("50% · 03:12", 12, ink-500).
        status_line = ctk.CTkFrame(card, fg_color="transparent")
        status_line.grid(row=4, column=0, padx=16, pady=(0, 16), sticky="ew")
        status_line.grid_columnconfigure(0, weight=1)
        self.run_stage_label = ctk.CTkLabel(
            status_line,
            text="",
            anchor="w",
            text_color=INK_700,
            font=self._font(12, mono=True),
        )
        self.run_stage_label.grid(row=0, column=0, sticky="w")
        self.run_elapsed_label = ctk.CTkLabel(
            status_line,
            text="",
            anchor="e",
            text_color=INK_500,
            font=self._font(12),
        )
        self.run_elapsed_label.grid(row=0, column=1, sticky="e")
        self._refresh_status_line()
        return card

    def _build_log_card(self, parent: object, row: int) -> object:
        # Spec section 7.2 card 6: toolbar with "Copy log" / "Open output" ghost
        # buttons, then the expanding log text box (min height 160).
        card = self._card(parent, row, "log_title", accent=VERM_500, expand=True)

        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="e")
        self.log_copy_button = self._ghost_button(toolbar, "button_copy_log", self._copy_log)
        self.log_copy_button.grid(row=0, column=0, padx=(0, 4))
        self.log_open_button = self._ghost_button(toolbar, "button_open", self._open_output)
        self.log_open_button.grid(row=0, column=1, padx=(0, 4))
        # Clear Log is not named in the spec; it is retained as existing behavior.
        self.clear_button = self._ghost_button(toolbar, "button_clear", self._clear_log)
        self.clear_button.grid(row=0, column=2)

        self.log_box = ctk.CTkTextbox(
            card,
            height=160,  # spec section 7.2: the Log card expands from min height 160
            wrap="word",
            corner_radius=6,
            border_width=1,
            border_color=LINE_200,
            fg_color=LOG_BG,
            text_color=INK_700,
            scrollbar_button_color=LINE_300,
            scrollbar_button_hover_color=LINE_400,
            font=self._font(12, mono=True),
        )
        self.log_box.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="nsew")
        card.grid_rowconfigure(2, weight=1)
        self._configure_log_tags()
        self._log("Ready. Configure inputs and click Run HemiSpec.\n")
        return card

    def _ghost_button(self, parent: object, key: str, command: Callable[[], None], width: int = 96) -> object:
        button = ctk.CTkButton(
            parent,
            text=self._t(key),
            command=command,
            height=28,
            width=width,
            corner_radius=6,
            fg_color="transparent",
            hover_color=TEAL_50,
            text_color=TEAL_600,
            text_color_disabled=INK_500,
            font=self._font(12),
        )
        self._register_label(button, key)
        # Spec section 7.5: every action is keyboard-reachable.
        bind_button_keyboard(button)
        return button

    def _browse_button(self, parent: object, command: Callable[[], None]) -> object:
        button = ctk.CTkButton(
            parent,
            text=self._t("button_browse"),
            width=88,
            height=32,
            corner_radius=6,
            command=command,
            fg_color=PAPER_0,
            hover_color=PAPER_100,
            border_width=1,
            border_color=LINE_300,
            text_color=INK_900,
            text_color_disabled=INK_500,
            font=self._font(13),
        )
        self._register_label(button, "button_browse")
        bind_button_keyboard(button)
        return button

    def _entry_row(self, parent: object, row: int, label_key: str, var_key: str, browse: Callable[[], None]) -> list[object]:
        label_widget = self._label(parent, label_key, text_color=INK_900, font=self._font(13))
        label_widget.grid(row=row, column=0, padx=(0, 8), pady=(0, 8), sticky="w")
        entry = ctk.CTkEntry(
            parent,
            textvariable=self.vars[var_key],
            height=34,
            corner_radius=6,
            border_width=1,
            border_color=LINE_400,
            fg_color=PAPER_0,
            text_color=INK_900,
            placeholder_text_color=INK_500,
            font=self._font(13),
        )
        entry.grid(row=row, column=1, padx=(0, 8), pady=(0, 8), sticky="ew")
        parent.grid_columnconfigure(1, weight=1)  # type: ignore[attr-defined]
        entry.bind("<KeyRelease>", lambda _event: self._on_config_changed())
        entry.bind("<FocusIn>", lambda _event: entry.configure(border_color=TEAL_500))
        entry.bind("<FocusOut>", lambda _event: entry.configure(border_color=LINE_400))
        button = self._browse_button(parent, browse)
        button.grid(row=row, column=2, pady=(0, 8), sticky="e")
        return [label_widget, entry, button]

    def _toggle_row(
        self,
        parent: object,
        row: int,
        label_key: str,
        var_key: str,
        command: Callable[[], None],
        *,
        description_key: str | None = None,
    ) -> list[object]:
        # Spec section 7.2/7.3: label 13 ink-900 with a 12 ink-500 description
        # below and a right-aligned Canvas capsule. The label is clickable.
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=0, padx=16, pady=(0, 12), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w")
        label = self._label(
            text_frame,
            label_key,
            anchor="w",
            justify="left",
            wraplength=330,
            text_color=INK_900,
            font=self._font(13),
        )
        label.grid(row=0, column=0, sticky="w")
        if description_key is not None:
            self._label(
                text_frame,
                description_key,
                anchor="w",
                justify="left",
                wraplength=330,
                text_color=INK_500,
                font=self._font(12),
            ).grid(row=1, column=0, pady=(2, 0), sticky="w")

        variable = self.vars[var_key]
        toggle = ToggleCapsule(frame, variable, command=command)
        toggle.grid(row=0, column=1, padx=(12, 0), sticky="ne")

        def click_label(_event: object = None) -> None:
            toggle.toggle()

        label.bind("<Button-1>", click_label)
        label.configure(cursor="hand2")

        self._language_refreshers.append(toggle._redraw)
        self.vars[var_key].trace_add(  # type: ignore[union-attr]
            "write", lambda *_args: toggle._redraw()
        )
        return [label, toggle]

    # --------------------------------------------------------------- browsing
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

    # ------------------------------------------------------------- validation
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
        # Spec section 7.2: the pickers are revealed only while ROI export is on.
        if hasattr(self, "roi_reveal"):
            if bool(self.vars["export_roi_table"].get()):  # type: ignore[union-attr]
                self.roi_reveal.grid()
            else:
                self.roi_reveal.grid_remove()
        self._on_config_changed()

    def _state_snapshot(self) -> dict[str, object]:
        snapshot: dict[str, object] = {}
        for key in WORKFLOW_VISIBLE_FIELDS:
            value = self.vars[key]
            snapshot[key] = value.get() if hasattr(value, "get") else value
        snapshot.update(ENCAPSULATED_DEFAULTS)
        return snapshot

    def _validate_state(self) -> tuple[dict[str, object], PreflightResult]:
        state = self._state_snapshot()
        make_workflow_config(state)
        preflight = preflight_workflow_state(state)
        self._log(f"[preflight] matched {len(preflight.matches)} input file(s)\n")
        if bool(state["export_roi_table"]):
            atlas = str(state.get("roi_atlas", ""))
            label_table = str(state.get("roi_label_table", ""))
            if atlas and not _path_exists_or_empty(atlas):
                self._log(f"[warning] ROI atlas not found; workflow will continue without ROI tables unless classifier validation requires ROI features: {atlas}\n")
            if label_table and not _path_exists_or_empty(label_table):
                self._log(f"[warning] ROI label table not found; labels will be skipped if ROI export runs: {label_table}\n")
        return state, preflight

    def _on_config_changed(self) -> None:
        self._refresh_cli_box()
        self._schedule_runtime_status_refresh()
        self._schedule_match_count()

    # ------------------------------------------------------ live match count
    def _schedule_match_count(self, delay_ms: int = MATCH_DEBOUNCE_MS) -> None:
        """Debounce the live glob match count so typing never scans every key."""

        if not hasattr(self, "match_count_label"):
            return
        if self._match_after_id is not None:
            try:
                self.after_cancel(self._match_after_id)
            except tk.TclError:
                pass
        self._match_after_id = self.after(delay_ms, self._refresh_match_count)

    def _refresh_match_count(self) -> None:
        self._match_after_id = None
        if not hasattr(self, "match_count_label"):
            return
        try:
            input_glob = str(self.vars["input_glob"].get())  # type: ignore[union-attr]
        except (AttributeError, tk.TclError):
            return
        count = safe_match_count(input_glob)
        text, color = match_count_display(count, str(self.language_var.get()))
        try:
            self.match_count_label.configure(text=text, text_color=color)
        except (tk.TclError, AttributeError, ValueError):
            pass

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
        mode_label = runtime_mode_label(statuses)
        mode = runtime_mode_display(mode_label, str(self.language_var.get()))
        self.runtime_mode_var.set(mode)
        if hasattr(self, "mode_badge"):
            model_enabled = mode_label == "Model-enabled"
            self.mode_badge.configure(
                fg_color=TEAL_50 if model_enabled else PAPER_200,
                text_color=TEAL_700 if model_enabled else INK_600,
                border_color=HIGHLIGHT,
            )

        # Spec section 7.3 status chips: 8px dot + word, then the asset name and
        # an ellipsized English-internally detail line (translated for display).
        chip_styles = {
            "ready": (SUCCESS_ACCENT, SUCCESS_FG, "chip_ready"),
            "partial": (WARNING_ACCENT, WARNING_FG, "chip_partial"),
            "missing": (VERM_600, VERM_700, "chip_missing"),
            "optional": (LINE_400, INK_500, "chip_optional"),
        }
        classifier_required = bool(self.vars.get("run_classifier").get())  # type: ignore[union-attr]
        for row, item in enumerate(statuses):
            state = runtime_status_state(item, classifier_required=classifier_required)
            dot_color, text_color, chip_key = chip_styles[state]
            row_frame = ctk.CTkFrame(self.asset_status_frame, fg_color="transparent")
            row_frame.grid(row=row, column=0, sticky="ew", pady=3)
            row_frame.grid_columnconfigure(1, weight=1)

            chip = ctk.CTkFrame(row_frame, fg_color="transparent")
            chip.grid(row=0, column=0, padx=(0, 10), sticky="w")
            dot = tk.Canvas(chip, width=8, height=8, highlightthickness=0, bd=0, bg=PAPER_0)
            dot.create_oval(0, 0, 8, 8, fill=dot_color, outline="")
            dot.pack(side="left", padx=(0, 6))
            # Plain label: _refresh_runtime_status rebuilds these rows on every
            # language switch and status refresh, so they must not accumulate in
            # the _i18n_labels registry.
            ctk.CTkLabel(
                chip,
                text=self._t(chip_key),
                text_color=text_color,
                font=self._font(12, "bold"),
            ).pack(side="left")

            detail_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            detail_frame.grid(row=0, column=1, sticky="ew")
            detail_frame.grid_columnconfigure(0, weight=1)
            label_key = f"asset_{item.key}"
            label_text = self._t(label_key) if label_key in TRANSLATIONS else item.label
            item_message, _item_guidance = runtime_status_display(item, str(self.language_var.get()))
            ctk.CTkLabel(
                detail_frame,
                text=label_text,
                text_color=INK_900,
                anchor="w",
                justify="left",
                font=self._font(13, "bold"),
            ).grid(row=0, column=0, sticky="ew")
            ctk.CTkLabel(
                detail_frame,
                text=ellipsize(item_message, 64),
                text_color=INK_500,
                anchor="w",
                justify="left",
                font=self._font(12),
            ).grid(row=1, column=0, sticky="ew")

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
            messagebox.showerror(self._t("dialog_cli_title"), str(exc))
            return
        self.clipboard_clear()
        self.clipboard_append(cli)
        self._set_status("status_copied")
        self._show_copy_feedback(self.copy_button)

    def _copy_log(self) -> None:
        # Spec section 7.2/7.3: Copy log is a ghost button with the same
        # "Copied ✓" feedback as the CLI Copy button.
        if not hasattr(self, "log_box"):
            return
        text = self.log_box.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status("status_log_copied")
        self._show_copy_feedback(self.log_copy_button)

    def _show_copy_feedback(self, button: object | None, duration_ms: int = COPY_FEEDBACK_MS) -> None:
        """Show "Copied ✓" on a Copy button, then revert after 1.5s."""

        if button is None:
            return
        self._revert_copy_feedback()
        try:
            button.configure(text=self._t("button_copied"))  # type: ignore[attr-defined]
        except (tk.TclError, AttributeError, ValueError):
            return
        self._copy_feedback_button = button
        self._copy_after_id = self.after(duration_ms, self._revert_copy_feedback)

    def _revert_copy_feedback(self) -> None:
        if self._copy_after_id is not None:
            try:
                self.after_cancel(self._copy_after_id)
            except tk.TclError:
                pass
            self._copy_after_id = None
        button = self._copy_feedback_button
        self._copy_feedback_button = None
        if button is None:
            return
        try:
            button.configure(text=self._t("button_copy"))  # type: ignore[attr-defined]
        except (tk.TclError, AttributeError, ValueError):
            pass

    def _open_output(self) -> None:
        # Spec section 7.2: Open output opens the folder in the OS file manager;
        # it is a no-op when the folder does not exist yet.
        try:
            out = Path(str(self.vars["out_dir"].get()))  # type: ignore[union-attr]
        except (AttributeError, tk.TclError, ValueError):
            return
        if not out.is_dir():
            return
        try:
            _open_path(out)
        except Exception as exc:
            messagebox.showerror(self._t("dialog_open_title"), str(exc))

    def _set_open_output_primary(self, primary: bool) -> None:
        # Spec section 7.3: after a successful run, "Open output" becomes a small
        # primary button; it returns to the ghost style when a new run starts.
        button = getattr(self, "log_open_button", None)
        if button is None:
            return
        try:
            if primary:
                button.configure(  # type: ignore[attr-defined]
                    fg_color=TEAL_600,
                    hover_color=TEAL_700,
                    text_color=PAPER_0,
                )
            else:
                button.configure(  # type: ignore[attr-defined]
                    fg_color="transparent",
                    hover_color=TEAL_50,
                    text_color=TEAL_600,
                )
        except (tk.TclError, AttributeError, ValueError):
            pass

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # -------------------------------------------------------------------- run
    def _run_clicked(self) -> None:
        if self.is_running:
            return
        try:
            state, preflight = self._validate_state()
            config = make_workflow_config(state)
        except NoInputFilesError as exc:
            # Spec section 7.3: "No inputs" is a blocking error dialog.
            messagebox.showerror(
                self._t("dialog_no_inputs_title"),
                self._t("dialog_no_inputs_body").format(glob=exc.input_glob),
            )
            return
        except Exception as exc:
            messagebox.showerror(self._t("dialog_invalid_title"), str(exc))
            return

        if preflight.requires_confirmation:
            # Spec section 7.3: non-empty output warns and lets the user continue.
            if not messagebox.askokcancel(
                self._t("dialog_nonempty_output_title"),
                self._t("dialog_nonempty_output_body"),
                parent=self,
            ):
                self._log(
                    "[preflight] Output folder is not empty; run cancelled by user.\n"
                )
                return

        self.cancel_event.clear()
        config = replace(config, should_cancel=self.cancel_event.is_set)
        self.is_running = True
        self.last_out_dir = config.out_dir
        self._close_when_done = False
        self._refresh_action_buttons()
        self._set_status("status_running")
        self._set_stage("stage_queued")
        self._reset_run_status()
        self._set_open_output_primary(False)
        if hasattr(self, "stepper"):
            self.stepper.reset(bool(self.vars["export_roi_table"].get()))  # type: ignore[union-attr]
        self.progress_bar.configure(progress_color=TEAL_500)
        self.progress_bar.set(0)
        # Spec section 7.3: startup is indeterminate until the first real count.
        self._set_progress_indeterminate()
        self._log("\n[run] Starting HemiSpec standard workflow\n")
        self._log(f"[run] output: {config.out_dir}\n")
        self._log(f"[run] CLI: {workflow_cli_command(state)}\n")

        thread = threading.Thread(target=self._run_worker, args=(config,), daemon=True)
        thread.start()

    def _refresh_action_buttons(self) -> None:
        if not hasattr(self, "run_button"):
            return
        stopping = self.cancel_event.is_set() and self.is_running
        self.run_button.configure(
            text=self._t("button_running" if self.is_running else "button_run"),
            state="disabled" if self.is_running else "normal",
            fg_color=LINE_200 if self.is_running else TEAL_600,
            hover_color=TEAL_700,
            text_color=INK_500 if self.is_running else PAPER_0,
            text_color_disabled=INK_500,
        )
        self.stop_button.configure(
            text=self._t("button_stop_requested" if stopping else "button_stop"),
            state="normal" if self.is_running and not stopping else "disabled",
        )
        self._refresh_theme_control()

    def _request_stop(self) -> None:
        if not self.is_running:
            return
        self.cancel_event.set()
        self._refresh_action_buttons()
        self._set_status("status_stopping")
        self._log(
            "[cancel] Cooperative stop requested. HemiSpec will stop after the current "
            "inference file and skip later stages; cleanup may still finish.\n"
        )

    def _stop_clicked(self) -> None:
        self._request_stop()

    def _run_worker(self, config: BilateralWorkflowConfig) -> None:
        def emit(text: str) -> None:
            self._events.put(("log", text))

        try:
            with contextlib.redirect_stdout(_StdoutProxy(emit)), contextlib.redirect_stderr(
                _StdoutProxy(emit)
            ):
                result = run_bilateral_workflow(config)
            self._events.put(("finished", (result, None)))
        except Exception as exc:  # pragma: no cover - GUI worker path
            detail = traceback.format_exc()
            self._events.put(("finished", (None, (exc, detail))))

    def _poll_events(self) -> None:
        self._poll_after_id = None
        try:
            for _ in range(400):
                kind, payload = self._events.get_nowait()
                if kind == "log":
                    self._handle_output_text(str(payload))
                elif kind == "finished":
                    result, error = payload  # type: ignore[misc]
                    self._run_finished(result, error)
                    if self._closing:
                        return
        except queue.Empty:
            pass
        if not self._closing:
            try:
                self._poll_after_id = self.after(80, self._poll_events)
            except tk.TclError:
                self._closing = True

    def _handle_output_text(self, text: str) -> None:
        self._log(text)
        for line in text.splitlines():
            update = parse_progress_line(line)
            if update is not None:
                self._apply_progress(update)
            elif classify_log_line(line) == LOG_TAG_MODELS:
                # Spec section 7.3: model download has no reliable counter, so
                # the bar animates until the next determinate update arrives.
                self._set_progress_indeterminate()

    def _set_progress_indeterminate(self) -> None:
        """Spec section 7.3: indeterminate during model download or startup."""

        try:
            self.progress_bar.configure(mode="indeterminate", progress_color=TEAL_500)
            self.progress_bar.start()
            self._progress_indeterminate = True
        except (tk.TclError, AttributeError):
            pass

    def _set_progress_determinate(self) -> None:
        """Stop the animation and return the bar to a real fraction."""

        if not getattr(self, "_progress_indeterminate", False):
            return
        try:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
        except (tk.TclError, AttributeError):
            pass
        self._progress_indeterminate = False

    def _apply_progress(self, update: ProgressUpdate) -> None:
        if update.stage:
            key = _STAGE_KEYS.get(update.stage)
            if key is not None:
                self._set_stage(key, update.detail)
            self._apply_stepper_stage(update.stage, update)
            self._run_stage = update.stage
        if update.current is not None and update.total:
            self._run_current = update.current
            self._run_total = update.total
        elif update.stage and update.stage in ("merge", "roi", "summary", "classifier", "trt"):
            # Stage-only lines have no counter; clear the stale per-file counter.
            self._run_current = None
            self._run_total = None
        if update.fraction is not None:
            # The first real counter update ends the startup animation.
            self._set_progress_determinate()
            self.progress_bar.set(update.fraction)
            self._run_fraction = update.fraction
        self._refresh_status_line()

    # ---------------------------------------------------------- run clock
    def _reset_run_status(self) -> None:
        self._run_started_at = time.monotonic()
        self._run_stage = "queued"
        self._run_current = None
        self._run_total = None
        self._run_fraction = 0.0
        self._set_status_line_override(None)
        self._refresh_status_line()
        self._schedule_elapsed_tick()

    def _schedule_elapsed_tick(self) -> None:
        if self._elapsed_after_id is not None:
            try:
                self.after_cancel(self._elapsed_after_id)
            except tk.TclError:
                pass
        self._elapsed_after_id = self.after(ELAPSED_TICK_MS, self._elapsed_tick)

    def _elapsed_tick(self) -> None:
        self._elapsed_after_id = None
        if not self.is_running:
            return
        self._refresh_status_line()
        self._schedule_elapsed_tick()

    def _stop_elapsed_tick(self) -> None:
        if self._elapsed_after_id is not None:
            try:
                self.after_cancel(self._elapsed_after_id)
            except tk.TclError:
                pass
            self._elapsed_after_id = None

    def _elapsed_seconds(self) -> float:
        if self._run_started_at is None:
            return 0.0
        return max(0.0, time.monotonic() - self._run_started_at)

    def _set_status_line_override(self, key: str | None, color: str | None = None) -> None:
        """Replace the left status-line text with a terminal-state message."""

        self._status_line_key = key
        self._status_line_color = INK_700 if color is None else color
        self._refresh_status_line()

    def _refresh_status_line(self) -> None:
        if not hasattr(self, "run_stage_label"):
            return
        language = str(self.language_var.get())
        color = INK_700
        elapsed = self._elapsed_seconds()
        if self._status_line_key is not None:
            # Terminal state: the message replaces the clock so a stopped or
            # failed run does not read as "0% · 00:45".
            left = self._t(self._status_line_key)
            color = self._status_line_color
            right = ""
        else:
            left, right = status_line_text(
                self._run_stage,
                self._run_current,
                self._run_total,
                self._run_fraction,
                elapsed,
                language,
            )
            if self._run_started_at is None:
                right = ""
        try:
            self.run_stage_label.configure(text=left, text_color=color)
            self.run_elapsed_label.configure(text=right)
        except (tk.TclError, AttributeError, ValueError):
            pass

    def _apply_stepper_stage(self, stage: str, update: ProgressUpdate | None = None) -> None:
        # Spec section 7.3: stage detection uses the existing English log lines;
        # classifier/TRT validation runs after Summary and gets no extra node.
        if not hasattr(self, "stepper"):
            return
        node = STEPPER_STAGE_TO_NODE.get(stage)
        if node is None:
            return
        if stage in ("classifier", "trt"):
            roi_enabled = bool(self.vars["export_roi_table"].get())  # type: ignore[union-attr]
            self.stepper.set_states(
                {
                    name: "skipped" if name == "roi" and not roi_enabled else "done"
                    for name in STEPPER_NODES
                },
                {},
            )
            return
        roi_enabled = bool(self.vars["export_roi_table"].get())  # type: ignore[union-attr]
        if node == "roi" and not roi_enabled:
            # Spec 7.3 / phase-2 scope: ROI is skipped whenever the table is off.
            return
        index = STEPPER_NODES.index(node)
        states: dict[str, str] = {}
        for position, name in enumerate(STEPPER_NODES):
            if name == "roi" and not roi_enabled:
                states[name] = "skipped"
            elif position < index:
                states[name] = "done"
            elif position == index:
                states[name] = "active"
            else:
                states[name] = "pending"
        sublabels: dict[str, str] = {}
        if update is not None and update.current is not None and update.total:
            sublabels[node] = f"{update.current}/{update.total}"
        self.stepper.set_states(states, sublabels)

    def _stepper_finished(self, state: str) -> None:
        if not hasattr(self, "stepper"):
            return
        if state == "done":
            # Spec section 7.3: the ROI node stays "skipped" when the table is off.
            self.stepper.set_states(
                {
                    name: "skipped" if self.stepper.node_state(name) == "skipped" else "done"
                    for name in STEPPER_NODES
                },
                {},
            )
        elif state == "error":
            # Spec section 7.3: the failed stage shows "!" in vermilion; earlier
            # nodes stay done and later nodes stay pending.
            current = next(
                (name for name in STEPPER_NODES if self.stepper.node_state(name) == "active"),
                None,
            )
            if current is None:
                current = next(
                    (
                        name
                        for name in STEPPER_NODES
                        if self.stepper.node_state(name) in ("pending", "skipped")
                    ),
                    STEPPER_NODES[0],
                )
            index = STEPPER_NODES.index(current)
            states = {
                name: ("done" if position < index else "error" if position == index else "pending")
                for position, name in enumerate(STEPPER_NODES)
            }
            self.stepper.set_states(states, {})

    def _finish_progress(self, fraction: float, key: str) -> None:
        # Spec section 7.3: stop the animation and show the terminal state.
        self._set_progress_determinate()
        try:
            self.progress_bar.set(fraction)
        except (tk.TclError, AttributeError):
            pass
        self._run_fraction = fraction
        self._set_stage(key)

    def _run_finished(self, result: BilateralWorkflowResult | None, error: tuple[BaseException, str] | None) -> None:
        self.is_running = False
        self.cancel_event.clear()
        self._stop_elapsed_tick()
        self._refresh_action_buttons()
        self._refresh_theme_control()
        if error is not None:
            exc, detail = error
            if isinstance(exc, CancelledError):
                self._set_status("status_stopped")
                self._set_status_line_override("status_stopped", INK_700)
                self._finish_progress(0.0, "stage_idle")
                self._log("[stopped] HemiSpec workflow stopped by user.\n")
                self._close_if_requested()
                return
            # Spec section 7.3: no modal on failure. The status line reports it,
            # the stepper shows the error node, and details go to the log.
            self._set_status("status_failed")
            self._set_status_line_override("status_run_failed", VERM_700)
            self._finish_progress(0.0, "stage_idle")
            self._stepper_finished("error")
            try:
                self.progress_bar.configure(progress_color=VERM_600)
            except (tk.TclError, AttributeError):
                pass
            self._log(f"[error] {exc}\n{detail}\n")
            self._close_if_requested()
            return
        assert result is not None
        self._set_status("status_done")
        self._set_summary("summary_done", path=result.hemi_maps_dir)
        self._finish_progress(1.0, "stage_idle")
        self._stepper_finished("done")
        self._run_fraction = 1.0
        self._set_status_line_override("status_done", SUCCESS_FG)
        self._set_open_output_primary(True)
        self._log("[done] HemiSpec workflow complete\n")
        self._log(f"out_dir: {result.out_dir}\n")
        self._log(f"voxel_maps: {result.hemi_maps_dir}\n")
        intermediate_dir = result.out_dir / "intermediate"
        if intermediate_dir.exists() and any(intermediate_dir.iterdir()):
            self._log(f"intermediate_outputs: retained under {intermediate_dir}\n")
        else:
            self._log(
                "intermediate_outputs: removed after a successful run. Enable "
                "'Keep intermediate reconstructions, direction metrics, and combined maps' "
                "to retain intermediate/recon, direction_metrics, and combined_maps.\n"
            )
        self._log(f"subject_summary_csv: {result.subject_summary_csv}\n")
        self._log(f"roi_csv: {result.roi_csv if result.roi_csv else 'skipped'}\n")
        self._log(f"roi_wide_csv: {result.roi_wide_csv if result.roi_wide_csv else 'skipped'}\n")
        if result.classifier is not None:
            self._log(f"classifier_summary: {result.classifier.summary_csv}\n")
        if result.trt is not None:
            self._log(f"trt_summary: {result.trt.summary_csv}\n")
        self._close_if_requested()

    def _close_if_requested(self) -> None:
        if not self._close_when_done:
            return
        self._closing = True
        self._log("[close] Run finished; closing HemiSpec.\n")
        try:
            self.after(150, self.destroy)
        except tk.TclError:
            self.destroy()

    def _on_close(self) -> None:
        if not self.is_running:
            self._closing = True
            self.destroy()
            return
        if messagebox.askyesno(
            self._t("dialog_close_title"),
            self._t("dialog_close_body"),
            parent=self,
        ):
            self._close_when_done = True
            self._set_status("status_closing")
            self._request_stop()
            self._log("[close] Close requested; HemiSpec will close after the current file and cleanup.\n")

    # -------------------------------------------------------------------- log
    def _threadsafe_log(self, text: str) -> None:
        """Queue worker output for the main-thread poller.

        Kept as a small public seam for compatibility with earlier GUI builds.
        """

        if text:
            self._events.put(("log", text))

    def _log_is_at_bottom(self) -> bool:
        """Return True when the log is scrolled to (or past) the end."""

        if not hasattr(self, "log_box"):
            return True
        try:
            return should_autoscroll(self.log_box.yview())
        except (tk.TclError, AttributeError, ValueError):
            return True

    def _log(self, text: str) -> None:
        if not hasattr(self, "log_box"):
            return
        # Spec section 7.2: autoscroll only while the user is already at the
        # bottom; stay put while the user has scrolled up to read.
        at_bottom = self._log_is_at_bottom()
        self.log_box.configure(state="normal")
        # Spec section 7.3 "Log tags": tag every chunk separately so a
        # multi-line write gets one style per line and a partial (unterminated)
        # final chunk is still classified.
        for chunk in str(text).splitlines(keepends=True) or ([str(text)] if text else []):
            start = self.log_box.index("end-1c")
            self.log_box.insert("end", chunk)
            self.log_box.tag_add(classify_log_line(chunk), start, "end-1c")
        if at_bottom:
            self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _configure_log_tags(self) -> None:
        """Create the spec section 7.3 log tags on the underlying tk.Text.

        ``CTkTextbox.tag_config`` rejects ``font`` (it would not scale), so the
        bold variants are configured directly on the inner tk.Text widget.
        """

        textbox = getattr(self.log_box, "_textbox", None)
        if textbox is None:
            return
        try:
            textbox.tag_configure(LOG_TAG_DEFAULT, foreground=INK_700)
            textbox.tag_configure(LOG_TAG_MODELS, foreground=TEAL_600)
            textbox.tag_configure(LOG_TAG_WARNING, foreground=WARNING_FG)
            textbox.tag_configure(LOG_TAG_ERROR, foreground=VERM_700)
        except tk.TclError:
            return
        self._refresh_log_tag_fonts()
        # The bold variants track the UI font family when the language changes.
        font_obj = getattr(self.log_box, "_font", None)
        if font_obj is not None and hasattr(font_obj, "add_size_configure_callback"):
            font_obj.add_size_configure_callback(self._refresh_log_tag_fonts)

    def _refresh_log_tag_fonts(self) -> None:
        """Re-create the bold log font from the log box's current UI font."""

        textbox = getattr(self.log_box, "_textbox", None)
        if textbox is None:
            return
        bold: object | None = None
        try:
            bold = tkfont.Font(root=self, font=textbox.cget("font"))
            bold.configure(weight="bold")
        except (tk.TclError, ValueError):
            bold = None
        self._log_bold_font = bold
        bold_kwargs = {"font": bold} if bold is not None else {}
        try:
            textbox.tag_configure(LOG_TAG_WORKFLOW, foreground=TEAL_700, **bold_kwargs)
            textbox.tag_configure(LOG_TAG_SUCCESS, foreground=SUCCESS_FG, **bold_kwargs)
        except tk.TclError:
            pass


def main() -> None:
    try:
        ensure_gui_dependency()
    except MissingGuiDependency as exc:
        root = tk.Tk()
        root.withdraw()
        _apply_window_icon(root)
        messagebox.showerror("Missing HemiSpec GUI dependency", str(exc))
        root.destroy()
        raise SystemExit(str(exc)) from exc
    app = HemiSpecGui()
    app.mainloop()


if __name__ == "__main__":
    main()
