# Game Market Research Assistant

Công cụ hỗ trợ nghiên cứu thị trường game. Người dùng đặt một câu hỏi, hệ thống tìm và đọc nguồn trên web rồi trả về một bản tóm tắt quyết định ngắn. Mỗi nhận định trong bản tóm tắt đi kèm câu trích nguyên văn, và code đã tìm thấy câu đó trong nguồn.

## Vấn đề

Số liệu thị trường game nằm rải rác, đến từ nhiều hãng với cách đo khác nhau, và thường bị các bài báo dẫn lại. Ví dụ, cùng thị trường game Đông Nam Á năm 2024 nhưng hai nguồn ghi 5,37 tỷ USD (Niko Partners) và 5,89 tỷ USD (Statista), còn Sensor Tower công bố 625 triệu USD cho riêng doanh thu mua trong ứng dụng của game mobile trong quý 1/2025. Hai con số đầu thật sự lệch nhau, con số thứ ba chỉ khác phạm vi và kỳ đo. Người làm nghiên cứu mất nhiều thời gian nhất ở việc phân biệt các trường hợp đó và truy xem số liệu của ai, đo gì, năm nào.

Chatbot trả lời nhanh nhưng hay gộp các con số khác bản chất vào một đoạn trôi chảy. Dự án này làm theo hướng ngược lại: AI chỉ đọc và trích, còn việc kiểm chứng do code làm theo quy tắc công khai.

## Mission 3: điều gì có thể tin, điều gì chưa chắc chắn, nên tìm hiểu tiếp ở đâu

Cùng một câu hỏi thường có nhiều nguồn khác nhau về thời điểm, độ tin cậy, thậm chí kết luận trái ngược. Phiên bản Mission 3 trả lời theo ba phần, do code xếp theo quy tắc cố định chứ không để AI tự chấm:

| Phần | Điều kiện (code kiểm) |
|---|---|
| Có thể tin | Mức tin cậy Cao hoặc Trung bình theo quy tắc M2, không mâu thuẫn, kỳ đo và thị trường khớp câu hỏi, không phải số dự báo. Số dẫn lại qua nguồn hạng A/B vẫn có thể tin nhưng kèm lưu ý nên đối chiếu bản gốc |
| Chưa chắc chắn | Có câu trích đã kiểm nhưng còn lý do cụ thể: các nguồn lệch hoặc trái chiều, chỉ có nguồn hạng C/D, số theo quý khi hỏi 12 tháng, số cũ hơn khung câu hỏi, số dự báo hoặc ước tính khi kỳ đo chưa kết thúc lúc đăng bài |
| Nên tìm hiểu tiếp ở đâu | Mỗi điểm chưa chắc chắn có một bước cụ thể: truy vấn tìm kiếm soạn sẵn, câu hỏi tiếp, hoặc link mở thẳng tới trang biểu đồ chưa đọc được. Bấm "Tìm thêm" để chạy luôn |

Số liệu đã kiểm nhưng thuộc thị trường hoặc kỳ khác câu hỏi được để riêng ở mục "ngoài phạm vi câu hỏi" thay vì trộn vào câu trả lời.

Những thay đổi khác so với M2:

- **Kiểm chứng một cú nhấp**: mỗi nhận định có nút mở nguồn tại đúng câu trích (trang web được cuộn tới và tô sáng câu đó nhờ text fragment) hoặc tại đúng trang của PDF, kèm đoạn văn quanh câu trích ngay trong app.
- **Nghiên cứu tiếp mà vẫn giữ bối cảnh**: gõ câu hỏi tiếp (ví dụ "Còn riêng Việt Nam thì sao?") hoặc bấm một bước tìm hiểu tiếp. Hệ thống viết lại câu hỏi tiếp thành câu hỏi đầy đủ (giữ chỉ số, kỳ đo; chỉ đổi phần người dùng đổi), giữ mọi nhận định đã kiểm và các nhận định người dùng đã loại, đọc lại các trang đã đọc từ bản lưu trên máy (không tải lại) để tìm số cho góc hỏi mới, và hiện chuỗi nghiên cứu. Bước "Tìm thêm" chỉ tìm và đọc trang mới.
- **Nguồn cũ và số dự báo**: số của một năm chưa kết thúc khi bài được đăng (ví dụ "năm 2025: 5,47 tỷ USD" trong bài tháng 9/2025) và kỳ đo kéo dài tới tương lai (ví dụ tăng trưởng 2024 đến 2029) được gắn cờ dự báo; số cũ đã có bản mới hơn được chỉ ra.
- **Kết luận hợp với loại câu hỏi**: câu hỏi tra cứu số liệu được trả lời "Đã có câu trả lời" thay vì luôn ra "Cần thêm dữ liệu"; mỗi lý do có dấu cho biết nó dựa trên nhận định có thể tin hay chưa chắc chắn. Code chặn kết luận chắc chắn khi không lý do nào dựa trên nhận định có thể tin: "Đã có câu trả lời" đổi thành "Có số liệu nhưng chưa chắc chắn", còn "Nên ưu tiên" hoặc "Chưa nên" đổi thành "Cần thêm dữ liệu".
- **Sửa lỗi M2**: số có trong câu hỏi ("12 tháng") không còn bị coi là số bịa làm mất câu tóm tắt (TC3); ô bảng "0.817" không còn bị đọc thành 817; nhãn bảng như "S-5.89 N-6.51" (S là Statista, N là Newzoo) không còn bị đọc thành số âm, và giá trị ghi hai con số bị loại vì không rõ số nào là của nhận định; số lượt gọi LLM tính riêng từng lần chạy.

