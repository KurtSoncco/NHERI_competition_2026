"""Digital twin graph model wrapping networkx."""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .policy import RecoveryPolicy

NodeID = str

# Default number of synthetic feeders (cluster centers)
DEFAULT_N_FEEDERS = 5


def _kmeans_cluster_centers(
    points: np.ndarray,
    k: int,
    max_iter: int = 50,
) -> np.ndarray:
    """Simple k-means: return k cluster centers (2D points)."""
    n = len(points)
    if n == 0 or k <= 0:
        return np.array([]).reshape(0, 2)
    if k >= n:
        return points.copy()

    # Initialize centers: k random points
    rng = np.random.default_rng(42)
    idx = rng.choice(n, size=min(k, n), replace=False)
    centers = points[idx].astype(float).copy()

    for _ in range(max_iter):
        # Assign each point to nearest center
        diff = points[:, np.newaxis, :] - centers[np.newaxis, :, :]  # (n, k, 2)
        dist_sq = (diff * diff).sum(axis=2)  # (n, k)
        labels = dist_sq.argmin(axis=1)  # (n,)
        # Update centers
        new_centers = np.empty_like(centers)
        for j in range(k):
            mask = labels == j
            if mask.any():
                new_centers[j] = points[mask].mean(axis=0)
            else:
                new_centers[j] = centers[j]
        if np.allclose(centers, new_centers):
            break
        centers = new_centers
    return centers


class DigitalTwinState:
    """
    Digital twin state wrapping a networkx.Graph with building and grid asset nodes.
    """

    def __init__(self, graph: nx.Graph | None = None):
        self.graph = graph if graph is not None else nx.Graph()
        self._t: float = 0.0

    @classmethod
    def from_buildings_df(
        cls,
        buildings: pd.DataFrame,
        n_feeders: int = DEFAULT_N_FEEDERS,
    ) -> "DigitalTwinState":
        """
        Create DigitalTwinState from a buildings DataFrame.

        Adds building nodes with attributes and a synthetic feeder network
        (k-means cluster centers as feeders). Each building is connected to
        its nearest feeder; feeders connect to one substation.

        Parameters
        ----------
        buildings : pd.DataFrame
            Must have columns: id, lat, lon; optional: event, damage_state, occupancy.
        n_feeders : int
            Number of synthetic feeders (cluster centers).

        Returns
        -------
        DigitalTwinState
        """
        G = nx.Graph()
        points = buildings[["lat", "lon"]].values.astype(float)
        n = len(buildings)

        # Build building nodes
        id_col = "id" if "id" in buildings.columns else buildings.columns[0]
        for i, row in buildings.iterrows():
            bid = str(row[id_col])
            event = str(row.get("event", "unknown"))
            damage_state = str(row.get("damage_state", "unknown"))
            occupancy = row.get("occupancy", "unknown")
            vulnerability_group = _occupancy_to_vulnerability(occupancy)
            G.add_node(
                bid,
                node_type="building",
                event=event,
                damage_state=damage_state,
                vulnerability_group=vulnerability_group,
                is_energized=False,
                outage_duration_days=0.0,
                lat=float(row["lat"]),
                lon=float(row["lon"]),
            )

        # Synthetic feeder network: substation + feeders from k-means
        substation_id: NodeID = "substation:0"
        centroid = points.mean(axis=0)
        G.add_node(
            substation_id,
            node_type="grid_asset",
            asset_type="substation",
            is_operational=False,
            lat=float(centroid[0]),
            lon=float(centroid[1]),
        )

        centers = _kmeans_cluster_centers(points, n_feeders)
        feeder_ids: list[NodeID] = [f"feeder:{j}" for j in range(len(centers))]
        for j, c in enumerate(centers):
            fid = feeder_ids[j]
            G.add_node(
                fid,
                node_type="grid_asset",
                asset_type="feeder",
                is_operational=False,
                lat=float(c[0]),
                lon=float(c[1]),
            )
            G.add_edge(substation_id, fid)

        # Assign each building to nearest feeder
        for i, bid in enumerate(buildings[id_col].astype(str)):
            pt = points[i]
            dist_sq = ((centers - pt) ** 2).sum(axis=1)
            nearest = int(np.argmin(dist_sq))
            G.add_edge(bid, feeder_ids[nearest])

        twin = cls(graph=G)
        twin._t = 0.0
        return twin

    def step(self, policy: "RecoveryPolicy", dt_days: float = 1.0) -> None:
        """
        Advance simulation by dt_days using the given recovery policy.

        The policy selects which grid nodes to repair; those become operational.
        Building is_energized and outage_duration_days are updated accordingly.

        Parameters
        ----------
        policy : RecoveryPolicy
            Policy that returns list of grid node IDs to repair.
        dt_days : float
            Timestep in days.
        """
        to_repair = policy.select_repairs(self, self._t)
        G = self.graph

        for nid in to_repair:
            if G.has_node(nid) and G.nodes[nid].get("node_type") == "grid_asset":
                G.nodes[nid]["is_operational"] = True

        self._propagate_power()
        self._update_outage_durations(dt_days)
        self._t += dt_days

    def _propagate_power(self) -> None:
        """Set is_energized for buildings based on feeder/substation status."""
        G = self.graph
        substations = [
            n for n in G.nodes
            if G.nodes[n].get("node_type") == "grid_asset"
            and G.nodes[n].get("asset_type") == "substation"
            and G.nodes[n].get("is_operational", False)
        ]
        sub_ok = len(substations) > 0

        for n in G.nodes:
            if G.nodes[n].get("node_type") != "building":
                continue
            energized = False
            for neighbor in G.neighbors(n):
                nd = G.nodes[neighbor]
                if nd.get("node_type") == "grid_asset" and nd.get("asset_type") == "feeder":
                    if sub_ok and nd.get("is_operational", False):
                        energized = True
                        break
            G.nodes[n]["is_energized"] = energized

    def _update_outage_durations(self, dt_days: float) -> None:
        """Increment outage_duration_days for buildings without power."""
        G = self.graph
        for n in G.nodes:
            if G.nodes[n].get("node_type") == "building":
                if not G.nodes[n].get("is_energized", False):
                    prev = G.nodes[n].get("outage_duration_days", 0.0)
                    G.nodes[n]["outage_duration_days"] = prev + dt_days


def _occupancy_to_vulnerability(occupancy: str | float) -> str:
    """Map occupancy to vulnerability_group for equity weighting."""
    if pd.isna(occupancy):
        return "unknown"
    s = str(occupancy).lower().strip()
    if "residential" in s or "res" in s:
        return "residential"
    if "commercial" in s or "comm" in s:
        return "commercial"
    if "critical" in s or "hospital" in s or "school" in s:
        return "critical"
    return "unknown"
