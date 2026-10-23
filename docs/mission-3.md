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
| Số dự báo cũ trông như số đã đo | Số "năm 2025: 5,47 tỷ USD" trong bài tháng 9/2025 chỉ bị cảnh báo vì nằm ngoài khung 2024 của câu hỏi TC2. M2 không có quy tắc nhận ra đây là số ước tính (năm 2025 chưa hết lúc đăng), nên với câu hỏi về năm 2025 nó sẽ hiện như số đã đo. Điều này suy ra từ quy tắc của M2; M2 chưa được chạy trên TC8 |
| Lỗi nhỏ | TC3 mất câu tóm tắt vì bộ kiểm coi "12 tháng" là số bịa; ô bảng "0.817" bị đọc thành 817; số lượt gọi LLM bị cộng dồn qua các case |

## 2. Yêu cầu mới

Người ra quyết định cần biết: **điều gì có thể tin, điều gì còn chưa chắc chắn và nên tìm hiểu tiếp ở đâu**, khi cùng một câu hỏi có nhiều nguồn khác nhau về thời điểm, độ tin cậy và kết luận.

**Change Request A4: Hỗ trợ quyết định.** Người dùng không muốn đọc một báo cáo dài. Họ muốn biết **nên làm gì tiếp theo và quyết định đó dựa trên bằng chứng nào**. Bản M3 trước khi nhận Change Request vẫn bắt người dùng đọc lý do, hai cột số liệu và danh sách bước mới thấy được việc cần làm.

## 3. Quyết định: thay đổi gì, không thay đổi gì

**Ưu tiên thay đổi** (theo thứ tự):

1. **Ba phần do code xếp**: có thể tin, chưa chắc chắn (kèm lý do), nên tìm hiểu tiếp ở đâu (kèm bước cụ thể). Đây là đúng câu hỏi của người ra quyết định, và xây trên quy tắc tin cậy đã công khai ở M2 nên không thêm chỗ cho AI tự chấm.
2. **Nghiên cứu tiếp giữ bối cảnh**: hỏi tiếp hoặc bấm một bước tìm hiểu tiếp mà không mất nhận định đã kiểm và nhận định người dùng đã loại.
3. **Kiểm chứng một cú nhấp**: link mở đúng câu trích hoặc đúng trang PDF.
4. **Nguồn cũ và dự báo**: cờ cho số của kỳ chưa kết thúc lúc đăng bài, kỳ kéo dài tới tương lai, số đã có bản mới hơn; số của thị trường hoặc kỳ khác được để riêng.
5. **Sửa các lỗi M2 đã ghi**.
6. **Change Request A4: khối "Quyết định nhanh"** ở ngay đầu kết quả và ở đầu bản Markdown tải về: đọc trong vài giây để biết **nên làm gì tiếp** (một câu hành động và bước tiếp theo, có nút bấm làm luôn) và **dựa trên bằng chứng nào** (tối đa 3 dòng, mỗi dòng có con số, nguồn gốc, hạng nguồn, trạng thái có thể tin hay chưa chắc chắn kèm lý do ngắn, và liên kết mở đúng câu trích của từng hãng). Khối do code chọn từ các phần đã kiểm, không gọi thêm AI. Quy tắc nội dung đơn giản:
   - Kết luận "Đã có câu trả lời" hoặc "Nên ưu tiên": hành động là dùng kết luận, bằng chứng lấy từ mục có thể tin.
   - "Có số liệu nhưng chưa chắc chắn": hành động là bước tìm tiếp đầu tiên; bằng chứng gồm cả số chưa chắc chắn và ghi rõ lý do vì sao chưa chắc.
   - "Cần thêm dữ liệu" hoặc "Chưa nên": hành động là bước thu thập dữ liệu đầu tiên; nói thẳng là chưa đủ cơ sở để quyết định, không bịa bằng chứng.
   - Không bao giờ liệt kê một con số chưa chắc chắn như thể nó có thể tin. Báo cáo chi tiết vẫn ở bên dưới cho ai muốn kiểm lại.

**Chủ động chưa làm**:

