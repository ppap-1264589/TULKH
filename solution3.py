"""
BÀI TOÁN XẾP LỊCH HỌC (Class Scheduling with OR-Tools)
=========================================================

PROBLEM STATEMENT:
  Cho n lớp học và m phòng. Mỗi lớp thứ i trong n lớp có:
  - Thời lượng d[i], giáo viên dạy g[i], sĩ số s[i]
  Mỗi phòng j trong m phòng có:
  - Sức chứa c[j]
  Thời lượng của mỗi ngày:
  - 12 tiết
  Mỗi ngày có hai nửa ngày:
  - Mỗi nửa gồm 6 tiết
  
  Yêu cầu: Xếp lịch và gán phòng cho 1 tuần sao cho:
  1. Tổng thời lượng trong một tuần gồm 5 ngày (tổng cộng 5*12 = 60 tiết)
  2. Một lớp không được dài vượt quá nửa hoặc cuối ngày
  3. Một giáo viên không dạy trùng tkb
  4. Phòng đủ sức chứa cho lớp
  5. Tối đa hóa số lớp được xếp

LIMIT:
  - Lớp nào cũng tồn tại ít nhất một phòng đủ chỗ để gán
  - Không có lớp nào lại dài hơn cả thời lượng của nửa ngày
  - Tất cả các lớp chỉ có 1, 2, 3 hoặc 4 tiết

APPROACH:
  CP-SAT solving

INPUT/OUTPUT:
  Input:  input.txt (n, m, d[i], g[i], s[i], c[j])
  Output: output.txt (class_id start_time room_id for each scheduled_class)
"""

from ortools.sat.python import cp_model
import sys
import os


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                     PHẦN 1: DỮ LIỆU INPUT & HẰNG SỐ                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# -------- Dữ liệu đầu vào từ input.txt --------
n, m = 0, 0         # Số lớp, số phòng
duration = []       # duration[i] = thời lượng lớp i
teacher = []        # teacher[i] = ID giáo viên dạy lớp i
attend = []         # attend[i] = sĩ số lớp i
capacity = []       # capacity[j] = sức chứa phòng j

# -------- Hằng số lịch học --------
num_day = 5                         # Số ngày trong tuần
num_half_day = num_day * 2          # Tổng nửa ngày (10 nửa)
day_time = 12                       # Thời gian 1 ngày
half_day_time = int(day_time / 2)   # Thời gian 1 nửa ngày = 6
max_duration = 4                    # Một lớp dài cùng lắm là 4 tiết

# Khoảng thời gian cho nửa ngày i
# start_half[i] = thời gian bắt đầu nửa thứ i
# end_half[i]   = thời gian kết thúc nửa thứ i
start_half = [i * half_day_time + 1 for i in range(num_day * 2)]
end_half = [start_half[i] + half_day_time - 1 for i in range(len(start_half))]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                 PHẦN 2: MODEL - SCHEDULING (Biến Toàn Cục)               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

model = None  # CP-SAT model

# Biến quyết định cho model:
start = []          # start[i] = thời gian bắt đầu lớp i (nếu được xếp)
is_present = []     # is_present[i] = 1 nếu lớp i được xếp, 0 nếu không
intervals = []      # intervals[i] = khoảng thời gian của lớp i

# Kết quả lưu được
room_for_class = []     # room_for_class[i] = x nếu lớp i có phòng là x
scheduled_classes = []  # Danh sách lớp xếp được

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    PHẦN 3: FILE OUTPUT (OJ Mode)                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

stat_file = open(os.devnull, 'w')       # Thống kê solver
viz_file = open(os.devnull, 'w')        # Visualization data
time_log_file = open(os.devnull, 'w')   # Log của solver


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                   PHẦN 4: HÀM I/O (Input/Output)                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def setup_files():
    """
    Định tuyến các luồng input/output nếu file tồn tại (OJ mode).

    Nếu tồn tại input.txt:
    - stdin  ← input.txt
    - stdout ← output.txt
    - Mở các file log (stat.txt, viz.txt, log.txt)
    """
    global stat_file, viz_file, log_file
    
    if os.path.exists('input.txt'):
        sys.stdin = open('input.txt', 'r', encoding='utf-8')
        sys.stdout = open('output.txt', 'w', encoding='utf-8')

        stat_file = open('stat.txt', 'w', encoding="utf-8")
        viz_file = open('viz.txt', 'w', encoding="utf-8")
        log_file = open("log.txt", "w", encoding="utf-8")


