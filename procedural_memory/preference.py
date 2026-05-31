"""
preference (선호) — 시스템이 *기초 제공* 하는 property 우선순위. **독립 모듈** 로 분리해
나중에 조절·진화 가능하게 한다 (진화 방식은 아직 미고려).

탐색을 bound 하는 세 축 중 '*어느 property 를 먼저 보나*' 축.
쓰임(설계):
  ① 객체 유사도/매칭의 가중 — 어느 속성이 '같은 객체'인지 더 결정하나
  ② 변화 분석 순서 — 매칭쌍의 변화를 어느 속성부터 설명하나
  ③ '같은 것 찾기' 앵커 — 한 속성을 기준 삼아 같은 객체 탐색할 때 어느 속성부터

※ 객체 매칭이 깔끔히 되는 건 *운 좋은* 경우다. 복잡한 상황에선 매칭이 안 일어나
  *새 변화에 대한 탐색공간* 을 열어야 하는데, 그 우선순위도 결국 선호의 영역이라 여기 둔다.

지금은 전역 기본 순서 하나. 용도별·맥락별 분화, 학습 진화는 추후 (여기만 고치면 됨).
"""

# property 선호 순서 (앞일수록 먼저 본다). 정체성↑ → 보통 '변화'하는 것 → 구조·메타↓
ORDER = [
    "color", "shape", "size", "grid_size", "area",   # 정체성에 가까움 (매칭에 강)
    "coordinate", "position",                         # 보통 '변화'하는 것
    "symmetry", "method", "contents",                 # 구조·메타·원시
]


def rank(prop: str) -> int:
    """선호 순위 (작을수록 먼저). 미등록 property 는 맨 뒤."""
    return ORDER.index(prop) if prop in ORDER else len(ORDER)


def by_preference(props):
    """property 목록을 선호 순서로 정렬해 반환."""
    return sorted(props, key=rank)
