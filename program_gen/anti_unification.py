"""
Anti-unification for abstracting pair-specific programs.

Pair-specific programs (generated per example pair in the solve process) are
generalized into a single parameterized program using anti-unification, i.e.
computing a least general generalization (LGG) of two program representations.

N개 프로그램(3개 이상)일 때:
  - 결과는 항상 1개. 두 개씩 반복 LGG: LGG(LGG(prog0, prog1), prog2), ...
  - compare가 두 대상을 비교하는 것처럼, anti-unify도 기본은 두 항(두 프로그램)의
    LGG이지만, N개는 이진 LGG를 순차 적용해 하나의 추상 프로그램으로 합침.

Usage:
  from program_gen.anti_unification import anti_unify_programs, load_pair_programs
  programs = load_pair_programs(task_hex_code, level="GRID")
  abstract, substs = anti_unify_programs(programs)  # abstract는 1개
"""

from typing import List, Tuple, Any, Optional
import os
import ast
import re
import json


# ---------------------------------------------------------------------------
# Program representation (term-like for anti-unification)
# ---------------------------------------------------------------------------

def program_lines_to_terms(lines: List[str]) -> List[Any]:
    """
    Convert a list of program source lines into a term representation
    suitable for anti-unification (e.g. DSL call terms with arguments).

    Each line is parsed into a simple structure:
    - assignment: ("assign", lhs, rhs_term)
    - DSL call: ("apply_DSL", var, op_name, args_dict)  # parsed from apply_DSL(...)
    - other: ("raw", line)
    """
    terms = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Match: tfgN = apply_DSL(main_grid=tfgM, func=op, key=val, ...)  (all kwargs)
        m_kw = re.match(r"(\w+)\s*=\s*apply_DSL\s*\((.*)\)\s*$", stripped)
        if m_kw:
            lhs, inner = m_kw.groups()
            parsed = _parse_apply_dsl_args(inner.strip())
            if "main_grid" in parsed and "func" in parsed:
                in_var = parsed.pop("main_grid")
                op_name = parsed.pop("func")
                terms.append(("apply_DSL", lhs, in_var, op_name, parsed))
                continue
            # Fall back to positional form: apply_DSL(tfgM, op, key=val, ...)
            parts = inner.split(", ", 2)
            if len(parts) >= 2 and "=" not in parts[0].strip() and "=" not in parts[1].strip():
                in_var = parts[0].strip()
                op_name = parts[1].strip()
                rest = parts[2].strip() if len(parts) > 2 else ""
                args = _parse_apply_dsl_args(rest)
                terms.append(("apply_DSL", lhs, in_var, op_name, args))
                continue
        # Match: tfgN = apply_DSL(tfgM, op, key=val, ...)  (positional grid, func)
        m = re.match(r"(\w+)\s*=\s*apply_DSL\s*\(\s*(\w+)\s*,\s*(\w+)\s*,(.*)\)\s*$", stripped)
        if m:
            lhs, in_var, op_name, args_str = m.groups()
            args = _parse_apply_dsl_args(args_str.strip())
            terms.append(("apply_DSL", lhs, in_var, op_name, args))
            continue
        # Match: tfg0 = input_grid / output_grid = tfgN / return output_grid
        if re.match(r"(\w+)\s*=\s*input_grid\s*$", stripped):
            terms.append(("assign", stripped.split("=")[0].strip(), ("input",)))
            continue
        if re.match(r"output_grid\s*=\s*(\w+)\s*$", stripped):
            terms.append(("assign", "output_grid", ("var", stripped.split("=")[1].strip())))
            continue
        if stripped == "return output_grid":
            terms.append(("return", "output_grid"))
            continue
        # Boilerplate: added_color = [] etc.
        terms.append(("raw", line))
    return terms


