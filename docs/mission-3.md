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

**Cùng một bộ điều kiện chấm, áp lên kết quả chạy thật của M2 và M3** (`eval/so-sanh-m2-m3.md`, sinh bằng `python -m eval.run_eval --compare`):

| | Bản M2 | Bản M3 |
|---|---|---|
| Điều kiện cũ của M2 (regression) | 18/19 | 20/21 (thêm 2 case mới, không mất điều kiện nào) |
| Điều kiện mới của M3 | 3/14 | 23/24 |
| Số case đạt | 5/6 | 7/8 |

Điều kiện duy nhất chưa đạt ở cả hai bản là TC6 (số nằm trong biểu đồ PDF), case đã được dự đoán là chưa đạt từ M2.

**Từng thay đổi và case chứng minh nó** (chi tiết trong `eval/ket-qua-kiem-thu.md`):

| Thay đổi | Trước (M2) | Sau (M3) |
|---|---|---|
| Tách điều có thể tin khỏi điều chưa chắc | TC2: 5,37 và 5,89 tỷ USD, số dự báo 2029 nằm chung, một nhãn "tin cậy Thấp" | TC2: ba nguồn gốc 5,37 / 5,89 / 6,51 tỷ USD gom thành một mâu thuẫn lệch 21%, xếp "chưa chắc chắn"; số 2029 để riêng; bước tiếp: so sánh cách đo của ba hãng |
| Số dự báo cũ | Số "2025: 5,47 tỷ USD" (bài tháng 9/2025) không có cảnh báo | TC8: xếp "chưa chắc chắn" vì năm 2025 chưa kết thúc lúc đăng; bước tiếp: tìm số đã đo |
| Nghiên cứu tiếp giữ bối cảnh | Không có | TC7: "Còn riêng Việt Nam thì sao?" thành câu hỏi đầy đủ về Việt Nam năm 2024, giữ 7/7 nhận định, đọc lại nguồn đã lưu, tìm ra 0,817 tỷ (Newzoo) và 0,46 tỷ (Statista) lệch 78%; 6 lượt gọi LLM |
| Kết luận hợp loại câu hỏi | TC1: "Cần thêm dữ liệu" dù đã có 625 triệu USD | TC1: "Đã có câu trả lời", 625 triệu USD ở "có thể tin" |
| Không đạt nhầm | TC6: "top_growth_genre" đạt nhờ số +50% của Indonesia | TC6: điều kiện mới chỉ xét số Đông Nam Á nên báo đúng là chưa đạt; có bước mở thẳng tới biểu đồ chưa đọc được |
| Lỗi M2 | TC3 rỗng tóm tắt; "0.817" đọc thành 817 | TC3 có tóm tắt; 0,817 đọc đúng (TC7) |

**Test offline**: 53 bài, gồm 32 bài M2 giữ nguyên (regression), 20 bài mới cho M3 và 1 bài giao diện (Streamlit AppTest). Mỗi lỗi tìm ra trong lúc làm M3 đều có test riêng: đơn vị USD bị thiếu, ô bảng "N-6.51" bị đọc thành số âm, độ lệch "21%" do code tính bị bộ kiểm loại, nhãn bị ghép với số trong biểu đồ.

**Lưu ý về độ ổn định**: kết luận (nhãn "Đã có câu trả lời", "Cần thêm dữ liệu") và câu tóm tắt vẫn do AI viết nên có thể khác nhau giữa các lần chạy; ở một lần chạy với prompt cũ, TC1 ra "Cần thêm dữ liệu". Ba phần có thể tin / chưa chắc chắn / tìm hiểu tiếp do code xếp nên cùng bằng chứng luôn ra cùng kết quả. Kết quả trong bảng là lần chạy đủ 8 case cuối cùng; riêng TC6 được chạy lại sau khi thêm bước chỉ tới biểu đồ khi nhãn bị ghép với số.

## 6. Giới hạn còn lại

