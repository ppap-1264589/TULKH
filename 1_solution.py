# Thư viện
from ortools.sat.python import cp_model
import sys
import os







# Đường dẫn file
if os.path.exists('input.txt'):
    sys.stdin = open('input.txt', 'r', encoding='utf-8')
    sys.stdout = open('output.txt', 'w', encoding='utf-8')










# Nhập input
n, m = map(int, input().split())

duration, teacher, attend, capacity =  [], [], [], []

for _ in range(n):
    i, j, k = map(int, input().split())
    duration.append(i)
    teacher.append(j)
    attend.append(k)

for v in map(int, input().split()):
    capacity.append(v)








# METADATA
num_day = 5
day_time = 12
half_day_time = int(day_time/2)











# Tạo mô hình
model = cp_model.CpModel()










# Ràng buộc: Một lớp không được dài vượt quá nửa ngày hoặc cuối ngày
# -> Chặn luôn bằng cách lập các domain xác định cho biến start




## Khởi tạo các vị trí không được dài vượt quá
start_half = []
for i in range(num_day*2):
    start_half.append(i*half_day_time + 1) #[1, 7, 13, 19, 25, 31, 37, 43, 49, 55]

end_half    =           [start_half[i] + half_day_time - 1 for i in range(len(start_half))]

forbidden_interval =    [model.new_fixed_size_interval_var(end_half[i], 1, f"forbidden {i+1}") for i in range(len(end_half))]
















## Tạo biến kiểu Domain và ép cho mô hình chỉ được start tại những Domain đã cho trước
## Domain hợp lý cho lớp thứ i là từ (start_half[i] -> end_half[i] - duration[i])
start = []
for cur_class in range(n):
    valid_interval_of_cur_class = []
    for s in range(len(start_half)):
        valid_interval_of_cur_class.append([start_half[s], end_half[s] - duration[cur_class] + 1])
    
    domain_of_cur_class = cp_model.Domain.from_intervals(valid_interval_of_cur_class)
    start.append(model.new_int_var_from_domain(domain_of_cur_class, f"start of task {cur_class+1}"))


is_present =            [model.new_bool_var(f"is present task {i+1}") for i in range(n)]
interval =              [model.new_optional_fixed_size_interval_var(start[i], duration[i], is_present[i], f"interval of task {i+1}") for i in range(n)]






















# Ràng buộc: Một giáo viên không thể dạy 2 lớp cùng lúc
teachers_set = set(teacher)
meeting_intervals_by_teacher = {key: [] for key in teachers_set}
for i in range(n):
    meeting_intervals_by_teacher[teacher[i]].append(interval[i])

for t, meeting_intervals in meeting_intervals_by_teacher.items():
    model.add_no_overlap(meeting_intervals)

















# Ràng buộc sức chứa phòng học
room_bool = {}
for r in range(m):
    for i in range(n):
        room_bool[r, i] = model.new_bool_var(f"room {r+1} has task {i+1}")
        if attend[i] > capacity[r]:
            model.add(room_bool[r, i] == 0)
















# Nếu được chọn thì phải xuất hiện
for i in range(n):
    in_one_room = sum(room_bool[r, i] for r in range(m))
    model.add(in_one_room == is_present[i])















# Ràng buộc một phòng không được chứa hai lớp trùng thời gian
interval_in_room = {}
for r in range(m):
    for i in range(n):
        interval_in_room[r, i] = model.new_optional_fixed_size_interval_var(
            start[i],
            duration[i],
            room_bool[r, i],
            f"room_{r+1}_has_interval_{i+1}"
        )

for r in range(m):
    model.add_no_overlap(
        [interval_in_room[r, i] for i in range(n)]
    )

model.maximize(cp_model.LinearExpr.sum(is_present))
    

solver = cp_model.CpSolver()

solver.parameters.max_time_in_seconds = 20

status = solver.solve(model)

status = solver.status_name(status)

print(solver.value(cp_model.LinearExpr.sum(is_present)))
for r in range(m):
    for i in range(n):
        if (solver.value(room_bool[r, i])):
            print(i+1, solver.value(start[i]), r+1)








if os.path.exists('viz.txt'):
    sys.stdout = open('viz.txt', 'w', encoding='utf-8')
print(status)
for r in range(m):
    for i in range(n):
        if (solver.value(room_bool[r, i])):
            print(f"{i+1} {solver.value(start[i])} {r+1} {duration[i]} {teacher[i]} {attend[i]} {capacity[r]}")
print(" ".join(map(str, capacity)))