def _parse_apply_dsl_args(args_str: str) -> dict:
    """Parse keyword arguments from apply_DSL(..., key=val, key2=val2)."""
    if not args_str.strip():
        return {}
    args = {}
    for part in re.split(r",\s*(?=[a-zA-Z_][a-zA-Z0-9_]*\s*=)", args_str):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            args[k.strip()] = v.strip()
    return args


_VAR_PATTERN = re.compile(r"\?v\d+")


def _py_var_name(gen_var: str) -> str:
    """?v1 -> v1 (valid Python identifier)."""
    return gen_var[1:] if gen_var.startswith("?") else gen_var


def _slot_to_str(x: Any) -> str:
    """Normalize a term slot to final Python name (e.g. for LHS). Handles (var,) and ('var', x)."""
    if x is None:
        return "None"
    if isinstance(x, str):
        return _py_var_name(x) if x.startswith("?") else x
    if isinstance(x, tuple):
        if len(x) == 1 and isinstance(x[0], str) and x[0].startswith("?"):
            return _py_var_name(x[0])
        if len(x) == 2 and x[0] == "var":
            return _slot_to_str(x[1])
    return str(x)


def _slot_to_line_str(x: Any) -> str:
    """String to embed in line so that ?vN is kept for ensure_declared_and_replace to find and declare."""
    if x is None:
        return "None"
    if isinstance(x, str):
        return x
    if isinstance(x, tuple):
        if len(x) == 1 and isinstance(x[0], str) and x[0].startswith("?"):
            return x[0]
        if len(x) == 2 and x[0] == "var":
            return _slot_to_line_str(x[1])
    return str(x)


def _is_whole_term(t: Any) -> bool:
    """True if t is a term tuple (apply_DSL, assign, return), not a (t1,t2) substitution pair."""
    if not isinstance(t, tuple) or len(t) < 1:
        return False
    if t[0] in ("apply_DSL", "assign", "return", "raw"):
        return True
    return False


def _term_to_line(t: Any, default_subst: dict, declared: set, lines: List[str]) -> None:
    """Emit one executable line for a concrete term t; append to lines. Uses default_subst/declared for ?v in args."""
    def ensure_declared_and_replace(line: str) -> str:
        nonlocal declared
        found = _VAR_PATTERN.findall(line)
        out = line
        for var in set(found):
            py_name = _py_var_name(var)
            if py_name not in declared:
                default_val = default_subst.get(var, "None")
                if isinstance(default_val, tuple) and len(default_val) == 2 and not _is_whole_term(default_val[0]) and not _is_whole_term(default_val[1]):
                    default_val = default_val[0] if default_val[0] is not None else default_val[1]
                elif isinstance(default_val, tuple) and _is_whole_term(default_val[0]):
                    default_val = default_val[0]
                elif isinstance(default_val, tuple) and len(default_val) >= 1 and _is_whole_term(default_val[0]):
                    default_val = default_val[0]
                elif isinstance(default_val, tuple) and len(default_val) == 2:
                    default_val = default_val[0] if default_val[0] is not None else default_val[1]
                if not isinstance(default_val, str) and not _is_whole_term(default_val):
                    default_val = repr(default_val) if default_val is not None else "None"
                if _is_whole_term(default_val):
                    default_val = "None"
                lines.append(f"    {py_name} = {default_val}  # generalized (instantiate per pair)")
                declared.add(py_name)
            out = out.replace(var, py_name)
        return out

    if not isinstance(t, tuple):
        return
    if t[0] == "raw":
        lines.append(t[1])
        return
    if t[0] == "assign":
        _, lhs, rhs = t
        lhs_str = _slot_to_str(lhs)
        if isinstance(rhs, tuple) and rhs[0] == "input":
            lines.append(f"    {lhs_str} = input_grid")
        else:
            line = f"    {lhs_str} = {_slot_to_line_str(rhs)}"
            lines.append(ensure_declared_and_replace(line))
        return
    if t[0] == "return":
        lines.append("    return output_grid")
        return
    if t[0] == "apply_DSL":
        _, lhs, in_var, op_name, args = t
        lhs_str = _slot_to_str(lhs)
        in_str = _slot_to_line_str(in_var)
        op_str = _slot_to_line_str(op_name) if not isinstance(op_name, str) else op_name
        args_str = ", ".join(f"{k}={_slot_to_line_str(v)}" for k, v in args.items())
        line = f"    {lhs_str} = apply_DSL(main_grid={in_str}, func={op_str}, {args_str})"
        lines.append(ensure_declared_and_replace(line))
        return


