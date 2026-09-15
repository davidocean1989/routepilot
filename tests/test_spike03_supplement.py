import unittest

from routepilot import optimize_route
from scripts.rerun_spike03 import load_verified_input
from test_optimizer import oracle


class SupplementTests(unittest.TestCase):
    def test_raw_provenance_and_directed_edges(self):
        p = load_verified_input()
        self.assertEqual(len(p['provenance']), 5)
        self.assertEqual(p['distance_m'][0][1], 84284)
        self.assertEqual(p['distance_m'][1][0], 82537)
        self.assertEqual(p['duration_s'][0][1], 4694)
        self.assertEqual(p['duration_s'][1][0], 5215)

    def test_real_five_point_results_and_dp(self):
        p = load_verified_input()
        t, d = p['duration_s'], p['distance_m']
        expected = {'fastest': ([0, 1, 2, 3, 4], 12954, 229985),
                    'shortest': ([0, 2, 1, 3, 4], 13233, 219289)}
        for o, (order, duration, distance) in expected.items():
            with self.subTest(objective=o):
                r = optimize_route(0, [2, 3, 1], 4, t, d, o)
                self.assertEqual(r['original'], dict(order=[0, 2, 3, 1, 4], total_duration=15912, total_distance=293861))
                self.assertEqual(r['optimized'], dict(order=order, total_duration=duration, total_distance=distance))
                self.assertAlmostEqual(r['savings']['duration_percent'], (15912-duration)/15912*100)
                self.assertAlmostEqual(r['savings']['distance_percent'], (293861-distance)/293861*100)
                self.assertEqual(oracle(0, [2, 3, 1], 4, t, d, o), (duration, distance, order))

    def test_real_optional_end_and_asymmetric_reverse(self):
        p = load_verified_input()
        t, d = p['duration_s'], p['distance_m']
        for start, w, end in [(0, [3, 2, 1], None), (0, [3, 2, 1], 0), (4, [1, 3, 2], 0)]:
            for o in ('fastest', 'shortest'):
                r = optimize_route(start, w, end, t, d, o)['optimized']
                self.assertEqual((r['total_duration'], r['total_distance'], r['order']), oracle(start, w, end, t, d, o))
