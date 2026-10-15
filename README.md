# Game Market Research Assistant

Công cụ hỗ trợ nghiên cứu thị trường game. Người dùng đặt một câu hỏi, hệ thống tìm và đọc nguồn trên web rồi trả về một bản tóm tắt quyết định ngắn. Mỗi nhận định trong bản tóm tắt đi kèm câu trích nguyên văn, và code đã tìm thấy câu đó trong nguồn.

## Vấn đề

Số liệu thị trường game nằm rải rác, đến từ nhiều hãng với cách đo khác nhau, và thường bị các bài báo dẫn lại. Ví dụ, cùng thị trường game Đông Nam Á năm 2024 nhưng hai nguồn ghi 5,37 tỷ USD (Niko Partners) và 5,89 tỷ USD (Statista), còn Sensor Tower công bố 625 triệu USD cho riêng doanh thu mua trong ứng dụng của game mobile trong quý 1/2025. Hai con số đầu thật sự lệch nhau, con số thứ ba chỉ khác phạm vi và kỳ đo. Người làm nghiên cứu mất nhiều thời gian nhất ở việc phân biệt các trường hợp đó và truy xem số liệu của ai, đo gì, năm nào.

Chatbot trả lời nhanh nhưng hay gộp các con số khác bản chất vào một đoạn trôi chảy. Dự án này làm theo hướng ngược lại: AI chỉ đọc và trích, còn việc kiểm chứng do code làm theo quy tắc công khai.

## Cách hoạt động

| Bước | Ai làm | Nội dung |
|---|---|---|
| 1. Lập kế hoạch | AI, người dùng duyệt | Tách câu hỏi thành 3 đến 4 tiêu chí và viết truy vấn tìm kiếm. Người dùng sửa được trước khi chạy |
| 2. Tìm và chọn nguồn | Code | Tìm bằng Tavily (hoặc DuckDuckGo nếu không có khóa). Nguồn hạng A, B được đọc trước; trang hạng D (trang SEO bán báo cáo) không được đọc |
| 3. Đọc nguồn | Code | Trang web đọc bằng trafilatura, PDF đọc bằng PyMuPDF (có ghi số trang). Người dùng có thể thêm link hoặc tải lên báo cáo riêng |
| 4. Trích nhận định | AI | Mỗi nhận định có: chỉ số, giá trị, thị trường, kỳ đo, phạm vi đo, thể loại, câu trích nguyên văn, tên chương hoặc bảng, hãng dữ liệu được dẫn |
| 5. Kiểm câu trích | Code | Câu trích phải có trong nguồn (chỉ bỏ qua khác biệt khoảng trắng, dấu câu, chữ hoa thường) và con số phải nằm trong câu trích. Không đạt thì loại và ghi lý do |
| 6. Chấm hạng và so sánh | Code | Hạng nguồn theo danh sách `data/source_tiers.yaml`, hạ hạng nếu cũ hoặc không rõ ngày. Truy về nguồn gốc ("according to Sensor Tower"). Gom các nhận định đo cùng một thứ, phân biệt mâu thuẫn thật với khác định nghĩa, gắn cảnh báo về kỳ đo và phạm vi địa lý |
| 7. Viết bản tóm tắt | AI, code kiểm lại | AI chỉ viết từ nhận định đã kiểm và phải ghi mã nhận định. Code bỏ mọi lý do không có mã hợp lệ hoặc có con số không nằm trong nhận định được trích. Mức tin cậy do code tính |

Sau bước 7, người dùng mở từng nhận định để xem câu trích và link, đánh dấu nhận định sai và cho viết lại bản tóm tắt.

### Hạng nguồn

| Hạng | Loại nguồn | Ví dụ |
|---|---|---|
| A | Dữ liệu gốc | Sensor Tower, Newzoo, Niko Partners, bảng xếp hạng store |
| B | Thứ cấp, có uy tín | Báo chuyên ngành, trang tổng hợp báo cáo |
| C | Ý kiến, blog, cộng đồng | Blog, diễn đàn, mạng xã hội, tên miền chưa có trong danh sách |
| D | Không dùng làm bằng chứng | Trang SEO bán báo cáo, không rõ tác giả |

Hạng được hạ một bậc khi nguồn đăng quá 24 tháng hoặc không rõ ngày. Danh sách nằm trong `data/source_tiers.yaml` và có thể tự chỉnh.

### Quy tắc mức tin cậy

Mức tin cậy do code tính, AI không tự chấm.

- Cao: ít nhất 2 nguồn gốc độc lập hạng A hoặc B, đăng trong 12 tháng, khớp nhau.
- Trung bình: chỉ một nguồn gốc hạng A hoặc B, hoặc nhiều bài viết cùng dẫn một nguồn gốc.
- Thấp: chỉ có nguồn hạng C, D, hoặc các nguồn gốc độc lập lệch nhau quá 5%.
- Có cảnh báo về kỳ đo (ngoài khung thời gian của câu hỏi, số theo quý khi hỏi 12 tháng, số dự báo) hoặc phạm vi địa lý thì hạ một mức.
- Chưa đủ dữ liệu: không có nhận định nào qua được bước kiểm câu trích. Khi đó hệ thống không gọi AI viết tóm tắt.

## Cài đặt và chạy

Cần Python 3.10 trở lên.

