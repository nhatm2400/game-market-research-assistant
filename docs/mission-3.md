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

Sau khi nhận yêu cầu mới bao gồm Change Request A4 về hỗ trợ quyết định (người dùng không muốn đọc báo cáo dài, muốn biết nên làm gì tiếp theo và quyết định đó dựa trên bằng chứng nào), em nhận thấy bản tóm tắt trước đó vẫn bắt người dùng phải đọc hết các lý do và hai cột số liệu mới nắm được hướng đi. Vì vậy em đã ưu tiên thực hiện theo thứ tự:
1. Thêm khối "Quyết định nhanh" ở ngay đầu kết quả trong ứng dụng và ở đầu bản markdown tải về. Khối gồm hai phần chính: câu nên làm gì tiếp (kèm nút bấm chạy luôn bước tiếp theo nếu có) và dựa trên bằng chứng nào (tối đa ba dòng, mỗi dòng gồm con số, nguồn gốc, hạng nguồn, trạng thái có thể tin hay chưa chắc chắn kèm lý do ngắn, và liên kết mở đúng câu trích của từng hãng). Khối hoàn toàn do code tự chọn từ các phần đã kiểm, không gọi thêm ai; câu hành động cụ thể chỉ hiện khi code để kết luận chắc chắn đứng vững.
2. Thiết lập quy tắc nội dung chặt chẽ: kết luận "Đã có câu trả lời" hoặc "Nên ưu tiên" thì hành động là dùng kết luận, bằng chứng lấy từ mục có thể tin; "Có số liệu nhưng chưa chắc chắn" thì hành động là bước tìm tiếp đầu tiên và bằng chứng gồm cả số chưa chắc chắn kèm lý do rõ ràng; "Cần thêm dữ liệu" hoặc "Chưa nên" thì hành động là bước thu thập dữ liệu đầu tiên, nói thẳng là chưa đủ cơ sở quyết định và không bịa bằng chứng; tuyệt đối không gắn nhãn có thể tin cho con số chưa chắc chắn.
3. Duy trì trọn vẹn các tính năng cốt lõi của Mission 3: ba phần có thể tin, chưa chắc chắn và nên tìm hiểu tiếp do code xếp; hỏi tiếp giữ nguyên bối cảnh; kiểm chứng một cú nhấp mở thẳng câu trích; nhận diện nguồn cũ và số dự báo.

Em chủ động chưa làm các việc sau:
- Không để ai chọn bằng chứng cho khối quyết định và không gọi thêm ai, vì code tự chọn từ nhận định đã kiểm giúp kết quả hoàn toàn ổn định, không tốn thêm lượt gọi và tránh bịa số.
- Không bỏ báo cáo chi tiết bên dưới, vì bản tóm tắt nhanh phục vụ quyết định tức thì, nhưng khi cần thẩm định sâu người dùng vẫn phải có toàn bộ số liệu và nguồn gốc đối chiếu.
- Không cho ai tự chấm mức độ tin cậy hay tự xếp mục có thể tin, để tránh việc cùng bằng chứng lại ra các kết luận khác nhau giữa các lần chạy.
- Không hạ chuẩn kiểm câu trích cho số liệu trong biểu đồ để tránh lọt các số bị ghép nhầm nhãn.
- Không thay đổi các ngưỡng và cách chấm của Mission 2 nhằm bảo đảm không bị regression và kết quả giữa hai phiên bản so sánh được với nhau.

**Câu 2. Thay đổi nào tạo ra khác biệt lớn nhất giữa sản phẩm Mission 2 và Mission 3? Bạn dùng bằng chứng nào để kết luận phiên bản mới tốt hơn?**

Khác biệt lớn nhất là người dùng không còn phải tự đọc toàn bộ báo cáo dài để tìm việc cần làm: ngay đầu trang có khối quyết định nhanh cho biết nên làm gì tiếp và dựa trên bằng chứng nào với tối đa ba dòng mở được câu trích; ngay bên dưới là ba phần có thể tin, chưa chắc chắn và bước tìm tiếp do code xếp, cho phép hỏi tiếp mà không mất bối cảnh nghiên cứu.

Em dùng các bằng chứng cụ thể sau để kết luận phiên bản mới tốt hơn:
- Bộ kiểm thử tự động offline tăng lên 76 bài kiểm thử đều vượt qua (trong đó có 7 bài riêng cho Change Request A4 và 3 bài kiểm thử giao diện streamlit apptest), kiểm tra toàn diện các trường hợp có câu trả lời, nguồn mâu thuẫn, thiếu dữ liệu, câu hỏi nên hay không nên, bằng chứng tối đa ba dòng, không số chưa chắc chắn nào bị gắn nhãn tin được, và nội dung chữ từ nguồn được escape an toàn.
- Áp cùng bộ điều kiện lên kết quả chạy thật của hai phiên bản: các điều kiện cũ của Mission 2 giữ nguyên đạt 21 trên 22 điều kiện (bản Mission 2 chỉ đạt 18 trên 19), chứng minh không bị regression. Các điều kiện mới của Mission 3 đạt 23 trên 24 (Mission 2 chỉ đạt 3 trên 14). Toàn bộ 11 trên 11 điều kiện của Change Request A4 đều đạt trên các ca áp dụng.
- Tình huống TC9 chạy thật kiểm tra đúng câu hỏi ra quyết định nên ưu tiên moba hay chiến thuật 4x: hệ thống trả về kết luận nên ưu tiên với độ tin cậy trung bình, khối quyết định nhanh đưa ra câu hành động cụ thể "ưu tiên moba, trước khi chốt kiểm tra thêm số liệu gốc từ sensor tower" cùng ba bằng chứng đã kiểm có liên kết câu trích (625 triệu usd của sensor tower hạng a, moba tăng 20,1 phần trăm và 4x tăng 17,6 phần trăm từ gamedev reports dẫn sensor tower hạng b), đạt toàn bộ các điều kiện kiểm tra.
- Bộ kiểm thử thật qua ba lần chạy độc lập đạt độ ổn định cao: 8 trên 9 tình huống đạt tuyệt đối cả ba lần; chỉ riêng tình huống TC6 (số nằm trong biểu đồ pdf) không đạt do hạn chế của việc trích xuất văn bản biểu đồ, đúng như dự đoán từ Mission 2.

