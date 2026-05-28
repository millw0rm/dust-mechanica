
from __future__ import annotations

from packages.domain.topologies.belt_axis.plugin import BeltAxisTopology
from packages.domain.topologies.ball_screw.plugin import BallScrewTopology
from packages.domain.topologies.direct_drive.plugin import DirectDriveRotaryTopology


_REGISTRY = {
    BeltAxisTopology.name: BeltAxisTopology(),
    BallScrewTopology.name: BallScrewTopology(),
    DirectDriveRotaryTopology.name: DirectDriveRotaryTopology(),
}


def all_topologies() -> dict:
    return dict(_REGISTRY)


def get_topology(name: str):
    return _REGISTRY.get(name)
