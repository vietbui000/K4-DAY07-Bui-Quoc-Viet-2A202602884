"""Build the personal report from saved evidence; never invent missing results."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', '<br>')


def main():
    report_path = REPORT / 'REPORT_CANHAN.md'
    previous_text = report_path.read_text(encoding='utf-8-sig') if report_path.exists() else ''
    assessment_match = re.search(
        r'^## (?:\d+\. )?Tự [Đđ]ánh [Gg]iá[^\n]*\n.*?(?=^## |\Z)',
        previous_text, re.MULTILINE | re.DOTALL,
    )
    assessment = assessment_match.group(0).rstrip() if assessment_match else '''## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |'''
    benchmark_path = REPORT / 'benchmark_viet_heading.json'
    similarity_path = REPORT / 'similarity_local_results.json'
    benchmark = json.loads(benchmark_path.read_text(encoding='utf-8')) if benchmark_path.exists() else None
    similarity = json.loads(similarity_path.read_text(encoding='utf-8')) if similarity_path.exists() else None
    semantic_available = similarity is not None
    if similarity is None:
        similarity = json.loads((REPORT / 'similarity_results.json').read_text(encoding='utf-8'))
    tests = (REPORT / 'test_results.txt').read_text(encoding='utf-8')
    test_summary = next(line.strip('= ') for line in reversed(tests.splitlines()) if 'passed' in line)
    text = '''# Báo cáo cá nhân — Truy xuất chính sách Lazada

**Họ tên:** Bùi Quốc Việt

**Mã sinh viên:** 2A202602884

**Nhóm:** Việt, Đông, Duyên, Na — đề tài chính sách thương mại điện tử Lazada.

**Ngày thực hiện:** 2026-09-20

Nguồn corpus được Việt xác nhận đúng trong phiên làm việc. Gold answer trích từ các file Markdown, kèm doc_id, URL, mục và hash trong [benchmark_queries.json](../data/lazada/benchmark_queries.json). Đánh giá dưới đây đo mức bám sát corpus này, không phải xác minh độc lập chính sách Lazada hiện hành. Sinh viên cần đọc hiểu và kiểm tra bản báo cáo hỗ trợ này trước khi nộp.

## 1. Khởi động

### Cosine similarity

Cosine similarity đo hướng tương đối của hai vector: `dot(a,b)/(norm(a)*norm(b))`. Gần 1 là cùng hướng, gần 0 là gần vuông góc, gần -1 là ngược hướng. Với embedding ngữ nghĩa phù hợp, điểm cao thường biểu thị nội dung gần nghĩa; điểm cao không bảo đảm hai câu có cùng sự thật hoặc cùng điều kiện áp dụng.

- Ví dụ dự đoán cao: “Tôi muốn trả lại sản phẩm bị lỗi.” và “Tôi cần đổi trả món hàng bị hỏng.” Cả hai nói về nhu cầu đổi trả hàng lỗi.
- Ví dụ dự đoán thấp: “Người mua yêu cầu hoàn tiền.” và “Hôm nay trời có mưa lớn.” Hai câu khác chủ đề.

Cosine bỏ qua độ lớn và tập trung vào hướng vector. Với embedding chuẩn hóa, cosine và Euclid cho thứ tự tương đồng tương đương; cosine không luôn tốt hơn trong mọi bài toán. Nếu một vector bằng 0, hàm trả 0 để tránh chia cho 0.

### Tính số chunk

Với N ký tự, kích thước C, overlap O và N>C, số chunk của FixedSizeChunker là `1 + ceil((N-C)/(C-O))`.

- N=10.000, C=500, O=50: `1 + ceil(9500/450) = 23 chunk`.
- O=100: `1 + ceil(9500/400) = 25 chunk`.

Overlap lớn giữ thêm ngữ cảnh ở ranh giới nhưng tăng dữ liệu lặp và chi phí embedding. Văn bản rỗng có 0 chunk; văn bản không rỗng dài không quá C có 1 chunk.

## 2. Hướng tiếp cận

### SentenceChunker

Dùng regex `(?<=[.!?])\\s+` tách sau dấu kết thúc câu và khoảng trắng/xuống dòng, giữ dấu câu, loại mảnh rỗng rồi gom tối đa số câu đã cấu hình. Đầu vào rỗng hoặc chỉ có khoảng trắng trả danh sách rỗng. Regex đơn giản có thể nhầm chữ viết tắt hoặc số thứ tự, nên cần xem chunk thực tế trên chính sách.

### RecursiveChunker

Thử separator theo thứ tự đoạn văn, dòng, câu, từ và ký tự. Mảnh quá dài được chia tiếp bằng separator cấp thấp hơn; mảnh liền kề được gom khi còn đủ dung lượng. Giữ dấu phân cách để không mất nội dung; hết separator thì cắt theo ký tự. Kích thước không dương bị từ chối. Hàm cốt lõi này vẫn được hoàn thiện dù chiến lược thử nghiệm cuối cùng của Việt là heading.

### HeadingChunker — chiến lược riêng

Chọn `HeadingChunker(chunk_size=500)`: mỗi heading/điều khoản là một đơn vị riêng. Nếu mục vượt giới hạn thì chia thân bằng RecursiveChunker và lặp heading trên từng mảnh; giữ heading cha khi gặp mục con. Giới hạn 500 tính cả heading, không overlap phần thân. Không gộp các mục ngang cấp chỉ để lấp đầy chunk.

Chính sách thường tổ chức theo điều kiện, thời hạn, quy trình và ngoại lệ nên heading cung cấp ngữ cảnh có ích. Hạn chế: mục dài vẫn có thể bị tách; ngoại lệ ở một heading khác có thể chưa vào top-3; lặp tiêu đề làm tăng số ký tự. Không được kết luận giữ đủ ngữ cảnh chỉ dựa vào tên chiến lược.

### compute_similarity và Comparator

Cosine kiểm tra cùng số chiều và xử lý vector 0; chuẩn hóa khi tính và chặn sai số ngoài [-1,1]. Comparator trả số chunk, độ dài trung bình và nội dung của FixedSize, Sentence, Recursive; đầu vào rỗng có count=0, avg_length=0. FixedSizeChunker của giảng viên được giữ nguyên.

### EmbeddingStore

Chọn in-memory. Mỗi chunk có ID bản ghi riêng, content, embedding và bản sao metadata; metadata.doc_id giữ tài liệu cha. Search tính dot product rồi lấy top-k giảm dần. Embedding local được chuẩn hóa nên dot product tương đương cosine. Bộ lọc so khớp metadata trước khi xếp hạng; delete_document xóa mọi chunk có cùng doc_id, trả False nếu không có. Kho không lưu bền sau khi tiến trình kết thúc.

### KnowledgeBaseAgent và backend thật

Agent nhận câu hỏi, lấy top-3 với filter tương ứng, ghép context đánh số nguồn, tạo prompt và gọi hàm LLM. Prompt yêu cầu trả lời theo context, dẫn nguồn, thừa nhận thiếu bằng chứng và không tự đặt thời hạn/ngoại lệ. Có prompt chưa bảo đảm đáp án đúng; vẫn phải đối chiếu với gold.

Cấu hình cuối: Groq `openai/gpt-oss-20b` sinh câu trả lời; embedding local `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Không dùng key Groq cho embedding Gemini, không fallback về mock. Metadata front matter được tách khỏi nội dung trước khi chunk.

## 3. Kết quả code

'''
    text += f'''Log đầy đủ: [test_results.txt](test_results.txt).

```text
python -m pytest tests/ -v -p no:cacheprovider
Python 3.13.3
{test_summary}
```

**42/42 test gốc đạt**, cộng **11 test bổ sung** cho heading, xử lý Gemini/Groq, loader và benchmark. Test adapter dùng phản hồi giả để kiểm tra logic; kết quả API thật được ghi riêng ở mục 5. Chưa kiểm tra trên Python 3.11 chuẩn lab.

## 4. Dự đoán similarity

Giữ nguyên 5 dự đoán đã lưu trước khi chạy tại [similarity_predictions.json](similarity_predictions.json). Dự đoán ban đầu được chuẩn bị trong phiên hỗ trợ, không thay bằng dự đoán mới sau khi thấy score.

'''
    if similarity:
        result_file = 'similarity_local_results.json' if semantic_available else 'similarity_results.json'
        text += f"Backend thực chạy: `{similarity['backend']}`. Kết quả đầy đủ: [{result_file}]({result_file}).\n\n"
        if not semantic_available:
            text += '**Đây là số liệu MockEmbedder đã chạy trước đó**, không phải embedding ngữ nghĩa. Thư viện embedding local đã cài, nhưng trọng số Hugging Face chưa tải hoàn tất nên chưa có số liệu local để thay thế.\n\n'
        text += '| Cặp | Câu A | Câu B | Dự đoán | Cosine thực tế |\n|---|---|---|---|---:|\n'
        for i, row in enumerate(similarity['results'], 1):
            text += f"| {i} | {cell(row['a'])} | {cell(row['b'])} | {row['prediction']} | {row['score']:.6f} |\n"
        text += '\nSo sánh trực tiếp các cặp gần nghĩa (2, 3) với khác chủ đề (4, 5); không đặt ngưỡng đúng/sai sau khi nhìn số liệu. Cặp giống hệt (1) là kiểm tra nhất quán, không chứng minh mô hình hiểu chính sách. Điểm similarity đo liên hệ ngữ nghĩa, không xác nhận một điều khoản đúng hay đang còn hiệu lực. Kết quả mock cũ trong similarity_results.json chỉ dùng làm lịch sử kiểm tra kỹ thuật.\n'
        if not semantic_available:
            text += '\n**Phản ngẫm trên số liệu mock:** cặp 1 đạt 1.0 vì cùng chuỗi; cặp 2 và 3 gần nghĩa nhưng chỉ đạt khoảng 0.09 và 0.15, không khớp dự đoán cao. Cặp 4 và 5 có điểm thấp đúng hướng dự đoán, nhưng đó không chứng minh hiểu ngữ nghĩa vì mock sinh vector từ hash. Không dùng mock để kết luận chiến lược nào tốt hơn.\n'
    else:
        text += 'Chưa có kết quả embedding local. Không dùng kết quả mock cũ để kết luận ngữ nghĩa; giữ nguyên dự đoán và chờ chạy scripts/run_similarity_local.py.\n'
    text += '\n## 5. Kết quả truy xuất của Việt\n\n'
    if benchmark:
        text += f"Lượt chạy: `{benchmark['executed_at']}`. **5 tài liệu, {benchmark['chunk_count']} chunk**, top-k=3; embedding `{benchmark['embedding_model']}`, LLM `{benchmark['llm_model']}` qua Groq.\n\n"
        text += 'Bằng chứng đầy đủ: [benchmark_viet_heading.json](benchmark_viet_heading.json) và [đầu ra agent](benchmark_viet_heading.md).\n\n'
        text += '| # | Câu hỏi | Top-1 chunk | Score | Đánh giá liên quan | Câu trả lời agent (nguyên văn) |\n|---|---|---|---:|---|---|\n'
        for row in benchmark['results']:
            top = row['top3'][0] if row['top3'] else None
            text += f"| {row['id']} | {cell(row['query'])} | {cell(top['id']) if top else 'Không có'} | {top['score'] if top else 0:.6f} | {cell(row.get('relevance_review') or 'Chờ đối chiếu')} | {cell(row['agent_answer'])} |\n"
        text += '\n### Ảnh hưởng của metadata filter\n\n'
        for row in benchmark['results']:
            if row['filter']:
                before = ', '.join(hit['id'] for hit in row['unfiltered_top3'])
                after = ', '.join(hit['id'] for hit in row['top3'])
                text += f"- Câu {row['id']}, `{row['filter']}`: trước lọc `{before}`; sau lọc `{after}`.\n"
        text += '\nNếu cả có và không filter đều tìm đúng, chỉ kết luận filter loại tài liệu ngoài đối tượng; chưa chứng minh filter bắt buộc để trả lời đúng. Không sửa riêng câu hỏi của Việt để tạo kết quả đẹp hơn; mọi thay đổi benchmark phải thống nhất cả nhóm.\n'
    else:
        text += 'Benchmark thật chưa hoàn tất. Heading dry-run tạo 11 chunk; không coi dry-run là kết quả truy xuất. Key Groq mới đã truy cập được danh sách model, cấu hình hiện dùng openai/gpt-oss-20b. Thư viện local đã cài nhưng lượt tải trọng số Hugging Face không hoàn tất sau khi thử cả bộ tải chuẩn và HTTP trực tiếp; đã dừng tiến trình bị đứng và giữ file tải dở. Chưa có đáp án Groq cho 5 câu hỏi để chấm. Kết quả Recursive/mock cũ trong ket_qua_benchmark.txt không phải kết quả của chiến lược mới.\n'
    review = REPORT / 'personal_review.md'
    if review.exists():
        text += '\n' + review.read_text(encoding='utf-8') + '\n'
    text += '''
## 6. Bài học cá nhân và đối chiếu nhóm

Qua phần code, việc giữ doc_id và tách metadata khỏi content là cần thiết để xóa/lọc đúng tài liệu. Khi đọc kết quả, phải xem chính chunk chứa bằng chứng, không chỉ tên tài liệu. Thêm LLM không thay thế việc kiểm tra nguồn và điều kiện áp dụng.

Phân công: Duyên — Fixed 300/30; Na — Sentence 2 câu; Đông — Recursive 300; Việt — Heading 500. **Chưa nhận kết quả thực chạy của Duyên, Na hoặc Đông**, nên chưa thể kết luận chiến lược nào tốt hơn hoặc viết rằng đã học được một kết quả cụ thể từ demo của họ. Cần bổ sung một ví dụ thật: câu hỏi, chunk của người đó, kết quả khác với Việt và bài học rút ra. Không dùng suy đoán lý thuyết thay cho kết quả thành viên.

## 7. Chạy lại và phần còn cần nhóm bổ sung

```powershell
..\\.venv\\Scripts\\python.exe -m pytest tests/ -v -p no:cacheprovider
..\\.venv\\Scripts\\python.exe bench.py
..\\.venv\\Scripts\\python.exe scripts/run_similarity_local.py
```

Key chỉ lưu trong .env đã gitignore. Bộ câu hỏi chung có gold và bằng chứng tại data/lazada/benchmark_queries.json. Nhóm cần dùng cùng corpus, backend embedding, top-k và quy tắc filter để so sánh công bằng.

Các cột quyền sử dụng còn trống trong sources.csv và phiên bản nguồn cần được nhóm ghi nhận căn cứ riêng; xác nhận nội dung đúng chưa thay thế căn cứ quyền sử dụng. Không tự điền các mục này để vượt checker.
'''
    text += '\n' + assessment + '\n'
    # Keep the manually reviewed group-template report intact.
    draft_path = REPORT / 'REPORT_CANHAN_generated.md'
    draft_path.write_text(text, encoding='utf-8')
    print('Saved REPORT_CANHAN_generated.md; the group-template report was not overwritten.')


if __name__ == '__main__':
    main()
