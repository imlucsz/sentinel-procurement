"""HTTP client for the public PNCP consultation API."""

import time
from collections.abc import Iterator
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://pncp.gov.br/api/consulta"
PUBLICATIONS_ENDPOINT = "/v1/contratacoes/publicacao"


def format_pncp_date(value: date | str) -> str:
    """Convert a date into the YYYYMMDD format expected by PNCP."""
    if isinstance(value, date):
        return value.strftime("%Y%m%d")

    normalized = value.strip()

    try:
        if len(normalized) == 8 and normalized.isdigit():
            parsed = date(
                int(normalized[:4]),
                int(normalized[4:6]),
                int(normalized[6:8]),
            )
        else:
            parsed = date.fromisoformat(normalized.replace("/", "-"))
    except ValueError as exc:
        raise ValueError(
            f"Invalid date: {value!r}. Use YYYY-MM-DD, YYYY/MM/DD or YYYYMMDD."
        ) from exc

    return parsed.strftime("%Y%m%d")


def _get_retry_delay(response: httpx.Response, retry_number: int) -> float:
    """Calculate a retry delay, respecting the server's Retry-After header."""
    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)

                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=UTC)

                return max(
                    0.0,
                    (retry_at - datetime.now(UTC)).total_seconds(),
                )
            except (TypeError, ValueError, OverflowError):
                pass

    # Exponential backoff: 2, 4, then 8 seconds.
    return min(2.0**retry_number, 8.0)


class PNCPClient:
    """Client for querying procurement publications from PNCP."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._client = http_client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )
        self._owns_client = http_client is None

    def close(self) -> None:
        """Close the HTTP session when this client owns it."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "PNCPClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_publications_page(
        self,
        *,
        start_date: date | str,
        end_date: date | str,
        modality_code: int,
        page: int = 1,
        uf: str | None = None,
        municipality_code: str | None = None,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Fetch one page of procurement publications."""
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        if modality_code < 1:
            raise ValueError("modality_code must be a positive integer")

        if not 10 <= page_size <= 50:
            raise ValueError("page_size must be between 10 and 50")

        formatted_start = format_pncp_date(start_date)
        formatted_end = format_pncp_date(end_date)

        if formatted_start > formatted_end:
            raise ValueError("start_date must not be after end_date")

        if uf and municipality_code:
            # Both filters are allowed by the API, but usually unnecessary
            # when querying all municipalities in one state.
            pass

        params: dict[str, str | int] = {
            "dataInicial": formatted_start,
            "dataFinal": formatted_end,
            "codigoModalidadeContratacao": modality_code,
            "pagina": page,
            "tamanhoPagina": page_size,
        }

        if uf:
            params["uf"] = uf.strip().upper()

        if municipality_code:
            params["codigoMunicipioIbge"] = municipality_code.strip()

        max_attempts = 4

        for attempt in range(max_attempts):
            response = self._client.get(
                PUBLICATIONS_ENDPOINT,
                params=params,
            )

            if response.status_code != 429:
                response.raise_for_status()
                break

            if attempt == max_attempts - 1:
                response.raise_for_status()

            delay = _get_retry_delay(response, attempt)
            time.sleep(delay)

        payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError("Unexpected PNCP response: expected a JSON object")

        if not isinstance(payload.get("data"), list):
            raise ValueError("Unexpected PNCP response: missing data list")

        return payload

    def iter_publications(
        self,
        *,
        start_date: date | str,
        end_date: date | str,
        modality_code: int,
        uf: str | None = None,
        municipality_code: str | None = None,
        page_size: int = 50,
    ) -> Iterator[dict[str, Any]]:
        """Yield every procurement returned by the paginated endpoint."""
        page = 1

        while True:
            if page > 1:
                time.sleep(1.0)

            payload = self.get_publications_page(
                start_date=start_date,
                end_date=end_date,
                modality_code=modality_code,
                page=page,
                uf=uf,
                municipality_code=municipality_code,
                page_size=page_size,
            )

            records = payload["data"]
            yield from records

            total_pages = payload.get("totalPaginas", page)

            if not records or page >= total_pages:
                break

            page += 1
