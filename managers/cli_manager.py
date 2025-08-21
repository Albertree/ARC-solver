import sys
import time
from datetime import datetime
from tqdm import tqdm
from ARCKG.grid import GRID
from components.transformation_history import TFHistory
from ARCKG.types.type import RawData_Type
from tools.grid_visualizers import color_text



class CLIManager():
    GRID_SEPARATOR ="\t\t"
    LABEL_SEPARATOR="\t\t\t"

    def __init__(self) -> None:
        self._pbar = tqdm(total=100, desc="Progress", unit="%", position=0)
        self._last_percentage = 0
        self._log = []
    
    def three_grid_layout(self, left:RawData_Type, center:RawData_Type, right:RawData_Type, sep=GRID_SEPARATOR):
        rows = []
        for i in range(len(left)):
            left_row = ''.join(color_text(color_str) for color_str in left[i])
            center_row = ''.join(color_text(color_str) for color_str in center[i])
            right_row = ''.join(color_text(color_str) for color_str in right[i])
            rows.append(f"{left_row}{sep}{center_row}{sep}{right_row}")
        return "\n".join(rows)

    def update_current_grid(self, input_grid: GRID, current_grid: GRID, output_grid: GRID,time_interval:float) -> None:
        # 커서를 그리드 시작점으로 이동 (라벨 포함, 라벨 1줄 + grid row 수)
        total_lines = len(input_grid.raw_data) + 1
        sys.stdout.write("\033[F" * total_lines)
        sys.stdout.flush()

        grid_str = self.three_grid_layout(input_grid.raw_data, current_grid.raw_data, output_grid.raw_data)
        latest_log = self._log[-1] if self._log else ""
        sys.stdout.write(grid_str + "\n" + latest_log + "\n")
        sys.stdout.flush()
        time.sleep(time_interval)

    def update_log(self,log:str)-> None:
        log_string = self._timestamp()+"   "+log+"                               "
        self._log.append(log_string)

    def update_progress(self,percentage:int) -> bool :
        if percentage > self._last_percentage:
            self._pbar.update(percentage - self._last_percentage)
            self._last_percentage = percentage
        time.sleep(0.5)

        if percentage >= 100:
            self._pbar.close()
            return True
            
        else :
            return False

    def visualize_tf_history(self, tf_history: TFHistory) -> None:
        input_grid = tf_history.pair_id.input_grid
        output_grid = tf_history.pair_id.output_grid
        current_grid = tf_history.initial_grid

        # ✅ 최초 한 번만 라벨과 초기 상태 출력
        print(f"\ninput_grid {self.LABEL_SEPARATOR} current_grid {self.LABEL_SEPARATOR} output_grid")
        print(self.three_grid_layout(input_grid.raw_data, current_grid.raw_data, output_grid.raw_data))

        print(" Visualizing transformation history for pair " + str(tf_history.pair_id.id))
        self.update_current_grid(input_grid, current_grid, output_grid,time_interval=0)


        if tf_history.steps:
            self.update_log(f"Applying {len(tf_history.steps)} transformation(s):")
            self.update_current_grid(input_grid, current_grid, output_grid,time_interval=0.5)


            for i, transformation in enumerate(tf_history.steps):
                transformation_result = transformation.execute()
                if transformation_result:
                    self.update_log(f"Step {i+1} {type(transformation).__name__}")
                    self.update_current_grid(input_grid, current_grid, output_grid,time_interval=1)

                    self.update_log("  → " + str(transformation_result))
                    self.update_current_grid(input_grid, current_grid, output_grid,time_interval=1)
                    self.update_progress((i+1)*100//len(tf_history.steps))
                    
        else:
            self.update_log("No transformation steps detected.")
            self.update_current_grid(input_grid, current_grid, output_grid,time_interval=0.3)


        self.update_log("Transformation visualization complete.")
        self.update_current_grid(input_grid, current_grid, output_grid,time_interval=0.3)



    def _clear(self):
        # ANSI escape code 사용 (cross-platform, 단 Windows cmd는 ANSI 지원 필요)
        print("\033[H\033[J", end="")

    def _timestamp(self) -> str:
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

    def print_log(self) : 
        for log in self._log :
            print(log)


