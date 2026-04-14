from __future__ import annotations

from app.domain.data_snapshots.entities import DatasetDefinition
from app.domain.data_snapshots.enums import DatasetCode, SnapshotCadence, SnapshotShape


_DATASET_DEFINITIONS: tuple[DatasetDefinition, ...] = (
    DatasetDefinition(
        code=DatasetCode.AUM,
        name="Assets Under Management",
        cadence=SnapshotCadence.DAILY,
        shape=SnapshotShape.SINGLE_ROW,
        snapshot_table="aum_snapshots",
        row_table="aum_rows",
        default_source_name="libapi",
        description="Daily AUM pull stored once per fund/day, with one official snapshot and raw API payload preservation.",
    ),
    DatasetDefinition(
        code=DatasetCode.SIMM,
        name="SIMM",
        cadence=SnapshotCadence.DAILY,
        shape=SnapshotShape.MULTI_ROW,
        snapshot_table="simm_snapshots",
        row_table="simm_snapshot_rows",
        default_source_name="libapi",
        description="Daily SIMM snapshot, usually loaded once per day and broken down by counterparty.",
    ),
    DatasetDefinition(
        code=DatasetCode.EXPIRIES,
        name="Expiries",
        cadence=SnapshotCadence.INTRADAY,
        shape=SnapshotShape.MULTI_ROW,
        snapshot_table="expiries_snapshots",
        row_table="expiries",
        default_source_name="file",
        description="Intraday expiries extract persisted as a snapshot with one row per position or structure.",
    ),
    DatasetDefinition(
        code=DatasetCode.NAV_ESTIMATED,
        name="Estimated NAV",
        cadence=SnapshotCadence.INTRADAY,
        shape=SnapshotShape.SINGLE_ROW,
        snapshot_table="nav_estimated_snapshots",
        row_table="nav_estimated",
        default_source_name="file",
        description="Intraday estimated NAV snapshot expected to produce a single fund-level row.",
    ),
    DatasetDefinition(
        code=DatasetCode.LEVERAGES,
        name="Leverages",
        cadence=SnapshotCadence.INTRADAY,
        shape=SnapshotShape.SINGLE_ROW,
        snapshot_table="leverages_snapshots",
        row_table="leverages",
        default_source_name="file",
        description="Intraday leverage summary snapshot with one fund-level aggregate row.",
    ),
    DatasetDefinition(
        code=DatasetCode.LEVERAGES_PER_TRADE,
        name="Leverages Per Trade",
        cadence=SnapshotCadence.INTRADAY,
        shape=SnapshotShape.MULTI_ROW,
        snapshot_table="leverages_per_trade_snapshots",
        row_table="leverages_per_trade",
        default_source_name="file",
        description="Intraday leverage decomposition stored one row per trade.",
    ),
    DatasetDefinition(
        code=DatasetCode.LEVERAGES_PER_UNDERLYING,
        name="Leverages Per Underlying",
        cadence=SnapshotCadence.INTRADAY,
        shape=SnapshotShape.MULTI_ROW,
        snapshot_table="leverages_per_underlying_snapshots",
        row_table="leverages_per_underlying",
        default_source_name="file",
        description="Intraday leverage decomposition stored one row per underlying.",
    ),
    DatasetDefinition(
        code=DatasetCode.LONG_SHORT_DELTA,
        name="Long Short Delta",
        cadence=SnapshotCadence.INTRADAY,
        shape=SnapshotShape.MULTI_ROW,
        snapshot_table="long_short_delta_snapshots",
        row_table="long_short_delta",
        default_source_name="file",
        description="Intraday long/short delta split stored one row per underlying asset.",
    ),
    DatasetDefinition(
        code=DatasetCode.COUNTERPARTY_CONCENTRATION,
        name="Counterparty Concentration",
        cadence=SnapshotCadence.INTRADAY,
        shape=SnapshotShape.MULTI_ROW,
        snapshot_table="counterparty_concentration_snapshots",
        row_table="counterparty_concentration",
        default_source_name="file",
        description="Intraday counterparty concentration snapshot stored one row per counterparty.",
    ),
)


def get_dataset_catalog() -> dict[DatasetCode, DatasetDefinition]:
    return {definition.code: definition for definition in _DATASET_DEFINITIONS}


def list_dataset_catalog() -> list[DatasetDefinition]:
    return list(_DATASET_DEFINITIONS)

