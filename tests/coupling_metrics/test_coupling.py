import unittest
import random

from coupling_metrics import coupling
from coupling_metrics.coupling import adjust_module_name_to_level

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

    def test_adjust_module_name_to_level(self):
        self.assertEqual('foo.bar',
                         adjust_module_name_to_level('foo.bar', -1))
        self.assertEqual('foo',
                         adjust_module_name_to_level('foo', 1))
        self.assertEqual('foo',
                         adjust_module_name_to_level('foo.bar.bor', 1))
        self.assertEqual('foo.bar',
                         adjust_module_name_to_level('foo.bar.bor', 2))
        self.assertEqual('foo.bar.bor',
                         adjust_module_name_to_level('foo.bar.bor', 3))
        self.assertEqual('foo.bar.bor',
                         adjust_module_name_to_level('foo.bar.bor', 0))
