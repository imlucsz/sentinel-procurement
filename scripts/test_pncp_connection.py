"""Small integration test against the real PNCP API."""

from datetime import date
from pathlib import Path

from procurement_monitor.clients.pncp import PNCPClient
from procurement_monitor.collectors.pncp_collector import collect_publications


def main() -> None:
    output_dir = Path("data/raw/pncp_test")

    with PNCPClient(timeout=60.0) as client:
        output_path = collect_publications(
            client=client,
            start_date=date(2026, 10, 20),
            end_date=date(2026, 10, 20),
            modality_code=6,
            uf="SP",
            output_dir=output_dir,
            page_size=10,
        )

    print(f"Arquivo salvo: {output_path}")

    import json

    document = json.loads(output_path.read_text(encoding="utf-8"))

    print(f"Total de registros: {document['record_count']}")
    print(f"Filtros utilizados: {document['filters']}")

    if document["records"]:
        first_record = document["records"][0]
        print("\nCampos do primeiro registro:")
        print(sorted(first_record.keys()))
        print("\nPrimeiro registro:")
        print(json.dumps(first_record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
