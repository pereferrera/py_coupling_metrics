import os
import ast
import random
import logging
from dataclasses import dataclass
from typing import Dict, List


logger = logging.getLogger(__name__)


"""
TODO Support different levels of grouping (packages/sub-packages)
"""


@dataclass
class CouplingMetrics:

    afferent_count: Dict[str, int]
    efferent_count: Dict[str, int]

    # Abstractness (A): The ratio of the number of abstract classes
    # (and interfaces) in the analyzed
    # package to the total number of classes in the analyzed package.
    # The range for this metric is 0 to 1,
    # with A=0 indicating a completely concrete package and A=1 indicating a
    # completely abstract package.
    abstractness: Dict[str, float]
    instability: Dict[str, float]

    # Distance from the main sequence (D): The perpendicular distance of a
    # package from the idealized line A + I = 1. D is calculated
    # as D = | A + I - 1 |.
    # This metric is an indicator of the package's balance between
    # abstractness and stability.
    # A package squarely on the main sequence is optimally balanced with
    # respect to its abstractness and stability. Ideal packages are either
    # ompletely abstract and stable (I=0, A=1)
    # or completely concrete and unstable (I=1, A=0).
    # The range for this metric is 0 to 1,
    # with D=0 indicating a package that is coincident with the main
    # sequence and D=1 indicating a package that is as far from the main
    # sequence as possible.
    distance_to_main_seq: Dict[str, float]

    uml_diagram: List[str]

    @classmethod
    def new(cls):
        return CouplingMetrics(
            afferent_count={},
            efferent_count={},
            abstractness={},
            instability={},
            distance_to_main_seq={},
            uml_diagram=[]
        )


def generate_metrics(project_root: str, package_name: str) -> CouplingMetrics:
    project_root = os.path.abspath(project_root)
    if not project_root.endswith('/'):
        project_root += '/'

    metrics = CouplingMetrics.new()

    metrics.uml_diagram = [
        '@startuml',
        f'package "{package_name}" ' + '{'
    ]

    # https://en.wikipedia.org/wiki/Software_package_metrics

    def find_decorator_name(decorator):
        if hasattr(decorator, 'id'):
            return decorator.id
        elif hasattr(decorator, 'attr'):
            return decorator.attr
        return ''

    def has_abstract_method(node):
        res = any(find_decorator_name(i) == 'abstractmethod'
                  for i in node.decorator_list)
        return res

    def is_abstract_class(node):
        return any(isinstance(n, ast.FunctionDef)
                   and has_abstract_method(n) for n in node.body)

    def parse_import_node(node, dependencies):
        for alias in node.names:
            # TODO what would happen with a * alias?
            to_corresponding_module = (
                '/'.join(f"{node.module}.{alias.name}"
                         .split('.'))
                + '.py'
            )

            while not os.path.exists(os.path.join(project_root,
                                                  to_corresponding_module)):
                file_tree = to_corresponding_module.split('/')
                if len(file_tree) < 2:
                    to_corresponding_module = None
                    break
                to_corresponding_module = '/'.join(file_tree[:-1]) + '.py'

            if not to_corresponding_module:
                logger.error(f'{node.module}.{alias.name} '
                             'cannot be traced back a python file')
                continue

            to_corresponding_module = '.'.join(
                '.'.join(to_corresponding_module.split('/')).split('.')[:-1]
            )
            logger.info(f' - imports {to_corresponding_module}')
            dependencies.add(to_corresponding_module)

    for root, _, files in os.walk(os.path.join(project_root, package_name),
                                  topdown=False):
        for name in files:
            if name.endswith('.py'):
                file_path = os.path.join(root, name)
                # super hacky?
                module_name = (
                    file_path.replace(project_root, '')
                    .replace('/', '.')
                    .replace('.py', '')
                )
                logger.info(f'Parsing {module_name}')
                depends_on = 0
                abstract = 0
                concrete = 0

                dependencies = set()

                with open(file_path, "r") as file:
                    code = file.read()
                    module = ast.parse(code)

                    for node in module.body:
                        if isinstance(node, ast.FunctionDef):
                            concrete += 1
                        elif isinstance(node, ast.ClassDef):
                            abstract += (
                                1 if is_abstract_class(node) else 0
                            )
                        elif isinstance(node, ast.ImportFrom):
                            if not node.module.startswith(package_name):
                                continue
                            parse_import_node(node, dependencies)

                for dependency in dependencies:
                    # draw a UML line in PlantUML format
                    to_ = '.'.join(f"{dependency}".split('.')[1:])
                    arrow_direction = random.choice(['', 'up.', 'down.'])
                    from_ = '.'.join(module_name.split('.')[1:])
                    metrics.uml_diagram.append(
                        f"  [{from_}] .{arrow_direction}> [{to_}]")
                    metrics.afferent_count[dependency] =\
                        metrics.afferent_count.get(dependency, 0) + 1
                    depends_on += 1

                metrics.efferent_count[module_name] = depends_on

                if abstract + concrete > 0:
                    metrics.abstractness[module_name] = (
                        abstract / (abstract + concrete)
                    )

    metrics.uml_diagram.append("}")
    metrics.uml_diagram.append("@enduml")

    metrics.instability = {
        module: (
            metrics.efferent_count.get(module, 0) /
            (metrics.efferent_count.get(module, 0)
             + metrics.afferent_count.get(module, 0))
        )
        for module in set(
            list(metrics.efferent_count.keys())
            + list(metrics.afferent_count.keys())
        )
        if (
            metrics.efferent_count.get(module, 0)
            + metrics.afferent_count.get(module, 0)
        ) > 0
    }

    metrics.distance_to_main_seq = {
        module: abs(metrics.abstractness.get(module, 0)
                    + metrics.instability.get(module) - 1)
        for module in metrics.instability.keys()
    }

    return metrics
