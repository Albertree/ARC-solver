"""
ARC-solver 통합 진입점.

train 모드: 기존 memory에서 이어서 태스크를 푼다.
eval  모드: eval_result/run_MMDD_HHMM/ 아래 격리된 fresh memory에서 시작한다.

사용법:
  python run.py --task HEX [HEX ...]             단일/복수 태스크
  python run.py --seq tasks.txt                  시퀀스 파일
  python run.py --split training --n 5           training에서 랜덤 5개
  python run.py --mode eval --task HEX           eval 격리 실행
  python run.py --task HEX --log-wm              WM 로그 포함

전체 옵션: python run.py --help
"""

import argparse
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from arc2_env.arc_environment import ARCEnvironment
from agent.active_agent import ActiveSoarAgent
from managers.arc_manager import ARCManager
from basics.viz import show_task

# ── 기본값 (자주 바꾸는 값은 여기서 수정) ──────────────────
DEFAULT_TASK         = "08ed6ac7"        # --task/--seq/--split 미지정 시 사용
DEFAULT_MODE         = "train"           # "train" | "eval"
DEFAULT_MAX_STEPS    = 50                # --max-steps  : SOAR 사이클 최대 스텝 수
DEFAULT_MAX_ATTEMPTS = 3                 # --max-attempts: 태스크당 최대 제출 횟수
DEFAULT_TIME_BUDGET  = None              # --time-budget : 에피소드 시간 제한(초), None=무제한
DEFAULT_SM_ROOT      = "semantic_memory" # --sm-root    : train 모드 semantic_memory 경로
DEFAULT_SEED         = 42                # --seed       : --n 랜덤 선택 시드
DEFAULT_TRACE_OUT    = None              # --trace-out  : trace JSON 저장 경로, None=저장 안 함
DEFAULT_LOG_OUT      = None              # --log-out    : 결과 로그 파일 경로, None=stdout만
DEFAULT_LOG_WM       = True              # --log-wm     : WM triplet 로그 출력
DEFAULT_QUIET        = False             # --quiet      : 진행 출력 억제
DEFAULT_OUT_DIR      = "run_logs"        # --out-dir    : 전체 출력 저장 폴더, None=저장 안 함
# ────────────────────────────────────────────────────────


def _parse_args():
    p = argparse.ArgumentParser(
        prog="run.py",
        description="ARC-solver 실행 진입점 (train / eval)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "예시:\n"
            "  python run.py --task 08ed6ac7\n"
            "  python run.py --mode eval --task 08ed6ac7 007bbfb7\n"
            "  python run.py --split training --n 10 --seed 0\n"
            "  python run.py --seq my_tasks.txt --log-wm\n"
        ),
    )
    p.add_argument(
        "--mode", choices=["train", "eval"], default=DEFAULT_MODE,
        help=f"train: 기존 memory 누적 사용. eval: 격리된 fresh memory 사용 (default: {DEFAULT_MODE})",
    )

    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument(
        "--task", nargs="+", metavar="HEX",
        help=f"풀 태스크 hex ID (복수 가능, 미지정 시 DEFAULT_TASK={DEFAULT_TASK})",
    )
    src.add_argument(
        "--seq", metavar="FILE",
        help="태스크 hex ID 목록 파일 (줄당 1개, # 로 주석 처리)",
    )
    src.add_argument(
        "--split", choices=["training", "evaluation", "easy"],
        help="전체 split 실행",
    )

    p.add_argument("--n", type=int, metavar="N",
                   help="--split에서 랜덤 N개 선택")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED,
                   help=f"--n 랜덤 시드 (default: {DEFAULT_SEED})")
    p.add_argument(
        "--max-steps", type=int, default=DEFAULT_MAX_STEPS, dest="max_steps",
        help=f"SOAR 사이클 최대 스텝 수 (default: {DEFAULT_MAX_STEPS})",
    )
    p.add_argument(
        "--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS, dest="max_attempts",
        help=f"태스크당 최대 제출 횟수 (default: {DEFAULT_MAX_ATTEMPTS})",
    )
    p.add_argument(
        "--time-budget", type=float, default=DEFAULT_TIME_BUDGET, dest="time_budget",
        help="에피소드 전체 시간 제한(초). 미지정 시 무제한",
    )
    p.add_argument(
        "--sm-root", default=DEFAULT_SM_ROOT, dest="sm_root",
        help=f"semantic_memory 루트 경로 (train 모드 전용, default: {DEFAULT_SM_ROOT})",
    )
    p.add_argument(
        "--trace-out", metavar="PATH", dest="trace_out", default=DEFAULT_TRACE_OUT,
        help=f"실행 trace JSON 저장 경로 (default: {DEFAULT_TRACE_OUT})",
    )
    p.add_argument(
        "--log-out", metavar="PATH", dest="log_out", default=DEFAULT_LOG_OUT,
        help=f"결과 로그 파일 경로 (train 모드, default: {DEFAULT_LOG_OUT}=stdout만)",
    )
    p.add_argument(
        "--log-wm", action="store_true", dest="log_wm", default=DEFAULT_LOG_WM,
        help=f"WM triplet 로그 출력 활성화 (default: {DEFAULT_LOG_WM})",
    )
    p.add_argument(
        "--quiet", action="store_true", default=DEFAULT_QUIET,
        help=f"진행률 출력 억제 (default: {DEFAULT_QUIET})",
    )
    p.add_argument(
        "--out-dir", metavar="DIR", dest="out_dir", default=DEFAULT_OUT_DIR,
        help=f"전체 stdout을 MMDD_HHMM.log 파일로 저장할 폴더 (default: {DEFAULT_OUT_DIR}, none=저장 안 함)",
    )
    return p.parse_args()


