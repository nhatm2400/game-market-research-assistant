# So sánh Mission 2 và Mission 3

Bảng do `python -m eval.run_eval --compare` sinh ra: cùng một bộ điều kiện chấm được áp lên kết quả chạy thật
của phiên bản M2 (`eval/results_m2/`) và M3 (`eval/results/`). "Điều kiện M2" là các điều kiện cũ, giữ nguyên để
kiểm regression. "Điều kiện M3" là các điều kiện mới cho yêu cầu cải tiến; M2 không có các tính năng này nên
không đạt là đúng. Cột cuối chỉ có ở M3: số mục có thể tin / chưa chắc chắn / ngoài phạm vi / bước tìm hiểu tiếp.

| Mã | Loại | Điều kiện M2: M2 → M3 | Điều kiện M3: M2 → M3 | Kết luận / tin cậy: M2 → M3 | Tóm tắt | M3: tin / chưa chắc / ngoài / bước |
|---|---|---|---|---|---|---|
| TC1 | Làm tốt | 3/3 → 3/3 | 0/2 → 2/2 | Cần thêm dữ liệu / Trung bình → Đã có câu trả lời / Trung bình | có → có | 5 / 0 / 6 / 1 |
| TC2 | Khó, dữ liệu không rõ ràng | 4/4 → 4/4 | 1/3 → 3/3 | Cần thêm dữ liệu / Thấp → Đã có câu trả lời / Thấp | có → có | 5 / 1 / 5 / 3 |
| TC3 | Khó, dữ liệu không rõ ràng | 3/3 → 3/3 | 1/4 → 4/4 | Cần thêm dữ liệu / Thấp → Cần thêm dữ liệu / Thấp | rỗng → có | 0 / 6 / 26 / 4 |
| TC4 | Làm tốt | 3/3 → 3/3 | 1/2 → 2/2 | Cần thêm dữ liệu / Trung bình → Cần thêm dữ liệu / Trung bình | có → có | 1 / 0 / 12 / 1 |
| TC5 | Thiếu dữ liệu | 3/3 → 3/3 | 0/1 → 1/1 | Cần thêm dữ liệu / Chưa đủ dữ liệu → Cần thêm dữ liệu / Chưa đủ dữ liệu | có → có | 0 / 0 / 0 / 3 |
| TC6 | Dự đoán chưa xử lý tốt | 2/3 → 2/3 | 0/2 → 1/2 | Cần thêm dữ liệu / Trung bình → Cần thêm dữ liệu / Trung bình | có → có | 0 / 0 / 3 / 5 |
| TC7 | Nghiên cứu tiếp, giữ bối cảnh | chưa có → 1/1 | chưa có → 4/5 | - / - → Cần thêm dữ liệu / Trung bình | - → có | 0 / 0 / 11 / 1 |
| TC8 | Nguồn cũ, số dự báo | chưa có → 1/1 | chưa có → 5/5 | - / - → Đã có câu trả lời / Thấp | - → có | 0 / 3 / 2 / 3 |

Tổng điều kiện M2 đạt: M2 18/19, M3 20/21. Tổng điều kiện M3 đạt: M2 3/14, M3 22/24.
