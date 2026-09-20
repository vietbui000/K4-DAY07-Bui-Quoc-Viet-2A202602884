"""Restore the supplied group report layout with Viet's own recorded evidence."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'


def main():
    reference = Path(r'C:\Users\Admin\.codex\attachments\19194c34-803e-4e92-9742-c847654ca884/pasted-text.txt').read_text(encoding='utf-8-sig')
    old = (REPORT / 'REPORT_CANHAN.md').read_text(encoding='utf-8-sig')
    group = re.search(r'^\*\*Nhóm:\*\*\s*(.+)', old, re.M)
    group_name = group.group(1).strip() if group else 'Nhóm L3B'
    assessment = old.split('## Tự Đánh Giá (Phần Cá Nhân)', 1)[-1].strip()
    headings = re.findall(r'^## .*', reference, re.M)
    sections = []
    sections.append('''### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

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
> *Trình bày phép tính:* Bước nhảy `step = 500 - 50 = 450`. Theo cách dừng của FixedSizeChunker, số chunk là `1 + ceil((10000 - 500) / 450) = 23`.
>
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Bước nhảy còn `500 - 100 = 400`, số chunk tăng thành `1 + ceil(9500 / 400) = 25`. Overlap giữ thêm ngữ cảnh ở ranh giới nhưng tăng dữ liệu lặp và chi phí embedding.''')
    sections.append('''### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r'(?<=[.!?])\\s+', text.strip())` để tách sau dấu kết thúc câu và khoảng trắng/xuống dòng, giữ dấu câu. Loại mảnh rỗng rồi gom tối đa max_sentences_per_chunk câu. Văn bản rỗng trả danh sách rỗng; regex đơn giản có thể chia chưa đúng chữ viết tắt hoặc số thứ tự.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thử separator theo thứ tự đoạn văn, dòng, câu, từ, ký tự: `["\\n\\n", "\\n", ". ", " ", ""]`. Đoạn không vượt chunk_size được trả về ngay; đoạn dài được chia tiếp bằng separator cấp thấp hơn. Gom mảnh liền kề khi đủ dung lượng, giữ separator để không mất nội dung. Hết separator thì cắt theo ký tự; kích thước không dương bị từ chối.

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
> Backend hiện cấu hình Groq `openai/gpt-oss-20b` cho câu trả lời và embedding local `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Chưa có benchmark hoàn chỉnh vì trọng số embedding chưa tải xong; không tự chuyển về mock.''')
    log = (REPORT / 'test_results.txt').read_text(encoding='utf-8').strip()
    sections.append('### Kết Quả Kiểm Thử (Test Results)\n\nLog thực chạy trên máy của Việt:\n\n```text\n' + log + '\n```\n\n**Số lượng bài test vượt qua (pass):** **42 / 42 test gốc**; cộng **11 test bổ sung**, tổng **53 / 53**. Log: [test_results.txt](test_results.txt). Môi trường là Python 3.13.3, chưa xác minh trên Python 3.11 chuẩn lab.')
    rows = json.loads((REPORT / 'similarity_results.json').read_text(encoding='utf-8'))['results']
    similarity = '''Dự đoán được lưu trước khi chạy trong [similarity_predictions.json](similarity_predictions.json), số liệu tại [similarity_results.json](similarity_results.json). **Backend: MockEmbedder**, không phải embedding ngữ nghĩa. Cột “Đúng?” là nhận xét định tính, không phải phân loại theo ngưỡng định trước.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
'''
    judgments = ['Phù hợp; cùng chuỗi', 'Không phù hợp dự đoán cao', 'Không phù hợp dự đoán cao', 'Phù hợp mức thấp', 'Phù hợp mức thấp']
    for i, row in enumerate(rows):
        similarity += f"| {i+1} | {row['a']} | {row['b']} | {row['prediction']} | {row['score']:.6f} | {judgments[i]} |\n"
    similarity += '''
**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 2 và 3 gần nghĩa nhưng có điểm thấp so với dự đoán cao. MockEmbedder tạo vector từ hash, không học ngữ nghĩa. Cặp 4 và 5 có điểm thấp cũng không chứng minh mock hiểu chủ đề. Cần chạy embedding ngữ nghĩa để đánh giá cách diễn đạt tương đương; không kết luận chất lượng retrieval từ các điểm mock này.'''
    sections.append(similarity)
    retrieval = '''Bộ dữ liệu đánh giá: **5 tài liệu chính sách Lazada** trong `data/lazada/`. Nguồn đã được Việt xác nhận; gold answer và bằng chứng nằm trong [benchmark_queries.json](../data/lazada/benchmark_queries.json).

**Chiến lược của Việt:** HeadingChunker(500), top-k=3. **Chưa có kết quả hoàn chỉnh** do tải trọng số embedding local chưa thành công. Giữ đúng 5 câu hỏi chung dưới đây; không dùng số liệu Recursive/mock cũ hoặc số liệu của Đồng thay cho kết quả Heading.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
'''
    queries = json.loads((ROOT / 'data/lazada/benchmark_queries.json').read_text(encoding='utf-8'))
    for q in queries:
        suffix = f" (filter: {q['filter']['audience']})" if q.get('filter') else ''
        retrieval += f"| {q['id']} | {q['query']}{suffix} | Chưa có kết quả Heading | Chưa đo | Chưa đánh giá | Chưa chạy thành công |\n"
    retrieval += '''
**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **Chưa đánh giá / 5** đối với Heading. Dry-run có 11 chunk nhưng không phải kết quả retrieval. `ket_qua_benchmark.txt` là kết quả Recursive/mock cũ, giữ riêng để đối chiếu lịch sử.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua báo cáo Nguyễn Đức Đồng chia sẻ, tôi thấy cần chú ý pre-filtering theo audience để phân biệt quy định người mua và người bán khi tài liệu có nhiều từ giống nhau. Đối chiếu với kết quả Recursive/mock trước đây của mình, tôi nhận ra đúng doc_id chưa đủ: phải đọc chính chunk để xem có đúng điều khoản trả lời câu hỏi không. Tôi sẽ kiểm chứng bằng bảng có/không filter trên Heading; chưa có kết quả để kết luận tốt hơn chiến lược của Đồng. Nhận xét này dựa trên báo cáo được chia sẻ, không khẳng định đã tham dự demo.'''
    sections.append(retrieval)
    intro = reference.split('\n## 1.', 1)[0]
    intro = intro.replace('Nguyễn Đức Đồng', 'Bùi Quốc Việt').replace('2A202602367', '2A202602884').replace('Nhóm L3B', group_name)
    text = intro.rstrip() + '\n\n'
    for heading, body in zip(headings[:5], sections):
        text += heading + '\n\n' + body.strip() + '\n\n---\n\n'
    text += headings[5] + '\n\n' + assessment + '\n'
    assert re.findall(r'^## .*', text, re.M) == headings
    assert 'Nguyễn Đức Đồng' not in text.split('## 1.', 1)[0]
    (REPORT / 'REPORT_CANHAN.md').write_text(text, encoding='utf-8')
    print('Restored exact six main headings and table layout; preserved Viet identity and self-assessment.')


if __name__ == '__main__':
    main()