- **Không để AI chọn bằng chứng cho khối quyết định, không gọi thêm AI**. Khối được dựng lại từ những gì đã kiểm, nên cùng kết quả luôn ra cùng khối và không tốn thêm lượt gọi.
- **Không bỏ báo cáo chi tiết**. Change Request cần bản ngắn, nhưng người muốn kiểm vẫn phải xem được toàn bộ số liệu và câu trích.
- **Không cho AI chấm độ tin cậy hay xếp "có thể tin"**. Nếu AI xếp, cùng bằng chứng có thể ra kết quả khác nhau giữa các lần chạy và không giải thích được.
- **Không hạ chuẩn kiểm câu trích**. Câu trích chỉ có con số (thường lấy từ biểu đồ PDF) vẫn bị loại; thay vào đó hệ thống chỉ tới đúng trang biểu đồ để người dùng tự đọc. Cho qua thì sẽ lọt số bị ghép nhầm nhãn như TC6 ở M2.
- **Chưa đọc biểu đồ bằng mô hình nhìn ảnh**. Code không kiểm được cặp nhãn và số mà mô hình thị giác đọc ra, mỗi trang tốn thêm một lượt gọi, và gói miễn phí giới hạn số lượt mỗi ngày.
- **Không đổi quy tắc tin cậy của M2**, để kết quả M2 và M3 so sánh được với nhau; ba phần mới dựa trên các quy tắc đó.
- **Chưa làm đăng nhập, lưu trữ lâu dài, nguồn tiếng Trung**: không phục vụ trực tiếp yêu cầu mới.

## 4. M3, sau cải tiến

Luồng mới trên giao diện:

1. Chạy câu hỏi như M2.
2. **Quyết định nhanh** (Change Request A4) ở đầu trang: kết luận, mức tin cậy, câu tóm tắt, **Nên làm gì tiếp** (kèm nút "Làm bước này"), **Dựa trên bằng chứng nào** (tối đa 3 dòng có link câu trích). Kết luận chắc chắn ("Đã có câu trả lời", "Nên ưu tiên") chỉ được giữ khi ít nhất một nửa lý do dựa trên nhận định có thể tin; nếu không, code đổi thành "Có số liệu nhưng chưa chắc chắn" hoặc "Cần thêm dữ liệu". Bản Markdown tải về cũng mở đầu bằng khối này.
3. Hai cột: **Có thể tin** (mỗi mục có giá trị, nguồn gốc, lưu ý nếu là số dẫn lại) và **Chưa chắc chắn** (mỗi mục có lý do cụ thể).
4. **Nên tìm hiểu tiếp ở đâu**: các bước đã gộp trùng, mỗi bước có nút "Tìm thêm" hoặc "Mở nguồn".
5. Ô **Hỏi tiếp**: câu hỏi tiếp được viết lại thành câu hỏi đầy đủ; chuỗi nghiên cứu hiện ở đầu trang.
6. Mỗi nhận định có nút **Mở nguồn tại câu trích** và đoạn văn quanh câu trích.

## 5. Bằng chứng

**Cùng một bộ điều kiện chấm, áp lên kết quả chạy thật của M2 và M3** (`eval/so-sanh-m2-m3.md`, sinh bằng `python -m eval.run_eval --compare`):

| | Bản M2 | Bản M3 |
|---|---|---|
| Điều kiện cũ của M2 (regression) | 18/19 | 21/22 |
| Điều kiện mới của M3 | 3/14 | 23/24 |
| Điều kiện Change Request A4 (khối quyết định nhanh) | 0/6 | 11/11 |
| Số case đạt | 5/6 | 8/9 |

Cách đọc con số 3/14: 8 trong 11 điều kiện M3 mà bản M2 không đạt là điều kiện về ba phần mới (có thể tin, chưa chắc chắn, bước tìm tiếp), M2 chưa có các phần này nên không đạt là đương nhiên; con số đó chỉ cho thấy phần mới có mặt và đúng trên các case. Trên 6 điều kiện chấm được cho cả hai bản, M2 đạt 3 (2 trong đó đạt vì M2 không có mục "có thể tin" để xếp sai), M3 đạt 5. Điều kiện còn trượt là của TC6.