```bat
git clone https://github.com/nhatm2400/game-market-research-assistant.git
cd game-market-research-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Mở file `.env`, điền khóa Gemini (lấy miễn phí ở https://aistudio.google.com/apikey) và khóa Tavily nếu có (https://tavily.com). Sau đó:

```bat
streamlit run app.py
```

Trên macOS hoặc Linux, thay `.venv\Scripts\activate` bằng `source .venv/bin/activate` và `copy` bằng `cp`.

| Biến môi trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| `GEMINI_API_KEY` | Có | Khóa Gemini API |
| `TAVILY_API_KEY` | Không | Có thì tìm bằng Tavily, không có thì dùng DuckDuckGo |
| `LLM_MODEL` | Không | Mặc định `gemini-2.5-flash`; đổi sang `gemini-2.5-flash-lite` nếu bị giới hạn lượt gọi |
| `LLM_FALLBACK_MODELS` | Không | Các mô hình dự phòng, cách nhau bằng dấu phẩy. Khi mô hình chính quá tải, hệ thống tự chuyển sang mô hình tiếp theo. Mặc định `gemini-2.5-flash,gemini-2.5-flash-lite` |
| `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_BASE_URL` | Không | Dùng API tương thích OpenAI (ví dụ Groq) thay cho Gemini; cần cài thêm gói `openai` |

Sau khi sửa code hoặc file `.env`, cần dừng Streamlit (Ctrl+C) và chạy lại, vì Streamlit giữ mã cũ trong bộ nhớ.

## Triển khai lên Streamlit Community Cloud

1. Đẩy repo lên GitHub. File `.env` đã nằm trong `.gitignore`.
2. Vào https://share.streamlit.io, chọn New app, chọn repo, nhánh `main`, file `app.py`.
3. Trong Advanced settings, mục Secrets, dán:
   ```toml
   GEMINI_API_KEY = "..."
   TAVILY_API_KEY = "..."
   ```
4. Deploy. Lịch sử các lần chạy lưu trong SQLite nên sẽ mất khi ứng dụng khởi động lại.

## Kiểm thử

```bat
python -m pytest -q
python -m eval.run_eval
```

- `pytest` chạy 32 bài test không cần mạng và không cần khóa API: kiểm câu trích (câu bịa, câu bị diễn đạt lại, số bị đổi), đọc giá trị và kỳ đo, hạng nguồn, truy nguồn gốc, phân biệt mâu thuẫn với khác định nghĩa, bẫy bảng của Việt Nam bị ghi là Đông Nam Á, bộ kiểm bản tóm tắt, và xử lý lỗi (thử lại khi mô hình quá tải, chuyển sang mô hình dự phòng, tải trang bị timeout, lỗi khi viết tóm tắt). Có một bài chạy toàn bộ luồng với một LLM giả cố tình trả về một nhận định bịa.
- `eval.run_eval` chạy 6 tình huống thật trong `eval/cases.yaml` (cần mạng và khóa Gemini), tự chấm theo các điều kiện ghi trong file và sinh bảng `eval/ket-qua-kiem-thu.md` gồm kỳ vọng, kết quả thực tế, đạt hoặc chưa đạt, điều học được. Kết quả chi tiết từng lần chạy nằm trong `eval/results/`.

## Hạn chế đã biết

- Kiểm câu trích chỉ chứng minh câu trích có thật trong nguồn, không chứng minh AI hiểu đúng câu đó. Các trường như thị trường, kỳ đo vẫn do AI điền và chỉ được kiểm một phần bằng cảnh báo (tên chương, kỳ đo so với câu hỏi).
- Số liệu nằm trong biểu đồ của PDF: khi đọc ra chữ, nhãn và số bị tách khỏi nhau. Câu trích vẫn có thật nhưng AI có thể ghép nhầm nhãn với số (tình huống TC6).
- Nhận định đúng nhưng AI chép lệch vài chữ sẽ bị loại oan. Đây là đánh đổi có chủ ý để không lọt nhận định bịa.
- Truy nguồn gốc dựa trên tên hãng dữ liệu xuất hiện gần câu trích, nên sẽ sót nếu bài viết không nhắc tên hãng.
- Hạng nguồn dựa trên danh sách tên miền; tên miền chưa có trong danh sách mặc định là hạng C.
- Nhiều trang chặn tải tự động hoặc nằm sau tường phí. Khi đó hệ thống ghi lỗi ở tab Nguồn, và người dùng có thể tải file lên.
- Gói miễn phí của Gemini giới hạn số lượt gọi mỗi phút và mỗi ngày theo từng mô hình (xem https://aistudio.google.com/rate-limit). Một lần chạy dùng 3 lượt gọi: lập kế hoạch, trích nhận định từ tất cả nguồn trong một lần gọi, và viết tóm tắt. Hết hạn mức của một mô hình thì hệ thống tự chuyển sang mô hình trong `LLM_FALLBACK_MODELS`.
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
core/fetch.py           tải trang web và đọc PDF
core/search.py          tìm kiếm (Tavily hoặc DuckDuckGo)
core/store.py           lưu lịch sử chạy vào SQLite
core/report.py          xuất bản tóm tắt dạng Markdown
data/source_tiers.yaml  danh sách hạng nguồn và hãng dữ liệu
eval/                   tình huống kiểm thử chạy thật và kết quả
tests/                  bài test không cần mạng
```
