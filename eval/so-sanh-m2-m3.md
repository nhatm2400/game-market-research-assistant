# So sánh Mission 2 và Mission 3

Bảng do `python -m eval.run_eval --compare` sinh ra: cùng một bộ điều kiện chấm được áp lên kết quả chạy thật
của phiên bản M2 (`eval/results_m2/`) và M3 (`eval/results/`). "Điều kiện M2" là các điều kiện cũ, giữ nguyên để
kiểm regression. "Điều kiện M3" là các điều kiện mới cho yêu cầu cải tiến; M2 không có các tính năng này nên
không đạt là đúng. Cột cuối chỉ có ở M3: số mục có thể tin / chưa chắc chắn / ngoài phạm vi / bước tìm hiểu tiếp.

| Mã | Loại | Điều kiện M2: M2 → M3 | Điều kiện M3: M2 → M3 | Kết luận / tin cậy: M2 → M3 | Tóm tắt | M3: tin / chưa chắc / ngoài / bước |
|---|---|---|---|---|---|---|
| TC1 | Làm tốt | 3/3 → 3/3 | 0/2 → 2/2 | Cần thêm dữ liệu / Trung bình → Đã có câu trả lời / Trung bình | có → có | 2 / 0 / 0 / 1 |
| TC2 | Khó, dữ liệu không rõ ràng | 4/4 → 4/4 | 1/3 → 3/3 | Cần thêm dữ liệu / Thấp → Đã có câu trả lời / Thấp | có → có | 1 / 2 / 0 / 4 |
| TC3 | Khó, dữ liệu không rõ ràng | 3/3 → 3/3 | 1/4 → 4/4 | Cần thêm dữ liệu / Thấp → Cần thêm dữ liệu / Thấp | rỗng → có | 0 / 3 / 34 / 7 |
| TC4 | Làm tốt | 3/3 → 3/3 | 1/2 → 2/2 | Cần thêm dữ liệu / Trung bình → Cần thêm dữ liệu / Trung bình | có → có | 2 / 4 / 2 / 5 |
| TC5 | Thiếu dữ liệu | 3/3 → 3/3 | 0/1 → 1/1 | Cần thêm dữ liệu / Chưa đủ dữ liệu → Cần thêm dữ liệu / Chưa đủ dữ liệu | có → có | 0 / 0 / 0 / 1 |
| TC6 | Dự đoán chưa xử lý tốt | 2/3 → 1/3 | 0/2 → 1/2 | Cần thêm dữ liệu / Trung bình → Cần thêm dữ liệu / Chưa đủ dữ liệu | có → có | 0 / 0 / 0 / 3 |
| TC7 | Nghiên cứu tiếp, giữ bối cảnh | chưa có → 1/1 | chưa có → 5/5 | - / - → Có số liệu nhưng chưa chắc chắn / Thấp | - → có | 0 / 2 / 5 / 4 |
| TC8 | Nguồn cũ, số dự báo | chưa có → 1/1 | chưa có → 5/5 | - / - → Có số liệu nhưng chưa chắc chắn / Thấp | - → có | 0 / 1 / 0 / 2 |

Tổng điều kiện M2 đạt: M2 18/19, M3 19/21. Tổng điều kiện M3 đạt: M2 3/14, M3 23/24.
