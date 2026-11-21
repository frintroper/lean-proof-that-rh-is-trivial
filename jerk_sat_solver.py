"""
jerk_sat_solver.py
Continuous Dynamical 3-SAT Relaxation Solver via 3rd-Order Jerk Feedback.

Demonstrates phase-locking convergence into a valid SAT assignment without
discrete backtracking or DPLL search trees.
"""

import math
import random
from typing import List, Tuple

Clause = Tuple[int, int, int]


class JerkSATSolver:
    """
    Maps a 3-SAT CNF formula onto a continuous dynamical system x in [-1, 1]^n
    stabilized by a 3rd-order feedback term (jerk damping / self-inversion).
    """

    def __init__(self, num_vars: int, clauses: List[Clause], dt: float = 0.04, max_steps: int = 8000):
        self.n = num_vars
        self.clauses = clauses
        self.dt = dt
        self.max_steps = max_steps

    def _clause_violation(self, x: List[float], clause: Clause) -> float:
        """Continuous violation energy C_m(x) in; 0 means clause satisfied."""
        prod = 1.0
        for lit in clause:
            idx = abs(lit) - 1
            sign = 1.0 if lit > 0 else -1.0
            # (1 - sign * x_i) / 2 is 0 when variable matches literal sign
            term = 0.5 * (1.0 - sign * x[idx])
            prod *= max(0.0, min(1.0, term))
        return prod

    def verify(self, assignment: List[int]) -> bool:
        """Verifies a discrete assignment (+1/-1 per variable) against all clauses."""
        for clause in self.clauses:
            satisfied = False
            for lit in clause:
                idx = abs(lit) - 1
                if (lit > 0 and assignment[idx] == 1) or (lit < 0 and assignment[idx] == -1):
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True

    def solve(self, seed: int = 42) -> Tuple[bool, List[int], int]:
        """
        Integrates the 3rd-order jerk-stabilized system until all clauses lock
        into an invariant equilibrium state (energy = 0).
        """
        rng = random.Random(seed)
        # Position (x), velocity (v), acceleration (a)
        x = [rng.uniform(-0.2, 0.2) for _ in range(self.n)]
        v = [0.0] * self.n
        a = [0.0] * self.n

        # Auxiliary clause weights (dynamical memory)
        weights = [1.0] * len(self.clauses)

        for step in range(1, self.max_steps + 1):
            # 1. Check if discrete projection already satisfies all clauses
            discrete = [1 if val >= 0.0 else -1 for val in x]
            if self.verify(discrete):
                return True, discrete, step

            # 2. Compute gradient of continuous SAT potential + bistable well
            grad = [0.0] * self.n
            for m, clause in enumerate(self.clauses):
                c_val = self._clause_violation(x, clause)
                if c_val > 1e-9:
                    weights[m] += 0.05 * c_val
                    for lit in clause:
                        idx = abs(lit) - 1
                        sign = 1.0 if lit > 0 else -1.0
                        denom = max(1e-4, 0.5 * (1.0 - sign * x[idx]))
                        d_c = -0.5 * sign * (c_val / denom)
                        grad[idx] += weights[m] * d_c

            # 3. 3rd-Order Jerk Dynamics:
            # j = -alpha * a - beta * v - grad + self-inverting boundary restore
            alpha = 1.8
            beta = 1.2
            for i in range(self.n):
                # Bistable attractor pushing x_i toward {-1, +1}
                bistable = -0.35 * x[i] * (1.0 - x[i] * x[i])
                force = -grad[i] - bistable

                # Jerk (3rd derivative) couples acceleration, velocity, and force
                jerk = -alpha * a[i] - beta * v[i] + force

                # Symplectic-style integration step
                a[i] += jerk * self.dt
                v[i] += a[i] * self.dt
                x[i] += v[i] * self.dt

                # Soft boundary clamp to [-1, 1]
                if x[i] > 1.0:
                    x[i] = 1.0
                    v[i] *= -0.5
                elif x[i] < -1.0:
                    x[i] = -1.0
                    v[i] *= -0.5

        final_discrete = [1 if val >= 0.0 else -1 for val in x]
        return self.verify(final_discrete), final_discrete, self.max_steps


def generate_planted_3sat(num_vars: int, ratio: float = 4.2, seed: int = 7) -> List[Clause]:
    """Generates a hard critical-ratio (4.2) 3-SAT instance with a known planted solution."""
    rng = random.Random(seed)
    plant = [rng.choice([-1, 1]) for _ in range(num_vars)]
    num_clauses = int(num_vars * ratio)
    clauses: List[Clause] = []

    while len(clauses) < num_clauses:
        vars_idx = rng.sample(range(1, num_vars + 1), 3)
        lits = [v * rng.choice([-1, 1]) for v in vars_idx]
        # Ensure clause is satisfied by planted assignment
        if any((l > 0 and plant[abs(l) - 1] == 1) or (l < 0 and plant[abs(l) - 1] == -1) for l in lits):
            clauses.append((lits[0], lits[1], lits[2]))

    return clauses


if __name__ == "__main__":
    N = 40
    clauses = generate_planted_3sat(num_vars=N, ratio=4.2, seed=42)
    solver = JerkSATSolver(num_vars=N, clauses=clauses)
    solved, assignment, steps = solver.solve(seed=101)

    print(f"3-SAT Instance: {N} variables, {len(clauses)} clauses (critical ratio 4.2)")
    print(f"Solved: {solved} | Relaxation Steps: {steps}")
    assert solved, "Solver failed to converge to a valid SAT assignment."
