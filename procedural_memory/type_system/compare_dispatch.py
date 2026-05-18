"""
타입 인식 비교 분기.

compare_typed(a, b, type_str) — 타입 문자열을 보고 적절한 비교 의미로 분기.
ARCKG.comparison.compare()가 leaf 단계에서 이 함수를 호출한다.

통일된 결과 형식:
  모든 결과는 {"type": "COMM"|"DIFF", "score": "n/N", ...} 로 시작한다.
  score 의 의미는 타입에 따라 다르지만 항상 "맞은 조각/총 조각" 분수.

타입별 추가 필드:
  class<X>           : comp1, comp2
  int                : comp1, comp2, diff
  bool               : comp1, comp2
  grid               : comp1, comp2     (사이즈 다르면 즉시 DIFF, 내부 분해 없음)
  shape              : alternates, comp1, comp2
                       (8 dihedral 변환 모두 시도, score = 매칭수/8)
  tuple<T1,T2,...>   : components       (자리별 결과 리스트)
  list<T>            : components       (원소별 결과 리스트)
                       (길이 다르면 length1, length2)
  set<T>             : common, only_in_1, only_in_2
"""

from procedural_memory.type_system.helpers import class_eq


def compare_typed(a, b, type_str: str) -> dict:
    """타입 문자열에 따라 두 값을 비교해 결과 dict 반환."""
    if type_str.startswith("class<"):
        return _compare_class(a, b)
    if type_str == "int":
        return _compare_int(a, b)
    if type_str == "bool":
        return _compare_bool(a, b)
    if type_str == "grid":
        return _compare_grid(a, b)
    if type_str == "shape":
        return _compare_shape(a, b)
    if type_str.startswith("tuple<"):
        return _compare_tuple(a, b, type_str)
    if type_str.startswith("list<"):
        return _compare_list(a, b, type_str)
    if type_str.startswith("set<"):
        return _compare_set(a, b, type_str)
    return _compare_default(a, b)


def _scalar_score(same: bool) -> str:
    return "1/1" if same else "0/1"


def _compare_class(a, b) -> dict:
    same = class_eq(a, b)
    return {
        "type":  "COMM" if same else "DIFF",
        "score": _scalar_score(same),
        "comp1": a,
        "comp2": b,
    }


def _compare_int(a, b) -> dict:
    same = (a == b)
    return {
        "type":  "COMM" if same else "DIFF",
        "score": _scalar_score(same),
        "comp1": a,
        "comp2": b,
        "diff":  b - a,
    }


def _compare_bool(a, b) -> dict:
    same = (a == b)
    return {
        "type":  "COMM" if same else "DIFF",
        "score": _scalar_score(same),
        "comp1": a,
        "comp2": b,
    }


def _compare_grid(a, b) -> dict:
    """grid — 2D 배열 전체를 단일 값으로 보고 같음/다름만 판정.
       사이즈가 다르면 == 가 자동으로 False 라 DIFF. 내부 셀 분해 없음."""
    same = (a == b)
    return {
        "type":  "COMM" if same else "DIFF",
        "score": _scalar_score(same),
        "comp1": a,
        "comp2": b,
    }


def _compare_shape(a, b) -> dict:
    """shape — bool mask. 8 dihedral alternate 모두 시도해 매칭된 결과를
       모두 기록한다. 하나라도 매칭되면 overall COMM, 다 안 맞으면 DIFF.
       score = '매칭된 alternate 수 / 8'."""
    from procedural_memory.type_system.dihedral import alternates

    a_alts = alternates(a)
    alt_results = [
        {"type": "COMM" if alt == b else "DIFF"}
        for alt in a_alts
    ]
    n_match = sum(1 for r in alt_results if r["type"] == "COMM")
    overall = "COMM" if n_match > 0 else "DIFF"
    return {
        "type":       overall,
        "score":      f"{n_match}/8",
        "alternates": alt_results,
        "comp1":      a,
        "comp2":      b,
    }


