"""Load and validate document-type configuration files."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


SUPPORTED_FIELD_TYPES = {"string", "integer", "number", "boolean", "date"}
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class FieldConfig:
    name: str
    type: str
    description: str
    required: bool
    regex: str | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    allowed_values: tuple[str | int | float | bool, ...] = ()


@dataclass(frozen=True)
class DocumentConfig:
    doc_type: str
    output_table: str
    confidence_threshold: float
    fields: tuple[FieldConfig, ...]


def load_document_config(path: str | Path) -> DocumentConfig:
    """Load a YAML file and reject invalid configuration with a useful error."""
    config_path = Path(path)
    try:
        with config_path.open(encoding="utf-8") as config_file:
            data = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")

    doc_type = _required_string(data, "doc_type", config_path)
    output_table = _required_string(data, "output_table", config_path)
    if not _IDENTIFIER_PATTERN.fullmatch(doc_type):
        raise ValueError("doc_type must be a simple identifier")
    if not _IDENTIFIER_PATTERN.fullmatch(output_table):
        raise ValueError("output_table must be a simple identifier")

    threshold = data.get("confidence_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("confidence_threshold must be a number between 0 and 1")
    if not 0 <= threshold <= 1:
        raise ValueError("confidence_threshold must be a number between 0 and 1")

    raw_fields = data.get("fields")
    if not isinstance(raw_fields, list) or not raw_fields:
        raise ValueError("fields must be a non-empty list")

    fields = tuple(
        _parse_field(field, index, config_path)
        for index, field in enumerate(raw_fields)
    )
    field_names = [field.name for field in fields]
    if len(set(field_names)) != len(field_names):
        raise ValueError("field names must be unique")

    return DocumentConfig(
        doc_type=doc_type,
        output_table=output_table,
        confidence_threshold=float(threshold),
        fields=fields,
    )


def _required_string(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {key} must be a non-empty string")
    return value.strip()


def _parse_field(value: Any, index: int, path: Path) -> FieldConfig:
    prefix = f"{path}: fields[{index}]"
    if not isinstance(value, dict):
        raise ValueError(f"{prefix} must be a mapping")

    name = value.get("name")
    if not isinstance(name, str) or not _IDENTIFIER_PATTERN.fullmatch(name):
        raise ValueError(f"{prefix}.name must be a simple identifier")

    field_type = value.get("type")
    if not isinstance(field_type, str) or field_type not in SUPPORTED_FIELD_TYPES:
        raise ValueError(
            f"{prefix}.type must be one of {', '.join(sorted(SUPPORTED_FIELD_TYPES))}"
        )

    description = value.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"{prefix}.description must be a non-empty string")

    required = value.get("required", False)
    if not isinstance(required, bool):
        raise ValueError(f"{prefix}.required must be a boolean")

    regex = value.get("regex")
    if regex is not None:
        if not isinstance(regex, str):
            raise ValueError(f"{prefix}.regex must be a string")
        try:
            re.compile(regex)
        except re.error as exc:
            raise ValueError(f"{prefix}.regex is invalid: {exc}") from exc

    minimum = _numeric_bound(value.get("min"), f"{prefix}.min")
    maximum = _numeric_bound(value.get("max"), f"{prefix}.max")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError(f"{prefix}.min cannot be greater than max")
    if (minimum is not None or maximum is not None) and field_type not in {
        "integer",
        "number",
    }:
        raise ValueError(f"{prefix} min/max rules require an integer or number field")

    allowed_values = value.get("allowed_values", [])
    if not isinstance(allowed_values, list):
        raise ValueError(f"{prefix}.allowed_values must be a list")
    if any(item is None or isinstance(item, (dict, list)) for item in allowed_values):
        raise ValueError(f"{prefix}.allowed_values entries must be scalar values")

    return FieldConfig(
        name=name,
        type=field_type,
        description=description.strip(),
        required=required,
        regex=regex,
        minimum=minimum,
        maximum=maximum,
        allowed_values=tuple(allowed_values),
    )


def _numeric_bound(value: Any, label: str) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    return value
