from jerk_sat_solver import JerkSATSolver, generate_planted_3sat


def test_critical_3sat_instances():
    for n, seed in [(20, 1), (30, 2), (40, 42)]:
        clauses = generate_planted_3sat(num_vars=n, ratio=4.2, seed=seed)
        solver = JerkSATSolver(num_vars=n, clauses=clauses, max_steps=10000)
        solved, assignment, steps = solver.solve(seed=seed + 10)
        assert solved, f"Failed on n={n}, seed={seed}"
        assert solver.verify(assignment)


if __name__ == "__main__":
    test_critical_3sat_instances()
    print("All critical 3-SAT relaxation tests passed.")