Mọi điều kiện chưa đạt đều ở TC6 (số nằm trong biểu đồ PDF), case đã được dự đoán là chưa đạt từ M2. Điều kiện cũ `top_growth_genre` của TC6 vẫn "đạt nhầm" ở cả hai bản nhờ số +50% của Indonesia; điều kiện mới chỉ xét số của Đông Nam Á nên báo đúng là chưa đạt.

**Độ ổn định qua 3 lần chạy đủ bộ kiểm thử** (`eval/do-on-dinh.md`, kết quả từng lần trong `eval/runs/`). Một lần đạt chưa đủ để kết luận vì câu trả lời của AI thay đổi giữa các lần, nên bộ kiểm thử được chạy lại 3 lần trên cùng bản code:

| Case | Đạt mọi điều kiện | Kết luận qua 3 lần |
|---|---|---|
| TC1 tra cứu một con số | 3/3 | Đã có câu trả lời (3) |
| TC2 ba nguồn mâu thuẫn | 3/3 | Có số liệu nhưng chưa chắc chắn (3) |
| TC3 khung 12 tháng | 3/3 | Cần thêm dữ liệu (2), Có số liệu nhưng chưa chắc chắn (1) |
| TC4 quyết định phát hành | 3/3 | Cần thêm dữ liệu (3) |
| TC5 không có dữ liệu | 3/3 | Cần thêm dữ liệu (3) |
| TC6 số trong biểu đồ | 0/3 | Cần thêm dữ liệu (3) |
| TC7 hỏi tiếp | 3/3 | Có số liệu nhưng chưa chắc chắn (3) |
| TC8 số dự báo cũ | 3/3 | Có số liệu nhưng chưa chắc chắn (3) |
| TC9 Change Request A4 | 3/3 | Nên ưu tiên (2), Cần thêm dữ liệu (1) |

Chỉ có hai điều kiện từng không đạt, cả hai đều của TC6 và không đạt ở cả 3 lần. Ba phần do code xếp cho cùng kết quả ở các điểm chính: TC2 cả 3 lần gom Niko 5,37 / Statista 5,89 / Newzoo 6,51 tỷ USD thành một mâu thuẫn lệch 21%; TC7 cả 3 lần tìm ra 0,46 và 0,817 tỷ USD lệch 78%; TC8 cả 3 lần xếp 5,47 tỷ USD vào chưa chắc chắn. Nhãn kết luận còn dao động ở TC3 và TC9; ở TC9, khối quyết định nhanh cả 3 lần đều có đúng 3 bằng chứng đã kiểm có link câu trích (625 triệu USD, MOBA +20,1%, 4X +17,6%).

**Từng thay đổi và case chứng minh nó** (chi tiết trong `eval/ket-qua-kiem-thu.md`):

| Thay đổi | Trước (M2) | Sau (M3) |
|---|---|---|
| Tách điều có thể tin khỏi điều chưa chắc | TC2: 5,37 và 5,89 tỷ USD, số dự báo 2029 nằm chung, một nhãn "tin cậy Thấp" | TC2: ba nguồn gốc 5,37 / 5,89 / 6,51 tỷ USD gom thành một mâu thuẫn lệch 21%, xếp "chưa chắc chắn"; tăng trưởng 5,2% ở "có thể tin"; bước tiếp: so sánh cách đo của các hãng |
| Số dự báo cũ | Số "2025: 5,47 tỷ USD" (bài tháng 9/2025): M2 chỉ cảnh báo khi số lệch khung của câu hỏi, không có quy tắc số ước tính | TC8: xếp "chưa chắc chắn" vì năm 2025 chưa kết thúc lúc đăng; kết luận "Có số liệu nhưng chưa chắc chắn"; bước tiếp: tìm số đã đo |
| Nghiên cứu tiếp giữ bối cảnh | Không có | TC7: "Còn riêng Việt Nam thì sao?" thành câu hỏi đầy đủ về Việt Nam năm 2024, giữ toàn bộ nhận định của TC2, đọc lại nguồn đã lưu, tìm ra 0,46 tỷ (Statista) và 0,817 tỷ (Newzoo) lệch 78% |
| Kết luận hợp loại câu hỏi | TC1: "Cần thêm dữ liệu" dù đã có 625 triệu USD | TC1: "Đã có câu trả lời" cả 3 lần, 625 triệu USD ở "có thể tin" |
| Không đạt nhầm | TC6: "top_growth_genre" đạt nhờ số +50% của Indonesia | TC6: điều kiện mới báo đúng là chưa đạt; có bước mở thẳng tới biểu đồ chưa đọc được |
| Lỗi M2 | TC3 rỗng tóm tắt; "0.817" đọc thành 817 | TC3 có tóm tắt cả 3 lần; 0,817 đọc đúng (TC7) |
| Change Request A4: nên làm gì tiếp, dựa trên gì | Không có; phải đọc cả báo cáo | TC9 ("Nên ưu tiên MOBA hay 4X?"): đầu trang là "Ưu tiên phát hành game MOBA; cần đối chiếu thêm báo cáo gốc của Sensor Tower trước khi chốt đầu tư", bước tiếp theo bấm được, và 3 bằng chứng có link câu trích. TC2: "Chưa nên dùng các con số này làm căn cứ chính" kèm bước so sánh cách đo của các hãng và link câu trích của từng hãng |

