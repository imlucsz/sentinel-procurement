from datetime import date

import httpx
import pytest

from procurement_monitor.clients.pncp import (
    DEFAULT_BASE_URL,
    PNCPClient,
    format_pncp_date,
)


def make_contract(contract_id: str) -> dict:
    """Build a minimal procurement record for testing."""
    return {
        "numeroControlePNCP": contract_id,
        "orgaoEntidade": {"cnpj": "12345678000199"},
        "anoCompra": 2026,
        "sequencialCompra": 1,
        "objetoCompra": "Aquisição de materiais",
    }


def make_client(handler) -> tuple[PNCPClient, httpx.Client]:
    """Create a PNCP client that uses mocked HTTP responses."""
    http_client = httpx.Client(
        base_url=DEFAULT_BASE_URL,
        transport=httpx.MockTransport(handler),
    )
    return PNCPClient(http_client=http_client), http_client


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (date(2026, 10, 13), "20261013"),
        ("2026-10-13", "20261013"),
        ("2026/10/13", "20261013"),
        ("20261013", "20261013"),
    ],
)
def test_format_pncp_date(value, expected):
    assert format_pncp_date(value) == expected


def test_format_pncp_date_rejects_invalid_date():
    with pytest.raises(ValueError, match="Invalid date"):
        format_pncp_date("31/12/2026")


def test_get_publications_page_sends_uf_filters():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/consulta/v1/contratacoes/publicacao"
        assert request.url.params["dataInicial"] == "20261013"
        assert request.url.params["dataFinal"] == "20261020"
        assert request.url.params["codigoModalidadeContratacao"] == "6"
        assert request.url.params["uf"] == "SP"
        assert request.url.params["pagina"] == "1"

        return httpx.Response(
            200,
            json={
                "data": [make_contract("contract-1")],
                "totalRegistros": 1,
                "totalPaginas": 1,
                "numeroPagina": 1,
                "paginasRestantes": 0,
                "empty": False,
            },
        )

    client, http_client = make_client(handler)

    try:
        payload = client.get_publications_page(
            start_date="2026-10-13",
            end_date="2026-10-20",
            modality_code=6,
            uf="sp",
            page=1,
        )

        assert len(payload["data"]) == 1
        assert payload["data"][0]["numeroControlePNCP"] == "contract-1"
    finally:
        http_client.close()


def test_get_publications_page_accepts_municipality_code():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["codigoMunicipioIbge"] == "3550308"
        assert "uf" not in request.url.params

        return httpx.Response(
            200,
            json={
                "data": [],
                "totalRegistros": 0,
                "totalPaginas": 0,
                "numeroPagina": 1,
                "paginasRestantes": 0,
                "empty": True,
            },
        )

    client, http_client = make_client(handler)

    try:
        payload = client.get_publications_page(
            start_date="2026-10-13",
            end_date="2026-10-20",
            modality_code=6,
            municipality_code="3550308",
        )

        assert payload["data"] == []
        assert payload["empty"] is True
    finally:
        http_client.close()


def test_iter_publications_collects_all_pages():
    records_by_page = {
        1: [make_contract("contract-1")],
        2: [make_contract("contract-2")],
        3: [make_contract("contract-3")],
    }
    requested_pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["pagina"])
        requested_pages.append(page)

        return httpx.Response(
            200,
            json={
                "data": records_by_page[page],
                "totalRegistros": 3,
                "totalPaginas": 3,
                "numeroPagina": page,
                "paginasRestantes": 3 - page,
                "empty": False,
            },
        )

    client, http_client = make_client(handler)

    try:
        records = list(
            client.iter_publications(
                start_date="2026-10-13",
                end_date="2026-10-20",
                modality_code=6,
                uf="SP",
            )
        )

        assert requested_pages == [1, 2, 3]
        assert len(records) == 3
        assert [record["numeroControlePNCP"] for record in records] == [
            "contract-1",
            "contract-2",
            "contract-3",
        ]

        # The original nested data is preserved.
        assert records[0]["orgaoEntidade"]["cnpj"] == "12345678000199"
    finally:
        http_client.close()


def test_iter_publications_stops_when_result_is_empty():
    requested_pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_pages.append(int(request.url.params["pagina"]))

        return httpx.Response(
            200,
            json={
                "data": [],
                "totalRegistros": 0,
                "totalPaginas": 0,
                "numeroPagina": 1,
                "paginasRestantes": 0,
                "empty": True,
            },
        )

    client, http_client = make_client(handler)

    try:
        records = list(
            client.iter_publications(
                start_date="2026-10-13",
                end_date="2026-10-20",
                modality_code=6,
                uf="SP",
            )
        )

        assert records == []
        assert requested_pages == [1]
    finally:
        http_client.close()


def test_get_publications_page_raises_for_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client, http_client = make_client(handler)

    try:
        with pytest.raises(httpx.HTTPStatusError):
            client.get_publications_page(
                start_date="2026-10-13",
                end_date="2026-10-20",
                modality_code=6,
                uf="SP",
            )
    finally:
        http_client.close()
