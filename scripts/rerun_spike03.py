"""Verify Spike 03 against the authenticated September 14 Spike 02 snapshot."""
import hashlib
import json
import math
from itertools import permutations
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from time import perf_counter_ns

from routepilot import optimize_route

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/spike-02-evidence/supplement-2026-09-14'
OUT = ROOT / 'docs/spike-03-evidence/rerun-2026-09-14'


def load_verified_input():
    p = json.loads((SOURCE / 'assembled-matrix.json').read_text())
    raw = json.loads((SOURCE / 'recovery-probe.json').read_text())
    events = {e['case']: e for e in raw['events']}
    provenance = []
    for i, row in enumerate(p['rows']):
        event = events[f'matrix-row-{i}']
        response = event['response']
        body = json.loads(response['content'][0]['text'])
        assert not response['is_error'] and body['status'] == 0
        assert body['result']['rows'][0]['elements'] == row
        destinations = event['arguments']['to'].split(';')
        assert event['arguments']['from'] == destinations[i]
        assert event['arguments']['to'] == events['matrix-row-0']['arguments']['to']
        provenance.append(dict(case=event['case'], sent_at=event['sent_at'], request_id=body['request_id']))
    assert len(p['rows']) == 5 and all(len(row) == 5 for row in p['rows'])
    assert p['duration_unit'] == 's' and p['distance_unit'] == 'm'
    t = [[0 if i == j else c['duration'] for j, c in enumerate(row)] for i, row in enumerate(p['rows'])]
    d = [[0 if i == j else c['distance'] for j, c in enumerate(row)] for i, row in enumerate(p['rows'])]
    return dict(point_order=p['point_order'], duration_s=t, distance_m=d,
                raw_diagonal=[p['rows'][i][i] for i in range(5)], provenance=provenance,
                normalization='Only diagonal set to zero in memory; all 20 directed edges unchanged.',
                atomic=False)


def enumerate_reference(start, w, end, t, d, objective):
    candidates = []
    for perm in permutations(w):
        order = [start, *perm] + ([] if end is None else [end])
        candidates.append(dict(order=order,
                               total_duration=sum(t[order[i]][order[i+1]] for i in range(len(order)-1)),
                               total_distance=sum(d[order[i]][order[i+1]] for i in range(len(order)-1))))
    fields = ('total_duration', 'total_distance') if objective == 'fastest' else ('total_distance', 'total_duration')
    return sorted(candidates, key=lambda c: (c[fields[0]], c[fields[1]], c['order']))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source_hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in SOURCE.glob('*.json')}
    p = load_verified_input()
    t, d = p['duration_s'], p['distance_m']
    cases = []
    for name, start, w, end in [
        ('real_five_fixed_end', 0, [2, 3, 1], 4),
        ('real_three_waypoints_open', 0, [3, 2, 1], None),
        ('real_five_open', 0, [2, 3, 1, 4], None),
        ('real_reverse_fixed_end', 4, [1, 3, 2], 0),
        ('real_return_to_start', 0, [3, 2, 1], 0),
    ]:
        for objective in ('fastest', 'shortest'):
            result = optimize_route(start, w, end, t, d, objective)
            candidates = enumerate_reference(start, w, end, t, d, objective)
            assert result['optimized'] == candidates[0]
            assert result['candidates_evaluated'] == math.factorial(len(w))
            cases.append(dict(name=name, start=start, waypoints=w, end=end, result=result, all_candidates=candidates))
    # Three total locations is below the V1 3-waypoint input floor. Enumerate its
    # two legal orders separately as a transparent arithmetic sanity check.
    small = {o: enumerate_reference(0, [1, 2], None, t, d, o) for o in ('fastest', 'shortest')}
    bench = []
    rng = random.Random(303)
    for k in (3, 5, 8):
        n = k + 2
        bt = t if k == 3 else [[0 if i == j else rng.randint(1, 10000) for j in range(n)] for i in range(n)]
        bd = d if k == 3 else [[0 if i == j else rng.randint(1, 100000) for j in range(n)] for i in range(n)]
        for objective in ('fastest', 'shortest'):
            args = (0, list(range(1, k + 1)), n-1, bt, bd, objective)
            optimize_route(*args)
            samples = []
            for _ in range(30):
                begin = perf_counter_ns()
                r = optimize_route(*args)
                samples.append((perf_counter_ns() - begin)/1e6)
            assert r['candidates_evaluated'] == math.factorial(k)
            bench.append(dict(waypoints=k, total_points=n, objective=objective,
                              source='real Spike 02' if k == 3 else 'synthetic performance only, seed 303',
                              duration_s=bt, distance_m=bd, candidates=math.factorial(k), samples_ms=samples,
                              median_ms=statistics.median(samples), p95_ms=sorted(samples)[28],
                              min_ms=min(samples), max_ms=max(samples)))
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT, capture_output=True, text=True)
    (OUT / 'unit-tests.txt').write_text(tests.stdout + tests.stderr)
    assert tests.returncode == 0, tests.stderr
    assert all(hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == digest for name, digest in source_hashes.items())
    result = dict(status='PASS', generated_at=datetime.now(timezone.utc).isoformat(),
                  python=sys.version, platform=platform.platform(), source_hashes=source_hashes,
                  input=p, cases=cases, three_total_points_reference_only=small,
                  benchmarks=bench, benchmark_protocol='1 warmup + 30 samples; full function; no IO/network; fixed distinct end; nearest-rank P95',
                  unit_test_exit_code=tests.returncode,
                  code_hashes={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                               ('routepilot/optimizer.py', 'scripts/rerun_spike03.py', 'tests/test_optimizer.py', 'tests/test_spike03_supplement.py')})
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    for c in cases[:2]:
        print(json.dumps(c['result'], ensure_ascii=False))
    for b in bench:
        print(f"k={b['waypoints']} {b['objective']} median={b['median_ms']:.3f}ms p95={b['p95_ms']:.3f}ms")


if __name__ == '__main__':
    main()