def terms_to_program_lines(
    terms: List[Any],
    default_subst: Optional[dict] = None,
) -> List[str]:
    """
    Convert term representation back to program source lines.
    Generalized variables (?v1, ?v2, ...) are turned into Python names (v1, v2, ...)
    and a declaration line is inserted right above the first use so the code is runnable.
    When a term is (var,) and default_subst[var] holds a concrete term (or (t1,t2)), we emit
    that concrete term as executable code so the abstract program runs instead of only variable declarations.
    default_subst: optional dict mapping "?v1" -> "[(0,0)]" or "?v1" -> (t1, t2) for whole-term vars.
    """
    default_subst = default_subst or {}
    declared: set = set()
    lines = []

    def ensure_declared_and_replace(line: str, defining_names: Optional[set] = None) -> str:
        """Insert declaration lines above (into `lines`) for any ?vN in line; skip names in defining_names (e.g. LHS). Return line with ?vN -> vN."""
        nonlocal declared
        defining_names = defining_names or set()
        found = _VAR_PATTERN.findall(line)
        out = line
        for var in set(found):
            py_name = _py_var_name(var)
            if py_name not in declared and py_name not in defining_names:
                default_val = default_subst.get(var, "None")
                if isinstance(default_val, tuple) and len(default_val) == 2 and not _is_whole_term(default_val[0]) and not _is_whole_term(default_val[1]):
                    default_val = default_val[0] if default_val[0] is not None else default_val[1]
                elif isinstance(default_val, tuple) and len(default_val) >= 1 and _is_whole_term(default_val[0]):
                    default_val = default_val[0]
                elif isinstance(default_val, tuple) and len(default_val) == 2:
                    default_val = default_val[0] if default_val[0] is not None else default_val[1]
                if not isinstance(default_val, str) and not _is_whole_term(default_val):
                    default_val = repr(default_val) if default_val is not None else "None"
                if _is_whole_term(default_val):
                    default_val = "None"
                lines.append(f"    {py_name} = {default_val}  # generalized (instantiate per pair)")
                declared.add(py_name)
            out = out.replace(var, py_name)
        return out

    for t in terms:
        if not isinstance(t, tuple):
            lines.append(f"    # {t}")
            continue
        if t[0] == "raw":
            lines.append(t[1])
            continue
        if len(t) == 1 and isinstance(t[0], str) and t[0].startswith("?"):
            var = t[0]
            default_val = default_subst.get(var)
            concrete = None
            if isinstance(default_val, tuple) and len(default_val) == 2:
                concrete = default_val[0] if default_val[0] is not None else default_val[1]
            elif _is_whole_term(default_val):
                concrete = default_val
            if concrete is not None and _is_whole_term(concrete):
                _term_to_line(concrete, default_subst, declared, lines)
                continue
            py_name = _py_var_name(var)
            if py_name not in declared:
                default_val = default_subst.get(var, "None")
                if isinstance(default_val, tuple):
                    default_val = default_val[0] if default_val[0] is not None else default_val[1]
                if not isinstance(default_val, str):
                    default_val = repr(default_val) if default_val is not None else "None"
                lines.append(f"    {py_name} = {default_val}  # generalized (instantiate per pair)")
                declared.add(py_name)
            continue
        if t[0] == "assign":
            _, lhs, rhs = t
            lhs_str = _slot_to_str(lhs)
            if isinstance(rhs, tuple) and rhs[0] == "input":
                lines.append(f"    {lhs_str} = input_grid")
            else:
                line = f"    {lhs_str} = {_slot_to_line_str(rhs)}"
                lines.append(ensure_declared_and_replace(line, defining_names={lhs_str}))
            declared.add(lhs_str)
            continue
        if t[0] == "return":
            lines.append("    return output_grid")
            continue
        if t[0] == "apply_DSL":
            _, lhs, in_var, op_name, args = t
            lhs_str = _slot_to_str(lhs)
            in_str = _slot_to_line_str(in_var)
            op_str = _slot_to_line_str(op_name) if not isinstance(op_name, str) else op_name
            args_str = ", ".join(f"{k}={_slot_to_line_str(v)}" for k, v in args.items())
            line = f"    {lhs_str} = apply_DSL(main_grid={in_str}, func={op_str}, {args_str})"
            lines.append(ensure_declared_and_replace(line, defining_names={lhs_str}))
            declared.add(lhs_str)
            continue
        lines.append(f"    # {t}")
    return lines


