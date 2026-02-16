"""Recovery policies for digital twin simulation."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph_model import DigitalTwinState

NodeID = str


class RecoveryPolicy(ABC):
    """Abstract policy for selecting which grid nodes to repair at each timestep."""

    @abstractmethod
    def select_repairs(
        self,
        twin_state: "DigitalTwinState",
        t: float,
    ) -> list[NodeID]:
        """
        Select grid asset nodes to repair.

        Parameters
        ----------
        twin_state : DigitalTwinState
            Current state of the digital twin.
        t : float
            Current simulation time in days.

        Returns
        -------
        list[NodeID]
            Node IDs of grid assets to repair (set is_operational=True).
        """
        ...


class BaselinePolicy(RecoveryPolicy):
    """
    Baseline policy: repair grid assets in fixed order (substations first, then feeders).
    Among same asset type, repair by node ID order.
    """

    def select_repairs(
        self,
        twin_state: "DigitalTwinState",
        t: float,
    ) -> list[NodeID]:
        graph = twin_state.graph
        broken = [
            n
            for n in graph.nodes
            if graph.nodes[n].get("node_type") == "grid_asset"
            and not graph.nodes[n].get("is_operational", True)
        ]
        # Substations first, then feeders
        def order(n: str) -> tuple[int, str]:
            at = graph.nodes[n].get("asset_type", "")
            return (1 if at == "feeder" else 0, n)

        broken.sort(key=order)
        return broken[:1]  # Repair one per step


class EquityPolicy(RecoveryPolicy):
    """
    Equity-focused policy: prioritize feeders serving buildings with higher
    vulnerability (e.g. vulnerable occupancy groups). Weights vulnerable groups higher.
    """

    def __init__(self, vulnerability_weights: dict[str, float] | None = None):
        """
        Parameters
        ----------
        vulnerability_weights : dict, optional
            Weight per vulnerability_group; higher = higher priority.
            Default: {"residential": 1.5, "commercial": 1.0, "critical": 2.0, "unknown": 1.0}
        """
        self.vulnerability_weights = vulnerability_weights or {
            "residential": 1.5,
            "commercial": 1.0,
            "critical": 2.0,
            "unknown": 1.0,
        }

    def select_repairs(
        self,
        twin_state: "DigitalTwinState",
        t: float,
    ) -> list[NodeID]:
        graph = twin_state.graph
        broken = [
            n
            for n in graph.nodes
            if graph.nodes[n].get("node_type") == "grid_asset"
            and not graph.nodes[n].get("is_operational", True)
        ]
        if not broken:
            return []

        def feeder_equity_score(node_id: str) -> float:
            """Sum of vulnerability weights of buildings served by this feeder."""
            if graph.nodes[node_id].get("asset_type") != "feeder":
                return float("inf")  # Substations first
            score = 0.0
            for neighbor in graph.neighbors(node_id):
                nd = graph.nodes[neighbor]
                if nd.get("node_type") == "building":
                    vg = nd.get("vulnerability_group", "unknown")
                    w = self.vulnerability_weights.get(vg, 1.0)
                    score += w
            return -score  # Higher equity = repair first (sort ascending)

        broken.sort(key=feeder_equity_score)
        return broken[:1]