def input_data():
    """
    Đọc dữ liệu từ stdin (hoặc input.txt nếu ở OJ mode).
    
    Format:
      Line 1: n m (số lớp, số phòng)
      Line 2..n+1: duration[i] teacher[i] attend[i]
      Line n+2: capacity[0] capacity[1] ... capacity[m-1]
    """
    global n, m, duration, teacher, attend, capacity
    
    n, m = map(int, input().split())
    
    for _ in range(n):
        i, j, k = map(int, input().split())
        duration.append(i)
        teacher.append(j)
        attend.append(k)

    capacity = list(map(int, input().split()))


def write_output(scheduled_classes):
    """
    Ghi kết quả cuối cùng ra stdout (nếu ở OJ MODE) hoặc ra output.txt ở LOCAL
    
    Format:
      Line 1: Q (số lớp được xếp)
      Line 2..Q+1: class_id+1 start_time room_id+1
    """
    print(len(scheduled_classes))
    for cls_id, start_time, room_id, dur, tch, att, cap in scheduled_classes:
        print(f"{cls_id+1} {start_time} {room_id+1}")


def write_viz_output(solver, status, scheduled_classes):
    """
    Ghi thông tin visualization ra viz.txt (cho debug/analysis).
    
    Format:
      Line 1: solver status name
      Line 2..Q+1: class_id+1 start_time room_id+1 duration teacher attend room_capacity
      Line Q+2: sức chứa các phòng học
    """
    print("solver status:", solver.status_name(status), file=viz_file)
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for cls_id, start_time, room_id, dur, tch, att, cap in scheduled_classes:
            print(f"{cls_id+1} {start_time} {room_id+1} {dur} {tch} {att} {cap}", 
                  file=viz_file)
    print(" ".join(map(str, capacity)), file=viz_file)


def log_to_file(msg):
    """Ghi log từ time solver vào file."""
    log_file.write(msg + "\n")
    log_file.flush()

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                      PHẦN 5: DEFINE CONSTRAINTS                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def define_model():
    """Khởi tạo CP-SAT model."""
    global model
    model = cp_model.CpModel()


def make_non_crossing_half_day_and_end_day():
    """
    Ràng buộc 1: Lớp không được dài đè lên nửa ngày hoặc cuối ngày.
    
    Logic:
      - Mỗi lớp chỉ được bắt đầu tại các vị trí trong nửa ngày
      - Tạo domain chứa các khoảng thời gian hợp lệ
      - Thêm biến is_present[i] (optional): lớp i có được xếp?
    """
    global start, is_present, intervals
    valid_domain_of_duration = {key: [] for key in range(1, max_duration+1)}

    # Tìm các khoảng hợp lệ của một lớp có duration là dur
    for dur in range(1, max_duration+1):
        for s in range(len(start_half)):
            valid_domain_of_duration[dur].append([
                start_half[s], end_half[s] - dur + 1
            ])

    for cur_class in range(n):
        # Tạo biến start[cur_class] với domain là các khoảng hợp lệ
        domain = cp_model.Domain.from_intervals(valid_domain_of_duration[duration[cur_class]])
        start.append(model.new_int_var_from_domain(domain, f"start_{cur_class+1}"))
        
        # Biến is_present: 1 nếu lớp được xếp, 0 nếu không
        is_present.append(model.new_bool_var(f"is_present_{cur_class+1}"))
        
        # Optional interval: chỉ tồn tại nếu is_present[i] = 1
        intervals.append(model.new_optional_fixed_size_interval_var(
            start[-1], duration[cur_class], is_present[-1], f"interval_{cur_class+1}"
        ))


