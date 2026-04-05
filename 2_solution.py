# Nạp các thư viện
from ortools.sat.python import cp_model
import sys
import os



# Đường dẫn file
if os.path.exists('input.txt'):
    sys.stdin = open('input.txt', 'r', encoding='utf-8')
    sys.stdout = open('output.txt', 'w', encoding='utf-8')

    stat_file = open('stat.txt', 'w')

    viz_file = open('viz.txt', 'w')



# Nhập input
n, m = map(int, input().split())

duration, teacher, attend, capacity = [], [], [], []
for _ in range(n):
    i, j, k = map(int, input().split())
    duration.append(i)
    teacher.append(j)
    attend.append(k)

capacity = list(map(int, input().split()))














# METADATA
num_day = 5
num_half_day = num_day * 2
day_time = 12
half_day_time = int(day_time / 2)


# Tạo model
model = cp_model.CpModel()

# Tạo các biến ban đầu
# start_half[i] = thời gian bắt đầu nửa thứ i
# end_half[i] là kết thúc nửa thứ i
start_half = [i * half_day_time + 1 for i in range(num_day * 2)]
end_half = [start_half[i] + half_day_time - 1 for i in range(len(start_half))]


# Tạo các biến trong mô hình
start = []
is_present = []
intervals = []













# Ràng buộc: Một lớp không được dài đè lên nửa hoặc cuối ngày
# Xử lý luôn bằng cách giới hạn trước miền xác định của biến start
for cur_class in range(n):
    valid_intervals = []
    if duration[cur_class] <= half_day_time:
        for s in range(len(start_half)):
            valid_intervals.append([start_half[s], end_half[s] - duration[cur_class] + 1])

    domain = cp_model.Domain.from_intervals(valid_intervals)
    start.append(model.new_int_var_from_domain(domain, f"start_{cur_class+1}"))
    is_present.append(model.new_bool_var(f"is_present_{cur_class+1}"))
    intervals.append(model.new_optional_fixed_size_interval_var(start[-1], duration[cur_class], is_present[-1], f"interval_{cur_class+1}"))













# Ràng buộc: Một giáo viên không dạy trùng giờ
teachers_set = set(teacher)
meeting_intervals_by_teacher = {key: [] for key in teachers_set}
for i in range(n):
    meeting_intervals_by_teacher[teacher[i]].append(intervals[i])

for t_intervals in meeting_intervals_by_teacher.values():
    if len(t_intervals) > 1:
        model.add_no_overlap(t_intervals)















# Ràng buộc sức chứa phòng bằng Cumulative Constraint
unique_attend_thresholds = sorted(list(set(attend)))
for attend_threshold in unique_attend_thresholds:
    # num_rooms_avaliable = "độ đè lịch tối đa" của các lớp có cùng số sinh viên tham dự
    num_rooms_available = sum(1 for c in capacity if c >= attend_threshold)
    # Danh sách interval của các lớp có thể đè lịch lên nhau
    classes_demanding_this_tier = [
        intervals[i] for i in range(n) if attend[i] >= attend_threshold
    ]
    # Điều kiện: "độ đè lịch" của các lớp xếp được tkb theo thời gian không được đè quá mức cho phép
    if classes_demanding_this_tier:
        model.add_cumulative(
            classes_demanding_this_tier,
            [1] * len(classes_demanding_this_tier),
            num_rooms_available
        )












# Tối đa hóa hàm mục tiêu trước
model.maximize(cp_model.LinearExpr.sum(is_present))


# Gọi bộ giải tối đa hóa hàm mục tiêu trước
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
status = solver.solve(model)









# Statistics solver đầu tiên
print("\nStatistics time solver", file=stat_file)
print(f"  - conflicts: {solver.num_conflicts}", file=stat_file)
print(f"  - branches : {solver.num_branches}", file=stat_file)
print(f"  - wall time: {solver.wall_time}s", file=stat_file)






















