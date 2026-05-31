"""
anti_unification — example 들의 산물을 across-pair 로 일반화해 *schema* 를 뽑는다.

Slice 2: 전경 객체 property 들을 일반화 (값 변수화는 최소 — 구조적 일치만 사용).
  · 모든 example 출력에서 동일      → const  (고정값)
  · pair 마다 다르나 같은 pair 입력과 일치 → from_g0 (출처 = 입력 같은 property)
  · 둘 다 아님                      → unexplained (현 슬라이스로 설명 불가)

(여러 step 프로그램의 일반 anti-unification[term alignment]은 Slice 3+ — 산물이
다단계 프로그램이 될 때 도입.)
"""


def anti_unify_objects(examples: list, props: list) -> dict:
    """examples: [(in_props, out_props), ...]  (전경 객체 to_json dict 쌍).
    props: 일반화할 property 키 목록.
    반환: { prop: {"kind": "const", "value": v}
                | {"kind": "from_g0", "attr": prop}
                | {"kind": "unexplained"} }
    """
    schema = {}
    for k in props:
        outs = [out[k] for _, out in examples]
        if all(o == outs[0] for o in outs):
            schema[k] = {"kind": "const", "value": outs[0]}
        elif all(out[k] == inp.get(k) for inp, out in examples):
            schema[k] = {"kind": "from_g0", "attr": k}
        else:
            schema[k] = {"kind": "unexplained"}
    return schema


def is_solvable(schema: dict) -> bool:
    """schema 의 모든 property 가 설명됨(const|from_g0)이면 True."""
    return all(e["kind"] != "unexplained" for e in schema.values())