- **"Có thể tin" không có nghĩa là đúng**: phân loại dựa trên quy tắc về nguồn, kỳ đo và thị trường. Số do chính hãng dữ liệu công bố vẫn là ước tính của hãng đó.
- **Các trường do AI điền chỉ được kiểm một phần**: code kiểm câu trích và con số, nhưng thị trường, kỳ đo, và đơn vị lấy từ tiêu đề bảng vẫn do AI điền.
- **Số trong biểu đồ** (TC6): hệ thống chỉ tới đúng chỗ để người dùng tự đọc, chưa tự đọc được.
- **Kết luận và tóm tắt do AI viết** có thể khác nhau giữa các lần chạy (xem mục 5).
- **Nguồn miễn phí phần lớn là bài dẫn lại**: hầu hết số liệu mang lưu ý "chưa đối chiếu bản gốc", vì báo cáo gốc của hãng dữ liệu thường phải trả phí. Người dùng có thể tải báo cáo đã mua lên.
- **Change Request chưa được giao**: khi có sẽ thêm TC9 và test riêng.
- **Bộ kiểm thử thật mới có 8 tình huống**: chưa đủ để đo tỷ lệ sai của mục "có thể tin".

## 7. Bộ kiểm thử Mission 3

| Yêu cầu của đề | Ở đâu |
|---|---|
| Chạy lại test quan trọng của M2 để kiểm regression | 32 test offline của M2 giữ nguyên; `checks` của TC1 đến TC6 giữ nguyên và chạy lại trên bản M3 |
| Test cho Change Request | Chưa có Change Request; sẽ là TC9 |
| Edge case / tình huống khó | TC8 (số dự báo trong bài cũ), TC7 (câu hỏi tiếp cụt ngủn cần bối cảnh), TC2 (ba nguồn mâu thuẫn), TC6 (biểu đồ); test offline: nhãn ghép với số, ô "N-6.51", số không ghi đơn vị |
| Regression test cho chức năng cũ | `checks` M2 của TC1 đến TC6; test offline `test_numbers_from_the_question_are_allowed...` (lỗi TC3), `test_decimal_with_leading_zero...` (lỗi 0.817), cùng 32 test M2 |

## 8. Ba câu hỏi bắt buộc (bản soạn)

**Câu 1. Sau khi nhận yêu cầu mới, bạn đã ưu tiên thay đổi điều gì và chủ động chưa làm điều gì? Vì sao?**

Em ưu tiên đúng câu người ra quyết định hỏi: điều gì có thể tin, điều gì chưa chắc chắn, nên tìm tiếp ở đâu. Bản M2 gộp mọi số liệu dưới một mức tin cậy chung, nên em làm theo thứ tự:
1. Chia bản tóm tắt thành ba phần do code xếp theo quy tắc. Mỗi điểm chưa chắc chắn ghi rõ lý do (mâu thuẫn, chỉ có bài dẫn lại từ nguồn hạng C, số cũ, số dự báo khi kỳ đo chưa kết thúc) và kèm một bước tìm tiếp bấm được.
2. Cho hỏi tiếp mà vẫn giữ bối cảnh: câu hỏi tiếp được viết lại thành câu hỏi đầy đủ, giữ các nhận định đã kiểm và các nhận định người dùng đã loại.
3. Kiểm chứng một cú nhấp tới đúng câu trích hoặc đúng trang PDF.
4. Sửa các lỗi M2 đã ghi lại.

Em chủ động chưa làm bốn việc:
- Không cho AI chấm độ tin cậy, vì kết quả không lặp lại được và không giải thích được.
- Không hạ chuẩn kiểm câu trích cho số trong biểu đồ. Trong lúc chạy, AI từng ghép +37,6% với Match Swap, trong khi đúng là Battle Royale; nới chuẩn thì số ghép sai sẽ lọt.
- Chưa dùng mô hình đọc ảnh cho biểu đồ, vì code chưa kiểm được kết quả và gói miễn phí giới hạn số lượt gọi.
- Không đổi quy tắc tin cậy của M2, để kết quả hai phiên bản so sánh được với nhau.

**Câu 2. Thay đổi nào tạo ra khác biệt lớn nhất giữa sản phẩm Mission 2 và Mission 3? Bạn dùng bằng chứng nào để kết luận phiên bản mới tốt hơn?**

Khác biệt lớn nhất là ba phần có thể tin / chưa chắc chắn / tìm hiểu tiếp do code xếp, cùng với khả năng hỏi tiếp từ chính các bước đó. Em áp cùng một bộ điều kiện chấm lên kết quả chạy thật của hai phiên bản. Bản M3 đạt 23/24 điều kiện mới, bản M2 chỉ đạt 3/14. Các điều kiện cũ của M2 vẫn đạt (18/19 ở M2, 20/21 ở M3), nghĩa là không có regression. Bằng chứng cụ thể:
- TC2: ba nguồn gốc 5,37 / 5,89 / 6,51 tỷ USD được nhận ra là một mâu thuẫn lệch 21% và không con số nào bị đưa vào phần có thể tin.
- TC8: số 5,47 tỷ USD cho năm 2025 trong bài đăng tháng 9/2025 được nhận ra là số dự báo.
- TC7: câu "Còn riêng Việt Nam thì sao?" giữ đủ bối cảnh và tìm ra hai con số lệch nhau 78%.
- TC1: kết luận đổi từ "Cần thêm dữ liệu" sang "Đã có câu trả lời".