**Test offline**: 76 bài, gồm 32 bài M2 (regression; một bài đổi điều kiện kiểm vì M3 thêm quy tắc kết luận), 34 bài mới cho M3 (32 trong `tests/test_m3.py`, 2 về lỗi hết lượt gọi AI), 7 bài cho Change Request A4 trong `tests/test_cr.py` và 3 bài giao diện (Streamlit AppTest: khối quyết định nhanh đứng trước báo cáo dài và hiện trong kết quả mẫu, chữ từ nguồn được escape trước khi chèn vào trang, kết quả có sẵn mở được không cần AI). Mỗi lỗi tìm ra trong lúc làm M3 đều có test riêng: đơn vị USD bị thiếu, số trong bảng không ghi đơn vị, ô bảng "S-5.89 N-6.51" bị đọc thành số âm, giá trị ghi hai con số, độ lệch "21%" do code tính bị bộ kiểm loại, nhãn bị ghép với số trong biểu đồ, kết luận chắc chắn khi không lý do nào dựa trên nhận định có thể tin, và không số chưa chắc chắn nào bị gắn nhãn tin được trong khối quyết định.

**Về độ ổn định**: câu tóm tắt và nhãn kết luận do AI viết nên có thể khác nhau giữa các lần chạy. Code chặn một chiều: không lý do nào dựa trên nhận định có thể tin thì không được ghi là "Đã có câu trả lời" hay "Nên ưu tiên". AI trích ra nhận định nào từ nguồn cũng khác nhau giữa các lần, nên số mục trong ba phần thay đổi (ví dụ TC4). Bảng kết quả chính (`eval/ket-qua-kiem-thu.md`) là lần chạy thứ 3. Ba lần chạy là chạy thật; sau đó các quy tắc mới (kết luận chắc chắn cần đa số lý do có thể tin, giá trị phải khớp con số trong câu trích cả về dấu, bậc và đơn vị) được áp lên chính các lần chạy đó bằng `python -m eval.run_eval --stability --rescore`, không gọi lại AI.
## 6. Giới hạn còn lại

- **"Có thể tin" không có nghĩa là đúng**: phân loại dựa trên quy tắc về nguồn, kỳ đo và thị trường. Số do chính hãng dữ liệu công bố vẫn là ước tính của hãng đó.
- **Các trường do AI điền chỉ được kiểm một phần**: code kiểm câu trích và con số, nhưng thị trường, kỳ đo, và đơn vị lấy từ tiêu đề bảng vẫn do AI điền.
- **Số trong biểu đồ** (TC6): hệ thống chỉ tới đúng chỗ để người dùng tự đọc, chưa tự đọc được.
- **Kết luận và tóm tắt do AI viết** có thể khác nhau giữa các lần chạy (xem mục 5).
- **Nguồn miễn phí phần lớn là bài dẫn lại**: hầu hết số liệu mang lưu ý "chưa đối chiếu bản gốc", vì báo cáo gốc của hãng dữ liệu thường phải trả phí. Người dùng có thể tải báo cáo đã mua lên.
- **Khối quyết định nhanh dựa trên lý do AI trích**: code chọn bằng chứng từ các nhóm số mà lý do chính dẫn, nên nếu AI bỏ sót một số quan trọng trong lý do thì khối cũng không có số đó (vẫn xem được ở báo cáo chi tiết).
- **Bộ kiểm thử thật mới có 9 tình huống**: chưa đủ để đo tỷ lệ sai của mục "có thể tin" hay của câu nên làm gì tiếp.

