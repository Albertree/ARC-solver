"""
Predict (PredictByAllPairCommOp) + K (output / emit_answer).

GRID 레벨의 결정적 비교 — 모든 example G1 이 COMM — 으로부터 test 출력을 도출한다.
값-agnostic: 정답 값을 하드코딩하지 않고 *비교 결과(공통 grid)* 에서 끌어온다 (P3/P4).
같은 코드가 easy000a((5,5)빨강) 도, easy000a2(다른 고정 출력) 도 통과해야 한다.
"""


def predict_by_all_pair_comm(evidence: dict):
    """모든 example G1 이 COMM → test 출력 = 그 공통 grid.

    contents 가 COMM(전부 동일)이므로 공통 contents 가 곧 답. evidence 는
    descend_to_decisive 의 결정적 결과 {size, color, contents} (값 하드코딩 ✗).
    """
    return evidence["contents"]


def emit_answer(task, grid) -> list:
    """K (output) — 모든 test pair 에 공통 grid 를 제출한다.
    Slice 1 은 출력 고정(input 무관)이라 test 마다 같은 grid."""
    return [grid for _ in task.test_pairs]