# ---------------------------------------------------------------------------
# Anti-unification (LGG)
# ---------------------------------------------------------------------------

def anti_unify_terms(t1: Any, t2: Any) -> Tuple[Any, dict]:
    """
    Anti-unify two terms. Returns (generalized_term, substitution_map).

    Substitution map maps variable names to the concrete values they replaced.
    The generalized term may contain variables (e.g. ("var", "?x")) where t1 and t2 differed.
    """
    if t1 == t2:
        return t1, {}

    if isinstance(t1, tuple) and isinstance(t2, tuple):
        if t1[0] != t2[0]:
            # Introduce variable for differing root
            var = _fresh_var()
            return (var,), {var: (t1, t2)}
        if t1[0] in ("raw", "return"):
            return t1, {} if t1 == t2 else ((_fresh_var(),), {_fresh_var(): (t1, t2)})
        if t1[0] == "assign":
            _, lhs1, rhs1 = t1
            _, lhs2, rhs2 = t2
            gen_lhs, s1 = anti_unify_terms(lhs1, lhs2) if lhs1 != lhs2 else (lhs1, {})
            gen_rhs, s2 = anti_unify_terms(rhs1, rhs2)
            return ("assign", gen_lhs, gen_rhs), {**s1, **s2}
        if t1[0] == "apply_DSL":
            _, lhs1, v1, op1, args1 = t1
            _, lhs2, v2, op2, args2 = t2
            if op1 != op2:
                var = _fresh_var()
                return (var,), {var: (t1, t2)}
            gen_lhs, s_l = anti_unify_terms(lhs1, lhs2) if lhs1 != lhs2 else (lhs1, {})
            gen_v, s_v = anti_unify_terms(v1, v2) if v1 != v2 else (v1, {})
            gen_args = {}
            all_keys = set(args1) | set(args2)
            for k in all_keys:
                a1, a2 = args1.get(k), args2.get(k)
                if a1 is None or a2 is None or a1 != a2:
                    v = _fresh_var()
                    gen_args[k] = v
                    s_v[v] = (a1, a2)
                else:
                    gen_args[k] = a1
            return ("apply_DSL", gen_lhs, gen_v, op1, gen_args), {**s_l, **s_v}
        # default: same structure, recurse
        if len(t1) != len(t2):
            var = _fresh_var()
            return (var,), {var: (t1, t2)}
        out = []
        subst = {}
        for a, b in zip(t1, t2):
            g, s = anti_unify_terms(a, b)
            out.append(g)
            subst.update(s)
        return tuple(out), subst

    # scalar or different types: generalize to variable
    var = _fresh_var()
    return (var,), {var: (t1, t2)}


_var_counter = 0


def _fresh_var() -> str:
    global _var_counter
    _var_counter += 1
    return f"?v{_var_counter}"


