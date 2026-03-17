"""
operators — SOAR Operator 기본 인터페이스.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] Operator는 반드시 precondition + effect 두 요소로 구성된다.
            precondition: WM을 읽어 제안 가능 여부 판단 (WM 수정 금지).
            effect:       WM을 변경/추가하고 op_status를 기록.

[설계 자유] 어떤 operator를 만들지, 이름, 인자, precondition 조건, effect 내용.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class Operator:
    """
    [SOAR 강제] Operator 인터페이스. precondition + effect.
    [설계 자유] 구체 operator 클래스 (active_operators.py).
    """

    def __init__(self, name: str):
        """
        [설계 자유] operator 이름. PREFERENCE_ORDER의 문자열과 일치해야 한다.
        """
        self.name = name

    def precondition(self, wm) -> bool:
        """
        [SOAR 강제] precondition 인터페이스 — WM 수정 금지.
        [설계 자유] 발화 조건 내용. wm.active["elaborated"]만 참조할 것.
        """
        pass

    def effect(self, wm):
        """
        [SOAR 강제] effect 인터페이스 — 반드시 op_status를 설정해야 한다.
        [설계 자유] WM에 무엇을 추가/변경할지.
                   effect의 주된 역할은 WM에 없던 지식을 추가하는 것.
                   실패 시 op_status = "failure" → impasse 트리거.
        """
        pass
