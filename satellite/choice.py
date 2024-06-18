from collections import defaultdict
import random

from satellite.expr import CNF, Connective, Expr, Lit, Not, Var


def count_lits(expr: Expr, counter: dict[Var, int]) -> None:
    match expr:
        case Var(_):
            # if name.startswith("x"):
            counter[expr] += 1
        case Not(p):
            count_lits(p, counter)
        case Connective(args):
            for arg in args:
                count_lits(arg, counter)


def common_lit(expr: CNF) -> Lit:
    counter = defaultdict(lambda: 0)
    count_lits(expr, counter)

    counts = sorted(counter.items(), key=lambda i: i[1], reverse=True)
    return counts[0][0]


def first_lit(expr: CNF) -> Lit:
    or_expr = expr.args[0]
    return or_expr.args[0]


def last_lit(expr: CNF) -> Lit:
    or_expr = expr.args[-1]
    return or_expr.args[-1]


def random_lit(expr: CNF) -> Lit:
    or_expr = random.choice(expr.args)
    lit = random.choice(or_expr.args)
    return lit
