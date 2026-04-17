"""Mapping service — apply a saved FieldMap to raw studio rows.

Takes a confirmed column mapping (from schema_agent) and transforms
raw studio rows into the PlayerPulse standard field names.

TODO (Sprint 5):
  - apply_field_map(rows, field_map) → standardized rows
"""


def apply_field_map(rows: list[dict], field_map: dict) -> list[dict]:
    """Rename columns in raw rows using the studio's confirmed field map.

    Args:
        rows: Raw rows from studio CSV/Excel
        field_map: Dict of {studio_column → playerpulse_field}
                   None values mean the column has no mapping (skipped)

    Returns:
        List of dicts with PlayerPulse standard field names

    TODO (Sprint 5): implement. Handle None mappings, type coercion,
    and missing required fields gracefully.
    """
    raise NotImplementedError("TODO (Sprint 5): implement field mapping transformation")