Toàn bộ có 53 test offline và 8 tình huống chạy thật lưu trong repo.

**Câu 3. Nếu sản phẩm này được đưa cho người dùng thật vào ngày mai, rủi ro hoặc giới hạn lớn nhất còn lại là gì? Bạn sẽ ưu tiên xử lý nó như thế nào?**

Rủi ro lớn nhất là người dùng hiểu "có thể tin" là "đúng". Thực ra nó chỉ có nghĩa là số đạt quy tắc về nguồn, kỳ đo và thị trường. Thêm nữa, các trường như thị trường, kỳ đo hay đơn vị lấy từ tiêu đề bảng vẫn do AI điền, và nhãn kết luận vẫn có thể dao động giữa các lần chạy. Em sẽ ưu tiên ba việc:
1. Mở rộng bộ kiểm thử lên khoảng 20 đến 30 câu hỏi có đáp án đã biết, để đo tỷ lệ "có thể tin nhưng sai" và tỷ lệ kết luận dao động giữa các lần chạy.
2. Để người dùng báo nhận định sai ngay trên giao diện, rồi đưa các ca đó vào bộ kiểm thử.
3. Kiểm thêm bằng code những trường AI điền, ví dụ tìm tiêu đề cột trong nguồn để xác nhận đơn vị, và tính nhãn kết luận bằng quy tắc từ ba phần thay vì để AI chọn.

Số trong biểu đồ để sau ba việc trên. Khi làm, kết quả đọc bằng mô hình nhìn ảnh mặc định chỉ được vào phần chưa chắc chắn.

## 9. Kịch bản video (dưới 5 phút)

Quay im lặng, chèn chữ khi dựng. Trước khi quay: mở app, bỏ chọn "Tìm nguồn trên web", để sẵn ba link của TC2.

| Thời gian | Màn hình | Chữ thuyết minh |
|---|---|---|
| 0:00–0:15 | Khung tiêu đề | Mission 3: điều gì có thể tin, điều gì chưa chắc chắn, nên tìm hiểu tiếp ở đâu |
| 0:15–0:45 | GitHub: `eval/results_m2/TC2.md` | Trước (M2): mọi số liệu dưới một mức tin cậy; cả 6 case đều ra "Cần thêm dữ liệu" |
| 0:45–1:10 | `docs/mission-3.md` mục 3 | Quyết định: ba phần do code xếp, hỏi tiếp giữ bối cảnh, kiểm chứng một cú nhấp. Không cho AI chấm tin cậy, không hạ chuẩn kiểm câu trích |
| 1:10–1:40 | App: chạy câu hỏi TC2 (tua nhanh lúc chờ) | Sau (M3): chạy cùng câu hỏi TC2 |
| 1:40–2:20 | Bản tóm tắt, hai cột, mục ngoài phạm vi | Có thể tin / Chưa chắc chắn: ba hãng lệch nhau 21% nên chưa chắc chắn; số 2029 để riêng |
| 2:20–2:45 | Bấm một nhận định, "Mở nguồn tại câu trích" | Kiểm chứng một cú nhấp: trang mở đúng câu trích, câu được tô sáng |
| 2:45–3:30 | Ô "Hỏi tiếp": gõ "Còn riêng Việt Nam thì sao?" | Hỏi tiếp giữ bối cảnh: hiểu thành Việt Nam năm 2024, giữ nhận định cũ, tìm ra 0,817 và 0,46 tỷ USD lệch 78% |
| 3:30–4:05 | GitHub: `eval/so-sanh-m2-m3.md`, terminal chạy pytest | Bằng chứng: điều kiện M3 từ 3/14 lên 23/24, điều kiện M2 không giảm, 53 test qua |
| 4:05–4:35 | `docs/mission-3.md` mục 6 | Giới hạn: "có thể tin" không có nghĩa là đúng; số trong biểu đồ chưa tự đọc được; Change Request đang chờ |
| 4:35–4:45 | Khung kết | Link app và repo |