def _is_structure(gen: Any) -> bool:
    """True if gen is a proper term (assign, apply_DSL, return, raw), not a single variable (var,)."""
    if not isinstance(gen, tuple) or len(gen) < 1:
        return False
    if len(gen) == 1 and isinstance(gen[0], str) and gen[0].startswith("?"):
        return False
    return gen[0] in ("assign", "apply_DSL", "return", "raw")


_CONTEXT_FUNC_RE = re.compile(r"func\s*=\s*(\w+)")


def load_context_for_pairs(
    task_hex_code: str,
    level: str,
    pair_indices: List[int],
    base_output_dir: str = "outputs/generated_codes",
) -> List[Optional[dict]]:
    """Load .context.json for each pair. Returns list of context dict or None if missing."""
    out = []
    for idx in pair_indices:
        path = os.path.join(
            base_output_dir, task_hex_code, level,
            f"{task_hex_code}_{idx}_{level.lower()}.context.json",
        )
        if os.path.isfile(path):
            try:
                with open(path) as f:
                    out.append(json.load(f))
            except Exception:
                out.append(None)
        else:
            out.append(None)
    return out


def term_list_to_func_names(terms: List[Any], context: Optional[dict]) -> List[Optional[str]]:
    """
    Map each term index to the DSL func name when the term is apply_DSL, else None.
    Uses context.steps[].line_ref to get func= value (in order of apply_DSL terms).
    """
    result: List[Optional[str]] = [None] * len(terms)
    if not context or "steps" not in context:
        return result
    steps = context["steps"]
    step_idx = 0
    for i, t in enumerate(terms):
        if isinstance(t, tuple) and len(t) >= 1 and t[0] == "apply_DSL":
            if step_idx < len(steps):
                line_ref = steps[step_idx].get("line_ref") or ""
                m = _CONTEXT_FUNC_RE.search(line_ref)
                if m:
                    result[i] = m.group(1)
                step_idx += 1
            else:
                result[i] = t[2] if len(t) > 2 else None
        else:
            result[i] = None
    return result


def _align_term_lists_dp(
    terms1: List[Any],
    terms2: List[Any],
    term1_funcs: Optional[List[Optional[str]]] = None,
    term2_funcs: Optional[List[Optional[str]]] = None,
) -> Tuple[List[Any], dict]:
    """
    Align two term lists so that terms with the same structure are paired (LGG), maximizing
    common structure. When term1_funcs/term2_funcs are provided (from context), same-func
    matches get a bonus so alignment prefers pairing e.g. coloring with coloring.
    Returns (aligned_abstract_terms, subst).
    """
    n, m = len(terms1), len(terms2)
    dp: List[List[Tuple[int, Optional[Tuple[int, int]], Any, dict]]] = [
        [(0, None, None, {}) for _ in range(m + 1)] for _ in range(n + 1)
    ]

    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            best_score = -1
            best_prev = None
            best_term = None
            best_subst = {}

            if i > 0 and j > 0:
                t1, t2 = terms1[i - 1], terms2[j - 1]
                gen, s = anti_unify_terms(t1, t2)
                score_inc = 1 if _is_structure(gen) else 0
                if term1_funcs and term2_funcs and i - 1 < len(term1_funcs) and j - 1 < len(term2_funcs):
                    f1, f2 = term1_funcs[i - 1], term2_funcs[j - 1]
                    if f1 is not None and f2 is not None and f1 == f2:
                        score_inc += 1
                prev_score = dp[i - 1][j - 1][0]
                cand = prev_score + score_inc
                if cand > best_score:
                    best_score = cand
                    best_prev = (i - 1, j - 1)
                    best_term = gen
                    best_subst = s

            if i > 0:
                prev_score = dp[i - 1][j][0]
                if prev_score > best_score:
                    var = _fresh_var()
                    best_score = prev_score
                    best_prev = (i - 1, j)
                    best_term = (var,)
                    best_subst = {var: (terms1[i - 1], None)}

            if j > 0:
                prev_score = dp[i][j - 1][0]
                if prev_score > best_score:
                    var = _fresh_var()
                    best_score = prev_score
                    best_prev = (i, j - 1)
                    best_term = (var,)
                    best_subst = {var: (None, terms2[j - 1])}

            dp[i][j] = (best_score, best_prev, best_term, best_subst)

    out_terms: List[Any] = []
    subst: dict = {}
    i, j = n, m
    while (i, j) != (0, 0):
        _, prev, term, subst_add = dp[i][j]
        if prev is None:
            break
        out_terms.insert(0, term)
        subst.update(subst_add)
        i, j = prev

    return out_terms, subst


