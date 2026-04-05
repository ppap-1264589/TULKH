from ortools.sat.python import cp_model
import sys
import os

####################################### CÁC BIẾN TOÀN CỤC
# Thông tin đầu vào
n, m = 0, 0
duration, teacher, attend, capacity = [], [], [], []

# Thông số lịch học
num_day = 5
num_half_day = num_day * 2
day_time = 12
half_day_time = int(day_time/2)

# Khoảng thời gian cho nửa ngày
# start_half[i] = thời gian bắt đầu nửa thứ i
# end_half[i] là kết thúc nửa thứ i
start_half = [i * half_day_time + 1 for i in range(num_day * 2)]
end_half = [start_half[i] + half_day_time - 1 for i in range(len(start_half))]

# OJ mode
stat_file = open(os.devnull, 'w')
viz_file = open(os.devnull, 'w')
time_log_file = open(os.devnull, 'w')
room_log_file = open(os.devnull, 'w')











####################################### CÁC BIẾN CHO TIME MODEL
time_model = None
start, is_present, intervals = [], [], []

####################################### CÁC BIẾN CHO ROOM MODEL
room_model = None
room_var = []
scheduled_classes = []
Q = 0

















####################################### HÀM I/O
def setup_files():
    """Định tuyến các luồng input/output nếu file tồn tại."""
    global stat_file, viz_file, time_log_file, room_log_file
    
    if os.path.exists('input.txt'):
        sys.stdin = open('input.txt', 'r', encoding='utf-8')
        sys.stdout = open('output.txt', 'w', encoding='utf-8')

        stat_file = open('stat.txt', 'w', encoding="utf-8")
        viz_file = open('viz.txt', 'w', encoding="utf-8")
        time_log_file = open("time_log.txt", "w", encoding="utf-8")
        room_log_file = open("room_log.txt", "w", encoding="utf-8")



def input_data():
    """Nhập dữ liệu đầu vào."""
    global n, m, duration, teacher, attend, capacity
    n, m = map(int, input().split())
    for _ in range(n):
        i, j, k = map(int, input().split())
        duration.append(i)
        teacher.append(j)
        attend.append(k)

    capacity = list(map(int, input().split()))

def time_log_to_file(msg):
    time_log_file.write(msg + "\n")
    time_log_file.flush()  # để thấy log ngay lập tức

def room_log_to_file(msg):
    room_log_file.write(msg + "\n")
    room_log_file.flush()  # để thấy log ngay lập tức


























####################################### KHỞI TẠO TIME MODEL 
def define_time_model():
    global time_model
    time_model = cp_model.CpModel()


####################################### CÁC RÀNG BUỘC CHO TIME MODEL
def make_non_overlapping_half_day_and_end_day():
    """
    Ràng buộc: Một lớp không được dài đè lên nửa hoặc cuối ngày.
    Xử lý luôn bằng cách giới hạn trước miền xác định của biến start.
    """
    global start, is_present, intervals
    for cur_class in range(n):
        valid_intervals = []
        if duration[cur_class] <= half_day_time:
            for s in range(len(start_half)):
                valid_intervals.append([
                    start_half[s], end_half[s] - duration[cur_class] + 1
                ])

        domain = cp_model.Domain.from_intervals(valid_intervals)
        start.append(time_model.new_int_var_from_domain(domain, f"start_{cur_class+1}"))
        is_present.append(time_model.new_bool_var(f"is_present_{cur_class+1}"))
        intervals.append(time_model.new_optional_fixed_size_interval_var(
            start[-1], duration[cur_class], is_present[-1], f"interval_{cur_class+1}"
        ))

def make_non_overlapping_classes_by_teacher():
    """Ràng buộc: Một giáo viên không dạy trùng giờ."""
    teachers_set = set(teacher)
    class_intervals_by_teacher = {key: [] for key in teachers_set}
    for i in range(n):
        class_intervals_by_teacher[teacher[i]].append(intervals[i])

    for t_intervals in class_intervals_by_teacher.values():
        if len(t_intervals) > 1:
            time_model.add_no_overlap(t_intervals)

