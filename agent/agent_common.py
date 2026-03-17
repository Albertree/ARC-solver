"""
agent_common — WM 초기화, 종료 조건 판단, 답변 추출 공통 유틸.
"""


def build_wm_from_task(task, wm) -> None:
    """
    [설계 자유] WM에 어떤 초기 정보를 담을지.
               task 참조 저장, goal 설정, subgoal 초기화,
               comparison_agenda 초기화 (각 example pair의 (input, output) 등록).
               SelectTargetOperator는 wm.task를 직접 참조하지 않고
               agenda에서만 읽으므로 여기서 의존성이 캡슐화된다.
    MUST NOT: 비교(comparison) 연산을 여기서 수행하지 마 — WM 초기화만.
    """
    pass


def goal_satisfied(wm) -> bool:
    """
    [SOAR 강제] 사이클 종료 조건 — 반드시 goal 달성 여부를 판단하는 함수가 있어야 한다.
    [설계 자유] 무엇을 "달성"으로 볼지 (모든 test subgoal solved 여부).
    """
    pass


def answers_from_wm(wm) -> list:
    """
    [설계 자유] WM.found에서 결과를 추출하는 방식.
               test_0, test_1, ... 순서대로 리스트 반환. 없으면 None.
    MUST NOT: None을 임의 값으로 대체하지 마.
    """
    pass
