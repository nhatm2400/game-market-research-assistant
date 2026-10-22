# Độ ổn định qua nhiều lần chạy

Bảng do `python -m eval.run_eval --stability` sinh ra từ 3 lần chạy đủ bộ kiểm thử, kết quả mỗi lần
lưu trong `eval/runs/`. Câu trả lời của AI thay đổi giữa các lần chạy, nên một lần đạt chưa đủ để kết luận.

| Mã | Loại | Số lần đạt mọi điều kiện | Kết luận qua các lần (số lần) |
|---|---|---|---|
| TC1 | Làm tốt | 3/3 | Đã có câu trả lời (3) |
| TC2 | Khó, dữ liệu không rõ ràng | 3/3 | Có số liệu nhưng chưa chắc chắn (3) |
| TC3 | Khó, dữ liệu không rõ ràng | 3/3 | Có số liệu nhưng chưa chắc chắn (1), Cần thêm dữ liệu (2) |
| TC4 | Làm tốt | 3/3 | Cần thêm dữ liệu (3) |
| TC5 | Thiếu dữ liệu | 3/3 | Cần thêm dữ liệu (3) |
| TC6 | Dự đoán chưa xử lý tốt | 0/3 | Cần thêm dữ liệu (3) |
| TC7 | Nghiên cứu tiếp, giữ bối cảnh | 3/3 | Có số liệu nhưng chưa chắc chắn (3) |
| TC8 | Nguồn cũ, số dự báo | 3/3 | Có số liệu nhưng chưa chắc chắn (3) |

Điều kiện không đạt ở ít nhất một lần chạy:

- TC6 `verified_numbers`: đạt 0/3
- TC6 `[M3] top_growth_genre_in_market`: đạt 0/3
