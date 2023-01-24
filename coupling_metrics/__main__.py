import argparse
from coupling_metrics.coupling import generate_metrics, CouplingMetrics

HELP_PACKAGE_NAME = """
Name of the root package to analyze where source files can be found.
For example if the project is in /home/user/my_project and 
root_package_name="my_package" then it is expected that the sources will be 
located in "/home/user/my_project/my_package" - only import references inside
the namespace of this package will be analyzed.
"""

HELP_LEVEL = """
Level of grouping to analyze. By default, level < 1 will not do any grouping 
at all, so the analysis will be done up to the individual file module.
This can result in an unreadable report and diagram for big projects.
With level = 2, all modules located 2 or more levels above the root namespace 
will be grouped into the same name. For example "my_package.foo.bar" will
collapse into "my_package.foo".
"""


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_root",
                        help=("Path of the python project to analyze"),
                        required=True)
    parser.add_argument("--package_name",
                        help=HELP_PACKAGE_NAME,
                        required=True)
    parser.add_argument("--level",
                        type=int,
                        default=0,
                        help=HELP_LEVEL)

    args = parser.parse_args()

    metrics = generate_metrics(project_root=args.project_root,
                               package_name=args.package_name,
                               level=args.level)

    def print_sorted_metric(metrics: CouplingMetrics, metric_name: str):
        cumulative = 0
        total_count = 0
        for module, count in (
            sorted([(k, v) for k, v in getattr(metrics, metric_name).items()],
                   key=lambda t: t[1],
                   reverse=True)):
            cumulative += count
            total_count += 1
            print(f'{module} -> {count}')
        if total_count > 0:
            print(f' -> average: {cumulative/total_count:.2f}')

    for reported_metric in (('Afferent coupling', 'afferent_count'),
                            ('Efferent coupling', 'efferent_count'),
                            ('Instability', 'instability'),
                            ('Abstractness', 'abstractness'),
                            ('Distance to main sequence',
                             'distance_to_main_seq')):
        print('------------------')
        print(f'{reported_metric[0]}:')
        print('------------------')

        print_sorted_metric(metrics, reported_metric[1])

    print('------------------')
    print('PlantUML diagram:')
    print('------------------')

    for line in metrics.uml_diagram:
        print(line)