## 7. Bộ kiểm thử Mission 3

| Yêu cầu của đề | Ở đâu |
|---|---|
| Chạy lại test quan trọng của M2 để kiểm regression | 32 test offline của M2 giữ nguyên; `checks` của TC1 đến TC6 giữ nguyên và chạy lại trên bản M3 |
| Test cho Change Request (A4: hỗ trợ quyết định) | `tests/test_cr.py` (7 test: có câu trả lời, nguồn mâu thuẫn, thiếu dữ liệu, câu hỏi nên hay không nên kèm hành động cụ thể, bằng chứng tối đa 3 dòng, không số chưa chắc chắn nào bị gắn nhãn tin được, nội dung chữ từ nguồn được escape); `tests/test_app.py` (khối hiển thị đầu kết quả và trong kết quả mẫu, escape chữ từ nguồn trong khối); TC9 chạy thật đạt 3/3 lần; điều kiện `checks_cr` trên TC1, TC2, TC4, TC5, TC8, TC9 (11/11) |
| Edge case / tình huống khó | TC8 (số dự báo trong bài cũ), TC7 (câu hỏi tiếp cụt ngủn cần bối cảnh), TC2 (ba nguồn mâu thuẫn), TC6 (biểu đồ); test offline: nhãn ghép với số, ô "N-6.51", số không ghi đơn vị |
| Regression test cho chức năng cũ | `checks` M2 của TC1 đến TC6; test offline `test_numbers_from_the_question_are_allowed...` (lỗi TC3), `test_decimal_with_leading_zero...` (lỗi 0.817), cùng 32 test M2 |

## 8. Ba câu hỏi bắt buộc

**Câu 1. Sau khi nhận yêu cầu mới, bạn đã ưu tiên thay đổi điều gì và chủ động chưa làm điều gì? Vì sao?**

Em nhận hai yêu cầu: yêu cầu chung (cho biết điều gì có thể tin, điều gì chưa chắc chắn, nên tìm tiếp ở đâu) và Change Request A4 (người dùng không đọc báo cáo dài, muốn biết nên làm gì tiếp và quyết định đó dựa trên bằng chứng nào). Bản M2 gộp mọi số liệu dưới một mức tin cậy chung và bắt người dùng đọc hết báo cáo, nên em làm theo thứ tự:
1. Khối "Quyết định nhanh" ở đầu trang (Change Request A4): kết luận, mức tin cậy, nên làm gì tiếp (một câu hành động và bước tiếp theo bấm được), dựa trên bằng chứng nào (tối đa 3 dòng, mỗi dòng mở được đúng câu trích của từng hãng). Bằng chứng do code chọn từ những gì đã kiểm; câu hành động cụ thể của AI chỉ hiện khi code để kết luận chắc chắn đứng.
2. Chia bằng chứng thành ba phần do code xếp theo quy tắc: có thể tin; chưa chắc chắn, kèm lý do (mâu thuẫn, chỉ có bài dẫn lại từ nguồn hạng C, số cũ, số dự báo khi kỳ đo chưa kết thúc); nên tìm hiểu tiếp ở đâu, kèm bước bấm được.
3. Cho hỏi tiếp mà vẫn giữ bối cảnh: câu hỏi tiếp được viết lại thành câu hỏi đầy đủ, giữ các nhận định đã kiểm và các nhận định người dùng đã loại.
4. Kiểm chứng một cú nhấp tới đúng câu trích hoặc đúng trang PDF.
5. Sửa các lỗi M2 đã ghi lại.

