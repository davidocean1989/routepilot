"""Exact directed route ordering for 3–8 waypoints, using only the stdlib."""

from itertools import permutations
from math import isfinite
from typing import Sequence, TypedDict

Number = int | float


class RouteTotals(TypedDict):
    order: list[int]
    total_duration: Number
    total_distance: Number


class Savings(TypedDict):
    duration: Number
    distance: Number
    duration_percent: float | None
    distance_percent: float | None


class OptimizationResult(TypedDict):
    objective: str
    original: RouteTotals
    optimized: RouteTotals
    savings: Savings
    candidates_evaluated: int


def _validate_matrix(matrix, size, name):
    if not isinstance(matrix, (list, tuple)) or len(matrix) != size or size == 0:
        raise ValueError(f'{name} must be a nonempty square matrix matching time_matrix')
    for i, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)) or len(row) != size:
            raise ValueError(f'{name}[{i}] must contain {size} entries')
        for j, value in enumerate(row):
            # Restrict to JSON-native numbers; bool is not a cost.
            if type(value) not in (int, float) or value < 0:
                raise ValueError(f'{name}[{i}][{j}] must be a finite nonnegative number')
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f'{name}[{i}][{j}] must be finite; missing/unreachable edges are unsupported')
            if i == j and value != 0:
                raise ValueError(f'{name} diagonal must be normalized to zero')


def optimize_route(
    start: int,
    waypoints: Sequence[int],
    end: int | None,
    time_matrix: Sequence[Sequence[Number]],
    distance_matrix: Sequence[Sequence[Number]],
    objective: str = 'fastest',
) -> OptimizationResult:
    """Return baseline, exact optimum and signed savings for one static snapshot.

    Indices address the same row/column order in both complete directed matrices.
    Costs are seconds and meters. end=None is open; end=start returns to start.
    There must be 3–8 distinct waypoints excluding start/end. Accept lists/tuples.
    Ties use the other metric, then lexicographically ascending index order.
    Invalid/incomplete inputs raise ValueError. Inputs are never modified.
    """
    if objective not in ('fastest', 'shortest'):
        raise ValueError('objective must be fastest or shortest')
    if not isinstance(time_matrix, (list, tuple)):
        raise ValueError('time_matrix must be a list or tuple of rows')
    size = len(time_matrix)
    _validate_matrix(time_matrix, size, 'time_matrix')
    _validate_matrix(distance_matrix, size, 'distance_matrix')
    if not isinstance(waypoints, (list, tuple)) or not 3 <= len(waypoints) <= 8:
        raise ValueError('waypoints must contain 3–8 indices')
    middle = tuple(waypoints)
    indices = (start,) + middle + (() if end is None else (end,))
    if any(type(i) is not int or not 0 <= i < size for i in indices):
        raise ValueError('all stop indices must be integers within the matrix')
    if len(set(middle)) != len(middle) or start in middle or end in middle:
        raise ValueError('waypoints must be unique and exclude start/end')

    def totals(order):
        duration, distance = 0, 0
        try:
            for a, b in zip(order, order[1:]):
                duration += time_matrix[a][b]
                distance += distance_matrix[a][b]
            if any(isinstance(v, float) and not isfinite(v) for v in (duration, distance)):
                raise ValueError('route costs overflow floating-point range')
        except OverflowError as exc:
            raise ValueError('route costs overflow floating-point range') from exc
        return duration, distance

    suffix = () if end is None else (end,)
    original_order = (start,) + middle + suffix
    original_time, original_distance = totals(original_order)
    best_key = None
    count = 0
    for perm in permutations(middle):
        order = (start,) + perm + suffix
        duration, distance = totals(order)
        key = (duration, distance, order) if objective == 'fastest' else (distance, duration, order)
        count += 1
        if best_key is None or key < best_key:
            best_key = key
            best_order, best_time, best_distance = order, duration, distance

    saved_time = original_time - best_time
    saved_distance = original_distance - best_distance
    return {
        'objective': objective,
        'original': dict(order=list(original_order), total_duration=original_time, total_distance=original_distance),
        'optimized': dict(order=list(best_order), total_duration=best_time, total_distance=best_distance),
        'savings': dict(duration=saved_time, distance=saved_distance,
                        duration_percent=None if original_time == 0 else saved_time / original_time * 100,
                        distance_percent=None if original_distance == 0 else saved_distance / original_distance * 100),
        'candidates_evaluated': count,
    }
