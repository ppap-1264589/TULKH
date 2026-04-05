# Tối ưu lập kế hoạch
Mini Project about Timetabling Problem - Lời giải tạm thời của Hoàng

# Hướng dẫn cách sử dụng

- Bước 0: Tạo một folder mới trên máy của bạn (Chả hạn, đặt tên nó là **MiniProject_HoangSolution**)

- Bước 1: Download toàn bộ source code này đặt vào folder đó
  
  Hoặc dùng lệnh trong terminal tại folder đã tạo:

  ```bash
  git clone https://github.com/ppap-1264589/TULKH.git
  ```

- Bước 2: Chạy file solution2_log_refactor.py

  Hoặc dùng lệnh trong terminal:

  ```bash
  python solution2_log_refactor.py
  ```

- Bước 3: Trong folder sẽ tự động hiện các file

| Tên file | Ý nghĩa |
| -------- | -------- |
| output.txt | Kết quả đúng theo format của đề bài yêu cầu |
| time_log.txt | Log của time_solver |
| room_log.txt | Log của room_solver |
| stat.txt | Thống kê các thông tin của hai solver đã chạy |
| viz.txt | File đệm để sử dụng visualize.py |

Các thông số lần lượt hiện trong mỗi bản ghi của file viz.txt:
| Thông số | Ý nghĩa |
| -------- | -------- |
| class_id | ID của lớp (1-indexed) |
| start_time | Slot bắt đầu trong TKB |
| room_id | ID của phòng đã gán cho lớp (1-indexed) |
| duration | Thời lượng của lớp |
| teacher_id | ID của giáo viên (1-indexed) |
| attend | Số sinh viên tham dự lớp |
| capacity | Sức chứa của phòng học |

- Bước 4: Chạy file visualize.py để thấy được biểu đồ
  
  Hoặc dùng lệnh trong terminal:

  ```bash
  python visualization.py
  ```
  
# Các biểu đồ ví dụ:

Ở một ô có giá trị (C200, T30) nghĩa là lớp đó có id là 200, teacher dạy của lớp đó có ID là 30

Testcase n = 50
<img width="2673" height="1232" alt="schedule_viz" src="https://github.com/user-attachments/assets/c9d59466-ce0e-4061-98cc-effb9cac0cf5" />

Testcase n = 1000
<img width="2685" height="8756" alt="schedule_viz" src="https://github.com/user-attachments/assets/0c045d17-e7d1-416e-905b-0569d105793c" />



# Lịch sử phát triển mã nguồn
| Phiên bản | File | Ý nghĩa |
| --------- | ---- | ------- |
| 1 | solution1.py | Đây là phiên bản đầu tiên, sơ khai nhất, mô hình hóa bằng boolean để tạo ràng buộc non_overlap giữa các lớp của cùng một giáo viên và các lớp trong cùng một phòng. Nhược điểm là chạy rất chậm trên bộ test có n = 1000 |
| 2 | solution2.py | Cố gắng cải tiến từ phiên bản thứ nhất bằng cách tách ra hai pha: Tối ưu về thời gian trước, rồi gán thỏa mãn cho không gian sau. Lời giải đã được cải thiện đáng kể đối với bộ dữ liệu n = 1000. Tuy nhiên với các testcase mà lịch có thể xếp vừa kín trong một tuần, solver sẽ rất khó để verify phương án tối ưu. Thường chỉ đưa ra được một phương án FEASIBLE khá tốt |
| 3 | solution2_log.py | Phiên bản ra đời với mong muốn in ra cả log của solver trong khi chạy. Vẫn giữ tư tưởng chia thành 2 pha từ phiên bản 2. Code được viết theo kiểu tuần tự, có gì viết đó |
| 4 (chốt sẽ dùng) | solution2_log_refactor.py | Phiên bản cuối, được refactor lại thành các hàm với hy vọng có thể hiểu được luồng logic tốt hơn |



# Mô hình hóa bài toán
[Google Docs](https://docs.google.com/document/d/18w3Dw3dqrWhsUHAf8Mz9rPZ1g4F-q0VhMoY1ULBX-S4/edit?usp=sharing)

# Acknowledgements
Có sự trợ giúp rất nhiều của ChatGPT, Claude, Grok và Google Studio AI Code

<p align="center">
  <img src="https://github.com/user-attachments/assets/32040bce-7dfb-413e-8c31-1a536ed333f7" width="120"/>
  <img src="https://github.com/user-attachments/assets/e53d743f-85f7-4088-8eb5-5201998b4975" width="120"/>


</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/8ba8b1a6-029f-4c7b-b57d-1ddfdf786fc3" width="120"/>
  <img src="https://github.com/user-attachments/assets/db9a4392-1d57-4046-addb-4476499761ec" width="120"/>
</p>


