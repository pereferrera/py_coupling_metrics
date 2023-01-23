import unittest
import random

from coupling_metrics import coupling

"""
TODO add example project of paper "Software Instability Analysis ..."
and check if obtained metrics are equivalent
"""


class TestCouplingMetrics(unittest.TestCase):

    def test(self):
        random.seed(1)

        metrics = coupling.generate_metrics('./tests/example_project',
                                            'my_module')
        # TODO add assertions
        for line in metrics.uml_diagram:
            print(line)