def make_limited_overlapping_classes():
    """Ràng buộc sức chứa phòng bằng Cumulative Constraint."""
    unique_attend_thresholds = sorted(list(set(attend)))
    for attend_threshold in unique_attend_thresholds:
        # num_rooms_available = "độ đè lịch tối đa" của các lớp có cùng số sinh viên tham dự
        num_rooms_available = sum(1 for c in capacity if c >= attend_threshold)
        # Danh sách interval của các lớp có thể đè lịch lên nhau
        classes_demanding_this_tier = [
            intervals[i] for i in range(n) if attend[i] >= attend_threshold
        ]
        # Điều kiện: "độ đè lịch" của các lớp xếp được tkb theo thời gian không được đè quá mức cho phép
        if classes_demanding_this_tier:
            time_model.add_cumulative(
                classes_demanding_this_tier,
                [1] * len(classes_demanding_this_tier),
                num_rooms_available
            )

####################################### SOLVE TIME MODEL
def solve_time_model():
    """Giải model thời gian và ghi log/thống kê."""
    time_solver = cp_model.CpSolver()

    # Thời gian tối đa của time_solver
    time_solver.parameters.max_time_in_seconds = 10

    # Setup các tham số để ghi ra log
    time_solver.parameters.log_search_progress = True
    time_solver.parameters.log_to_stdout = False
    time_solver.log_callback = time_log_to_file

    # Chính thức giải time model
    status = time_solver.solve(time_model)

    # Statistics time_solver
    print("\nStatistics time solver", file=stat_file)
    print(f"  - conflicts: {time_solver.num_conflicts}", file=stat_file)
    print(f"  - branches : {time_solver.num_branches}", file=stat_file)
    print(f"  - wall time: {time_solver.wall_time}s", file=stat_file)

    return time_solver, status





























####################################### HÀM MỤC TIÊU
def define_objective():
    """Hàm mục tiêu: Tối đa hóa số lớp được xếp."""
    time_model.maximize(cp_model.LinearExpr.sum(is_present))

































# =========================================================
# Dùng CP-SAT thứ hai để gán phòng
# Giả sử phương án tối ưu là xếp được Q = 100-500 lớp và vẫn có 50 phòng có thể xếp
# -> Có thể tìm được assignment hợp lệ trong thời gian đủ tốt
# =========================================================


####################################### KHỞI TẠO ROOM MODEL
def define_room_model(time_solver):
    """Lọc các lớp đã được xếp lịch từ Model 1 và khởi tạo biến cho Model 2"""
    global room_model, room_var, scheduled_classes, Q

    room_model = cp_model.CpModel()
        
    # Q là số lớp thực sự đã thỏa mãn về thời gian
    Q = int(time_solver.value(cp_model.LinearExpr.sum(is_present)))

    scheduled_classes = []
    for i in range(n):
        if time_solver.value(is_present[i]):
            s = time_solver.value(start[i])
            scheduled_classes.append({
                'id': i,
                'start': s,
                'end': s + duration[i],
                'attend': attend[i]
            })

    # room_var[i] = chỉ số phòng được gán cho scheduled_classes[i]
    room_var = [room_model.new_int_var(0, m - 1, f"room_var_{i}") for i in range(Q)]


####################################### CÁC RÀNG BUỘC CHO ROOM MODEL
def make_non_overloaded_room():
    """Ràng buộc 1: Sức chứa phòng >= sĩ số lớp"""
    for i, cls in enumerate(scheduled_classes):
        # Liệt kê các phòng hợp lệ (capacity đủ)
        valid_rooms = [r for r in range(m) if capacity[r] >= cls['attend']]
        if valid_rooms:
            room_model.add_allowed_assignments(
                [room_var[i]],
                [[r] for r in valid_rooms]
            )
        else:
            # Nếu không tìm thấy một phòng hợp lệ cho lớp đã thỏa mãn về thời gian
            # thì thôi không làm gì nữa (Trường hợp này không nên xảy ra!)
            continue