def _build_task_list(args) -> list[str]:
    if args.task:
        return list(args.task)

    if args.seq:
        seq_path = Path(args.seq)
        if not seq_path.exists():
            sys.exit(f"[오류] 시퀀스 파일을 찾을 수 없음: {args.seq}")
        tasks = [
            line.strip()
            for line in seq_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not tasks:
            sys.exit(f"[오류] 시퀀스 파일에 유효한 태스크 ID가 없음: {args.seq}")
        return tasks

    if args.split:
        mgr = ARCManager(data_root="data", semantic_memory_root="semantic_memory")
        all_tasks = mgr.load_all_tasks(split=args.split)
        all_hex = [t.task_hex for t in all_tasks]
        if args.n:
            n = min(args.n, len(all_hex))
            if args.n > len(all_hex):
                print(f"[경고] --n {args.n} > 사용 가능 태스크 수 {len(all_hex)}, 전체 사용")
            return random.Random(args.seed).sample(all_hex, n)
        return all_hex

    print(f"[기본값] --task/--seq/--split 미지정 → DEFAULT_TASK={DEFAULT_TASK} 사용")
    return [DEFAULT_TASK]


def _prepare_eval_run() -> tuple[Path, dict]:
    """eval 격리 폴더 생성. (run_dir, 메모리 루트 dict) 반환."""
    run_dir = Path(f"eval_result/run_{datetime.now():%m%d_%H%M}")
    run_dir.mkdir(parents=True, exist_ok=True)
    for mem in ["semantic_memory", "episodic_memory", "procedural_memory"]:
        mem_dir = run_dir / mem
        mem_dir.mkdir(exist_ok=True)
        (mem_dir / ".gitkeep").touch()
    return run_dir, {
        "semantic_memory_root": str(run_dir / "semantic_memory"),
        "episodic_memory_root": str(run_dir / "episodic_memory"),
        "procedural_memory_root": str(run_dir / "procedural_memory"),
    }


def _append_log(path: Path, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


class _Tee:
    """stdout을 터미널과 파일에 동시에 기록한다. ANSI 코드 그대로 보존."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(path, "w", encoding="utf-8")
        self._stdout = sys.stdout

    def write(self, data: str):
        self._stdout.write(data)
        self._file.write(data)

    def flush(self):
        self._stdout.flush()
        self._file.flush()

    def close(self):
        sys.stdout = self._stdout
        self._file.close()

    def fileno(self):
        return self._stdout.fileno()

    def isatty(self):
        return self._stdout.isatty()


def _run_single_verbose(env: ARCEnvironment, agent: ActiveSoarAgent,
                        task_id: str, log_path, quiet: bool):
    """단일 태스크: show_task 후 풀기. 재시도 지원."""
    task = env.get_task()
    if task is None:
        print(f"[오류] 태스크 로드 실패: {task_id}")
        return

    if not quiet:
        # show_task의 ANSI 그리드는 터미널에만 출력 (로그 파일 제외)
        tee = sys.stdout if isinstance(sys.stdout, _Tee) else None
        if tee:
            sys.stdout = tee._stdout
        show_task(task)
        if tee:
            sys.stdout = tee

    t0 = time.perf_counter()
    attempts = 0
    reward = 0.0
    info = {}

    while True:
        answer = agent.solve(task)
        reward, _next, done, info = env.step(answer)
        attempts += 1

        if reward >= 1.0 or not info.get("can_retry") or not agent.can_retry:
            break
        task = env.get_task()
        if task is None:
            break

    elapsed = time.perf_counter() - t0
    line = (
        f"[task] {task_id}  reward={reward:.1f}  "
        f"correct={info.get('correct_per_pair')}  "
        f"submissions={attempts}  t={elapsed:.2f}s"
    )
    if not quiet:
        print(line)
    if log_path:
        _append_log(log_path, line)


def _run_benchmark_with_log(env: ARCEnvironment, agent: ActiveSoarAgent,
                             log_path, quiet: bool) -> dict:
    results = env.run_benchmark(agent)
    correct = results["correct"]
    total = results["total"]
    pct = (correct / total * 100) if total else 0.0

    per_task_lines = [
        f"[task] {r['task_id']}  reward={r['reward']:.1f}  submissions={r['num_submissions']}"
        for r in results["results"]
    ]
    summary_line = f"[summary] correct={correct}/{total} ({pct:.1f}%)"

    if not quiet:
        for line in per_task_lines:
            print(line)
        print("-" * 62)
        print(summary_line)

    if log_path:
        for line in per_task_lines:
            _append_log(log_path, line)
        _append_log(log_path, "-" * 62)
        _append_log(log_path, summary_line)

    return results


def _print_run_header(args, task_list) -> None:
    """로그 최상단에 실행 정보를 출력한다."""
    import sys as _sys
    w = 62
    print("=" * w)
    print(f"  [ARC-solver] {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  cmd  : {' '.join(_sys.argv)}")
    print(f"  mode : {args.mode}")
    if len(task_list) <= 6:
        print(f"  tasks: {' '.join(task_list)}  (n={len(task_list)})")
    else:
        preview = ' '.join(task_list[:3])
        print(f"  tasks: {preview} … (n={len(task_list)})")
    print(f"  steps: max_steps={args.max_steps}  max_attempts={args.max_attempts}", end="")
    if args.time_budget:
        print(f"  time_budget={args.time_budget}s", end="")
    print()
    print(f"  log  : log_wm={args.log_wm}  quiet={args.quiet}")
    print("=" * w)
    print()


def main():
    args = _parse_args()
    task_list = _build_task_list(args)

    try:
        _main(args, task_list)
    except Exception:
        raise


def _main(args, task_list):
    """실제 실행 로직."""

    log_path = None
    tee = None

    if args.mode == "eval":
        run_dir, mem_roots = _prepare_eval_run()
        log_path = run_dir / "run.log"

        # eval 모드: run.log에 전체 stdout tee (WM 로그 포함)
        tee = _Tee(log_path)
        sys.stdout = tee

        _print_run_header(args, task_list)
        if not args.quiet:
            print(f"[eval] 결과 경로: {run_dir}")
        print()

    else:
        mem_roots = {
            "semantic_memory_root": args.sm_root,
            "episodic_memory_root": "episodic_memory",
            "procedural_memory_root": "procedural_memory",
        }
        if args.log_out:
            log_path = Path(args.log_out)
            log_path.parent.mkdir(parents=True, exist_ok=True)

        # train 모드: run_logs/MMDD_HHMM.log에 tee
        if args.out_dir and args.out_dir.lower() != "none":
            out_path = Path(args.out_dir) / f"{datetime.now():%m%d_%H%M}.log"
            tee = _Tee(out_path)
            sys.stdout = tee
            print(f"[run-log] {out_path}")
            _print_run_header(args, task_list)

    env = ARCEnvironment(
        task_list=task_list,
        time_budget_sec=args.time_budget,
        max_attempts_per_task=args.max_attempts,
        semantic_memory_root=mem_roots["semantic_memory_root"],
    )
    agent = ActiveSoarAgent(
        semantic_memory_root=mem_roots["semantic_memory_root"],
        episodic_memory_root=mem_roots["episodic_memory_root"],
        procedural_memory_root=mem_roots["procedural_memory_root"],
        max_steps=args.max_steps,
        log_wm=args.log_wm,
    )

    if len(task_list) == 1:
        env.reset(task_list=task_list)
        _run_single_verbose(env, agent, task_list[0], log_path if args.mode != "eval" else None, args.quiet)
    else:
        _run_benchmark_with_log(env, agent, log_path if args.mode != "eval" else None, args.quiet)

    if args.trace_out:
        env.save_trace(args.trace_out)

    if tee:
        tee.close()


if __name__ == "__main__":
    main()
