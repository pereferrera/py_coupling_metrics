import os
import ast
import random
import logging

from coupling_metrics.metrics import CouplingMetrics


logger = logging.getLogger(__name__)

"""
TODO: Allow for external libraries / submodules
For example accept a "whitelist" of libraries that should be considered,
with a defined level for each (for submodules we might want level 2,
for third party libraries we might want level 1)
"""


def adjust_module_name_to_level(module: str, level: int):
    if level < 1:
        # full module name
        return module
    splitted = module.split('.')
    return '.'.join(splitted[:min(len(splitted),
                                  level)])


def generate_metrics(project_root: str, package_name: str,
                     level: int = 0) -> CouplingMetrics:
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

    def parse_import_node(node, dependencies, module_name, level):
        for alias in node.names:
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
                             'cannot be traced back to a module file!')
                continue

            to_corresponding_module = '.'.join(
                '.'.join(to_corresponding_module.split('/')).split('.')[:-1]
            )
            logger.info(f' - imports {to_corresponding_module}')

            dependency = adjust_module_name_to_level(to_corresponding_module,
                                                     level)
            if module_name != dependency:
                dependencies.add(dependency)

    afferent_set = {}
    efferent_set = {}
    abstract_count = {}
    concrete_count = {}
    uml_diagram_set = set()

    for root, _, files in os.walk(os.path.join(project_root, package_name),
                                  topdown=False):
        for name in files:
            if not name.endswith('.py'):
                continue

            file_path = os.path.join(root, name)
            # super hacky?
            module_name = adjust_module_name_to_level(
                file_path.replace(project_root, '')
                .replace('/', '.')
                .replace('.py', ''),
                level=level
            )
            logger.info(f'Parsing {module_name}')

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
                        parse_import_node(node, dependencies, module_name,
                                          level)

            for dependency in dependencies:
                # draw a UML line in PlantUML format
                to_ = '.'.join(f"{dependency}".split('.')[1:])
                from_ = '.'.join(module_name.split('.')[1:])
                uml_diagram_set.add((from_, to_))
                afferent_set[dependency] =\
                    afferent_set.get(dependency, set()).union(
                        set([module_name]))

            efferent_set[module_name] =\
                efferent_set.get(module_name, set()).union(dependencies)

            abstract_count[module_name] =\
                abstract_count.get(module_name, 0) + abstract
            concrete_count[module_name] =\
                concrete_count.get(module_name, 0) + concrete

    for from_, to_ in uml_diagram_set:
        arrow_direction = random.choice(['', 'up.', 'down.'])
        metrics.uml_diagram.append(
            f"  [{from_}] .{arrow_direction}> [{to_}]")

    for module, deps in efferent_set.items():
        metrics.efferent_count[module] = len(deps)
    for module, deps in afferent_set.items():
        metrics.afferent_count[module] = len(deps)
    for module, count in abstract_count.items():
        metrics.abstractness[module] = count / (
            count + concrete_count.get(module_name, 0)) if count > 0 else 0.0

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

    metrics.efferent_set = efferent_set
    metrics.afferent_set = afferent_set

    return metrics