def make_non_overlapping_classes_in_same_room():
    """Ràng buộc 2: Hai lớp trùng giờ phải ở phòng khác nhau"""
    for i in range(Q):
        for j in range(i + 1, Q):
            ci, cj = scheduled_classes[i], scheduled_classes[j]
            # Kiểm tra overlap
            # ==================
            # Giả sử có 2 lớp học ci và cj. 
            # Hai lớp này KHÔNG TRÙNG GIỜ (không giao nhau) 
            # khi xảy ra 1 trong 2 trường hợp sau:
            # HOẶC: ci['end'] <= cj['start']
            # HOẶC: cj['end'] <= ci['start']
            # Theo định lý De Morgan, phủ định của (A <= B hoặc C <= D) chính là (A > B VÀ C > D).
            # ==================
            if ci['start'] < cj['end'] and cj['start'] < ci['end']:
                room_model.add(room_var[i] != room_var[j])

####################################### SOLVE ROOM MODEL
def solve_room_model():
    """Chạy solver gán phòng và thống kê kết quả"""
    
    room_solver = cp_model.CpSolver()

    # Thời gian tối đa của room_solver
    room_solver.parameters.max_time_in_seconds = 10

    # Setup các tham số để ghi ra log
    room_solver.parameters.log_search_progress = True
    room_solver.parameters.log_to_stdout = False
    room_solver.log_callback = room_log_to_file

    # Chính thức giải room model
    room_status = room_solver.solve(room_model)

    # Statistics room_solver
    print("\nStatistics room solver", file=stat_file)
    print(f"  - conflicts: {room_solver.num_conflicts}", file=stat_file)
    print(f"  - branches : {room_solver.num_branches}", file=stat_file)
    print(f"  - wall time: {room_solver.wall_time}s", file=stat_file)

    return room_solver, room_status


























####################################### IN KẾT QUẢ OUTPUT
def write_output(final_assignments):
    """IN RA FILE OUTPUT.TXT"""
    print(Q)
    for cls_id, start_time, room_id, dur, tch, att, cap in final_assignments:
        print(f"{cls_id+1} {start_time} {room_id+1}")
















####################################### IN KẾT QUẢ VIZ
def write_viz_output(time_solver, status, final_assignments):
    """IN RA FILE VIZ.TXT"""
    print("time_solver status:", time_solver.status_name(status), file=viz_file)
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for cls_id, start_time, room_id, dur, tch, att, cap in final_assignments:
            print(f"{cls_id+1} {start_time} {room_id+1} {dur} {tch} {att} {cap}", file=viz_file)
    print(" ".join(map(str, capacity)), file=viz_file)


























####################################### HÀM MAIN
def main():
    setup_files()
    input_data()

    # --- MODEL 1: THỜI GIAN ---
    define_time_model()
    make_non_overlapping_half_day_and_end_day()
    make_non_overlapping_classes_by_teacher()
    make_limited_overlapping_classes()
    define_objective()
    time_solver, time_status = solve_time_model()
    if (time_status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]): return

    # --- MODEL 2: KHÔNG GIAN ---
    define_room_model(time_solver)
    make_non_overloaded_room()
    make_non_overlapping_classes_in_same_room()
    room_solver, room_status = solve_room_model()
    if (room_status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]): return

    # --- XÁC ĐỊNH FINAL ASSIGNMENTS ---
    final_assignments = []
    for i, cls in enumerate(scheduled_classes):
        r = room_solver.value(room_var[i])
        final_assignments.append((
            cls['id'], cls['start'], r,
            duration[cls['id']], teacher[cls['id']], attend[cls['id']], capacity[r]
        ))

    # --- IN KẾT QUẢ ---
    write_output(final_assignments)
    write_viz_output(time_solver, time_status, final_assignments)

if __name__ == "__main__":
    main()
