import copy
import json
import math
from functools import lru_cache
from pathlib import Path
import random
import unittest

from routepilot.optimizer import optimize_route

ROOT = Path(__file__).resolve().parents[1]


def matrix(n, value=10):
    return [[0 if i == j else value for j in range(n)] for i in range(n)]


def oracle(start, waypoints, end, t, d, objective):
    """Subset DP, independent of the production permutation enumeration."""
    @lru_cache(None)
    def solve(current, remaining):
        if not remaining:
            return (0, 0, ()) if end is None else (t[current][end], d[current][end], (end,))
        candidates = []
        for nxt in remaining:
            a, b, tail = solve(nxt, tuple(x for x in remaining if x != nxt))
            candidates.append((t[current][nxt] + a, d[current][nxt] + b, (nxt,) + tail))
        return min(candidates, key=lambda x: (x[0], x[1], x[2]) if objective == 'fastest' else (x[1], x[0], x[2]))
    a, b, tail = solve(start, tuple(sorted(waypoints)))
    return a, b, [start, *tail]


class OptimizerTests(unittest.TestCase):
    def test_real_fixed_end(self):
        p = json.loads((ROOT / 'docs/spike-02-evidence/spike-03-input.json').read_text())
        for objective in ('fastest', 'shortest'):
            r = optimize_route(0, [1, 2, 3], 4, p['duration_s'], p['distance_m'], objective)
            self.assertEqual(r['original'], dict(order=[0, 1, 2, 3, 4], total_duration=12138, total_distance=229701))
            self.assertEqual(r['optimized'], dict(order=[0, 2, 1, 3, 4], total_duration=11936, total_distance=219006))
            self.assertEqual(r['savings']['duration'], 202)
            self.assertEqual(r['savings']['distance'], 10695)
            self.assertAlmostEqual(r['savings']['duration_percent'], 202 / 12138 * 100)
            self.assertEqual(r['candidates_evaluated'], 6)

    def test_return_to_start(self):
        t = matrix(4)
        for a, b in [(0, 2), (2, 1), (1, 3), (3, 0)]:
            t[a][b] = 1
        r = optimize_route(0, [1, 2, 3], 0, t, t, 'fastest')
        self.assertEqual(r['optimized']['order'], [0, 2, 1, 3, 0])
        self.assertEqual(r['optimized']['total_duration'], 4)
        self.assertEqual(r['original']['total_duration'], 31)

    def test_directed_open_path_and_objective_tradeoff(self):
        t, d = matrix(4, 50), matrix(4, 50)
        for a, b in [(0, 1), (1, 2), (2, 3)]:
            t[a][b], d[a][b] = 1, 20
        for a, b in [(0, 3), (3, 2), (2, 1)]:
            t[a][b], d[a][b] = 10, 1
        fast = optimize_route(0, [1, 2, 3], None, t, d, 'fastest')
        short = optimize_route(0, [1, 2, 3], None, t, d, 'shortest')
        self.assertEqual(fast['optimized']['order'], [0, 1, 2, 3])
        self.assertEqual(short['optimized']['order'], [0, 3, 2, 1])
        self.assertEqual(short['savings']['duration'], -27)
        self.assertEqual(short['savings']['distance'], 57)

    def test_ties_secondary_then_lexicographic(self):
        t, d = matrix(4, 1), matrix(4, 1)
        r = optimize_route(0, [3, 2, 1], None, t, d, 'fastest')
        self.assertEqual(r['optimized']['order'], [0, 1, 2, 3])
        d[0][1] = 100
        r = optimize_route(0, [3, 2, 1], None, t, d, 'fastest')
        self.assertEqual(r['optimized']['order'], [0, 2, 1, 3])

    def test_zero_costs_and_no_mutation(self):
        t, d, w = matrix(4, 0), matrix(4, 0), [3, 1, 2]
        before = copy.deepcopy((t, d, w))
        r = optimize_route(0, w, None, t, d, 'shortest')
        self.assertIsNone(r['savings']['duration_percent'])
        self.assertEqual(r['savings']['distance'], 0)
        self.assertEqual((t, d, w), before)

    def test_symmetric_matrix(self):
        t = [[abs(i - j) for j in range(5)] for i in range(5)]
        r = optimize_route(0, [3, 1, 2], 4, t, t, 'shortest')
        self.assertEqual(r['optimized']['order'], [0, 1, 2, 3, 4])
        self.assertEqual(r['optimized']['total_distance'], 4)
        self.assertEqual(r['original']['total_distance'], 8)

    def test_random_matrices_against_independent_dp(self):
        rng = random.Random(303)
        for k in range(3, 9):
            n = k + 2
            t = [[0 if i == j else rng.randint(1, 100) for j in range(n)] for i in range(n)]
            d = [[0 if i == j else rng.randint(1, 100) for j in range(n)] for i in range(n)]
            for end in (None, 0, n - 1):
                for objective in ('fastest', 'shortest'):
                    with self.subTest(k=k, end=end, objective=objective):
                        r = optimize_route(0, list(range(1, k + 1)), end, t, d, objective)
                        expected = oracle(0, list(range(1, k + 1)), end, t, d, objective)
                        self.assertEqual((r['optimized']['total_duration'], r['optimized']['total_distance'], r['optimized']['order']), expected)
                        self.assertEqual(r['candidates_evaluated'], math.factorial(k))

    def test_invalid_inputs(self):
        valid = dict(start=0, waypoints=[1, 2, 3], end=4, time_matrix=matrix(5), distance_matrix=matrix(5), objective='fastest')
        overrides = [dict(objective='cheap'), dict(start=True), dict(start=-1), dict(end=5), dict(end=1), dict(waypoints=[1, 1, 2]), dict(waypoints=[0, 1, 2]), dict(waypoints=[1, 2]), dict(waypoints=list(range(1, 10))), dict(waypoints=[1, 2, 3.0]), dict(time_matrix=[]), dict(distance_matrix=matrix(4)), dict(time_matrix=[[0], [1]])]
        for value in (None, float('inf'), float('nan'), -1, '10', True):
            for field in ('time_matrix', 'distance_matrix'):
                m = matrix(5)
                m[1][2] = value
                overrides.append({field: m})
        m = matrix(5)
        m[1][1] = 1
        overrides.append(dict(time_matrix=m))
        for override in overrides:
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    optimize_route(**(valid | override))


if __name__ == '__main__':
    unittest.main()
