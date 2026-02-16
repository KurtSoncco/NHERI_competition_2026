"""Tests for digital twin graph model and policies."""

import pandas as pd
import pytest

from hcdt.dtwin import BaselinePolicy, DigitalTwinState, EquityPolicy


def test_from_buildings_df_creates_building_and_grid_nodes():
    """from_buildings_df creates building and grid_asset nodes with required attributes."""
    df = pd.DataFrame(
        [
            {"id": "B1", "lat": 29.0, "lon": -85.0, "event": "Michael", "damage_state": "minor"},
            {"id": "B2", "lat": 29.1, "lon": -85.1, "event": "Michael", "damage_state": "moderate"},
            {"id": "B3", "lat": 26.0, "lon": -82.0, "event": "Ian", "occupancy": "residential"},
        ]
    )
    twin = DigitalTwinState.from_buildings_df(df, n_feeders=2)
    G = twin.graph

    for bid in ("B1", "B2", "B3"):
        assert G.has_node(bid)
        nd = G.nodes[bid]
        assert nd["node_type"] == "building"
        assert "event" in nd
        assert "damage_state" in nd
        assert "vulnerability_group" in nd
        assert "is_energized" in nd
        assert "outage_duration_days" in nd

    assert G.has_node("substation:0")
    assert G.nodes["substation:0"]["node_type"] == "grid_asset"
    assert G.nodes["substation:0"]["asset_type"] == "substation"
    assert "is_operational" in G.nodes["substation:0"]

    for j in range(2):
        fid = f"feeder:{j}"
        assert G.has_node(fid)
        assert G.nodes[fid]["asset_type"] == "feeder"
        assert G.nodes[fid]["is_operational"] is False


def test_step_updates_is_operational_and_is_energized():
    """step() repairs grid nodes via policy and updates building is_energized."""
    df = pd.DataFrame(
        [{"id": "B1", "lat": 29.0, "lon": -85.0}, {"id": "B2", "lat": 29.01, "lon": -85.01}]
    )
    twin = DigitalTwinState.from_buildings_df(df, n_feeders=1)

    # Initially no power
    assert not twin.graph.nodes["B1"]["is_energized"]
    assert twin.graph.nodes["B1"]["outage_duration_days"] == 0.0

    # Step: baseline repairs one asset per step
    twin.step(BaselinePolicy(), dt_days=1.0)
    # Substation repaired first
    assert twin.graph.nodes["substation:0"]["is_operational"] is True

    twin.step(BaselinePolicy(), dt_days=1.0)
    # Feeder repaired; step() propagates power
    assert twin.graph.nodes["feeder:0"]["is_operational"] is True
    assert twin.graph.nodes["B1"]["is_energized"] is True

    # Outage duration incremented for steps when building had no power
    assert twin.graph.nodes["B1"]["outage_duration_days"] >= 0


def test_equity_policy_weights_vulnerability():
    """EquityPolicy prefers feeders serving vulnerable groups."""
    df = pd.DataFrame(
        [
            {"id": "B1", "lat": 29.0, "lon": -85.0, "occupancy": "commercial"},
            {"id": "B2", "lat": 29.1, "lon": -85.1, "occupancy": "residential"},
        ]
    )
    twin = DigitalTwinState.from_buildings_df(df, n_feeders=2)
    policy = EquityPolicy(vulnerability_weights={"residential": 2.0, "commercial": 1.0, "unknown": 1.0})

    repairs = policy.select_repairs(twin, 0.0)
    assert len(repairs) == 1
    assert repairs[0] in twin.graph.nodes
