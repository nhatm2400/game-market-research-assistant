# Trợ lý nghiên cứu thị trường game (MVP, Mission 2)

Bản MVP cho bài test A của chương trình AI Talent (Gamota). Người dùng đặt một câu hỏi thị trường, hệ thống tìm và đọc nguồn rồi trả về một bản tóm tắt quyết định. Mỗi nhận định trong bản tóm tắt đi kèm câu trích nguyên văn, và code đã tìm thấy câu đó trong nguồn.

- Bản chạy thử: _(điền link Streamlit Cloud)_
- Video trình bày: _(điền link YouTube)_
- Kết quả kiểm thử: [eval/ket-qua-kiem-thu.md](eval/ket-qua-kiem-thu.md)

## Phần được chọn để chứng minh

Ở Mission 1, em cho rằng vấn đề lớn nhất của người làm nghiên cứu không phải là tìm thông tin mà là biết thông tin nào đủ chắc để dựa vào. MVP này chỉ làm phần lõi để kiểm tra giả thuyết đó:

> AI có thể đưa ra nhận định mà người dùng tự kiểm chứng được, nếu AI chỉ làm việc đọc và trích, còn việc kiểm câu trích, chấm hạng nguồn và tính mức tin cậy do code làm theo quy tắc công khai.

Nếu phần này chạy được, những phần còn lại (giao diện tốt hơn, nhiều nguồn dữ liệu hơn, theo dõi liên tục) chỉ là mở rộng. Nếu phần này không chạy được thì sản phẩm chỉ là một chatbot tóm tắt khác.

## Cách hoạt động

| Bước | Ai làm | Nội dung |
|---|---|---|
| 1. Lập kế hoạch | AI, người dùng duyệt | Tách câu hỏi thành 3 đến 4 tiêu chí và viết truy vấn tìm kiếm. Người dùng sửa được trước khi chạy |
| 2. Tìm và chọn nguồn | Code | Tìm bằng Tavily (hoặc DuckDuckGo nếu không có khóa). Nguồn hạng A, B được đọc trước; trang hạng D (trang SEO bán báo cáo) không được đọc |
| 3. Đọc nguồn | Code | Trang web đọc bằng trafilatura, PDF đọc bằng PyMuPDF (có ghi số trang). Người dùng có thể thêm link hoặc tải lên báo cáo đã mua |
| 4. Trích nhận định | AI | Mỗi nhận định có: chỉ số, giá trị, thị trường, kỳ đo, phạm vi đo, thể loại, câu trích nguyên văn, tên chương/bảng, hãng dữ liệu được dẫn |
| 5. Kiểm câu trích | Code | Câu trích phải có trong nguồn (chỉ bỏ qua khác biệt khoảng trắng, dấu câu, chữ hoa thường) và con số phải nằm trong câu trích. Không đạt thì loại và ghi lý do |
| 6. Chấm hạng và so sánh | Code | Hạng nguồn theo danh sách `data/source_tiers.yaml`, hạ hạng nếu cũ hoặc không rõ ngày. Truy về nguồn gốc ("according to Sensor Tower"). Gom các nhận định đo cùng một thứ, phân biệt mâu thuẫn thật với khác định nghĩa, gắn cảnh báo về kỳ đo và phạm vi địa lý |
| 7. Viết bản tóm tắt | AI, code kiểm lại | AI chỉ viết từ nhận định đã kiểm và phải ghi mã nhận định. Code bỏ mọi lý do không có mã hợp lệ hoặc có con số không nằm trong nhận định được trích. Mức tin cậy do code tính |

Sau bước 7 người dùng mở từng nhận định để xem câu trích và link, đánh dấu nhận định sai và cho viết lại bản tóm tắt.

### Quy tắc mức tin cậy (code tính, AI không tự chấm)

- Cao: ít nhất 2 nguồn gốc độc lập hạng A hoặc B, đăng trong 12 tháng, khớp nhau.
- Trung bình: chỉ một nguồn gốc hạng A hoặc B, hoặc nhiều bài viết cùng dẫn một nguồn gốc.
- Thấp: chỉ có nguồn hạng C, D, hoặc các nguồn gốc lệch nhau quá 5%.
- Có cảnh báo về kỳ đo (ngoài khung thời gian, số theo quý khi hỏi 12 tháng, số dự báo) hoặc phạm vi địa lý thì hạ một mức.
- Chưa đủ dữ liệu: không có nhận định nào qua được bước kiểm câu trích. Khi đó hệ thống không gọi AI viết tóm tắt.

## Chạy trên máy (Windows)

Cần Python 3.10 trở lên.