**Câu 3. Nếu sản phẩm này được đưa cho người dùng thật vào ngày mai, rủi ro hoặc giới hạn lớn nhất còn lại là gì? Bạn sẽ ưu tiên xử lý nó như thế nào?**

Rủi ro lớn nhất là người dùng có thể tin tưởng tuyệt đối vào câu hành động và ngộ nhận trạng thái có thể tin là số liệu đúng hoàn toàn trong thực tế, trong khi đó chỉ là số liệu đạt tiêu chuẩn về nguồn gốc, kỳ đo và thị trường theo quy tắc định sẵn. Thêm vào đó, câu hành động cụ thể và các trường trích xuất như thị trường, kỳ đo vẫn do ai điền, nhãn kết luận còn có thể dao động nhẹ giữa các lần chạy do tính chất sinh văn bản của mô hình ngôn ngữ.

Em sẽ ưu tiên xử lý theo ba bước:
1. Mở rộng bộ kiểm thử lên từ 20 đến 30 câu hỏi thực tế đa dạng hơn để đo lường độ chính xác của câu nên làm gì tiếp và theo dõi độ biến thiên kết luận giữa các lần chạy.
2. Bổ sung nút phản hồi nhanh trên giao diện để người dùng báo cáo khi phát hiện nhận định hoặc hành động gợi ý chưa chuẩn, từ đó thu thập dữ liệu làm ca kiểm thử hồi quy.
3. Tăng cường kiểm tra bằng code cho các trường ai điền (như đối chiếu tiêu đề cột để xác thực đơn vị) và chuyển hẳn việc chọn nhãn kết luận sang quy tắc code dựa trên tỷ lệ nhận định tin cậy thay vì để ai chọn.

Vấn đề đọc biểu đồ phức tạp sẽ giải quyết sau ba việc trên. Khi triển khai mô hình thị giác cho biểu đồ, kết quả đọc được mặc định chỉ xếp vào mục chưa chắc chắn để người dùng kiểm tra lại.

## 9. Kịch bản video (dưới 5 phút)

Quay im lặng, chèn chữ khi dựng. Trước khi quay: mở app, bỏ chọn "Tìm nguồn trên web", để sẵn ba link của TC2.

| Thời gian | Màn hình | Chữ thuyết minh |
|---|---|---|
| 0:00–0:15 | Khung tiêu đề | Mission 3: điều gì có thể tin, điều gì chưa chắc chắn, nên tìm hiểu tiếp ở đâu |
| 0:15–0:45 | GitHub: `eval/results_m2/TC2.md` | Trước (M2): mọi số liệu dưới một mức tin cậy; cả 6 case đều ra "Cần thêm dữ liệu" |
| 0:45–1:10 | `docs/mission-3.md` mục 3 | Quyết định: ba phần do code xếp, hỏi tiếp giữ bối cảnh, kiểm chứng một cú nhấp. Không cho AI chấm tin cậy, không hạ chuẩn kiểm câu trích |
| 1:10–1:40 | App: chạy câu hỏi TC2 (tua nhanh lúc chờ) | Sau (M3): chạy cùng câu hỏi TC2 |
| 1:40–2:10 | Khối Quyết định nhanh (Change Request A4) | Quyết định nhanh: nên làm gì tiếp kèm nút làm luôn, dựa trên tối đa 3 bằng chứng có link mở đúng câu trích; xem kết quả mẫu TC9 và TC2 |
| 2:10–2:40 | Bản tóm tắt, hai cột, mục ngoài phạm vi | Có thể tin / Chưa chắc chắn: Niko 5,37, Statista 5,89, Newzoo 6,51 tỷ USD lệch nhau 21% nên chưa chắc chắn; tăng trưởng 5,2% ở có thể tin |
| 2:40–3:05 | Bấm một nhận định, "Mở nguồn tại câu trích" | Kiểm chứng một cú nhấp: trang mở đúng câu trích, câu được tô sáng |
| 3:05–3:45 | Ô "Hỏi tiếp": gõ "Còn riêng Việt Nam thì sao?" | Hỏi tiếp giữ bối cảnh: hiểu thành Việt Nam năm 2024, giữ nhận định cũ, tìm ra 0,817 và 0,46 tỷ USD lệch 78% |
| 3:45–4:20 | GitHub: `eval/so-sanh-m2-m3.md`, terminal chạy pytest | Bằng chứng: điều kiện M3 từ 3/14 lên 23/24, điều kiện M2 không giảm, 8/9 case đạt cả 3 lần chạy, 76 test qua |
| 4:20–4:45 | `docs/mission-3.md` mục 6 và khung kết | Giới hạn: "có thể tin" không có nghĩa là đúng; số trong biểu đồ chưa tự đọc được. Link app và repo |
