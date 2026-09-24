from typing import Any, Dict, List, Optional
from app.models.response import DocumentTable


def format_currency(amount: Optional[float], currency: Optional[str] = "EUR") -> str:
    """Formats numeric amount to standard currency string representation."""
    if amount is None:
        return ""
    curr = currency or "EUR"
    return f"{amount:,.2f} {curr}"


def to_markdown_table(table: DocumentTable) -> str:
    """Converts an extracted DocumentTable into a clean Markdown table string."""
    if not table.cells:
        return ""

    grid: Dict[int, Dict[int, str]] = {}
    for cell in table.cells:
        if cell.row_index not in grid:
            grid[cell.row_index] = {}
        grid[cell.row_index][cell.column_index] = cell.content.replace("\n", " ").strip()

    rows: List[str] = []
    header_cells = [grid.get(0, {}).get(c, "") for c in range(table.column_count)]
    rows.append("| " + " | ".join(header_cells) + " |")
    rows.append("| " + " | ".join(["---"] * table.column_count) + " |")

    for r in range(1, table.row_count):
        row_cells = [grid.get(r, {}).get(c, "") for c in range(table.column_count)]
        rows.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(rows)