Chi tiết trước và sau cải tiến, quyết định thay đổi gì và không thay đổi gì, bằng chứng và giới hạn còn lại: [docs/mission-3.md](docs/mission-3.md). Bảng so sánh kết quả chạy thật M2 và M3: [eval/so-sanh-m2-m3.md](eval/so-sanh-m2-m3.md).

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

| Bước (M3) | Ai làm | Nội dung |
|---|---|---|
| 8. Xếp bằng chứng | Code | Mỗi nhóm số liệu vào "có thể tin", "chưa chắc chắn" (kèm lý do) hoặc "ngoài phạm vi câu hỏi"; sinh các bước tìm hiểu tiếp |
| 9. Nghiên cứu tiếp | AI viết lại câu hỏi, code giữ bối cảnh | Hỏi tiếp hoặc bấm một bước: chạy lại bước 2 đến 8 cho phần còn thiếu, giữ nhận định cũ |

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

- `pytest` chạy 55 bài test không cần mạng và không cần khóa API:
  - 32 bài từ M2 (giữ nguyên, là test regression): kiểm câu trích (câu bịa, câu bị diễn đạt lại, số bị đổi), đọc giá trị và kỳ đo, hạng nguồn, truy nguồn gốc, phân biệt mâu thuẫn với khác định nghĩa, bẫy bảng của Việt Nam bị ghi là Đông Nam Á, bộ kiểm bản tóm tắt, xử lý lỗi (mô hình quá tải, mô hình dự phòng, tải trang timeout, lỗi khi viết tóm tắt), và một bài chạy toàn bộ luồng với LLM giả cố tình trả về một nhận định bịa.
  - 22 bài mới trong `tests/test_m3.py`: xếp có thể tin / chưa chắc chắn / ngoài phạm vi, số dẫn lại, mâu thuẫn và trái chiều, số dự báo tại thời điểm đăng, số cũ có bản mới hơn, biểu đồ chỉ tới đúng trang hoặc đúng con số kể cả khi nhãn bị ghép với số, số không ghi đơn vị tiền, giá trị ghi hai con số, link mở câu trích, nghiên cứu tiếp giữ bối cảnh (đổi thị trường, giữ năm, giữ nhận định đã loại, bước tìm thêm bỏ qua trang đã đọc), số lượt gọi LLM từng lần chạy, kết luận không được ghi là đã trả lời khi mọi lý do chỉ dựa trên nhận định chưa chắc chắn, và regression cho các lỗi M2 (mất tóm tắt vì "12 tháng", "0.817" bị đọc thành 817, ô bảng "S-5.89 N-6.51" bị đọc thành số âm).
  - 1 bài trong `tests/test_app.py` dựng trang Streamlit bằng AppTest với một kết quả có sẵn và kiểm ba phần mới hiển thị.
- `eval.run_eval` chạy 8 tình huống thật trong `eval/cases.yaml` (cần mạng và khóa Gemini), tự chấm và sinh bảng `eval/ket-qua-kiem-thu.md`. Mỗi case có `checks` (điều kiện M2, giữ nguyên để kiểm regression) và `checks_m3` (điều kiện mới). TC7 hỏi tiếp từ kết quả TC2 để kiểm việc giữ bối cảnh; TC8 là nguồn cũ có số dự báo. Kết quả chi tiết từng lần chạy nằm trong `eval/results/`, kết quả của M2 giữ ở `eval/results_m2/` và `eval/ket-qua-m2.md`.
- `eval.run_eval --compare` áp cùng bộ điều kiện lên kết quả M2 và M3, sinh `eval/so-sanh-m2-m3.md`. `eval.run_eval --report` dựng lại bảng từ kết quả đã lưu mà không gọi LLM.

