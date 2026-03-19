from satisfaction.expr import Equivalent, Implies, Not, Or, Var, var
from satisfaction.tseitin import Tseitin
from satisfaction.utils import numbered_var


def test_tseitin_default_name_gen() -> None:
    """Tseitin with default name_gen should use letters()."""
    p, q = var("p q")
    tseitin = Tseitin(p | q, rename_vars=False)
    # Root should be a generated variable with a letter name
    assert isinstance(tseitin.root, Var)
    assert tseitin.root.generated


def test_tseitin_rename_vars() -> None:
    """With rename_vars=True, original vars get renamed via lookup."""
    p, q = var("p q")
    tseitin = Tseitin(p | q, rename_vars=True, name_gen=numbered_var("x", 1))
    # p and q should have been renamed
    assert len(tseitin.renames) == 2
    assert p in tseitin.renames
    assert q in tseitin.renames


def test_tseitin_rename_negated_var() -> None:
    """With rename_vars=True, Not(Var) should rename the inner var."""
    (p,) = var("p")
    # ~p as a standalone expression triggers the Not(Var) case
    tseitin = Tseitin(~p, rename_vars=True, name_gen=numbered_var("x", 1))
    assert isinstance(tseitin.root, Not)
    assert p in tseitin.renames


def test_tseitin_lookup_cache() -> None:
    """lookup should return the same renamed var for repeated occurrences."""
    p, q = var("p q")
    # p appears twice in (p | q) & (p | ~q)
    expr = (p | q) & (p | ~q)
    tseitin = Tseitin(expr, rename_vars=True, name_gen=numbered_var("x", 1))
    # p should only have one rename entry despite appearing twice
    assert len(tseitin.renames) == 2  # p and q


def test_tseitin_equiv_to_cnf_implies() -> None:
    """Test equiv_to_cnf with an Implies RHS."""
    p, q, r = var("p q r")
    equiv = Equivalent(p, Implies(q, r))
    result = Tseitin.equiv_to_cnf(equiv)
    # p <-> (q -> r) = (~p | ~q | r) & (q | p) & (~r | p)
    assert result == (~p | ~q | r) & (q | p) & (~r | p)


def test_tseitin_unsorted_transform() -> None:
    """Transform without sort=True should still produce valid CNF."""
    p, q = var("p q")
    tseitin = Tseitin(p | q, rename_vars=False, name_gen=numbered_var("x", 1))
    cnf = tseitin.transform(sort=False)
    assert len(cnf.args) > 0


def test_tseitin_transform() -> None:
    p, q, r = var("p q r")

    # (r -> p) -> (~(q & r) -> p)
    expr = Implies(Implies(r, p), Implies(~(q & r), p))

    tseitin = Tseitin(expr, rename_vars=False, name_gen=numbered_var("x", 1))

    x1, x2, x3, x4, x5 = var("x1 x2 x3 x4 x5", generated=True)

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
