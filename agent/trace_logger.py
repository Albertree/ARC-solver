"""
trace_logger — Annotated Trace Log for SOAR cycle.

logs/trace_{task_id}_{timestamp}.log 파일을 자동 생성하고
터미널 출력과 동시에 파일에도 기록한다 (tee 방식).
각 Cycle 블록 다음에 [해석] 블록을 추가한다.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any


class TeeWriter:
    """sys.stdout을 래핑하여 터미널 + 파일 동시 출력 (tee)."""

    def __init__(self, file_handle, original_stdout):
        self._file = file_handle
        self._stdout = original_stdout

    def write(self, text: str) -> int:
        self._stdout.write(text)
        self._file.write(text)
        self._file.flush()
        return len(text)

    def flush(self):
        self._stdout.flush()
        self._file.flush()

    @property
    def encoding(self):
        return getattr(self._stdout, "encoding", "utf-8")

    def isatty(self):
        return False


class TraceLogger:
    """
    태스크별 annotated trace log를 관리한다.

    사용법:
        logger = TraceLogger(task_id)
        logger.start()          # tee 시작 + 헤더 출력
        logger.begin_cycle(1, "SelectTarget")
        logger.write_wm_changes(wm_lines)
        logger.write_interpretation(interp)
        ...
        logger.write_result(success, rule_id, output_info)
        logger.stop()           # tee 해제 + 파일 닫기
    """

    def __init__(self, task_id: str, log_dir: str = "logs"):
        self.task_id = task_id
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(log_dir, exist_ok=True)
        self.log_path = os.path.join(
            log_dir, f"trace_{task_id}_{self._timestamp}.log"
        )
        self._file = None
        self._tee = None
        self._original_stdout = None
        self._cycle_num = 0

    def start(self):
        """tee 출력을 시작하고 로그 헤더를 작성한다."""
        self._file = open(self.log_path, "w", encoding="utf-8")
        self._original_stdout = sys.stdout
        self._tee = TeeWriter(self._file, self._original_stdout)
        sys.stdout = self._tee
        self._write_header()

    def stop(self):
        """tee 출력을 해제하고 파일을 닫는다."""
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
        if self._file is not None:
            self._file.close()
            self._file = None

    def _write_header(self):
        print("=" * 50)
        print(f"TASK: {self.task_id}  |  {self._timestamp}")
        print("=" * 50)

    def begin_cycle(self, cycle_num: int, operator_name: str):
        """새 사이클 블록을 시작한다."""
        self._cycle_num = cycle_num
        print(f"\n[Cycle {cycle_num}] Operator: {operator_name}")

    def write_wm_changes(self, wme_records: list[dict], before_len: int):
        """사이클 동안 추가된 WME를 SOAR triplet 형식으로 출력한다."""
        print("--- WM 변화 ---")
        new_records = wme_records[before_len:]
        if not new_records:
            print("(변화 없음)")
        else:
            seen = set()
            for rec in new_records:
                ident = rec["identifier"]
                attr = rec["attribute"]
                val = _fmt_value(rec["value"])
                line = f"({ident} ^{attr} {val})"
                if line not in seen:
                    seen.add(line)
                    print(line)

    def write_interpretation(self, interp: dict | None):
        """[해석] 블록을 출력한다."""
        print("--- [해석] ---")
        if interp is None:
            print("행동: (operator가 해석을 반환하지 않음)")
            print("의미: (없음)")
            print("선택 근거: (없음)")
            print("저장 위치: (없음)")
        else:
            print(f"행동: {interp.get('action', '(없음)')}")
            print(f"의미: {interp.get('meaning', '(없음)')}")
            print(f"선택 근거: {interp.get('reason', '(없음)')}")
            print(f"저장 위치: {interp.get('storage', '(없음)')}")

    def write_result(
        self,
        success: bool,
        rule_id: str = "없음",
        output_info: str = "없음",
    ):
        """로그 마지막에 [결과] 블록을 출력한다."""
        print("\n[결과]")
        status = "SUCCESS" if success else "FAILURE"
        print(f"성공 여부: {status}")
        print(f"시도한 rule: {rule_id}")
        print(f"최종 출력 그리드: {output_info}")


def _fmt_value(value: Any) -> str:
    """WME 값을 SOAR 스타일 문자열로 포맷한다."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dict):
        if not value:
            return "{}"
        # compare-result 같은 큰 dict는 요약
        if "result" in value and "id" in value:
            id_dict = value.get("id", {})
            res = value.get("result", {})
            score = res.get("score", "?")
            rtype = res.get("type", "?")
            id1 = id_dict.get("id1", "?")
            id2 = id_dict.get("id2", "?")
            return f"<compare {id1} vs {id2}: {rtype} {score}>"
        keys = list(value.keys())[:3]
        preview = ", ".join(f"{k}: ..." for k in keys)
        if len(value) > 3:
            preview += ", ..."
        return "{" + preview + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        # 큰 리스트는 요약
        if len(value) > 3:
            return f"[...{len(value)} items]"
        # 리스트 항목이 dict이면 요약
        parts = []
        for item in value:
            if isinstance(item, dict) and "pair_id" in item:
                parts.append(f"{item.get('pair_id', '?')}")
            else:
                s = str(item)
                if len(s) > 40:
                    s = s[:37] + "..."
                parts.append(s)
        return "[" + ", ".join(parts) + "]"
    if isinstance(value, str):
        if all(ch.isalnum() or ch in ("_", "-", ".") for ch in value):
            return value
        return f'"{value}"'
    return str(value)
