# from ARCKG.grid import GRID
from managers.arc_manager import ARCManager
import os
import ast
import json
# from .program_optimizer import ProgramOptimizer
from ARCKG.comparison import * 
from pprint import pprint
from program_gen import ProgramManager, get_matching_actions

from DSL.apply import *
from DSL.object_finder import *
from DSL.selection import *
from DSL.layer import *
from DSL.transformation import *
from basics.utils import printcg, print_grids_side_by_side


class ARCSolver:
    def __init__(self, task_hex_code: str, interactive: bool = True):
        self.task = ARCManager.from_hex_code(task_hex_code)
        self.task_hex_code = task_hex_code
        self.program_manager = ProgramManager()
        self.interactive = interactive
        # self.programs = []  # Store programs for each pair

    # def solve(self):
    #     for i, pair in enumerate(self.task.example_pairs):
    #         print(f"Processing example pair {i} for task {self.task_hex_code}")
    #         lv1_program = self.program_manager.generate_program(pair, i)
    #         self.program_manager.save_program(lv1_program, i, "GRID", self.task_hex_code)
    #         # lv2_program = self._generate_level_2_program(lv1_program, pair, i)
    #         # lv3_program = self._generate_level_3_program(lv2_program, pair, i)
        
    #     print(f"Level 1 programs generated for task {self.task_hex_code} in 'result_code'")
    #     if lv1_program:
    #         for line in lv1_program:
    #             print(line)

    # def try_DSL(self):
    #     input_grid = self.task.example_pairs[0].input_grid
    #     grid = apply_DSL(input_grid, make_grid, 10, 10, 1)
    #     grid = apply_DSL(grid, coloring, [(0, 0), (1, 1), (2, 2)], 7)
    #     printcg(grid.view)
    #     breakpoint()

    def _set_goal_from_task_and_pairs(self):
        """
        목적 세우기 (수도코드 1. TASK 수준).
        TASK property만으로는 목적 불명 → 각 PAIR 노드 property 확인 → 목적 설정.
        """
        task = self.task
        if not hasattr(task, "property") or not task.property:
            if hasattr(task, "update_property"):
                task.update_property()
            task.property = getattr(task, "property", {})
        task.property.setdefault("example_pair_count", len(task.example_pairs))
        task.property.setdefault("test_pair_count", len(task.test_pairs))

        example_pair_count = task.property["example_pair_count"]
        test_pair_count = task.property["test_pair_count"]
        pair_counts_by_type = {"example": [], "test": []}

        for pair in task.example_pairs:
            gc = pair.property.get("grid_count")
            if gc is None:
                gc = len(getattr(pair, "childs", [pair.input_grid, pair.output_grid]))
            pair_counts_by_type["example"].append(gc)
        # test pair는 문제 풀이 시 정답(output grid)을 보면 안 되므로, property 상으로는 grid 1개(입력만)로 취급
        for _ in task.test_pairs:
            pair_counts_by_type["test"].append(1)

        # test pair에는 grid가 적은 경우가 많음 (예: 1개) → 없는 그리드를 생성하는 것이 목적
        self.goal = "create_missing_grid"
        self._goal_reason = (
            f"TASK property: example_pair_count={example_pair_count}, test_pair_count={test_pair_count}; "
            f"example grid_counts={pair_counts_by_type['example']}, test grid_counts={pair_counts_by_type['test']} "
            f"→ 목적: test pair에 없는 그리드 생성 (test pair의 output grid 만들기)"
        )
        print(f"[목적 세우기] {self._goal_reason}")

    def _ensure_grid_property(self, grid):
        """Grid에 property가 있도록 함 (compare가 property를 사용)."""
        if not getattr(grid, "property", None) or not grid.property:
            if hasattr(grid, "update_property"):
                grid.update_property()
            grid.property = getattr(grid, "property", {})

    def _grid_compare_is_3of3(self, grid_a, grid_b) -> bool:
        """두 그리드 비교 시 score가 3/3 (size, color, contents 모두 일치)인지. docs/grid_level_prediction_flow.md 기준."""
        self._ensure_grid_property(grid_a)
        self._ensure_grid_property(grid_b)
        try:
            res = compare(grid_a, grid_b, save=False)
            score = res.get("result", {}).get("score", "0/0")
            parts = score.split("/")
            if len(parts) != 2:
                return False
            comm, total = int(parts[0]), int(parts[1])
            return total > 0 and comm == total
        except Exception:
            return False

    def _compare_grids_across_pairs(self):
        """
        PAIR 간 GRID 비교. test input(PaG0, PbG0)은 각각 해당 test pair의 G1 예측 시에만 사용.
        - 먼저 example pair끼리만 비교 (P0G0-P1G0, P0G1-P1G1 등).
        - 그 다음 test pair별로 독립: PaG0는 PaG1 예측할 때만 쓰이도록 PaG0 vs P0G0, P1G0 등만 비교.
        """
        from ARCKG.memory_paths import MEMORY_ROOT

        task = self.task

        def _grid_index_from_label(lbl: str) -> int:
            try:
                return int(lbl.split("G")[1])
            except (ValueError, IndexError):
                return -1

        def _run_compare(label_i, grid_i, label_j, grid_j):
            try:
                result = compare(grid_i, grid_j, save=True, label1=label_i, label2=label_j)
                score = result.get("result", {}).get("score", "?/?")
                saved = result.get("saved_path", "")
                print(f"  {label_i} - {label_j} → score = {score}  저장: {saved}")
            except Exception as e:
                print(f"  {label_i} - {label_j} → 오류: {e}")

        # 1) Example pair끼리만 비교 (test input 미포함)
        print("  [Solver] PAIR 간 GRID 비교 — example만 (P0G0,P0G1, P1G0,P1G1)")
        grids_with_labels = []
        for i, pair in enumerate(task.example_pairs):
            self._ensure_grid_property(pair.input_grid)
            self._ensure_grid_property(pair.output_grid)
            grids_with_labels.append((f"P{i}G0", pair.input_grid))
            grids_with_labels.append((f"P{i}G1", pair.output_grid))

        print(f"\n[PAIR 간 GRID 비교] example 그리드 {len(grids_with_labels)}개 → G가 같은 것만 비교")
        print(f"[PAIR 간 GRID 비교] 저장 루트: {MEMORY_ROOT}")
        for i in range(len(grids_with_labels)):
            for j in range(i + 1, len(grids_with_labels)):
                label_i, grid_i = grids_with_labels[i]
                label_j, grid_j = grids_with_labels[j]
                pi, pj = label_i[1:].split("G")[0], label_j[1:].split("G")[0]
                if pi == pj:
                    continue  # 같은 PAIR 내부 제외
                if _grid_index_from_label(label_i) != _grid_index_from_label(label_j):
                    continue
                _run_compare(label_i, grid_i, label_j, grid_j)

        # 2) Test pair별로 독립: PaG0 포함 비교는 PaG1 예측 시에만 사용되도록, PbG0는 PbG1 예측 시에만
        for test_idx, test_pair in enumerate(task.test_pairs):
            self._ensure_grid_property(test_pair.input_grid)
            letter = chr(ord("a") + test_idx)
            test_label = f"P{letter}G0"
            test_grid = test_pair.input_grid
            print(f"\n[PAIR 간 GRID 비교] test pair P{letter} (P{letter}G0 ↔ example G0만 비교)")
            for i, pair in enumerate(task.example_pairs):
                ex_label = f"P{i}G0"
                _run_compare(ex_label, pair.input_grid, test_label, test_grid)

        print("[PAIR 간 GRID 비교] 완료\n")
        print("  [Solver] PaG1 예측 시도 (test pair별 독립)")
        self._predict_test_g1()

    def _predict_test_g1(self):
        """
        PAIR 간 GRID 비교 이후: test output(PaG1) 예측 시도. docs/grid_level_prediction_flow.md 기준.
        Step 1: input 일치(3/3) → output 복사
        Step 2: 모든 example output 동일(3/3) → 그 output 사용
        Step 3: (fallback) size/color/contents 모두 동일 → contents 복사. 불가 시 예측 불가 → OBJECT/PIXEL로.
        """
        import copy
        task = self.task
        n_test = len(task.test_pairs)
        self._pa_g1_prediction_attempted = False
        self._pa_g1_prediction_correct = False
        self._test_output_predictions = [None] * n_test
        self._test_output_prediction_candidates_list = [None] * n_test
        self._pa_g1_correct_per_pair = [False] * n_test
        if not task.test_pairs:
            print("[PaG1 예측] test pair 없음 → 스킵")
            return
        examples = task.example_pairs
        if not examples:
            print("[PaG1 예측] example pair 없음 → 예측 불가 (OBJECT/PIXEL로)")
            return

        test_letters = [chr(ord("a") + i) for i in range(n_test)]
        lines = []
        lines.append("\n[PaG1 예측] test pair별 독립 예측 — Step1 input일치 → Step2 output동일 → Step3 all-same")

        for test_idx, test_pair in enumerate(task.test_pairs):
            letter = test_letters[test_idx]
            test_input = test_pair.input_grid
            self._ensure_grid_property(test_input)
            lines.append(f"  --- P{letter}G1 (test pair {letter}) ---")

            pred_contents = None
            step1_candidates = []  # input 일치하는 여러 k의 output (서로 다를 수 있음)

            # Step 1: input_grid_k == test_input_grid (3/3)인 k의 output 수집 (여러 개면 후보로)
            for k, ex in enumerate(examples):
                if self._grid_compare_is_3of3(ex.input_grid, test_input):
                    out_view = getattr(ex.output_grid, "view", None) or getattr(ex.output_grid, "colorgrid", None) or getattr(ex.output_grid, "raw_data", None)
                    if out_view is not None:
                        view_copy = copy.deepcopy(out_view)
                        # 동일한 view 이미 있으면 제외 (재제출 시 다른 답만 시도)
                        if not self._view_in_list(view_copy, step1_candidates):
                            step1_candidates.append(view_copy)
                        lines.append(f"    Step1: input 일치(3/3) → example P{k} output 수집")
            if step1_candidates:
                pred_contents = step1_candidates[0]
                if len(step1_candidates) > 1:
                    lines.append(f"    Step1: 후보 {len(step1_candidates)}개 (재제출 시 다음 후보 시도)")
                self._apply_prediction_and_compare(test_idx, test_pair, pred_contents, lines, candidates_list=step1_candidates)
                lines.append("")
                continue

            # Step 2: 모든 example output이 동일(3/3)이면 그 output 사용
            first_out = examples[0].output_grid
            all_output_same = True
            for k in range(1, len(examples)):
                if not self._grid_compare_is_3of3(first_out, examples[k].output_grid):
                    all_output_same = False
                    break
            if all_output_same:
                out_view = getattr(first_out, "view", None) or getattr(first_out, "colorgrid", None) or getattr(first_out, "raw_data", None)
                if out_view is not None:
                    pred_contents = copy.deepcopy(out_view)
                    lines.append("    Step2: 모든 example output 동일(3/3) → 그 output 사용")
            if pred_contents is not None:
                self._apply_prediction_and_compare(test_idx, test_pair, pred_contents, lines)
                lines.append("")
                continue

            # Step 3: (fallback) size, color, contents 모두 example G1과 동일한 경우만 예측 가능
            lines.append("    Step1·2 불가 → Step3: size/color/contents 모두 동일 여부 확인")
            example_g1s = [ex.output_grid for ex in examples]
            for g in example_g1s:
                self._ensure_grid_property(g)

            def _norm_size(g):
                p = getattr(g, "property", None) or {}
                s = p.get("size")
                if isinstance(s, dict):
                    return (s.get("height"), s.get("width"))
                return (getattr(g, "height", None), getattr(g, "width", None))

            def _norm_color(g):
                p = getattr(g, "property", None) or {}
                c = p.get("color")
                if c is None:
                    c = getattr(g, "color", None)
                if c is None:
                    return {}
                if isinstance(c, dict):
                    return dict((k, bool(v)) for k, v in sorted(c.items()))
                used = set(str(x) for x in c)
                palette = sorted(set(used) | set(str(i) for i in range(10)))
                return dict((k, k in used) for k in palette)

            def _norm_contents(g):
                p = getattr(g, "property", None) or {}
                return p.get("contents") or getattr(g, "colorgrid", None)

            sizes = [_norm_size(g) for g in example_g1s]
            color_dicts = [_norm_color(g) for g in example_g1s]
            contents_list = [_norm_contents(g) for g in example_g1s]
            all_same_size = len(set(sizes)) == 1 and sizes[0][0] is not None and sizes[0][1] is not None
            all_same_color = len(color_dicts) > 0 and all(d == color_dicts[0] for d in color_dicts)
            all_same_contents = len(contents_list) > 0 and all(c is not None for c in contents_list) and len(set(str(c) for c in contents_list)) == 1

            if all_same_size:
                lines.append(f"    size:   예측 가능 → {sizes[0]}")
            else:
                lines.append("    size:   예측 불가 (example G1들 간 다름)")
            if all_same_color:
                lines.append("    color:  예측 가능 (example G1들 동일)")
            else:
                lines.append("    color:  예측 불가 (example G1들 간 다름)")
            if all_same_contents:
                lines.append("    contents: 예측 가능 (example G1들 동일)")
            else:
                lines.append("    contents: 예측 불가 (example G1들 간 다름)")

            if all_same_size and all_same_color and all_same_contents:
                pred_contents = copy.deepcopy(contents_list[0])
                lines.append("    Step3: size/color/contents 모두 동일 → 예측 그리드 생성")
            else:
                lines.append("    결론: 예측 불가 → OBJECT/PIXEL 분석으로 진행")

            if pred_contents is not None:
                self._apply_prediction_and_compare(test_idx, test_pair, pred_contents, lines)
            lines.append("")

        print("\n".join(lines))
        self._pa_g1_prediction_attempted = any(p is not None for p in self._test_output_predictions)
        self._pa_g1_prediction_correct = (
            self._pa_g1_prediction_attempted
            and all(self._test_output_predictions[i] is not None for i in range(n_test))
            and all(self._pa_g1_correct_per_pair[i] for i in range(n_test))
        )
        if n_test == 1 and self._test_output_predictions[0] is not None:
            self._test_output_prediction = self._test_output_predictions[0]
            self._test_output_prediction_candidates = self._test_output_prediction_candidates_list[0]
        else:
            self._test_output_prediction = None
            self._test_output_prediction_candidates = None

    def _view_in_list(self, view, list_of_views):
        """view가 list_of_views 중 하나와 동일(shape+contents)한지."""
        if not view or not list_of_views:
            return False
        for v in list_of_views:
            if len(view) != len(v) or (view and (len(view[0]) != len(v[0]) if v else True)):
                continue
            if all(view[i][j] == v[i][j] for i in range(len(view)) for j in range(len(view[0]) if view[0] else 0)):
                return True
        return False

    def _apply_prediction_and_compare(self, test_idx: int, test_pair, pred_contents, lines, candidates_list=None):
        """test pair별 예측 저장 및 GT와 비교. candidates_list 있으면 재제출 시 다음 후보 시도용."""
        self._test_output_predictions[test_idx] = pred_contents
        self._test_output_prediction_candidates_list[test_idx] = candidates_list if candidates_list else None
        gt_grid = test_pair.output_grid
        gt_view = getattr(gt_grid, "view", None) or getattr(gt_grid, "raw_data", None) or getattr(gt_grid, "colorgrid", None)
        if gt_view is not None and pred_contents is not None:
            same_shape = len(pred_contents) == len(gt_view) and (
                len(pred_contents) == 0 or (len(gt_view) > 0 and len(pred_contents[0]) == len(gt_view[0]))
            )
            if same_shape:
                match = all(
                    pred_contents[i][j] == gt_view[i][j]
                    for i in range(len(pred_contents))
                    for j in range(len(pred_contents[0]) if pred_contents and len(pred_contents[0]) else 0)
                )
            else:
                match = False
            self._pa_g1_correct_per_pair[test_idx] = match
            lines.append("    [예측 실행] GT와 비교: " + ("일치" if match else "불일치"))
        else:
            self._pa_g1_correct_per_pair[test_idx] = False
            self._test_output_predictions[test_idx] = None
            lines.append("    [예측 실행] GT 또는 예측 없음 → 비교 스킵")

    def _try_make_grid_from_property(self, pair) -> bool:
        """
        그리드 만들기 시도 (수도코드 2. PAIR 수준).
        PAIR 아래 GRID property(size, color, contents)만으로 output grid를 만들 수 있는지 시도.
        하나라도 만들지 못하면 False → GRID 내부 탐색(compare input/output)으로 전환.
        """
        out_g = pair.output_grid
        in_g = pair.input_grid
        if not getattr(out_g, "property", None) or not out_g.property:
            if hasattr(out_g, "update_property"):
                out_g.update_property()
            out_g.property = getattr(out_g, "property", {})
        if not getattr(in_g, "property", None) or not in_g.property:
            if hasattr(in_g, "update_property"):
                in_g.update_property()
            in_g.property = getattr(in_g, "property", {})

        out_size = out_g.property.get("size") or (getattr(out_g, "height", None), getattr(out_g, "width", None))
        in_size = in_g.property.get("size") or (getattr(in_g, "height", None), getattr(in_g, "width", None))
        if out_size and in_size:
            if isinstance(out_size, dict):
                out_h, out_w = out_size.get("height"), out_size.get("width")
            else:
                out_h, out_w = out_size[0], out_size[1]
            if isinstance(in_size, dict):
                in_h, in_w = in_size.get("height"), in_size.get("width")
            else:
                in_h, in_w = in_size[0], in_size[1]
            size_same = (out_h is not None and out_w is not None and in_h is not None and in_w is not None and out_h == in_h and out_w == in_w)
        else:
            size_same = False

        out_colors = set(out_g.property.get("color") or getattr(out_g, "color", []) or [])
        in_colors = set(in_g.property.get("color") or getattr(in_g, "color", []) or [])
        color_covered = bool(out_colors and out_colors <= in_colors) if in_colors else False

        # contents는 property만으로는 셀 단위 채우기 불가 → 항상 실패
        contents_ok = False

        size_ok = size_same
        can_make = size_ok and color_covered and contents_ok
        size_msg = "입력과 동일" if size_same else "결정 불가"
        color_msg = "입력 색으로 커버 가능" if color_covered else "결정 불가"
        print(
            f"[그리드 만들기 시도] size={size_msg}, color={color_msg}, contents=직접 생성 불가 "
            f"→ {'그리드 직접 생성 가능' if can_make else 'GRID 내부 탐색으로 전환'}"
        )
        return can_make

    def _compare_pair_components(self, pair0, pair1, pair0_idx: int, pair1_idx: int):
        """
        PAIR 간 OBJECT 레벨 비교 (수도코드 3.3).
        pair0 vs pair1: P0G0 객체들 vs P1G0 객체들, P0G1 객체들 vs P1G1 객체들 비교 후 memory에 저장.
        """
        task_hex = self.task_hex_code
        self._ensure_grid_property(pair0.input_grid)
        self._ensure_grid_property(pair0.output_grid)
        self._ensure_grid_property(pair1.input_grid)
        self._ensure_grid_property(pair1.output_grid)

        def _ensure_obj_property(obj):
            if not getattr(obj, "property", None):
                obj.property = {}

        def _compare_objects_from_grids(grid0, grid1, label_g0: str, label_g1: str):
            objs0 = getattr(grid0, "objects", []) or []
            objs1 = getattr(grid1, "objects", []) or []
            for i, o0 in enumerate(objs0):
                _ensure_obj_property(o0)
                for j, o1 in enumerate(objs1):
                    _ensure_obj_property(o1)
                    compare(o0, o1, save=True, label1=f"{label_g0}O{i}", label2=f"{label_g1}O{j}")

        # P0G0 vs P1G0 (input grids)
        _compare_objects_from_grids(
            pair0.input_grid, pair1.input_grid,
            f"P{pair0_idx}G0", f"P{pair1_idx}G0"
        )
        # P0G1 vs P1G1 (output grids)
        _compare_objects_from_grids(
            pair0.output_grid, pair1.output_grid,
            f"P{pair0_idx}G1", f"P{pair1_idx}G1"
        )
        print(f"[PAIR 간 OBJECT 비교] P{pair0_idx}↔P{pair1_idx}: P{pair0_idx}G0-P{pair1_idx}G0, P{pair0_idx}G1-P{pair1_idx}G1 객체 비교 완료 → memory/N_T{task_hex}/")

    def test(self):
        if not getattr(self, "goal", None):
            self._set_goal_from_task_and_pairs()

        # PAIR 간 GRID 비교 (pair-program 생성보다 먼저): 엣지 생성, symbolic distance 확인
        self._compare_grids_across_pairs()

        # 예측으로 test output 일치 시 여기서 종료 (pair 루프·이후 단계 모두 브랜칭 아웃)
        if getattr(self, "_pa_g1_prediction_attempted", False) and getattr(self, "_pa_g1_prediction_correct", False):
            self._finished_by_pa_g1_prediction = True
            print("  [Solver] PaG1 성공 → test output 일치, pair program 생성 생략")
            return
        self._finished_by_pa_g1_prediction = False
        print("  [Solver] PaG1 불가 → example PAIR별 GRID→OBJECT→PIXEL 프로그램 생성·실행")
        if self.interactive:
            input("[PAIR 간 GRID 비교] 다음 단계(pair program 생성)로 진행하려면 Enter를 누르세요... ")

        for pair_idx, pair in enumerate(self.task.example_pairs):
            if len(pair.program) == 0:
                # no prgrogram in PAIR -> Do deeper analysis of a PAIR to make program
                print(f"  [Solver] PAIR {pair_idx} program 없음 → input↔output 비교·프로그램 생성")
                print(f"PAIR {pair_idx} has no program -> Do deeper analysis of a PAIR to make program")

                # ==================== 그리드 만들기 시도 (transition 전) ====================
                if self._try_make_grid_from_property(pair):
                    # 직접 생성 가능(이론상) → 여기서 실제 생성하면 됨. 현재는 미구현.
                    print(f"[PAIR {pair_idx}] 그리드 property만으로 생성 가능 → 스킵(미구현)")
                    continue
                # 직접 생성 불가 → GRID 내부 탐색(입력 vs 출력 비교)으로 전환

                # ==================== GRID LEVEL ====================
                print(f"  [Solver] PAIR {pair_idx} GRID level: input↔output 비교, rule 추출·프로그램 생성·실행")
                print(f"\n=== GRID Level Program Generation ===")
                comparison_result = compare(pair.input_grid, pair.output_grid, save=True)
                rules = get_matching_actions(comparison_result)
                
                # Generate GRID program
                if rules:
                    grid_program = self.program_manager.generate_program_with_rules(pair, pair_idx, rules)
                    self.program_manager.save_program(grid_program, pair_idx, "GRID", self.task_hex_code)
                    print(f"✅ GRID program generated with {len(rules)} rules")
                else:
                    # Create a basic GRID program with wrapper structure
                    grid_program = self.program_manager.generate_program_with_rules(pair, pair_idx, [])
                    self.program_manager.save_program(grid_program, pair_idx, "GRID", self.task_hex_code)
                    print(f"⚠️ No GRID rules found, created basic program")

                # Execute GRID program to get result for OBJECT level
                print(f"\n=== GRID Level Program Execution ===")
                grid_result = self.program_manager.execute_saved_program(pair_idx, "GRID", self.task_hex_code)
                
                if grid_result:
                    print("  [Solver] GRID level: Input | Output | GT")
                    print_grids_side_by_side(
                        ["Input", "Output", "GT"],
                        [pair.input_grid, grid_result, pair.output_grid],
                    )
                    if grid_result.view == pair.output_grid.view:
                        print(f"✅ GRID program successfully solves PAIR {pair_idx}!")
                        if pair_idx >= 1:
                            self._compare_pair_components(self.task.example_pairs[0], pair, 0, pair_idx)
                        continue  # Success! Move to next pair
                    else:
                        print(f"❌ GRID program cannot solve PAIR {pair_idx} -> proceeding to OBJECT level")
                else:
                    print(f"❌ Failed to execute GRID program for PAIR {pair_idx}")
                    grid_result = pair.input_grid



                    # comparison_result = compare(code_result, pair.output_grid, save=False)
                    # path = id_pair_to_comparison_path(get_component_full_id(code_result), get_component_full_id(pair.output_grid))
                    # path = f"{self.task_hex_code}_PAIR_{pair_idx}-GRID-level_TFG{pair_idx}.json"
                    
                    # save_comparison_result(comparison_result, path)
                    # print("^^^ above is comparison result of code_result and output_grid ^^^")
                    # breakpoint()

                # breakpoint()  # Commented out to allow OBJECT generation to proceed





                # ==================== OBJECT LEVEL ====================
                print(f"  [Solver] PAIR {pair_idx} OBJECT level: 객체 비교·rule 추출·프로그램 생성·실행")
                print(f"\n=== OBJECT Level Program Generation ===")
                print(f"Comparing {len(grid_result.objects)} objects in GRID result and {len(pair.output_grid.objects)} objects in output grid")
                
                # Accumulate all actions from all object comparisons
                all_object_actions = []
                for obj_i in grid_result.objects:
                    for obj_o in pair.output_grid.objects:
                        comparison_result = compare(obj_i, obj_o, save=True)
                        rules = get_matching_actions(comparison_result)
    
                        if rules:
                            all_object_actions.extend(rules)
                
                # Generate OBJECT program starting from GRID program
                if all_object_actions:
                    print(f"Found {len(all_object_actions)} total object actions, generating OBJECT program...")
                    # Start with GRID program and add OBJECT actions
                    object_program = self.program_manager.generate_program_with_rules(pair, pair_idx, all_object_actions, base_program=grid_program)
                    self.program_manager.save_program(object_program, pair_idx, "OBJECT", self.task_hex_code)
                else:
                    # No OBJECT actions found, use GRID program as OBJECT program
                    print(f"⚠️ No OBJECT rules found, using GRID program as OBJECT program")
                    self.program_manager.save_program(grid_program, pair_idx, "OBJECT", self.task_hex_code)

                # Execute OBJECT program to get result for PIXEL level
                print(f"\n=== OBJECT Level Program Execution ===")
                object_result = self.program_manager.execute_saved_program(pair_idx, "OBJECT", self.task_hex_code)
                
                if object_result:
                    print("  [Solver] OBJECT level: Input | Output | GT")
                    print_grids_side_by_side(
                        ["Input", "Output", "GT"],
                        [pair.input_grid, object_result, pair.output_grid],
                    )
                    if object_result.view == pair.output_grid.view:
                        print(f"✅ OBJECT program successfully solves PAIR {pair_idx}!")
                        if pair_idx >= 1:
                            self._compare_pair_components(self.task.example_pairs[0], pair, 0, pair_idx)
                        continue  # Success! Move to next pair
                    else:
                        print(f"❌ OBJECT program cannot solve PAIR {pair_idx} -> proceeding to PIXEL level")
                else:
                    print(f"❌ Failed to execute OBJECT program for PAIR {pair_idx}")
                    object_result = grid_result


                # ==================== OBJECT LEVEL ====================
                # Perform object comparisons
                for i, obj1 in enumerate(pair.input_grid.objects):
                    for j, obj2 in enumerate(pair.output_grid.objects):
                        comparison = compare(obj1, obj2, save=True)

                # make rules from object comparison result

                # breakpoint()  # Commented out to allow PIXEL generation to proceed


                # make program using object comparison result
                








                # ==================== PIXEL LEVEL ====================
                print(f"  [Solver] PAIR {pair_idx} PIXEL level: 픽셀 비교·rule 추출·프로그램 생성·실행")
                print(f"\n=== PIXEL Level Program Generation ===")
                print(f"Comparing {len(object_result.pixels)} pixels in OBJECT result and {len(pair.output_grid.pixels)} pixels in output grid")
                
                # Debug: Check object_result properties
                print(f"OBJECT result grid size: {object_result.height}x{object_result.width}")
                print(f"OBJECT result colorgrid size: {len(object_result.colorgrid)}x{len(object_result.colorgrid[0]) if object_result.colorgrid else 'N/A'}")
                print(f"Output grid size: {pair.output_grid.height}x{pair.output_grid.width}")
                print(f"Output grid colorgrid size: {len(pair.output_grid.colorgrid)}x{len(pair.output_grid.colorgrid[0]) if pair.output_grid.colorgrid else 'N/A'}")
                
                # Accumulate all actions from all pixel comparisons
                all_pixel_actions = []
                for pix_i in object_result.pixels:
                    for pix_o in pair.output_grid.pixels:
                        comparison_result = compare(pix_i, pix_o, save=True)
                        rules = get_matching_actions(comparison_result)
                
                        if rules:
                            all_pixel_actions.extend(rules)
                
                # Generate PIXEL program starting from OBJECT program
                if all_pixel_actions:
                    print(f"Found {len(all_pixel_actions)} total pixel actions, generating PIXEL program...")
                    # Get the OBJECT program to use as base
                    object_program = self.program_manager.load_program(pair_idx, "OBJECT", self.task_hex_code)
                    if object_program:
                        object_program_lines = object_program.split('\n')
                    else:
                        object_program_lines = grid_program
                    # Start with OBJECT program and add PIXEL actions
                    pixel_program = self.program_manager.generate_program_with_rules(pair, pair_idx, all_pixel_actions, base_program=object_program_lines)
                    self.program_manager.save_program(pixel_program, pair_idx, "PIXEL", self.task_hex_code)
                else:
                    # No PIXEL actions found, use OBJECT program as PIXEL program
                    print(f"⚠️ No PIXEL rules found, using OBJECT program as PIXEL program")
                    object_program = self.program_manager.load_program(pair_idx, "OBJECT", self.task_hex_code)
                    if object_program:
                        object_program_lines = object_program.split('\n')
                        self.program_manager.save_program(object_program_lines, pair_idx, "PIXEL", self.task_hex_code)
                    else:
                        self.program_manager.save_program(grid_program, pair_idx, "PIXEL", self.task_hex_code)

                # Execute and verify PIXEL level program
                print(f"\n=== PIXEL Level Program Execution ===")
                try:
                    code_result = self.program_manager.execute_saved_program(pair_idx, "PIXEL", self.task_hex_code)
                    
                    if code_result:
                        print("  [Solver] PIXEL level: Input | Output | GT")
                        print_grids_side_by_side(
                            ["Input", "Output", "GT"],
                            [pair.input_grid, code_result, pair.output_grid],
                        )
                        if code_result.view == pair.output_grid.view:
                            print(f"✅ PIXEL program successfully solves PAIR {pair_idx}!")
                        else:
                            print(f"❌ PIXEL program cannot solve PAIR {pair_idx}")
                    else:
                        print(f"❌ Failed to execute PIXEL program for PAIR {pair_idx}")
                except Exception as e:
                    print(f"❌ PIXEL program execution failed for PAIR {pair_idx}: {e}")
                    print("Continuing to next pair...")

                if pair_idx >= 1:
                    self._compare_pair_components(self.task.example_pairs[0], pair, 0, pair_idx)

                # print(f"{len(pair.input_grid.pixels) * len(pair.output_grid.pixels)} PIXEL comparisons are completed!")

                # make rules from pixel comparison result

                # breakpoint()  # Commented out to allow full execution


                # make GRID level program using grid, object, pixel comparison result
            

            if self.interactive:
                input(f"[PAIR {pair_idx} 처리 완료] 다음으로 진행하려면 Enter를 누르세요... ")

        print("[Solver.test] 모든 pair 처리 완료")

    def temp_solve(self):
        """Temporary solve method for testing"""
        for pair_idx, pair in enumerate(self.task.example_pairs):
            print(f"Processing pair {pair_idx}")
            
            # Generate and save program
            program = self.program_manager.generate_and_save_program(pair, pair_idx, level="GRID")
            
            # Execute the program
            result = self.program_manager.execute_saved_program(pair_idx, "GRID")
            
            if result:
                print(f"Pair {pair_idx} result:")
                # printcg(result.view)
            else:
                print(f"Failed to execute program for pair {pair_idx}")






    def object_mapping(self):
        def color_text_no_bg(index, text):
            COLORS = {
                0: (0, 0, 0),         # black
                1: (0, 116, 217),     # blue
                2: (255, 65, 54),     # red
                3: (46, 204, 64),     # green
                4: (255, 220, 0),     # yellow
                5: (170, 170, 170),   # gray
                6: (240, 18, 190),    # pink
                7: (255, 133, 27),    # orange
                8: (127, 219, 255),   # light blue
                9: (135, 12, 37),     # dark red
                10: (128, 0, 128),    # purple
                11: (0, 128, 128),    # teal
                12: (101, 67, 33),    # brown
                13: (214, 255, 255),  # white
                14: (79, 79, 79)      # dark gray
            }
            r, g, b = COLORS[index]
            return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


        def visualize_objects_side_by_side(obj1, obj2):
            print("\nOBJECT COMPARISON")
            max_height = max(len(obj1.view), len(obj2.view))
            max_width1 = max(len(row) for row in obj1.view) if obj1.view else 0
            max_width2 = max(len(row) for row in obj2.view) if obj2.view else 0
            
            print("Object 1          |  Object 2")
            print("-" * 60)
            for i in range(max_height):
                if i < len(obj1.view):
                    row1 = obj1.view[i]
                    colored1 = ''.join([color_text_no_bg(val, "██") for val in row1])
                else:
                    colored1 = ' ' * (max_width1 * 2)  # Empty row with proper width
                
                if i < len(obj2.view):
                    row2 = obj2.view[i]
                    colored2 = ''.join([color_text_no_bg(val, "██") for val in row2])
                else:
                    colored2 = ' ' * (max_width2 * 2)  # Empty row with proper width
                
                obj1_width = max_width1 * 2
                print(f"{colored1:<{obj1_width}} | {colored2}")
            print()


        task = self.task
        pair = task.example_pairs[0]
        comp1 = pair.input_grid
        comp2 = pair.output_grid

        total_comparisons = len(comp1.objects) * len(comp2.objects)
        comparison_count = 0

        for i, obj1 in enumerate(comp1.objects):
            for j, obj2 in enumerate(comp2.objects):
                comparison_count += 1
                print("\033[2J\033[H", end='', flush=True)
                print(f"Comparison {comparison_count}/{total_comparisons} - Object {i} vs Object {j}")
                
                visualize_objects_side_by_side(obj1, obj2)
                comparison = compare(obj1, obj2, save=True)

                score = int(comparison["result"]["score"].split("/")[0])
                total_checks = int(comparison["result"]["score"].split("/")[1])
                
                print(f"Score: {score}/{total_checks}")
                
                if score > 4:
                    print("\n" + "-" * 70)
                    print(f"OBJECT COMPARISON SUMMARY [score: {score}/{total_checks}]")
                    print()
                    
                    pprint(comparison["result"]["category"])
                    
                    # print()
                    print("Controls: [Enter] = Next comparison | [q] = Quit")
                    if self.interactive:
                        user_input = input().strip().lower()
                    else:
                        user_input = ""
                    if user_input == 'q':
                        print("Exiting...")
                        exit()
                else:
                    continue

        print(f"\nCompleted all {total_comparisons} comparisons!")


if __name__ == "__main__":
    solver = ARCSolver("007bbfb7")
    solver.test()
