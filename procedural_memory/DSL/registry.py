"""
DSL registry — DSL 한 항목 = 두 얼굴을 함께 등록.

@dsl 데코레이터가 함수(*실행 본체*, procedural)를 등록하면서 그 *선언적 명세*
(= semantic DSL 라이브러리 씨앗) 를 SPECS 에 남긴다.

  SPECS[name] = {name, kind, in, out, body}
  · 선언적 명세(semantic) = body 를 뺀 나머지 {name, kind, in, out}
  · 실행 본체(procedural) = body (호출 가능한 함수)

Slice 1 의 명세는 최소형. 합성 문법·anti-unify 스키마·학습된 고급 DSL 적재는
Slice 2 에서 자란다 (지금 풍부하게 짜면 "그럴싸한 추상" — 금지).
"""

SPECS: dict = {}


def dsl(kind: str, sig_in: list, sig_out: str):
    """함수를 DSL 본체로 등록하고 그 선언적 명세를 SPECS 에 남긴다.

    kind: "property" | "util" | "transformation"
    """
    def deco(fn):
        SPECS[fn.__name__] = {
            "name": fn.__name__,
            "kind": kind,
            "in": list(sig_in),
            "out": sig_out,
            "body": fn,
        }
        return fn
    return deco


def spec(name: str) -> dict:
    """선언적 명세만 반환 (body 제외) — semantic 라이브러리 조회용."""
    s = SPECS[name]
    return {k: v for k, v in s.items() if k != "body"}


def body(name: str):
    """실행 본체(함수) 반환 — procedural 호출용."""
    return SPECS[name]["body"]