Em chủ động chưa làm năm việc:
- Không cho AI chấm độ tin cậy hay chọn bằng chứng cho khối quyết định, vì kết quả không lặp lại được và không giải thích được.
- Không bỏ báo cáo chi tiết: Change Request cần bản ngắn, nhưng người muốn kiểm vẫn phải xem được toàn bộ số liệu và câu trích, nên báo cáo nằm ngay dưới khối quyết định.
- Không hạ chuẩn kiểm câu trích cho số trong biểu đồ. Trong lúc chạy, AI từng ghép +37,6% với Match Swap, trong khi đúng là Battle Royale; nới chuẩn thì số ghép sai sẽ lọt.
- Chưa dùng mô hình đọc ảnh cho biểu đồ, vì code chưa kiểm được kết quả và gói miễn phí giới hạn số lượt gọi.
- Giữ nguyên các ngưỡng và cách chấm Cao / Trung bình / Thấp của M2, chỉ thêm cờ cảnh báo mới, để kết quả hai phiên bản so sánh được với nhau.

**Câu 2. Thay đổi nào tạo ra khác biệt lớn nhất giữa sản phẩm Mission 2 và Mission 3? Bạn dùng bằng chứng nào để kết luận phiên bản mới tốt hơn?**

Khác biệt lớn nhất là người dùng không còn phải đọc cả báo cáo: đầu trang cho biết nên làm gì tiếp và dựa trên bằng chứng nào; ngay dưới là ba phần có thể tin / chưa chắc chắn / tìm hiểu tiếp do code xếp, và có thể hỏi tiếp từ chính các bước đó. Em áp cùng một bộ điều kiện chấm lên kết quả chạy thật của hai phiên bản:
- Điều kiện cũ của M2 vẫn đạt (18/19 ở M2, 21/22 ở M3), nghĩa là không có regression.
- Điều kiện mới của M3: M2 đạt 3/14, M3 đạt 23/24.
- Điều kiện của Change Request A4: M2 đạt 0/6, M3 đạt 11/11.

Em chạy lại cả bộ kiểm thử 3 lần: 8/9 case đạt đủ cả 3 lần; chỉ TC6 (số trong biểu đồ) không đạt, đúng như dự đoán từ M2. Bằng chứng cụ thể:
- TC9 (Change Request, "Nên ưu tiên MOBA hay 4X?"): cả 3 lần, đầu trang có câu nên làm gì tiếp và 3 bằng chứng có link câu trích (625 triệu USD, MOBA +20,1%, 4X +17,6%), ví dụ "Ưu tiên phát hành game MOBA; cần đối chiếu thêm báo cáo gốc của Sensor Tower trước khi chốt đầu tư".
- TC2: cả 3 lần, Niko 5,37 / Statista 5,89 / Newzoo 6,51 tỷ USD được gom thành một mâu thuẫn lệch 21%, không số nào vào phần có thể tin; khối quyết định nói "chưa nên dùng các con số này làm căn cứ chính" và chỉ bước so sánh cách đo của các hãng.
- TC8: số 5,47 tỷ USD cho năm 2025 trong bài đăng tháng 9/2025 được nhận ra là số dự báo.
- TC7: câu "Còn riêng Việt Nam thì sao?" giữ đủ bối cảnh và tìm ra hai con số lệch nhau 78%.
- TC1: kết luận đổi từ "Cần thêm dữ liệu" sang "Đã có câu trả lời", cả 3 lần.

Toàn bộ có 76 test offline (7 test riêng cho Change Request), 9 tình huống chạy thật và kết quả 3 lần chạy lưu trong repo.

**Câu 3. Nếu sản phẩm này được đưa cho người dùng thật vào ngày mai, rủi ro hoặc giới hạn lớn nhất còn lại là gì? Bạn sẽ ưu tiên xử lý nó như thế nào?**

Rủi ro lớn nhất là người dùng làm theo ngay câu "nên làm gì tiếp" và hiểu "có thể tin" là "đúng". Thực ra "có thể tin" chỉ có nghĩa là số đạt quy tắc về nguồn, kỳ đo và thị trường. Câu hành động cụ thể vẫn do AI viết (chỉ hiện khi kết luận đứng được), các trường như thị trường, kỳ đo hay đơn vị lấy từ tiêu đề bảng vẫn do AI điền, và nhãn kết luận còn dao động giữa các lần chạy; code hiện mới chặn một chiều: không đủ căn cứ có thể tin thì không được ghi kết luận chắc chắn. Em sẽ ưu tiên ba việc:
1. Mở rộng bộ kiểm thử lên khoảng 20 đến 30 câu hỏi có đáp án đã biết, để đo tỷ lệ "có thể tin nhưng sai", tỷ lệ câu nên làm gì tiếp sai, và tỷ lệ kết luận dao động giữa các lần chạy.
2. Để người dùng báo nhận định hoặc câu hành động sai ngay trên giao diện, rồi đưa các ca đó vào bộ kiểm thử.
3. Kiểm thêm bằng code những trường AI điền, ví dụ tìm tiêu đề cột trong nguồn để xác nhận đơn vị, và tính nhãn kết luận hoàn toàn bằng quy tắc từ ba phần thay vì để AI chọn.

