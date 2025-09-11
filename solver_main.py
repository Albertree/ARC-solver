from workers.arc_solver import ARCSolver
from managers.arc_manager import ARCManager
from basics.utils import printcg

if __name__ == "__main__":
    # TASK_HEX_CODE = "08ed6ac7"
    # TASK_HEX_CODE = "007bbfb7"
    # TASK_HEX_CODE = "a61f2674" # 가장 길고 짧은 회색 막대 파랑 빨강으로 칠하고 나머지 회색막대 지우기
    # TASK_HEX_CODE = "aabf363d" # 객체 좌하단 픽셀 색으로 색칠하기
    TASK_HEX_CODE = "ae3edfdc" # 빨강 파랑 점 기준으로 픽셀 모임
    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    solver = ARCSolver(TASK_HEX_CODE)
    # solver.try_DSL()
    solver.test() 
    # solver.object_mapping()