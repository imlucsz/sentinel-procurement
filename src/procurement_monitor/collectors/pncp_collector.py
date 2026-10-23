"""Collect and persist raw procurement publications from PNCP."""

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from procurement_monitor.clients.pncp import (
    DEFAULT_BASE_URL,
    PUBLICATIONS_ENDPOINT,
    PNCPClient,
    format_pncp_date,
)


def collect_publications(
    *,
    client: PNCPClient,
    start_date: date | str,
    end_date: date | str,
    modality_code: int,
    output_dir: str | Path,
    uf: str | None = None,
    municipality_code: str | None = None,
    page_size: int = 50,
) -> Path:
    """Collect publications and save the raw records and metadata to JSON."""
    if bool(uf) == bool(municipality_code):
        raise ValueError(
            "Provide exactly one location filter: uf or municipality_code."
        )

    formatted_start = format_pncp_date(start_date)
    formatted_end = format_pncp_date(end_date)

    if formatted_start > formatted_end:
        raise ValueError("start_date must not be after end_date")

    normalized_uf = uf.strip().upper() if uf else None
    normalized_municipality = municipality_code.strip() if municipality_code else None

    if normalized_uf == "":
        raise ValueError("uf must not be empty")

    if normalized_municipality == "":
        raise ValueError("municipality_code must not be empty")

    collected_at = datetime.now(UTC)
    records: list[dict[str, Any]] = list(
        client.iter_publications(
            start_date=formatted_start,
            end_date=formatted_end,
            modality_code=modality_code,
            uf=normalized_uf,
            municipality_code=normalized_municipality,
            page_size=page_size,
        )
    )

    # Keep source records intact. Metadata describes how they were collected.
    document = {
        "schema_version": 1,
        "source": "PNCP",
        "source_base_url": DEFAULT_BASE_URL,
        "source_endpoint": PUBLICATIONS_ENDPOINT,
        "collected_at_utc": collected_at.isoformat(),
        "filters": {
            "start_date": formatted_start,
            "end_date": formatted_end,
            "modality_code": modality_code,
            "uf": normalized_uf,
            "municipality_code": normalized_municipality,
            "page_size": page_size,
        },
        "record_count": len(records),
        "records": records,
    }

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    filename_timestamp = collected_at.strftime("%Y%m%dT%H%M%S%fZ")
    output_path = destination / f"pncp_publications_{filename_timestamp}.json"
    temporary_path = output_path.with_suffix(".json.tmp")

    # Write to a temporary file first to avoid leaving a partial JSON file.
    temporary_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(output_path)

    return output_path