Số trong biểu đồ để sau ba việc trên. Khi làm, kết quả đọc bằng mô hình nhìn ảnh mặc định chỉ được vào phần chưa chắc chắn.

## 9. Video trình bày cải tiến (4:50)

Video quay im lặng trên bản demo, chữ thuyết minh chèn khi dựng; đoạn chờ AI chạy được tua nhanh. Phần chạy TC2 trong video bật tìm nguồn trên web nên con số khác lần chạy trong bộ kiểm thử; chữ thuyết minh ghi đúng số hiện trên màn hình.

| Thời gian | Màn hình | Nội dung |
|---|---|---|
| 0:00–0:18 | Khung tiêu đề, `eval/results_m2/TC2.md` | Trước (M2): một mức tin cậy chung cho mọi số liệu; cả 6 case ra "Cần thêm dữ liệu" |
| 0:18–0:46 | `docs/mission-3.md` mục 1 đến 4 | Yêu cầu mới; quyết định làm gì và chủ động chưa làm gì; luồng mới |
| 0:46–1:02 | `docs/mission-3.md` mục 5 | Bằng chứng: điều kiện M3 từ 3/14 lên 23/24; 7/8 case đạt cả 3 lần (lúc quay, trước Change Request) |
| 1:02–1:34 | App: chạy TC2 có tìm nguồn trên web | Kết luận "Có số liệu nhưng chưa chắc chắn" |
| 1:34–1:48 | Hai cột | Chưa chắc chắn: Niko 5,5 / Statista 5,89 / Newzoo 6,51 / Yahoo Finance 14,8 tỷ USD lệch 169%; số 2024 trong bài đăng khi năm chưa hết bị gắn cờ dự báo |
| 1:48–2:18 | Nhận định, nút mở nguồn | Kiểm chứng một cú nhấp: bài gốc mở và cuộn tới câu trích; đoạn văn quanh câu trích được tô sáng |
| 2:18–3:16 | Nên tìm hiểu tiếp, ô Hỏi tiếp | "Còn riêng Việt Nam thì sao?": Statista 0,46 và Newzoo 0,817 tỷ USD lệch 78%; bấm "Tìm thêm" chạy luôn một bước |
| 3:16–3:35 | `eval/so-sanh-m2-m3.md` | Bằng chứng trên kết quả chạy thật: điều kiện M2 không giảm, điều kiện M3 từ 3/14 lên 23/24 |
| 3:35–3:53 | `docs/mission-3.md` mục 6 | Giới hạn: "có thể tin" chưa có nghĩa là đúng; số trong biểu đồ PDF chưa tự đọc được |
| 3:53–4:07 | Khung tiêu đề, kết quả mẫu TC9 | Change Request A4: Quyết định nhanh ở đầu trang, "Ưu tiên MOBA", dựa trên MOBA +20,1%, 4X +17,6% và 625 triệu USD của Sensor Tower |
| 4:07–4:22 | Bấm tên hãng, rồi cuộn xuống | Trang Sensor Tower mở và tô sáng đúng câu được trích; báo cáo chi tiết vẫn ở bên dưới |
| 4:22–4:45 | Nút "Làm bước này" | Chạy luôn bước tiếp theo; kết quả mới vẫn mở đầu bằng Quyết định nhanh và giữ 9 nhận định đã kiểm |
| 4:45–4:50 | Khung kết | Link app và repo |

Ở đoạn 3:35–3:53, trang GitHub được quay trước khi nhận Change Request nên còn dòng "Change Request chưa được giao"; tài liệu hiện tại đã cập nhật phần này (mục 2, 3, 5, 7).
