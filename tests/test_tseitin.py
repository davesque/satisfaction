from satellite.expr import And, Equivalent, Implies, Or, Var, var
from satellite.tseitin import Tseitin
from satellite.utils import numbered_var


def test_tseitin_transform() -> None:
    p, q, r = var("p q r")

    # (r -> p) -> (~(q & r) -> p)
    expr = Implies(Implies(r, p), Implies(~(q & r), p))

    tseitin = Tseitin(expr, rename_vars=False, name_gen=numbered_var("x", 1))

    x1, x2, x3, x4, x5 = var("x1 x2 x3 x4 x5")

    assert tseitin.root == x1
    assert tseitin.renames == {}

    assert tseitin.equivalences == {
        Equivalent(x1, Implies(x2, x3)),
        Equivalent(x2, Implies(r, p)),
        Equivalent(x3, Implies(x4, p)),
        Equivalent(x4, ~x5),
        Equivalent(x5, q & r),
    }

    assert tseitin.transform(sort=True) == (
        Or(x1)
        # equiv 1
        & (~x1 | ~x2 | x3)
        & (x2 | x1)
        & (~x3 | x1)
        # equiv 2
        & (~x2 | ~r | p)
        & (r | x2)
        & (~p | x2)
        # equiv 3
        & (~x3 | ~x4 | p)
        & (x4 | x3)
        & (~p | x3)
        # equiv 4
        & (~x4 | ~x5)
        & (x5 | x4)
        # equiv 5
        & (~x5 | q)
        & (~x5 | r)
        & (~q | ~r | x5)
    )