def make_non_overlapping_classes_by_teacher():
    """
    Ràng buộc 2: Một giáo viên không dạy trùng giờ.
    
    Logic:
      - Nhóm các lớp theo giáo viên
      - Thêm no_overlap constraint cho từng giáo viên
        (các lớp của cùng 1 giáo viên không được giao nhau về thời gian)
    """
    teachers_set = set(teacher)
    class_intervals_by_teacher = {key: [] for key in teachers_set}
    
    for i in range(n):
        class_intervals_by_teacher[teacher[i]].append(intervals[i])

    for t_intervals in class_intervals_by_teacher.values():
        model.add_no_overlap(t_intervals)


def make_non_overlapping_classes_by_room():
    """
    Ràng buộc 3: Các lớp trong cùng một phòng không được trùng giờ

    Logic: 
      - Coi mỗi lớp như một block có chiều dài là dur, chiều rộng là 1
      - Các block không được giao nhau.
    """
    global room_for_class
    intervals_by_room = []  # interval theo chiều phòng
    
    for i in range(n):
        # Biến phòng cho lớp i hiện tại
        rv = model.new_int_var(0, m - 1, f"room_p1_{i+1}")
        room_for_class.append(rv)
        
        # Ràng buộc sức chứa (chỉ khi present)
        valid_rooms = [r for r in range(m) if capacity[r] >= attend[i]]
        model.add_allowed_assignments(
            [rv], [[r] for r in valid_rooms]
        )
        
        # Interval theo chiều phòng: [room_var, room_var + 1)
        # (mỗi lớp chiếm đúng 1 đơn vị trong chiều phòng)
        room_interval = model.new_optional_fixed_size_interval_var(
            rv, 1, is_present[i], f"room_interval_{i+1}"
        )
        intervals_by_room.append(room_interval)
    
    # no_overlap_2d: không có 2 hình chữ nhật (time × room) nào giao nhau
    # Tức là: nếu 2 lớp cùng phòng thì không được trùng giờ, và ngược lại
    model.add_no_overlap_2d(intervals, intervals_by_room)
            
                  
def define_objective():
    """
    Hàm mục tiêu: Tối đa hóa số lớp được xếp.
    """
    model.maximize(sum(is_present))


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         PHẦN 6: SOLVE MODEL                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def solve_model():
    """
    Giải model và ghi thống kê.
    
    Return:
      (solver, status)
    """
    solver = cp_model.CpSolver()

    # Thời gian tối đa cho solver
    solver.parameters.max_time_in_seconds = 20

    # Setup log
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    solver.log_callback = log_to_file

    # Setup gap
    # Chấp nhận hàm mục tiêu tìm được 
    # nằm trong mức sai lệch 5% so với best_bound 
    # solver.parameters.relative_gap_limit = 0.05

    # Giải
    status = solver.solve(model)

    # Ghi thống kê
    print("\n=== Statistics Time Solver ===", file=stat_file)
    print(f"  Status       : {solver.status_name(status)}", file=stat_file)
    print(f"  Conflicts    : {solver.num_conflicts}", file=stat_file)
    print(f"  Branches     : {solver.num_branches}", file=stat_file)
    print(f"  Wall time    : {solver.wall_time}s", file=stat_file)

    return solver, status


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                   PHẦN 7: ENTRY POINT - MAIN FUNCTION                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def main():    
    # --- Bước 1: Setup ---
    setup_files()

    # --- Bước 2: Input ---
    input_data()

    # --- Bước 3: Scheduling
    define_model()
    make_non_crossing_half_day_and_end_day()
    make_non_overlapping_classes_by_teacher()
    make_non_overlapping_classes_by_room()
    define_objective()
    solver, status = solve_model()

    if (status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]): 
        print(solver.status_name(status))
        return

    # --- Bước 4: Tìm lớp tham gia ---
    for i in range(n):
        if solver.value(is_present[i]):  # Lớp i được xếp
            s = solver.value(start[i])
            r = solver.value(room_for_class[i])
            scheduled_classes.append((
                i,
                s,
                r,
                duration[i],
                teacher[i],
                attend[i],
                capacity[r]
            ))     

    # --- Bước 5: Output ---
    write_output(scheduled_classes)
    write_viz_output(solver, status, scheduled_classes)


if __name__ == "__main__":
    main()