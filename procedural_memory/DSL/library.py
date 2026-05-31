"""
DSL 학습 라이브러리 — semantic 의 *자라는* 부분 ([[arbor-memory-contents]]).

anti-unify 산물(schema)을 재사용 가능한 고급 DSL 항목으로 적재한다. 문제를 풀수록
여기가 채워진다 (DreamCoder 식 library learning). 디스크(JSON)에 영속.

항목: {"schema": <anti-unify schema>, "provenance": {...}}
주의(Slice 2 한계): 아직 *과제 간* 일반화(c·d 의 위치 const 를 슬롯으로 합치기)는
안 한다 — schema 구조 비교·병합은 Slice 3+ (compare/merge DSL structures).
"""

import json
import os

DEFAULT_PATH = "semantic_memory/dsl_library.json"


def load(path: str = DEFAULT_PATH) -> list:
    """라이브러리 항목 목록 (없으면 빈 목록)."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def deposit(schema: dict, provenance: dict, path: str = DEFAULT_PATH) -> dict:
    """schema 를 라이브러리에 적재 (동일 schema 중복은 skip). 적재된 항목 반환."""
    lib = load(path)
    entry = {"schema": schema, "provenance": provenance}
    if not any(e["schema"] == schema for e in lib):
        lib.append(entry)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(lib, f, indent=2, ensure_ascii=False)
    return entry
