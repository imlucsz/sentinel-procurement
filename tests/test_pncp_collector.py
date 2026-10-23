import json
from pathlib import Path
from typing import Any

import pytest

from procurement_monitor.collectors.pncp_collector import collect_publications


class FakePNCPClient:
    """Fake PNCP client that returns predefined records without HTTP."""

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records
        self.received_arguments: dict[str, Any] = {}

    def iter_publications(self, **kwargs: Any):
        self.received_arguments = kwargs
        yield from self.records


@pytest.fixture
def sample_records() -> list[dict[str, Any]]:
    """Example records resembling the PNCP response."""
    return [
        {
            "numeroControlePNCP": "12345678000199-1-000001/2026",
            "objetoCompra": "Aquisição de materiais escolares",
            "valorTotalEstimado": 15000.00,
            "orgaoEntidade": {
                "cnpj": "12345678000199",
                "razaoSocial": "Prefeitura de Exemplo",
            },
        },
        {
            "numeroControlePNCP": "12345678000199-1-000002/2026",
            "objetoCompra": "Aquisição de equipamentos",
            "valorTotalEstimado": 25000.00,
            "orgaoEntidade": {
                "cnpj": "12345678000199",
                "razaoSocial": "Prefeitura de Exemplo",
            },
        },
    ]


def test_collect_publications_saves_records_and_metadata(
    tmp_path: Path,
    sample_records: list[dict[str, Any]],
) -> None:
    client = FakePNCPClient(sample_records)
    output_dir = tmp_path / "raw"

    output_path = collect_publications(
        client=client,
        start_date="2026-10-13",
        end_date="2026-10-20",
        modality_code=6,
        uf="sp",
        output_dir=output_dir,
    )

    assert output_path.exists()
    assert output_path.parent == output_dir
    assert output_path.suffix == ".json"
    assert not output_path.with_suffix(".json.tmp").exists()

    document = json.loads(output_path.read_text(encoding="utf-8"))

    assert document["schema_version"] == 1
    assert document["source"] == "PNCP"
    assert document["source_base_url"] == "https://pncp.gov.br/api/consulta"
    assert document["source_endpoint"] == "/v1/contratacoes/publicacao"
    assert document["collected_at_utc"].endswith("+00:00")

    assert document["filters"] == {
        "start_date": "20261013",
        "end_date": "20261020",
        "modality_code": 6,
        "uf": "SP",
        "municipality_code": None,
        "page_size": 50,
    }

    assert document["record_count"] == 2
    assert document["records"] == sample_records

    # Confirm the collector passes normalized filters to the client.
    assert client.received_arguments == {
        "start_date": "20261013",
        "end_date": "20261020",
        "modality_code": 6,
        "uf": "SP",
        "municipality_code": None,
        "page_size": 50,
    }


def test_collect_publications_accepts_municipality_code(
    tmp_path: Path,
) -> None:
    client = FakePNCPClient([])

    output_path = collect_publications(
        client=client,
        start_date="20261013",
        end_date="20261020",
        modality_code=6,
        municipality_code="3550308",
        output_dir=tmp_path,
    )

    document = json.loads(output_path.read_text(encoding="utf-8"))

    assert document["filters"]["uf"] is None
    assert document["filters"]["municipality_code"] == "3550308"
    assert document["record_count"] == 0
    assert document["records"] == []


@pytest.mark.parametrize(
    ("uf", "municipality_code"),
    [
        (None, None),
        ("SP", "3550308"),
    ],
)
def test_collect_publications_requires_exactly_one_location_filter(
    tmp_path: Path,
    uf: str | None,
    municipality_code: str | None,
) -> None:
    client = FakePNCPClient([])

    with pytest.raises(ValueError, match="exactly one location filter"):
        collect_publications(
            client=client,
            start_date="2026-10-13",
            end_date="2026-10-20",
            modality_code=6,
            uf=uf,
            municipality_code=municipality_code,
            output_dir=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_collect_publications_rejects_empty_uf(
    tmp_path: Path,
) -> None:
    client = FakePNCPClient([])

    with pytest.raises(ValueError, match="uf must not be empty"):
        collect_publications(
            client=client,
            start_date="2026-10-13",
            end_date="2026-10-20",
            modality_code=6,
            uf="   ",
            output_dir=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_collect_publications_rejects_reversed_date_range(
    tmp_path: Path,
) -> None:
    client = FakePNCPClient([])

    with pytest.raises(ValueError, match="start_date must not be after end_date"):
        collect_publications(
            client=client,
            start_date="2026-10-20",
            end_date="2026-10-13",
            modality_code=6,
            uf="SP",
            output_dir=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_collect_publications_preserves_unicode(
    tmp_path: Path,
) -> None:
    records = [
        {
            "objetoCompra": "Aquisição de café, açúcar e pão",
        }
    ]
    client = FakePNCPClient(records)

    output_path = collect_publications(
        client=client,
        start_date="2026-10-13",
        end_date="2026-10-20",
        modality_code=6,
        uf="SP",
        output_dir=tmp_path,
    )

    raw_json = output_path.read_text(encoding="utf-8")

    assert "Aquisição" in raw_json
    assert json.loads(raw_json)["records"] == records
