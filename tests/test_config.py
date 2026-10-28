from pathlib import Path

import pytest

from doc_pipeline.config import load_document_config


PROJECT_ROOT = Path(__file__).parents[1]


def test_loads_receipt_config() -> None:
    config = load_document_config(PROJECT_ROOT / "configs" / "receipt.yaml")

    assert config.doc_type == "receipt"
    assert config.output_table == "silver_receipts"
    assert config.confidence_threshold == 0.75
    assert [field.name for field in config.fields] == [
        "merchant_name",
        "transaction_date",
        "currency",
        "total_amount",
        "tax_amount",
        "payment_method",
    ]
    assert config.fields[3].minimum == 0


def test_rejects_duplicate_field_names(tmp_path: Path) -> None:
    config_path = tmp_path / "duplicate.yaml"
    config_path.write_text(
        """
doc_type: receipt
output_table: silver_receipts
confidence_threshold: 0.75
fields:
  - {name: total, type: number, description: Receipt total}
  - {name: total, type: number, description: Duplicate total}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="field names must be unique"):
        load_document_config(config_path)


def test_rejects_out_of_range_confidence_threshold(tmp_path: Path) -> None:
    config_path = tmp_path / "threshold.yaml"
    config_path.write_text(
        """
doc_type: receipt
output_table: silver_receipts
confidence_threshold: 1.1
fields:
  - {name: total, type: number, description: Receipt total}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="confidence_threshold"):
        load_document_config(config_path)


def test_rejects_non_string_field_type(tmp_path: Path) -> None:
    config_path = tmp_path / "field-type.yaml"
    config_path.write_text(
        """
doc_type: receipt
output_table: silver_receipts
confidence_threshold: 0.75
fields:
  - name: total
    type: []
    description: Receipt total
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"fields\[0\]\.type"):
        load_document_config(config_path)
