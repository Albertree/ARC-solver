#!/usr/bin/env bash
# run.sh — 자주 쓰는 실행 커맨드 모음
# 실행할 커맨드의 주석을 해제하고:  bash run.sh

# ──────────────────────────────────────────────────────────
# train 모드
# ──────────────────────────────────────────────────────────

# 단일 태스크
# python run.py --task 08ed6ac7

# 복수 태스크
python run.py --task 08ed6ac7 007bbfb7

# 단일 태스크 + WM 로그 (run_logs/MMDD_HHMM.log 자동 저장)
# python run.py --task 08ed6ac7 --log-wm

# 단일 태스크 + WM 로그 + 저장 끄기
# python run.py --task 08ed6ac7 --log-wm --out-dir none

# 단일 태스크 + 스텝 수 조정
# python run.py --task 08ed6ac7 --max-steps 1

# 시퀀스 파일
# python run.py --seq my_tasks.txt

# training split 랜덤 10개
# python run.py --split training --n 10 --seed 0

# training split 전체
# python run.py --split training

# ──────────────────────────────────────────────────────────
# eval 모드  (eval_result/run_MMDD_HHMM/ 자동 생성)
# ──────────────────────────────────────────────────────────

# python run.py --mode eval --task 08ed6ac7

# python run.py --mode eval --task 08ed6ac7 007bbfb7

# python run.py --mode eval --split evaluation --n 20 --seed 0

# ──────────────────────────────────────────────────────────
# 메모리 초기화
# ──────────────────────────────────────────────────────────

# python init.py           # dry-run (변경 없음, 목록만 출력)
# python init.py --confirm # 실제 초기화