def anti_unify_term_lists(
    terms1: List[Any],
    terms2: List[Any],
    term1_funcs: Optional[List[Optional[str]]] = None,
    term2_funcs: Optional[List[Optional[str]]] = None,
) -> Tuple[List[Any], dict]:
    """
    Anti-unify two lists of terms. Uses structure-preserving alignment (DP).
    When term1_funcs/term2_funcs are provided (from context), same-func steps get a match bonus.
    """
    return _align_term_lists_dp(terms1, terms2, term1_funcs, term2_funcs)


# ---------------------------------------------------------------------------
# High-level: abstract pair-specific programs
# ---------------------------------------------------------------------------

def anti_unify_programs(
    program_sources: List[List[str]],
    task_hex_code: Optional[str] = None,
    pair_indices: Optional[List[int]] = None,
    level: Optional[str] = None,
    base_output_dir: str = "outputs/generated_codes",
) -> Tuple[List[str], List[dict]]:
    """
    Anti-unify multiple pair-specific programs into one abstract program.

    - 2개: LGG(prog0, prog1) → 추상 프로그램 1개.
    - 3개 이상: 순차 이진 LGG로 하나로 합침.
    - task_hex_code + level이 있으면 해당 .context.json을 로드해, 같은 func끼리 우선 매칭 (context 활용).
    - task_hex_code가 주어지면, 일반화 변수(?vN)에 대해 ARCKG를 탐색해 DSL 식으로 표현.

    Args:
        program_sources: List of programs, each a list of source lines.
        task_hex_code: If set, resolve variables via ARCKG and load context when level is set.
        pair_indices: Pair indices for ARCKG/context lookup; default [0,1,...,n-1].
        level: If set with task_hex_code, load context for this level to guide alignment.
        base_output_dir: Where to find .context.json files.

    Returns:
        (abstract_program_lines, list_of_substitutions).
    """
    if not program_sources:
        return [], []
    if len(program_sources) == 1:
        return program_sources[0], [{}]

    global _var_counter
    _var_counter = 0

    term_lists = [program_lines_to_terms(p) for p in program_sources]
    if pair_indices is None:
        pair_indices = list(range(len(program_sources)))

    context_list = []
    term_funcs_list = [None] * len(term_lists)
    if task_hex_code and level:
        context_list = load_context_for_pairs(task_hex_code, level, pair_indices, base_output_dir)
        for k, ctx in enumerate(context_list):
            if k < len(term_lists) and ctx is not None:
                term_funcs_list[k] = term_list_to_func_names(term_lists[k], ctx)

    abstract_terms = term_lists[0]
    all_subst = [{} for _ in program_sources]

    for i in range(1, len(term_lists)):
        term1_funcs = term_funcs_list[0] if len(term_funcs_list) > 0 else None
        term2_funcs = term_funcs_list[i] if i < len(term_funcs_list) else None
        if i == 1:
            abstract_terms, subst = anti_unify_term_lists(
                abstract_terms, term_lists[i], term1_funcs, term2_funcs
            )
        else:
            abstract_terms, subst = anti_unify_term_lists(abstract_terms, term_lists[i])
        all_subst[0] = {**all_subst[0], **subst}
        all_subst[i] = subst

    if task_hex_code:
        from program_gen.value_from_arckg import expression_subst_from_arckg
        if pair_indices is None:
            pair_indices = list(range(len(program_sources)))
        default_subst = expression_subst_from_arckg(task_hex_code, all_subst, pair_indices)
    else:
        default_subst = {}
        for k, v in all_subst[0].items():
            if isinstance(v, tuple) and len(v) >= 2:
                first = v[0] if v[0] is not None else v[1]
                if _is_whole_term(first):
                    default_subst[k] = v
                else:
                    default_subst[k] = first if isinstance(first, str) else "None"
            elif v is not None:
                default_subst[k] = v if isinstance(v, str) else "None"

    lines = terms_to_program_lines(abstract_terms, default_subst=default_subst)

    # Prepend value_dsl import when output uses ARCKG expressions
    if task_hex_code and any(
        "object_at_input(" in line or "left_top_of(" in line or "color_of(" in line
        or "center_of(" in line or "coords_of(" in line or "selection_left_top_of(" in line
        for line in lines
    ):
        import_line = "from program_gen.value_dsl import object_at_input, left_top_of, selection_left_top_of, center_of, coords_of, color_of"
        if lines and not lines[0].strip().startswith("from program_gen.value_dsl"):
            lines.insert(0, import_line)
            lines.insert(1, "")

    return lines, all_subst