# --- POST-PROCESSING: GÁN PHÒNG BẰNG CP-SAT THỨ HAI ---
# Ở solver đầu, các lớp đã chắc chắn thỏa mãn điều kiện về thời gian
# Ở solver này, các lớp sẽ được gán sao cho thỏa mãn điều kiện về không gian
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    Q = int(solver.value(cp_model.LinearExpr.sum(is_present)))

    scheduled_classes = []
    for i in range(n):
        if solver.value(is_present[i]):
            s = solver.value(start[i])
            scheduled_classes.append({
                'id': i,
                'start': s,
                'end': s + duration[i],
                'attend': attend[i]
            })

    # =========================================================
    # Dùng CP-SAT thứ hai để gán phòng
    # Giả sử phương án tối ưu vào khoảng Q = 100-500 lớp và vẫn có 50 phòng có thể xếp
    # -> Có thể tìm được assignment hợp lệ trong thời gian đủ tốt
    # =========================================================

    room_model = cp_model.CpModel()

    # room_var[i] = chỉ số phòng được gán cho scheduled_classes[i]
    room_var = [room_model.new_int_var(0, m - 1, f"rv_{i}") for i in range(Q)]

    # Ràng buộc 1: Sức chứa phòng >= sĩ số lớp
    for i, cls in enumerate(scheduled_classes):
        # Liệt kê các phòng hợp lệ (capacity đủ)
        valid_rooms = [r for r in range(m) if capacity[r] >= cls['attend']]
        if valid_rooms:
            room_model.add_allowed_assignments(
                [room_var[i]],
                [[r] for r in valid_rooms]
            )
        else:
            # Không có phòng nào đủ (không nên xảy ra sau bước lọc)
            continue

    # Ràng buộc 2: Hai lớp trùng giờ phải ở phòng khác nhau
    for i in range(Q):
        for j in range(i + 1, Q):
            ci, cj = scheduled_classes[i], scheduled_classes[j]
            # Kiểm tra overlap
            if ci['start'] < cj['end'] and cj['start'] < ci['end']:
                room_model.add(room_var[i] != room_var[j])
    # ==================
    #     Giả sử bạn có 2 lớp học ci và cj. Hai lớp này KHÔNG TRÙNG GIỜ (không giao nhau) khi xảy ra 1 trong 2 trường hợp sau:
    # HOẶC: ci['end'] <= cj['start']
    # HOẶC: cj['end'] <= ci['start']
    # Theo định lý De Morgan, phủ định của (A <= B hoặc C <= D) chính là (A > B VÀ C > D).
    # ==================



    room_solver = cp_model.CpSolver()
    room_solver.parameters.max_time_in_seconds = 10
    room_status = room_solver.solve(room_model)

    # Lưu kết quả gán phòng để dùng cho viz.txt
    final_assignments = []  # list of (cls_id, start_time, room_id, duration, teacher, attend, capacity_of_room)

    if room_status == cp_model.OPTIMAL or room_status == cp_model.FEASIBLE:
        print(Q)
        for i, cls in enumerate(scheduled_classes):
            r = room_solver.value(room_var[i])
            print(f"{cls['id'] + 1} {cls['start']} {r + 1}")
            final_assignments.append((
                cls['id'], cls['start'], r,
                duration[cls['id']], teacher[cls['id']], attend[cls['id']], capacity[r]
            ))












# Statistics room solver
print("\nStatistics room solver", file=stat_file)
print(f"  - conflicts: {room_solver.num_conflicts}", file=stat_file)
print(f"  - branches : {room_solver.num_branches}", file=stat_file)
print(f"  - wall time: {room_solver.wall_time}s", file=stat_file)















# ==========================================
# IN RA FILE VIZ.TXT
# ==========================================
print(solver.status_name(status), file=viz_file)
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for cls_id, start_time, room_id, dur, tch, att, cap in final_assignments:
        print(f"{cls_id+1} {start_time} {room_id+1} {dur} {tch} {att} {cap}", file=viz_file)
print(" ".join(map(str, capacity)), file=viz_file)



