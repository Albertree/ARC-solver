"""
anti_unification — example 들의 산물을 across-pair 로 일반화해 *schema* 를 뽑는다.

각 출력 property 를 우선순위 탐색 엔진([[program/search]])으로 설명한다 — "어느 입력
property + 어떤 산술" 인지 탐색해 binding 을 얻는다. schema = {property: binding}.
(const/from_g0/offset/corner 가 손 move 가 아니라 하나의 탐색에서 나온다.)
"""

from program.search import explain_property, resolve_property  # noqa: F401 (재노출)


def anti_unify_objects(examples: list, props: list) -> dict:
    """examples: [(in_ctx, out_ctx), ...]. 각 property 를 탐색으로 설명."""
    return {k: explain_property(examples, k) for k in props}


def is_solvable(schema: dict) -> bool:
    """schema 의 모든 property 가 설명됨(unexplained 아님)이면 True."""
    return all(e["kind"] != "unexplained" for e in schema.values())
