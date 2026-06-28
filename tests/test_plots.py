import numpy as np

from hemispec.plots import _boxplot_label_keyword, plot_within_between_box


def test_plot_within_between_box_handles_modern_matplotlib_keyword(tmp_path):
    out_png = tmp_path / "boxplot.png"
    plot_within_between_box(
        within=np.array([0.92, 0.88], dtype=np.float32),
        between=np.array([], dtype=np.float32),
        out_png=out_png,
        title="ANS.L",
    )
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_boxplot_label_keyword_supports_old_and_new_matplotlib_names():
    def old_boxplot(data, labels=None, showfliers=True):
        return data, labels, showfliers

    def new_boxplot(data, tick_labels=None, showfliers=True):
        return data, tick_labels, showfliers

    assert _boxplot_label_keyword(old_boxplot) == "labels"
    assert _boxplot_label_keyword(new_boxplot) == "tick_labels"
