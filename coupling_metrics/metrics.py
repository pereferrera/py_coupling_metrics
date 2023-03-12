from dataclasses import dataclass
from typing import Dict, List


"""
https://en.wikipedia.org/wiki/Software_package_metrics
"""


@dataclass
class CouplingMetrics:

    afferent_count: Dict[str, int]
    efferent_count: Dict[str, int]
    abstractness: Dict[str, float]
    instability: Dict[str, float]
    distance_to_main_seq: Dict[str, float]

    afferent_set: Dict[str, List[str]]
    efferent_set: Dict[str, List[str]]

    uml_diagram: List[str]

    @classmethod
    def new(cls):
        return CouplingMetrics(
            afferent_count={},
            efferent_count={},
            abstractness={},
            instability={},
            distance_to_main_seq={},
            uml_diagram=[],
            afferent_set={},
            efferent_set={}
        )
