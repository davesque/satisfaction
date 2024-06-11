from satellite.expr import Var, var, Implies
from satellite.tseitin import Tseitin


def test_tseitin_transform() -> None:
    p, q, r = var("p q r")

    # (r -> p) -> (~(q & r) -> p)
    expr = Implies(Implies(r, p), Implies(~(q & r), p))
    # expr = (p & p) | (q & q)
    tseitin = Tseitin(expr)

    assert (tseitin.equivalences, tseitin.renames, tseitin.root, tseitin.transform()) == (
        set(),
        {},
        Var("a"),
        Var("a"),
    )