def _compare_tuple(a, b, type_str: str) -> dict:
    """tuple<T1,T2,...> — 자리별 재귀."""
    inner = type_str[len("tuple<"):-1]
    inner_types = _split_top_level(inner)

    if len(a) != len(b) or len(a) != len(inner_types):
        n = max(len(a), len(b), len(inner_types))
        return {
            "type":    "DIFF",
            "score":   f"0/{n}",
            "length1": len(a),
            "length2": len(b),
        }

    components = [
        compare_typed(av, bv, t)
        for av, bv, t in zip(a, b, inner_types)
    ]
    n_comm = sum(1 for c in components if c["type"] == "COMM")
    n_total = len(components)
    overall = "COMM" if n_comm == n_total else "DIFF"
    return {
        "type":       overall,
        "score":      f"{n_comm}/{n_total}",
        "components": components,
    }


def _compare_list(a, b, type_str: str) -> dict:
    """list<T> — 원소별 재귀. 길이가 다르면 score 0/max(len)."""
    inner = type_str[len("list<"):-1]
    if len(a) != len(b):
        n = max(len(a), len(b))
        return {
            "type":    "DIFF",
            "score":   f"0/{n}",
            "length1": len(a),
            "length2": len(b),
        }
    components = [compare_typed(av, bv, inner) for av, bv in zip(a, b)]
    n_comm = sum(1 for c in components if c["type"] == "COMM")
    n_total = len(components)
    overall = "COMM" if n_comm == n_total else "DIFF"
    return {
        "type":       overall,
        "score":      f"{n_comm}/{n_total}",
        "components": components,
    }


def _compare_set(a, b, type_str: str) -> dict:
    """set<T> — 순서 무관.
       inner 타입이 class<X> 이고 X 의 cardinality 가 알려져 있으면
       universe = X 전체로 잡고 presence/absence 모두 일치 카운트한다.
       그 외에는 Jaccard (교집합/합집합).
       원소가 hashable 해야 한다."""
    from procedural_memory.type_system.classes import get_class_cardinality

    sa = set(a)
    sb = set(b)
    common    = sorted(sa & sb, key=str)
    only_in_a = sorted(sa - sb, key=str)
    only_in_b = sorted(sb - sa, key=str)
    overall = "COMM" if not only_in_a and not only_in_b else "DIFF"

    inner = type_str[len("set<"):-1]
    score = None

    if inner.startswith("class<") and inner.endswith(">"):
        class_name = inner[len("class<"):-1]
        cardinality = get_class_cardinality(class_name)
        if cardinality is not None:
            # universe 가 정해진 경우: 양쪽 다 있음 + 양쪽 다 없음 모두 일치
            both_present = len(common)
            both_absent  = cardinality - len(sa | sb)
            agreements   = both_present + both_absent
            score = f"{agreements}/{cardinality}"

    if score is None:
        # Jaccard fallback (universe 가 무한/불명)
        union_size = len(sa | sb)
        inter_size = len(sa & sb)
        score = f"{inter_size}/{union_size}" if union_size > 0 else "0/0"

    return {
        "type":      overall,
        "score":     score,
        "common":    common,
        "only_in_1": only_in_a,
        "only_in_2": only_in_b,
    }


def _compare_default(a, b) -> dict:
    same = (a == b)
    return {
        "type":  "COMM" if same else "DIFF",
        "score": _scalar_score(same),
        "comp1": a,
        "comp2": b,
    }


def _split_top_level(s: str) -> list:
    """쉼표로 분리하되 꺽쇠 안의 쉼표는 무시.
       'int,int' → ['int','int'],  'class<color>,int' → ['class<color>','int']."""
    parts = []
    depth = 0
    start = 0
    for i, ch in enumerate(s):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(s[start:i].strip())
            start = i + 1
    parts.append(s[start:].strip())
    return parts
