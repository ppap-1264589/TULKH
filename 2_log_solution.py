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

APPROACH:
  Two-phase CP-SAT solving:
  - Phase 1 (Time Model): Xếp thời gian hợp lệ, tối đa hóa số lớp
  - Phase 2 (Room Model): Gán phòng cho các lớp đã xếp thời gian

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

# Khoảng thời gian cho nửa ngày i
# start_half[i] = thời gian bắt đầu nửa thứ i
# end_half[i]   = thời gian kết thúc nửa thứ i
start_half = [i * half_day_time + 1 for i in range(num_day * 2)]
end_half = [start_half[i] + half_day_time - 1 for i in range(len(start_half))]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║               PHẦN 2: MODEL 1 - TIME SCHEDULING (Biến Toàn Cục)         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

time_model = None  # CP-SAT model cho phase 1

# Biến quyết định cho time model:
start = []          # start[i] = thời gian bắt đầu lớp i (nếu được xếp)
is_present = []     # is_present[i] = 1 nếu lớp i được xếp, 0 nếu không
intervals = []      # intervals[i] = khoảng thời gian của lớp i


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║               PHẦN 3: MODEL 2 - ROOM ASSIGNMENT (Biến Toàn Cục)         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

room_model = None        # CP-SAT model cho phase 2
room_var = []            # room_var[i] = phòng được gán cho scheduled_classes[i]
scheduled_classes = []   # Danh sách lớp đã được xếp thời gian (từ phase 1)
Q = 0                    # Số lớp thực sự được xếp (tính sau phase 1)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    PHẦN 4: FILE OUTPUT (OJ Mode)                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

stat_file = open(os.devnull, 'w')       # Thống kê solver
viz_file = open(os.devnull, 'w')        # Visualization data
time_log_file = open(os.devnull, 'w')   # Log của time solver
room_log_file = open(os.devnull, 'w')   # Log của room solver


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                   PHẦN 5: HÀM I/O (Input/Output)                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def setup_files():
    """
    Định tuyến các luồng input/output nếu file tồn tại (OJ mode).

    Nếu tồn tại input.txt:
    - stdin  ← input.txt
    - stdout ← output.txt
    - Mở các file log (stat.txt, viz.txt, time_log.txt, room_log.txt)
    """
    global stat_file, viz_file, time_log_file, room_log_file
    
    if os.path.exists('input.txt'):
        sys.stdin = open('input.txt', 'r', encoding='utf-8')
        sys.stdout = open('output.txt', 'w', encoding='utf-8')

        stat_file = open('stat.txt', 'w', encoding="utf-8")
        viz_file = open('viz.txt', 'w', encoding="utf-8")
        time_log_file = open("time_log.txt", "w", encoding="utf-8")
        room_log_file = open("room_log.txt", "w", encoding="utf-8")


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


def write_output(final_assignments):
    """
    Ghi kết quả cuối cùng ra stdout (nếu ở OJ MODE) hoặc ra output.txt ở LOCAL
    
    Format:
      Line 1: Q (số lớp được xếp)
      Line 2..Q+1: class_id+1 start_time room_id+1
    """
    print(Q)
    for cls_id, start_time, room_id, dur, tch, att, cap in final_assignments:
        print(f"{cls_id+1} {start_time} {room_id+1}")


def write_viz_output(time_solver, status, final_assignments):
    """
    Ghi thông tin visualization ra viz.txt (cho debug/analysis).
    
    Format:
      Line 1: time_solver status name
      Line 2..Q+1: class_id+1 start_time room_id+1 duration teacher attend room_capacity
      Line Q+2: sức chứa các phòng học
    """
    print("time_solver status:", time_solver.status_name(status), file=viz_file)
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for cls_id, start_time, room_id, dur, tch, att, cap in final_assignments:
            print(f"{cls_id+1} {start_time} {room_id+1} {dur} {tch} {att} {cap}", 
                  file=viz_file)
    print(" ".join(map(str, capacity)), file=viz_file)


def time_log_to_file(msg):
    """Ghi log từ time solver vào file."""
    time_log_file.write(msg + "\n")
    time_log_file.flush()


def room_log_to_file(msg):
    """Ghi log từ room solver vào file."""
    room_log_file.write(msg + "\n")
    room_log_file.flush()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║            PHẦN 6: PHASE 1 - TIME SCHEDULING MODEL                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def define_time_model():
    """Khởi tạo CP-SAT model cho phase 1 (xếp thời gian)."""
    global time_model
    time_model = cp_model.CpModel()


