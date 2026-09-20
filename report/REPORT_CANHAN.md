# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Quốc Việt  
**MSSV:** 2A202602884  
**Nhóm:** Nhomtoi  
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Cosine cao, gần 1, nghĩa là hai vector gần cùng hướng. Với embedding ngữ nghĩa phù hợp, điều này thường biểu thị nội dung gần nghĩa; không bảo đảm hai câu có cùng điều kiện hay con số. Mock embedding không có khả năng này.

**Ví dụ có độ tương tự CAO:**

- Câu A: “Tôi muốn trả lại sản phẩm bị lỗi.”
- Câu B: “Tôi cần đổi trả món hàng bị hỏng.”
- Tại sao tương đồng: Hai câu cùng diễn đạt nhu cầu đổi trả hàng lỗi.

**Ví dụ có độ tương tự THẤP:**

- Câu A: “Người mua yêu cầu hoàn tiền.”
- Câu B: “Hôm nay trời có mưa lớn.”
- Tại sao khác: Hai câu nói về thương mại điện tử và thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine tập trung vào hướng vector và bỏ qua độ lớn, hữu ích khi độ lớn không phải đặc trưng cần so sánh. Với vector đã chuẩn hóa, cosine và Euclid cho thứ tự tương đồng tương đương; cosine không luôn tốt hơn trong mọi trường hợp.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> _Trình bày phép tính:_ Bước nhảy `step = 500 - 50 = 450`. Theo cách dừng của FixedSizeChunker, số chunk là `1 + ceil((10000 - 500) / 450) = 23`.
>
> _Đáp án:_ **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Bước nhảy còn `500 - 100 = 400`, số chunk tăng thành `1 + ceil(9500 / 400) = 25`. Overlap giữ thêm ngữ cảnh ở ranh giới nhưng tăng dữ liệu lặp và chi phí embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng `re.split(r'(?<=[.!?])\s+', text.strip())` để tách sau dấu kết thúc câu và khoảng trắng/xuống dòng, giữ dấu câu. Loại mảnh rỗng rồi gom tối đa max_sentences_per_chunk câu. Văn bản rỗng trả danh sách rỗng; regex đơn giản có thể chia chưa đúng chữ viết tắt hoặc số thứ tự.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thử separator theo thứ tự đoạn văn, dòng, câu, từ, ký tự: `["\n\n", "\n", ". ", " ", ""]`. Đoạn không vượt chunk_size được trả về ngay; đoạn dài được chia tiếp bằng separator cấp thấp hơn. Gom mảnh liền kề khi đủ dung lượng, giữ separator để không mất nội dung. Hết separator thì cắt theo ký tự; kích thước không dương bị từ chối.

**Chiến lược riêng của Việt — `HeadingChunker(chunk_size=500)`:**

> Chia theo tiêu đề/điều khoản, không gộp các mục ngang cấp. Mục quá dài được chia tiếp và lặp heading trên các chunk con; giữ heading cha khi có mục con. Giới hạn 500 tính cả heading, không overlap phần thân. Cách này phù hợp chính sách có cấu trúc, nhưng ngoại lệ ở mục khác vẫn có thể không được truy xuất. Dry-run trên 5 tài liệu Lazada tạo **11 chunk**.

**`compute_similarity` và `ChunkingStrategyComparator`:**

