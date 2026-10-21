# Mission 3: trước và sau cải tiến

## 1. M2, trước cải tiến

Phiên bản Mission 2 đã chứng minh được giá trị cốt lõi: mỗi nhận định có câu trích nguyên văn và code đã tìm thấy câu đó trong nguồn; hạng nguồn, nguồn gốc dữ liệu, mâu thuẫn và mức tin cậy đều do code tính. Kết quả chạy thật lúc đó: 5/6 tình huống đạt (`eval/ket-qua-m2.md`).

Nhưng bản tóm tắt M2 chỉ có **một** mức tin cậy chung cho cả câu trả lời. Khi đọc lại kết quả M2 có thể thấy:

| Vấn đề ở M2 | Bằng chứng (kết quả chạy thật M2) |
|---|---|
| Không tách được điều có thể tin khỏi điều chưa chắc | TC2: con số 5,37 tỷ USD (Niko Partners), cặp số mâu thuẫn 5,37 và 5,89 tỷ, và số dự báo 2029 nằm chung một danh sách, dưới một nhãn "tin cậy Thấp" |
| Không chỉ ra nên tìm tiếp ở đâu | Chỉ có mục "Điều gì sẽ làm thay đổi khuyến nghị" do AI viết chung chung; không có truy vấn hay link cụ thể |
| Kết luận không hợp với loại câu hỏi | Cả 6 case đều ra "Cần thêm dữ liệu", kể cả TC1 đã tìm được đúng con số 625 triệu USD |
| Mỗi câu hỏi là một lần chạy riêng | Muốn hỏi "còn Việt Nam thì sao" phải gõ lại câu hỏi từ đầu, chạy lại toàn bộ, mất nhận định đã loại |
| Kiểm chứng tốn công | Link chỉ mở đầu trang; người dùng phải tự tìm câu trích trong bài dài hoặc PDF 20 trang |
| Số dự báo cũ trông như số đã đo | Số "năm 2025: 5,47 tỷ USD" trong bài tháng 9/2025 không có cảnh báo gì |
| Lỗi nhỏ | TC3 mất câu tóm tắt vì bộ kiểm coi "12 tháng" là số bịa; ô bảng "0.817" bị đọc thành 817; số lượt gọi LLM bị cộng dồn qua các case |

## 2. Yêu cầu mới

Người ra quyết định cần biết: **điều gì có thể tin, điều gì còn chưa chắc chắn và nên tìm hiểu tiếp ở đâu**, khi cùng một câu hỏi có nhiều nguồn khác nhau về thời điểm, độ tin cậy và kết luận.

## 3. Quyết định: thay đổi gì, không thay đổi gì

**Ưu tiên thay đổi** (theo thứ tự):

1. **Ba phần do code xếp**: có thể tin, chưa chắc chắn (kèm lý do), nên tìm hiểu tiếp ở đâu (kèm bước cụ thể). Đây là đúng câu hỏi của người ra quyết định, và xây trên quy tắc tin cậy đã công khai ở M2 nên không thêm chỗ cho AI tự chấm.
2. **Nghiên cứu tiếp giữ bối cảnh**: hỏi tiếp hoặc bấm một bước tìm hiểu tiếp mà không mất nhận định đã kiểm và nhận định người dùng đã loại.
3. **Kiểm chứng một cú nhấp**: link mở đúng câu trích hoặc đúng trang PDF.
4. **Nguồn cũ và dự báo**: cờ cho số của kỳ chưa kết thúc lúc đăng bài, kỳ kéo dài tới tương lai, số đã có bản mới hơn; số của thị trường hoặc kỳ khác được để riêng.
5. **Sửa các lỗi M2 đã ghi**.

**Chủ động chưa làm**:

- **Không cho AI chấm độ tin cậy hay xếp "có thể tin"**. Nếu AI xếp, cùng bằng chứng có thể ra kết quả khác nhau giữa các lần chạy và không giải thích được.
- **Không hạ chuẩn kiểm câu trích**. Câu trích chỉ có con số (thường lấy từ biểu đồ PDF) vẫn bị loại; thay vào đó hệ thống chỉ tới đúng trang biểu đồ để người dùng tự đọc. Cho qua thì sẽ lọt số bị ghép nhầm nhãn như TC6 ở M2.
- **Chưa đọc biểu đồ bằng mô hình nhìn ảnh**. Code không kiểm được cặp nhãn và số mà mô hình thị giác đọc ra, mỗi trang tốn thêm một lượt gọi, và gói miễn phí giới hạn số lượt mỗi ngày.
- **Không đổi quy tắc tin cậy của M2**, để kết quả M2 và M3 so sánh được với nhau; ba phần mới dựa trên các quy tắc đó.
- **Chưa làm đăng nhập, lưu trữ lâu dài, nguồn tiếng Trung**: không phục vụ trực tiếp yêu cầu mới.

## 4. M3, sau cải tiến

Luồng mới trên giao diện:

1. Chạy câu hỏi như M2.
2. Đầu bản tóm tắt: kết luận, mức tin cậy, số mục có thể tin / chưa chắc chắn.
3. Hai cột: **Có thể tin** (mỗi mục có giá trị, nguồn gốc, lưu ý nếu là số dẫn lại) và **Chưa chắc chắn** (mỗi mục có lý do cụ thể).
4. **Nên tìm hiểu tiếp ở đâu**: các bước đã gộp trùng, mỗi bước có nút "Tìm thêm" hoặc "Mở nguồn".
5. Ô **Hỏi tiếp**: câu hỏi tiếp được viết lại thành câu hỏi đầy đủ; chuỗi nghiên cứu hiện ở đầu trang.
6. Mỗi nhận định có nút **Mở nguồn tại câu trích** và đoạn văn quanh câu trích.

## 5. Bằng chứng

_(điền sau khi chạy eval)_

## 6. Giới hạn còn lại

_(điền sau khi chạy eval)_