def make_non_overlapping_half_day_and_end_day():
    """
    Ràng buộc 1: Lớp không được dài đè lên nửa ngày hoặc cuối ngày.
    
    Logic:
      - Mỗi lớp chỉ được bắt đầu tại các vị trí trong nửa ngày
      - Nếu duration[i] <= half_day_time, có thể fit vào 1 nửa ngày
      - Tạo domain chứa các khoảng thời gian hợp lệ
      - Thêm biến is_present[i] (optional): lớp i có được xếp?
    """
    global start, is_present, intervals
    
    for cur_class in range(n):
        valid_intervals = []
        
        # Lớp chỉ hợp lệ nếu duration không quá nửa ngày
        if duration[cur_class] <= half_day_time:
            for s in range(len(start_half)):
                valid_intervals.append([
                    start_half[s], end_half[s] - duration[cur_class] + 1
                ])

        # Tạo biến start[cur_class] với domain là các khoảng hợp lệ
        domain = cp_model.Domain.from_intervals(valid_intervals)
        start.append(time_model.new_int_var_from_domain(domain, f"start_{cur_class+1}"))
        
        # Biến is_present: 1 nếu lớp được xếp, 0 nếu không
        is_present.append(time_model.new_bool_var(f"is_present_{cur_class+1}"))
        
        # Optional interval: chỉ tồn tại nếu is_present[i] = 1
        intervals.append(time_model.new_optional_fixed_size_interval_var(
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
        if len(t_intervals) > 1:
            time_model.add_no_overlap(t_intervals)


def make_limited_overlapping_classes():
    """
    Ràng buộc 3: Sức chứa phòng (Cumulative Constraint).
    
    Logic:
      - Các lớp có cùng "sĩ số threshold" cần phòng có sức chứa >= threshold
      - Đếm số phòng hợp lệ cho mỗi threshold
      - Đảm bảo "độ đè lịch" (overlapping degree) không vượt số phòng
      
    Ví dụ:
      - Lớp A: 40 sinh viên → có 25 phòng capacity >= 40
      - Lớp B: 40 sinh viên → có 25 phòng capacity >= 40
      - Lớp C:...
      - Giới hạn: tối đa 25 lớp như lớp A,B,C (với sĩ số >= 40) có thể xếp trùng giờ

    Mục đích:
      - Tách biệt phase thời gian với phase gán phòng
    """
    unique_attend_thresholds = sorted(list(set(attend)))
    
    for attend_threshold in unique_attend_thresholds:
        # Đếm số phòng đủ sức chứa cho threshold này
        num_rooms_available = sum(1 for c in capacity if c >= attend_threshold)
        
        # Danh sách lớp có sĩ số >= threshold
        classes_demanding_this_tier = [
            intervals[i] for i in range(n) if attend[i] >= attend_threshold
        ]
        
        # Cumulative constraint: 
        # độ đè lịch của các lớp có cùng threshold <= số phòng hợp lệ
        if classes_demanding_this_tier:
            time_model.add_cumulative(
                classes_demanding_this_tier,
                [1] * len(classes_demanding_this_tier),
                num_rooms_available
            )


def define_objective():
    """
    Hàm mục tiêu cho phase 1: Tối đa hóa số lớp được xếp.
    """
    time_model.maximize(cp_model.LinearExpr.sum(is_present))


def solve_time_model():
    """
    Giải phase 1 (time model) và ghi thống kê.
    
    Return:
      (time_solver, status)
    """
    time_solver = cp_model.CpSolver()

    # Thời gian tối đa cho solver
    time_solver.parameters.max_time_in_seconds = 10

    # Setup log
    time_solver.parameters.log_search_progress = True
    time_solver.parameters.log_to_stdout = False
    time_solver.log_callback = time_log_to_file

    # Giải
    status = time_solver.solve(time_model)

    # Ghi thống kê
    print("\n=== Statistics Time Solver ===", file=stat_file)
    print(f"  Status       : {time_solver.status_name(status)}", file=stat_file)
    print(f"  Conflicts    : {time_solver.num_conflicts}", file=stat_file)
    print(f"  Branches     : {time_solver.num_branches}", file=stat_file)
    print(f"  Wall time    : {time_solver.wall_time}s", file=stat_file)

    return time_solver, status


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║            PHẦN 7: PHASE 2 - ROOM ASSIGNMENT MODEL                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def define_room_model(time_solver):
    """
    Khởi tạo phase 2 (room model) dựa trên kết quả phase 1.
    
    Logic:
      1. Lọc ra danh sách lớp đã được xếp thời gian (is_present[i] = 1)
      2. Tạo room_var[j] cho mỗi lớp (chỉ số phòng được gán)
      3. Cập nhật global Q (số lớp thực sự được xếp)
    """
    global room_model, room_var, scheduled_classes, Q

    room_model = cp_model.CpModel()
    
    # Q = số lớp được xếp từ phase 1
    Q = int(time_solver.value(cp_model.LinearExpr.sum(is_present)))

    # Xây dựng danh sách lớp đã xếp
    scheduled_classes = []
    for i in range(n):
        if time_solver.value(is_present[i]):  # Lớp i được xếp
            s = time_solver.value(start[i])
            scheduled_classes.append({
                'id': i,
                'start': s,
                'end': s + duration[i],
                'attend': attend[i]
            })

    # room_var[j] = ID phòng được gán cho scheduled_classes[j]
    room_var = [
        room_model.new_int_var(0, m - 1, f"room_var_{j}") 
        for j in range(Q)
    ]


def make_non_overloaded_room():
    """
    Ràng buộc 1 (Room Model): Sức chứa phòng >= sĩ số lớp.
    
    Logic:
      - Cho mỗi lớp đã xếp
      - Tìm danh sách phòng có sức chứa >= attend[class]
      - Sử dụng add_allowed_assignments để giới hạn room_var
    """
    for i, cls in enumerate(scheduled_classes):
        # Tìm phòng hợp lệ
        valid_rooms = [r for r in range(m) if capacity[r] >= cls['attend']]
        
        if valid_rooms:
            room_model.add_allowed_assignments(
                [room_var[i]],
                [[r] for r in valid_rooms]
            )
        else:
            # Nếu không tìm thấy phòng hợp lệ thì skip 
            # (trường hợp này không nên xảy ra)
            continue


def make_non_overlapping_classes_in_same_room():
    """
    Ràng buộc 2 (Room Model): Hai lớp trùng giờ phải ở phòng khác.
    
    Logic:
      - Kiểm tra xem hai lớp có giao nhau về thời gian?
      - Nếu có giao nhau: room_var[i] != room_var[j]
      
    Overlap condition:
      Hai lớp giao nhau nếu: start_i < end_j AND start_j < end_i
    """
    for i in range(Q):
        for j in range(i + 1, Q):
            ci, cj = scheduled_classes[i], scheduled_classes[j]
            
            # Kiểm tra xem ci và cj có giao nhau?
            # --> Giả sử có 2 lớp học ci và cj. 
            # Hai lớp này KHÔNG TRÙNG GIỜ (không giao nhau) 
            # khi xảy ra 1 trong 2 trường hợp sau:
            # HOẶC: ci['end'] <= cj['start']
            # HOẶC: cj['end'] <= ci['start']
            # Theo định lý De Morgan, phủ định của (A <= B hoặc C <= D) 
            # chính là (A > B VÀ C > D).
            if ci['start'] < cj['end'] and cj['start'] < ci['end']:
                # Nếu giao nhau: phải gán vào 2 phòng khác nhau
                room_model.add(room_var[i] != room_var[j])


def solve_room_model():
    """
    Giải phase 2 (room model) và ghi thống kê.
    
    Return:
      (room_solver, status)
    """
    room_solver = cp_model.CpSolver()

    # Thời gian tối đa cho solver
    room_solver.parameters.max_time_in_seconds = 10

    # Setup log
    room_solver.parameters.log_search_progress = True
    room_solver.parameters.log_to_stdout = False
    room_solver.log_callback = room_log_to_file

    # Giải
    room_status = room_solver.solve(room_model)

    # Ghi thống kê
    print("\n=== Statistics Room Solver ===", file=stat_file)
    print(f"  Status       : {room_solver.status_name(room_status)}", file=stat_file)
    print(f"  Conflicts    : {room_solver.num_conflicts}", file=stat_file)
    print(f"  Branches     : {room_solver.num_branches}", file=stat_file)
    print(f"  Wall time    : {room_solver.wall_time}s", file=stat_file)

    return room_solver, room_status


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                   PHẦN 8: ENTRY POINT - MAIN FUNCTION                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def main():
    """
    Luồng chính của chương trình.
    
    Bước 1: Setup I/O (dùng input.txt nếu ở OJ mode)
    Bước 2: Đọc dữ liệu đầu vào
    Bước 3: Phase 1 - Time Scheduling
            - Định nghĩa model + constraints + objective
            - Giải → nhận danh sách thời gian hợp lệ
    Bước 4: Phase 2 - Room Assignment
            - Từ danh sách thời gian, gán phòng
            - Giải → nhận gán phòng cuối cùng
    Bước 5: Ghi nhận final assignment
    Bước 6: Output kết quả
    """
    
    # --- Bước 1: Setup ---
    setup_files()


    # --- Bước 2: Input ---
    input_data()

    # --- Bước 3: Phase 1 - TIME SCHEDULING ---
    define_time_model()
    make_non_overlapping_half_day_and_end_day()
    make_non_overlapping_classes_by_teacher()
    make_limited_overlapping_classes()
    define_objective()
    time_solver, time_status = solve_time_model()
    if time_status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]: return
    

    # --- Bước 4: Phase 2 - ROOM ASSIGNMENT ---  
    define_room_model(time_solver)
    make_non_overloaded_room()
    make_non_overlapping_classes_in_same_room()
    room_solver, room_status = solve_room_model()
    if room_status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]: return
    

    # --- Bước 5: Build final assignments ---
    final_assignments = []
    for i, cls in enumerate(scheduled_classes):
        r = room_solver.value(room_var[i])
        final_assignments.append((
            cls['id'], cls['start'], r,
            duration[cls['id']], teacher[cls['id']], attend[cls['id']], capacity[r]
        ))


    # --- Bước 6: Output ---
    write_output(final_assignments)
    write_viz_output(time_solver, time_status, final_assignments)


if __name__ == "__main__":
    main()