## Hạn chế đã biết

- Kiểm câu trích chỉ chứng minh câu trích có thật trong nguồn, không chứng minh AI hiểu đúng câu đó. Các trường như thị trường, kỳ đo vẫn do AI điền và chỉ được kiểm một phần bằng cảnh báo (tên chương, kỳ đo so với câu hỏi).
- Số liệu nằm trong biểu đồ của PDF: khi đọc ra chữ, nhãn và số bị tách khỏi nhau. Câu trích vẫn có thật nhưng AI có thể ghép nhầm nhãn với số (tình huống TC6).
- Nhận định đúng nhưng AI chép lệch vài chữ sẽ bị loại oan. Đây là đánh đổi có chủ ý để không lọt nhận định bịa.
- Truy nguồn gốc dựa trên tên hãng dữ liệu xuất hiện gần câu trích, nên sẽ sót nếu bài viết không nhắc tên hãng.
- Hạng nguồn dựa trên danh sách tên miền; tên miền chưa có trong danh sách mặc định là hạng C.
- Nhiều trang chặn tải tự động hoặc nằm sau tường phí. Khi đó hệ thống ghi lỗi ở tab Nguồn, và người dùng có thể tải file lên.
- Gói miễn phí của Gemini giới hạn số lượt gọi mỗi phút và mỗi ngày theo từng mô hình (xem https://aistudio.google.com/rate-limit). Một lần chạy dùng 1 lượt lập kế hoạch, 1 lượt cho mỗi đoạn nguồn được đọc (tối đa 3 đoạn mỗi nguồn) và 1 lượt viết tóm tắt, cộng các lượt thử lại. Một lần hỏi tiếp đọc lại (từ bản đã lưu) các nguồn từng cho nhận định đã kiểm cùng các nguồn mới (TC7: 6 lượt). Hết hạn mức của một mô hình thì hệ thống tự chuyển sang mô hình trong `LLM_FALLBACK_MODELS`.
- Phân loại "có thể tin" dựa trên quy tắc về nguồn, kỳ đo và thị trường; nó không chứng minh con số đúng với thực tế. Một số do hãng dữ liệu tự công bố vẫn chỉ là ước tính của hãng đó.
- Bước "Tìm thêm" chỉ đọc trang mới; câu hỏi tiếp thì đọc lại các trang từng cho nhận định đã kiểm. Trang chưa từng cho nhận định nào sẽ không được đọc lại trừ khi người dùng thêm lại link.
- Lịch sử và chuỗi nghiên cứu lưu trong SQLite trên máy chủ, mất khi Streamlit Community Cloud khởi động lại.
- Chưa có: đăng nhập, nguồn tiếng Trung, đọc biểu đồ bằng mô hình thị giác, theo dõi theo thời gian.

## Cấu trúc thư mục

```
app.py                  giao diện Streamlit
core/pipeline.py        ghép các bước, nghiên cứu tiếp giữ bối cảnh (follow_up)
core/extract.py         prompt lập kế hoạch, kế hoạch cho câu hỏi tiếp, trích nhận định (AI)
core/verify.py          kiểm câu trích (code)
core/sources.py         hạng nguồn, truy nguồn gốc (code)
core/periods.py         đọc kỳ đo, so với khung thời gian câu hỏi (code)
core/analyze.py         gom nhóm, mâu thuẫn, mức tin cậy, số dự báo, số mới hơn (code)
core/evidence.py        có thể tin / chưa chắc chắn / ngoài phạm vi, bước tìm hiểu tiếp, link mở câu trích (code)
core/brief.py           viết bản tóm tắt (AI) và kiểm lại (code)
core/fetch.py           tải trang web và đọc PDF
core/search.py          tìm kiếm (Tavily hoặc DuckDuckGo)
core/store.py           lưu lịch sử chạy vào SQLite
core/report.py          xuất bản tóm tắt dạng Markdown
data/source_tiers.yaml  danh sách hạng nguồn và hãng dữ liệu
eval/                   tình huống kiểm thử chạy thật, kết quả M3, kết quả M2 (results_m2) và bảng so sánh
docs/mission-3.md       trước và sau cải tiến, quyết định, bằng chứng, giới hạn
tests/                  bài test không cần mạng
```
