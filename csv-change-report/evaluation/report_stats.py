"""Optional local CSV Change JSON recipe; no report mutation or dependencies."""
import json
import sys


def statistics(report):
    c = report['counts']
    names = ('before', 'after', 'added', 'removed', 'changed', 'unchanged')
    if any(type(c.get(n)) is not int or c[n] < 0 for n in names):
        raise ValueError('counts must be nonnegative integers')
    if c['before'] != c['removed'] + c['changed'] + c['unchanged']:
        raise ValueError('inconsistent original record counts')
    if c['after'] != c['added'] + c['changed'] + c['unchanged']:
        raise ValueError('inconsistent final record counts')
    def metric(numerator, denominator):
        return {'numerator': numerator, 'denominator': denominator,
                'percent': 100 * numerator / denominator if denominator else None}
    return {
        'original_records_changed_or_removed': metric(c['changed'] + c['removed'], c['before']),
        'final_records_newly_added': metric(c['added'], c['after'])
    }


def render(report):
    stats = statistics(report)
    labels = ('Original records changed or removed', 'Final records newly added')
    lines = []
    for label, value in zip(labels, stats.values()):
        percentage = 'N/A (empty denominator)' if value['percent'] is None else f"{value['percent']:.2f}%"
        lines.append(f"{label}: {value['numerator']}/{value['denominator']} = {percentage}")
    return '\n'.join(lines)


if __name__ == '__main__':
    try:
        with open(sys.argv[1], encoding='utf-8') as source:
            print(render(json.load(source)))
    except (IndexError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Cannot summarize report ({type(exc).__name__}).', file=sys.stderr)
        sys.exit(2)
