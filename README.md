# Config-Driven Document-to-Dataset Pipeline

A local-first pipeline for turning PDFs and scans into validated, queryable datasets. Document behavior is defined in YAML so additional document types can be added without changing pipeline logic.

## Project status

Phase 1 is in place: the Python package, validated YAML configuration, receipt document type, synthetic receipt fixture, tests, and a Docker development image. Local OCR is the next implementation phase; extraction, Spark processing, cloud deployment, and benchmarks follow.

## Project layout

```text
configs/              Document-type YAML configurations
examples/             Synthetic fixtures for local development
src/doc_pipeline/     Reusable pipeline code
tests/                Automated tests
data/raw/             Local input files (git-ignored)
data/processed/       Local generated output (git-ignored)
```

## Quick start

Requires Python 3.11+ and Tesseract OCR installed on the host for OCR development.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

The first document type is a receipt. Its field definitions and validation rules are in [`configs/receipt.yaml`](configs/receipt.yaml). [`examples/receipt.txt`](examples/receipt.txt) is synthetic text for development and contains no real customer data; it is not an OCR image or PDF.

## Docker development environment

Build and run the test image from the project directory:

```powershell
docker build -t document-to-dataset-pipeline .
docker run --rm document-to-dataset-pipeline
```

The image includes Tesseract and the Python development dependencies. It does not call AWS services or download an LLM.

## Planned processing flow

```text
PDFs/images -> raw storage -> OCR -> text -> config-driven extraction
            -> explicit-schema Spark processing -> clean/quarantine Parquet
            -> metrics and drift checks
```

Local OCR and Ollama development come before AWS integration. Any third-party sample datasets added later will include their source and license; this repository currently redistributes no third-party documents.
