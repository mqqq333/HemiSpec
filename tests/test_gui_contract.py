from hemispec.gui import (
    WORKFLOW_ENCAPSULATED_FIELDS,
    WORKFLOW_REQUIRED_FIELDS,
    WORKFLOW_VISIBLE_FIELDS,
)


def test_standard_workflow_exposes_only_user_decisions() -> None:
    assert WORKFLOW_VISIBLE_FIELDS == (
        "input_glob",
        "out_dir",
        "export_roi_table",
        "roi_atlas",
        "roi_label_table",
        "run_classifier",
        "run_trt",
    )



def test_standard_workflow_encapsulates_model_assets_and_internal_parameters() -> None:
    encapsulated = set(WORKFLOW_ENCAPSULATED_FIELDS)
    assert {"model_root", "device", "classifier_model_dir"}.issubset(encapsulated)
    assert {"gm_thresh", "eps", "pred_suffix", "actual_suffix", "trt_file_regex", "roi_stat"}.issubset(encapsulated)
    assert encapsulated.isdisjoint(WORKFLOW_VISIBLE_FIELDS)



def test_standard_workflow_field_contract_has_no_duplicates() -> None:
    assert len(WORKFLOW_REQUIRED_FIELDS) == len(set(WORKFLOW_REQUIRED_FIELDS))
    assert set(WORKFLOW_REQUIRED_FIELDS) == set(WORKFLOW_VISIBLE_FIELDS) | set(WORKFLOW_ENCAPSULATED_FIELDS)
