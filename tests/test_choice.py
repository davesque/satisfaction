from satisfaction.choice import first_lit, last_lit, random_lit
from satisfaction.expr import And, Or, var

x, y, z = var("x y z")

cnf = And(Or(x, y), Or(~y, z))


def test_first_lit() -> None:
    assert first_lit(cnf) == x


def test_last_lit() -> None:
    assert last_lit(cnf) == z


def test_random_lit() -> None:
    lit = random_lit(cnf)
    all_lits = {x, y, ~y, z}
    assert lit in all_lits
