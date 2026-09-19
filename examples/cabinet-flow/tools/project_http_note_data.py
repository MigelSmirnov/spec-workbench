"""Project accepted HTTP catalogues into addressable data; never invent semantics.

Run before HTTP note checks. --check is read-only and exits nonzero on drift.
The source route/context/contract catalogues remain authoritative. This utility
is project data projection, not a replacement Workbench phase or runtime emitter.
"""
from pathlib import Path
import argparse
import json


def projection(project: Path) -> dict:
    read = lambda name: json.loads((project / name).read_text())
    errors = read('60_http_errors.json')
    wire = read('70_http_transport_closure.json')
    context = read('70_router_context.json')
    routes = read('70_router_closure.json')['items']
    contracts = read('60_contracts.json')['contracts']
    if wire['status'] != 'closed' or context['status'] != 'closed':
        raise ValueError('HTTP source closures must be closed')
    codes = {row['code'] for row in errors['errors']}
    if len(codes) != len(errors['errors']) or errors['unknown_error'] not in codes:
        raise ValueError('HTTP error codes must be unique with a declared fallback')
    categories = errors['failure_categories']
    if len({row['category'] for row in categories}) != len(categories):
        raise ValueError('HTTP failure categories must be unique')
    if any(row['code'] not in codes for row in categories):
        raise ValueError('HTTP failure category references an undeclared error code')
    by_handler = {row['handler']: row for row in wire['operation_models']}
    if len(by_handler) != len(routes):
        raise ValueError('HTTP operation-model binding count differs from routes')
    for row in routes:
        bound = by_handler[row['handler']]
        if any(bound[k] != row[k] for k in ('handler', 'method', 'path')):
            raise ValueError('HTTP binding drift: ' + row['handler'])
        operation = row['operation'].rsplit('.', 1)[1]
        if bound['operation'] != operation:
            raise ValueError('HTTP operation drift: ' + row['handler'])
        signature = contracts[operation]
        if 'request: ' + bound['request_model'] + ')' not in signature or not signature.endswith(' -> ' + bound['result_model']):
            raise ValueError('HTTP canonical model drift: ' + operation)
    return {
        'operations': [dict(row, success_status=next(route['success_status'] for route in routes if route['handler'] == row['handler'])) for row in wire['operation_models']],
        'errors': errors['errors'],
        'failure_categories': errors['failure_categories'],
        'framing_codes': errors['framing_codes'],
        'unknown_error': errors['unknown_error'],
        'runtime_slot': wire['runtime_slot'],
        'credential_extractor': context['wiring']['credential_extractors']['bearer'],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    target = project / '60_data_closure.json'
    original = target.read_text()
    data = json.loads(original)
    values = projection(project)
    data['sections']['rules']['http_transport'] = values
    data['placements'] = [row for row in data['placements'] if not row['address'].startswith('rules.http_transport.')]
    def place(prefix, value):
        if isinstance(value, dict):
            for key, child in value.items():
                place(prefix + '.' + key, child)
        else:
            data['placements'].append({
                'address': prefix,
                'source_refs': ['decision:A22', '70_http_transport_closure.json', '70_router_context.json', '60_http_errors.json'],
                'reason': 'Deterministic addressable projection of accepted HTTP transport data for Notes; canonical signatures and backend IR remain in their post-contract owners.',
            })
    place('rules.http_transport', values)
    emitted = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if json.loads(original) != data:
            print('HTTP note-data projection is stale. Run without --check.')
            return 1
        print('HTTP note-data projection matches its closed sources.')
        return 0
    target.write_text(emitted)
    print('Projected HTTP note data without changing source catalogues.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