```bat
cd E:\FPTU\PRJ\Appota
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Mở file `.env`, dán khóa Gemini (lấy miễn phí ở https://aistudio.google.com/apikey) và khóa Tavily nếu có (https://tavily.com). Sau đó:

```bat
streamlit run app.py
```

Trên macOS hoặc Linux thay `.venv\Scripts\activate` bằng `source .venv/bin/activate` và `copy` bằng `cp`.

## Đưa lên Streamlit Community Cloud

1. Đẩy repo lên GitHub (public). File `.env` đã nằm trong `.gitignore`.
2. Vào https://share.streamlit.io, chọn New app, chọn repo, nhánh `main`, file `app.py`.
3. Trong Advanced settings, mục Secrets, dán:
   ```toml
   GEMINI_API_KEY = "..."
   TAVILY_API_KEY = "..."
   ```
4. Deploy. Dữ liệu lịch sử chạy trên Cloud sẽ mất khi ứng dụng khởi động lại; đây là bản demo nên em chấp nhận.

## Kiểm thử

Có hai lớp:

```bat
python -m pytest -q
python -m eval.run_eval
```

- `pytest` chạy 21 bài test không cần mạng và không cần khóa: kiểm câu trích (câu bịa, câu bị diễn đạt lại, số bị đổi), đọc giá trị và kỳ đo, hạng nguồn, truy nguồn gốc, phân biệt mâu thuẫn với khác định nghĩa, bẫy bảng Việt Nam bị ghi là Đông Nam Á, và bộ kiểm bản tóm tắt. Có một bài chạy toàn bộ luồng với một LLM giả cố tình trả về một nhận định bịa.
- `eval.run_eval` chạy 6 tình huống thật trong `eval/cases.yaml` (cần mạng và khóa Gemini), tự chấm theo các điều kiện ghi trong file và sinh bảng `eval/ket-qua-kiem-thu.md` theo mẫu Kỳ vọng, Kết quả thực tế, Đạt/Chưa đạt, Điều học được. Kết quả chi tiết từng lần chạy nằm trong `eval/results/`.

## Hạn chế đã biết

- Kiểm câu trích chỉ chứng minh câu trích có thật trong nguồn. Nó không chứng minh AI hiểu đúng câu đó; các trường như thị trường, kỳ đo vẫn do AI điền và chỉ được kiểm một phần bằng cảnh báo (tên chương, kỳ đo so với câu hỏi).
- Số liệu nằm trong biểu đồ của PDF: khi đọc ra chữ, nhãn và số bị tách khỏi nhau. Câu trích vẫn "có thật" nhưng AI có thể ghép nhầm nhãn với số. Xem tình huống TC6.
- Nhận định đúng nhưng AI chép lệch vài chữ sẽ bị loại oan. Em chấp nhận mất vài nhận định đúng để không lọt nhận định bịa.
- Truy nguồn gốc dựa trên tên hãng dữ liệu xuất hiện gần câu trích, nên sẽ sót nếu bài viết không nhắc tên hãng.
- Hạng nguồn dựa trên danh sách tên miền do người dùng quản lý; tên miền lạ mặc định hạng C.
- Nhiều trang chặn tải tự động hoặc nằm sau tường phí. Khi đó hệ thống ghi lỗi ở tab Nguồn; người dùng có thể tải file lên.
- Gói miễn phí của Gemini giới hạn số lượt gọi mỗi phút, nên một câu hỏi mất từ một đến vài phút.
- Chưa có: đăng nhập, nguồn tiếng Trung, đọc biểu đồ bằng mô hình thị giác, theo dõi theo thời gian.

## Cấu trúc thư mục

```
app.py                  giao diện Streamlit
core/pipeline.py        ghép các bước
core/extract.py         prompt lập kế hoạch và trích nhận định (AI)
core/verify.py          kiểm câu trích (code)
core/sources.py         hạng nguồn, truy nguồn gốc (code)
core/periods.py         đọc kỳ đo, so với khung thời gian câu hỏi (code)
core/analyze.py         gom nhóm, mâu thuẫn, mức tin cậy (code)
core/brief.py           viết bản tóm tắt (AI) và kiểm lại (code)
data/source_tiers.yaml  danh sách hạng nguồn, người dùng tự sửa
eval/                   bộ kiểm thử chạy thật và kết quả
tests/                  bài test không cần mạng
```

## Ghi chú về việc dùng AI

Code được viết cùng Claude (Anthropic), dựa trên thiết kế em nộp ở Mission 1. Em đọc lại code, chạy kiểm thử trên máy và ghi kết quả trong thư mục `eval/`.
#   g a m e - m a r k e t - r e s e a r c h - a s s i s t a n t  
 