def load_pair_programs(
    task_hex_code: str,
    level: str = "GRID",
    base_output_dir: str = "outputs/generated_codes",
) -> List[List[str]]:
    """
    Load all pair-specific programs for a task and level from disk.

    Returns:
        List of programs; each program is a list of source lines.
    """
    task_dir = os.path.join(base_output_dir, task_hex_code, level)
    if not os.path.isdir(task_dir):
        return []

    programs = []
    for name in sorted(os.listdir(task_dir)):
        if not name.endswith(".py") or name.startswith("__") or "abstract" in name.lower():
            continue
        path = os.path.join(task_dir, name)
        with open(path, "r") as f:
            programs.append(f.read().splitlines())
    return programs


def abstract_task_programs(
    task_hex_code: str,
    level: str = "GRID",
    base_output_dir: str = "outputs/generated_codes",
) -> Tuple[Optional[List[str]], List[dict]]:
    """
    Load pair-specific programs for a task/level and return their anti-unification.
    Uses ARCKG to express generalized variables as DSL (e.g. coord_of(object_at_input(...))).

    Returns:
        (abstract_program_lines, list_of_substitutions) or (None, []) if no programs found.
    """
    programs = load_pair_programs(task_hex_code, level=level, base_output_dir=base_output_dir)
    if not programs:
        return None, []
    pair_indices = list(range(len(programs)))
    return anti_unify_programs(
        programs,
        task_hex_code=task_hex_code,
        pair_indices=pair_indices,
        level=level,
        base_output_dir=base_output_dir,
    )


def save_abstract_program(
    task_hex_code: str,
    level: str = "GRID",
    base_output_dir: str = "outputs/generated_codes",
) -> Optional[str]:
    """
    Load pair-specific programs for the task/level, anti-unify them, and save
    the abstract program in the same directory as the pair programs.

    Output path: {base_output_dir}/{task_hex_code}/{level}/{task_hex_code}_abstract_{level}.py

    Returns:
        Path to the saved file, or None if no pair programs were found to abstract.
    """
    abstract_lines, _ = abstract_task_programs(
        task_hex_code, level=level, base_output_dir=base_output_dir
    )
    if not abstract_lines:
        return None
    level_dir = os.path.join(base_output_dir, task_hex_code, level)
    os.makedirs(level_dir, exist_ok=True)
    filename = f"{task_hex_code}_abstract_{level.lower()}.py"
    path = os.path.join(level_dir, filename)
    with open(path, "w") as f:
        f.write("\n".join(abstract_lines))
    return path
