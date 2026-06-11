"""
Goal (모듈 B 보강) — 목표를 *물질적으로* 들고 있는 구조.

목표는 "발견되며 날카로워진다": 처음엔 막연한 intent 뿐이고, 비교 심화로
미충족 조건이 *국소화*되면 need(Need) 가 채워진다. 그 need 를 이 scope 에서
충족할 DSL 이 없으면 status=BLOCKED 가 되고, 그 막힘이 scope 하강을 정당화한다.

(GoalStack 은 이 Goal 프레임들의 스택 = SOAR substate 의 목표-증강 뷰.)
"""

OPEN = "open"          # 아직 추구 중
BLOCKED = "blocked"    # 막힘 — 이 scope 에선 need 를 못 채움 (reason 에 사유)
ACHIEVED = "achieved"  # 충족됨


class Need:
    """국소화된 미충족 조건 — 비교 심화(모듈 2)의 산물, DSL 탐색(모듈 3)의 입력.

    'target 의 attr 을 have 에서 want 로 바꿔야 한다.'
      requires : 이 need 를 해소하는 *효과* (effect 양식). DSL 탐색의 매칭 키 —
                 계층이 아니라 *효과* 로 건다. (예: effect("add","roles"))
      holds    : 그 슬롯이 *담는 실체 타입* (예 "grid"). 값 자체가 아니라 무언가를
                 *만들어* 채워야 하는 need 일 때, 하강 시 새 need 의 효과 kind 가 된다.
                 (None 이면 값 자체를 바꾸는 need.)
    """

    def __init__(self, target, attr, have, want, requires, holds=None):
        self.target = target     # 노드 (예: Pa)
        self.attr = attr         # 속성 경로 (예: "roles.output")
        self.have = have         # 현재 값 (예: False)
        self.want = want         # 원하는 값 (예: True)
        self.requires = requires # 해소 효과 (effect 양식) — 탐색 매칭 키
        self.holds = holds       # 슬롯이 담는 실체 타입 (예: "grid") — 하강 가이드

    def __repr__(self):
        h = f" holds={self.holds}" if self.holds else ""
        return (f"Need({self.target}.{self.attr}: {self.have!r}→{self.want!r} "
                f"requires={self.requires}{h})")

    def to_wme(self) -> dict:
        """WM 적재용 dict (값은 프리미티브/노드 id — 로거가 Ix 로 펼친다)."""
        return {
            "target": getattr(self.target, "node_id", str(self.target)),
            "attr": self.attr,
            "have": self.have,
            "want": self.want,
            "requires": dict(self.requires) if self.requires else None,
            "holds": self.holds,
        }


class Goal:
    """물질적 목표 프레임.

      intent : 사람이 읽는 서술 ("Pa 의 빠진 output 만들기")
      scope  : 지금 이 목표를 다루는 노드/레벨
      need   : 국소화되면 채워지는 Need (None 이면 아직 막연)
      status : OPEN / BLOCKED / ACHIEVED
      reason : 막힘/충족 사유 (서술)
      parent : 복기(復棋)용 상위 목표
    """

    def __init__(self, intent, scope, parent=None):
        self.intent = intent
        self.scope = scope
        self.parent = parent
        self.need = None
        self.status = OPEN
        self.reason = None

    def sharpen(self, need, intent=None):
        """비교 심화로 미충족 조건이 국소화됨 → need 를 달아 목표를 구체화."""
        self.need = need
        if intent is not None:
            self.intent = intent
        return self

    def block(self, reason):
        """이 scope 에서 need 를 충족할 DSL 이 없음 → 막힘 (scope 하강 정당화)."""
        self.status = BLOCKED
        self.reason = reason
        return self

    def achieve(self, reason=None):
        """need 가 채워짐 → 충족. (복기 시 parent 로 올라간다.)"""
        self.status = ACHIEVED
        self.reason = reason
        return self

    def subgoal(self, intent, scope):
        """막힌 need 를 풀기 위해 더 깊은 scope 의 하위목표 — parent 연결(복기)."""
        return Goal(intent, scope, parent=self)

    def __repr__(self):
        return f"Goal({self.intent!r} @{self.scope} {self.status} need={self.need})"

    def to_wme(self) -> dict:
        """WM 적재용 dict — 로거가 (Sx ^goal Ig)(Ig ^intent …)(Ig ^need In)… 로 펼친다."""
        return {
            "intent": self.intent,
            "status": self.status,
            "reason": self.reason,
            "need": self.need.to_wme() if self.need else None,
        }


def deposit_goal(wm, goal) -> None:
    """현재 상태(wm.active)에 목표를 wme 로 적재/갱신 — 매 변화마다 호출."""
    wm.active["goal"] = goal.to_wme()