> Cosine dùng dot product chia tích hai norm, kiểm tra cùng số chiều và trả 0 khi một vector bằng 0. Comparator trả count, avg_length và chunks của FixedSize, Sentence, Recursive; xử lý đầu vào rỗng. Giữ nguyên FixedSizeChunker của giảng viên.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Lưu in-memory record gồm ID riêng, content, metadata và embedding. metadata.doc_id giữ tài liệu cha, mặc định lấy Document.id nếu chưa có. Search tạo vector query, tính dot product, sắp giảm dần và lấy top-k. Dot product bằng cosine khi vector đã chuẩn hóa.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Pre-filter bằng tất cả cặp key-value trong metadata_filter trước khi xếp hạng. Xóa toàn bộ chunk có metadata.doc_id khớp tài liệu cần xóa; trả False nếu không tìm thấy. Lọc buyer không tự bao gồm both, nên câu hỏi bảo hành hiện không lọc để giữ tài liệu both trong tập ứng viên.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Lấy top-k theo câu hỏi và filter, dựng context đánh số nguồn [1], [2] kèm doc_id, tạo prompt rồi gọi llm_fn. Prompt yêu cầu dựa vào context, dẫn nguồn và nói rõ nếu thiếu thông tin. Khi không có kết quả, code vẫn gọi llm_fn với thông báo context rỗng; không thể chỉ dựa vào prompt để bảo đảm LLM không bịa.
>
> Backend hiện cấu hình Groq `openai/gpt-oss-20b` cho câu trả lời và embedding local `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Chưa có benchmark hoàn chỉnh vì trọng số embedding chưa tải xong; không tự chuyển về mock.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

Log thực chạy trên máy của Việt:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-9.1.1, pluggy-1.6.0 -- D:\AI_thuc_chien\lab_07\.venv\Scripts\python.exe
rootdir: D:\AI_thuc_chien\lab_07\K4-DAY07-Bui-Quoc-Viet-2A202602884
plugins: anyio-4.15.1
collecting ... collected 53 items

tests/test_groq_runtime.py::test_groq_requires_own_key PASSED            [  1%]
tests/test_groq_runtime.py::test_groq_generation_and_model_check PASSED  [  3%]
tests/test_groq_runtime.py::test_groq_rejects_incomplete_answer PASSED   [  5%]
tests/test_heading_benchmark.py::test_heading_keeps_sections_separate PASSED [  7%]
tests/test_heading_benchmark.py::test_long_section_repeats_heading_and_preserves_words PASSED [  9%]
tests/test_heading_benchmark.py::test_nested_heading_keeps_parent_context PASSED [ 11%]
tests/test_heading_benchmark.py::test_gemini_requires_key PASSED         [ 13%]
tests/test_heading_benchmark.py::test_normalization_cache_and_generation PASSED [ 15%]
tests/test_heading_benchmark.py::test_no_fake_answer_for_blocked_output PASSED [ 16%]
tests/test_heading_benchmark.py::test_benchmark_calls_agent_with_filtered_context PASSED [ 18%]
tests/test_heading_benchmark.py::test_loader_excludes_frontmatter_and_retains_doc_id PASSED [ 20%]
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [ 22%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [ 24%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [ 26%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [ 28%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 30%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 32%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 33%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 35%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 37%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 39%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 41%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 43%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 45%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 47%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 49%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 50%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 52%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 54%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 56%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 58%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 60%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 62%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 64%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 66%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 67%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 69%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 71%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 73%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 75%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 77%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 79%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 81%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 84%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 86%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 94%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 96%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 98%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 53 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42 test gốc**; cộng **11 test bổ sung**, tổng **53 / 53**. Log: [test_results.txt](test_results.txt). Môi trường là Python 3.13.3, chưa xác minh trên Python 3.11 chuẩn lab.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Dự đoán được lưu trước khi chạy trong [similarity_predictions.json](similarity_predictions.json), số liệu tại [similarity_results.json](similarity_results.json). **Backend: MockEmbedder**, không phải embedding ngữ nghĩa. Cột “Đúng?” là nhận xét định tính, không phải phân loại theo ngưỡng định trước.

| Cặp | Câu A                                   | Câu B                                               | Dự đoán | Điểm thực tế | Đúng?                     |
| --- | --------------------------------------- | --------------------------------------------------- | ------- | ------------ | ------------------------- |
| 1   | Người mua yêu cầu hoàn tiền.            | Người mua yêu cầu hoàn tiền.                        | cao     | 1.000000     | Phù hợp; cùng chuỗi       |
| 2   | Tôi muốn trả lại sản phẩm bị lỗi.       | Tôi cần đổi trả món hàng bị hỏng.                   | cao     | 0.092362     | Không phù hợp dự đoán cao |
| 3   | Người bán tiếp nhận yêu cầu bảo hành.   | Cửa hàng xử lý đề nghị sửa chữa theo bảo hành.      | cao     | 0.146931     | Không phù hợp dự đoán cao |
| 4   | Người mua yêu cầu hoàn tiền.            | Hôm nay trời có mưa lớn.                            | thấp    | -0.077553    | Phù hợp mức thấp          |
| 5   | Sản phẩm cần còn nguyên tem để đổi trả. | Đội bóng đã giành chiến thắng trong trận chung kết. | thấp    | 0.059368     | Phù hợp mức thấp          |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Cặp 2 và 3 gần nghĩa nhưng có điểm thấp so với dự đoán cao. MockEmbedder tạo vector từ hash, không học ngữ nghĩa. Cặp 4 và 5 có điểm thấp cũng không chứng minh mock hiểu chủ đề. Cần chạy embedding ngữ nghĩa để đánh giá cách diễn đạt tương đương; không kết luận chất lượng retrieval từ các điểm mock này.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Bộ dữ liệu đánh giá: **5 tài liệu chính sách Lazada** trong `data/lazada/`. Nguồn đã được Việt xác nhận; gold answer và bằng chứng nằm trong [benchmark_queries.json](../data/lazada/benchmark_queries.json).

**Chiến lược của Việt:** HeadingChunker(500), top-k=3. **Chưa có kết quả hoàn chỉnh** do tải trọng số embedding local chưa thành công. Giữ đúng 5 câu hỏi chung dưới đây; không dùng số liệu Recursive/mock cũ hoặc số liệu của Đồng thay cho kết quả Heading.

| #   | Câu hỏi (Query)                                                                                | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| --- | ---------------------------------------------------------------------------------------------- | ------------------------------------ | ---------- | ------------------------------ | ------------------------------- |
| 1   | Thời hạn trả hàng của sản phẩm LazMall là bao lâu?                                             | Chưa có kết quả Heading              | Chưa đo    | Chưa đánh giá                  | Chưa chạy thành công            |
| 2   | Thời gian và quy trình xử lý hoàn tiền cho người mua như thế nào? (filter: buyer)              | Chưa có kết quả Heading              | Chưa đo    | Chưa đánh giá                  | Chưa chạy thành công            |
| 3   | Nhà bán hàng có bao nhiêu ngày để mở khiếu nại khi nhận hàng hoàn bị hư hỏng? (filter: seller) | Chưa có kết quả Heading              | Chưa đo    | Chưa đánh giá                  | Chưa chạy thành công            |
| 4   | Sản phẩm điện tử mua trên Lazada có các hình thức bảo hành nào?                                | Chưa có kết quả Heading              | Chưa đo    | Chưa đánh giá                  | Chưa chạy thành công            |
| 5   | Chính sách đền bù của Lazada khi sản phẩm LazMall bị phát hiện là hàng giả? (filter: buyer)    | Chưa có kết quả Heading              | Chưa đo    | Chưa đánh giá                  | Chưa chạy thành công            |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **Chưa đánh giá / 5** đối với Heading. Dry-run có 11 chunk nhưng không phải kết quả retrieval. `ket_qua_benchmark.txt` là kết quả Recursive/mock cũ, giữ riêng để đối chiếu lịch sử.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Qua báo cáo Nguyễn Đức Đồng chia sẻ, tôi thấy cần chú ý pre-filtering theo audience để phân biệt quy định người mua và người bán khi tài liệu có nhiều từ giống nhau. Đối chiếu với kết quả Recursive/mock trước đây của mình, tôi nhận ra đúng doc_id chưa đủ: phải đọc chính chunk để xem có đúng điều khoản trả lời câu hỏi không. Tôi sẽ kiểm chứng bằng bảng có/không filter trên Heading; chưa có kết quả để kết luận tốt hơn chiến lược của Đồng. Nhận xét này dựa trên báo cáo được chia sẻ, không khẳng định đã tham dự demo.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5 / 5            |
| Hướng tiếp cận của tôi (My Approach)            | 10 / 10          |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30          |
| Dự đoán độ tương tự (Similarity Predictions)    | 5 / 5            |
| Kết quả truy xuất của tôi (Competition Results) | 5 / 10           |
| **Tổng phần cá nhân**                           | 60 / 60\*\*      |
