# Việt — heading chunking và Gemini

> **C?p nh?t Groq:** bench.py ?? h? tr? LLM_PROVIDER=groq, d?ng GROQ_API_KEY v? openai/gpt-oss-20b cho c?u tr? l?i; embedding d?ng model local sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2. C?n c?i requirements-local.txt v? t?i model tr??c khi ch?y embedding. Ch?a c?i/t?i trong l??t n?y v? vi?c x?c th?c Groq b? ch?n tr??c b?i b? duy?t t? ??ng: key ???c chuy?n t? bi?n GEMINI_API_KEY sang GROQ_API_KEY n?n c?n x?c nh?n r? nh? cung c?p credential. Ch?a c? request Groq th?nh c?ng ho?c k?t qu? benchmark m?i. Code m?i ???c ki?m tra b?ng ph?n h?i gi?: 42 test g?c v? 3 test Groq ??u ??t.

C?u h?nh Groq:
```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=YOUR_NEW_GROQ_KEY
GROQ_LLM_MODEL=openai/gpt-oss-20b
LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Sau khi x?c nh?n key v? cho ph?p k?t n?i, c?i embedding local b?ng `python -m pip install -r requirements-local.txt`, r?i ch?y `python bench.py`. Kh?ng d?ng Gemini model ID l?m model Groq. Endpoint theo t?i li?u [Groq](https://console.groq.com/docs/openai). Kh?ng c? fallback v? mock.


> **C?p nh?t:** Vi?t ?? x?c nh?n ngu?n l? ??ng. ?? ?i?n 5 gold answer b?ng ?o?n tr?ch trong corpus, ghi tr?ng th?i `user_confirmed_source`; ??y l? x?c nh?n c?a ng??i d?ng, kh?ng ph?i x?c minh ??c l?p c?a tr? l?. C?c ghi ch? ch?a x?c minh ph?a d??i l? l?ch s? tr??c x?c nh?n. C?n c? quy?n s? d?ng v? phi?n b?n ch?a ???c x?c nh?n ri?ng.


Chiến lược mới: **HeadingChunker(chunk_size=500)**. Giữ từng mục/điều khoản riêng; nếu mục quá dài thì chia tiếp và lặp heading để giữ ngữ cảnh. Heading cha được giữ khi có mục con. Giới hạn 500 ký tự bao gồm heading. Không overlap phần thân. Đây là chiến lược khác Recursive 300 của Đông, Fixed 300/30 của Duyên và Sentence 2 câu của Na.

## Cấu hình và chạy

Mở `.env` tại thư mục gốc repo và điền `GEMINI_API_KEY` bằng key của bạn. File này đã được gitignore; không gửi key vào chat, báo cáo hoặc commit. Các tên model mặc định được chọn theo tài liệu Google đã đối chiếu ngày 2026-09-20; có thể đổi theo model được tài khoản của bạn hỗ trợ.

```dotenv
GEMINI_API_KEY=YOUR_REAL_KEY
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_LLM_MODEL=gemini-3.8-flash
```

Chạy từ thư mục dự án:

```powershell
..\.venv\Scripts\python.exe bench.py --dry-run
..\.venv\Scripts\python.exe bench.py
```

Dry-run chỉ kiểm tra dữ liệu/chunk, không gọi mạng và không sinh số liệu retrieval. Lệnh thứ hai gửi nội dung corpus và câu hỏi tới Gemini để tạo embedding và đáp án; cần key/model/quota hợp lệ và kết nối mạng. Sử dụng REST và thư viện chuẩn Python, không cần cài Google SDK. Thiếu key/API lỗi sẽ dừng, không chuyển sang mock.

Embedding được chuẩn hóa về độ dài 1 để dot product trong store tương đương cosine. Cache trong bộ nhớ tránh gọi lại embedding cho cùng chuỗi trong một lượt chạy. Agent dùng đúng filter của câu hỏi, trả lời tiếng Việt và được nhắc dẫn nguồn theo số chunk. Không tự động đánh giá đúng chỉ vì agent trả lời được.

Khi chạy thật thành công:

- `report/benchmark_viet_heading.json`: top-3 đầy đủ, score, metadata, kết quả không filter, agent answer, model và hash dữ liệu/câu hỏi.
- `report/benchmark_viet_heading.md`: bản dễ đọc để đối chiếu và đưa vào báo cáo.
- `report/heading_chunks_preview.json`: chỉ là bản xem chunk từ dry-run.

Kết quả Recursive/mock cũ trong `ket_qua_benchmark.txt` giữ làm lịch sử, không phải kết quả của chiến lược mới. Các lần chạy lại ghi đè kết quả heading cùng tên; lưu bản sao nếu cần so sánh nhiều model.

## Nguồn và gold answer

Năm câu hỏi của Đông giữ nguyên trong `data/lazada/benchmark_queries.json`. Gold answer hiện để null vì nguồn chưa xác minh. Benchmark cho chạy thử kỹ thuật, luôn ghi trạng thái provisional; không tự chấm điểm chính thức.

Xem [SOURCE_VERIFICATION.md](../report/SOURCE_VERIFICATION.md). Khi có trang nguồn đọc được, đối chiếu từng thời hạn/mức phí/ngoại lệ, điền `gold_answer`, `evidence` (doc_id, mục, đoạn trích, source_url), cập nhật trạng thái xác minh và chia sẻ cùng file câu hỏi cho cả nhóm. Lúc đó cần người đánh giá `relevance_review` và `answer_correctness_review` dựa trên bằng chứng thật, không chỉ score.

Metadata `audience=both` chỉ xuất hiện khi không lọc hoặc lọc đúng both; giữ cùng quy tắc so khớp với các thành viên. Câu bảo hành hiện không lọc nên vẫn tìm được tài liệu both.

## Tài liệu kỹ thuật đã đối chiếu

- [Google: Embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
- [Google: GenerateContent API](https://ai.google.dev/api/generate-content)

Việc unit test dùng phản hồi giả chỉ kiểm tra xử lý request/response; không phải bằng chứng đã gọi Gemini thật thành công.
