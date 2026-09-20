# Hướng dẫn Checkpoint 2 — Nhóm 4 người

Mục tiêu: chuẩn bị bộ dữ liệu sạch, có nguồn và metadata để bước sau chunking và benchmark. Chuẩn chấm là [DATA_COLLECTION.md](DATA_COLLECTION.md); ràng buộc chủ đề xem [K4_VARIANT.md](../K4_VARIANT.md).

## 1. Kết quả cần có tại CP2

- 5–10 tài liệu Markdown về đổi trả, bảo hành hoặc quy định người mua/người bán trong thương mại điện tử.
- Mỗi tài liệu có đủ metadata, nội dung đã làm sạch, giữ tiêu đề/mục để thử heading chunking.
- `sources.csv` có đúng một dòng cho mỗi tài liệu.
- `audience` có ít nhất hai giá trị; nên có cả `buyer` và `seller`.
- Điền Data Inventory và Metadata Schema tại mục 1 của [REPORT_NHOM.md](../report/REPORT_NHOM.md).

Hai file trong `data/ecommerce/` lúc thiết lập hướng dẫn là dữ liệu khởi động dùng URL mẫu, chưa phải nguồn thật đủ điều kiện nộp. Không tính chúng vào corpus hoàn chỉnh nếu chưa thay bằng nội dung đã kiểm chứng.

## 2. Phân công trong 30 phút thu thập

| Người | Phần việc | Bàn giao |
|---|---|---|
| TV1 — Data Lead | Chốt một sàn/cửa hàng, gom danh sách URL, thu thập khoảng 2 tài liệu cho buyer; kiểm tra corpus cuối | Danh sách URL, file sạch, metadata và sources.csv thống nhất |
| TV2 — Benchmark Lead | Thu thập khoảng 2 tài liệu đổi trả/bảo hành; đánh dấu đoạn có thể làm đáp án | File sạch và ghi chú câu hỏi/đoạn nguồn |
| TV3 — Strategy Lead | Thu thập khoảng 2 tài liệu cho seller; giữ rõ heading và điều khoản | File sạch, kiểm tra cấu trúc heading và phân biệt audience |
| TV4 — Report & Demo Lead | Thu thập khoảng 2 tài liệu bổ sung không trùng; gom thông tin mục 1 báo cáo | File sạch, bảng Data Inventory và Metadata Schema |

Mốc gợi ý: 5 phút chốt nguồn → 15 phút lấy và làm sạch → 5 phút gom dữ liệu → 5 phút kiểm tra và điền báo cáo. Nếu thiếu thời gian, ưu tiên 5 tài liệu chất lượng. Mỗi người vẫn tự code và chạy benchmark ở giai đoạn sau.

## 3. Mở terminal PowerShell và chuẩn bị

Chạy các lệnh từ thư mục gốc repo (nơi có `README.md` và `scripts/`):

```powershell
Set-Location D:\AI_thuc_chien\lab_07\K4-DAY07-Bui-Quoc-Viet-2A202602884
python --version
```

Python 3.11 là chuẩn lab. Nếu `python` không trỏ tới môi trường đã cài, có thể thay bằng `..\.venv\Scripts\python.exe` sau khi kiểm tra phiên bản.

Tạo danh sách URL riêng cho CP2, không ghi đè nếu đã có:

```powershell
if (-not (Test-Path data/urls-cp2.csv)) {
    Copy-Item scripts/urls.example.csv data/urls-cp2.csv
}
```

Mở `data/urls-cp2.csv`, xóa dòng URL ví dụ và điền 5–10 URL nguồn thật. Giữ header:

```csv
url,doc_id,title,audience,category,language,document_version,license_or_permission
```

Quy ước: `doc_id` duy nhất, chữ thường không dấu nối bằng dấu gạch ngang; `audience` là `buyer`, `seller` hoặc `both`; `category` mô tả nhóm chính sách; `language` theo ngôn ngữ nguồn. Nếu nguồn không nêu phiên bản thì dùng `not-stated`. Ghi căn cứ sử dụng thật trong `license_or_permission`; nhãn `public-source` không thay thế việc kiểm tra quyền sử dụng.

## 4. Thu thập và làm sạch

Đọc điều khoản sử dụng và robots.txt trước khi crawl. Chỉ lấy nội dung công khai được phép dùng. Chọn thư mục riêng `data/ecommerce-cp2` để không lẫn dữ liệu mẫu:

```powershell
python scripts/fetch_public_pages.py data/urls-cp2.csv --output-dir data/ecommerce-cp2
```

Chỉ TV1 chạy lượt gom cuối để tránh nhiều người cùng ghi vào một `sources.csv`. Crawler kiểm tra robots.txt, giãn cách request tối thiểu 1 giây và tạo file Markdown cùng CSV.

- Bị robots.txt chặn: đổi nguồn, không tìm cách vượt chặn.
- Trang dùng JavaScript trả nội dung quá ngắn: đổi nguồn.
- `LookupError: unknown encoding`: bỏ URL lỗi khỏi danh sách, chạy tiếp và xử lý nguồn đó riêng sau.
- Xóa menu, banner, footer lặp lại và danh sách sản phẩm không liên quan; giữ nguyên điều kiện, ngoại lệ, thời hạn, con số, heading và bảng cần thiết.
- Đọc đối chiếu với nguồn, không tự dịch hoặc thêm thông tin.
- Làm sạch sau lượt crawl cuối: chạy crawler lại có thể ghi đè file đã sửa.

Nếu trang gộp quy định buyer/seller, tách thành các file có `doc_id` riêng và cùng `source_url`, mỗi file giữ phần nội dung đúng đối tượng. Cập nhật `sources.csv` cho từng file mới, bỏ bản gộp khỏi corpus nếu đã thay thế hoàn toàn.

## 5. Kiểm tra metadata và CSV

Ví dụ cấu trúc dưới đây chỉ để tham khảo, phải thay chỗ giữ chỗ bằng thông tin thật:

```yaml
---
doc_id: buyer-return-policy
title: Chính sách đổi trả dành cho người mua
source_url: "URL_NGUON_THAT"
retrieved_at: "YYYY-MM-DD"
document_version: "not-stated"
audience: buyer
category: returns-policy
language: vi
---
```

Tên file tương ứng là `buyer-return-policy.md`. Nội dung chính sách đã làm sạch nằm dưới dấu `---` thứ hai. `retrieved_at` là ngày thực tế lấy dữ liệu.

Header của `sources.csv`:

```csv
doc_id,file_path,title,source_url,retrieved_at,document_version,license_or_permission
```

`file_path` tính từ thư mục gốc repo, ví dụ `data/ecommerce-cp2/buyer-return-policy.md`. Mỗi file một dòng, thông tin phải khớp metadata. Nếu trường có dấu phẩy, bọc giá trị trong dấu ngoặc kép. Lưu file bằng UTF-8.

Chạy công cụ kiểm tra đã chuẩn bị:

```powershell
python scripts/check_checkpoint2.py data/ecommerce-cp2
```

Sửa các dòng `FAIL` rồi chạy lại cho đến khi `Structural errors: 0`. Công cụ chỉ hỗ trợ metadata phẳng, mỗi trường một dòng như crawler mẫu; không cần cài thêm thư viện. Nó không truy cập mạng, không xác minh tính đúng của chính sách hay quyền sử dụng, và không tự sửa dữ liệu.

## 6. Điền mục 1 báo cáo nhóm

TV4 điền theo bộ dữ liệu thực tế:

- **Chủ đề và lý do chọn:** tên sàn/cửa hàng, phạm vi chính sách và lý do phù hợp với câu hỏi của nhóm.
- **Data Inventory:** mỗi file một hàng gồm tên, URL, ngày lấy/phiên bản, số ký tự nội dung sau front matter và metadata đã gán. Thêm hàng nếu có hơn 5 file.
- **Metadata Schema:** ghi đủ các trường đang dùng, kiểu dữ liệu, ví dụ thật và công dụng. `audience` giúp phân biệt đối tượng; `category` giúp lọc loại chính sách; `source_url` giúp đối chiếu nguồn; `document_version` giúp nhận diện phiên bản.
- Chỉ đánh dấu checklist quản trị dữ liệu sau khi đã kiểm tra thật.

## 7. Checklist chốt CP2

- [ ] Có 5–10 tài liệu thật, không còn URL/nội dung mẫu trong corpus nộp.
- [ ] Công cụ kiểm tra báo `Structural errors: 0`.
- [ ] Mỗi người đã đọc và đối chiếu phần tài liệu mình phụ trách.
- [ ] Nguồn truy cập được, được phép dùng, không có dữ liệu cá nhân/nội bộ.
- [ ] Đã bỏ nội dung thừa, giữ đủ điều kiện, ngoại lệ, thời hạn và heading.
- [ ] Mục 1 báo cáo có Data Inventory và Metadata Schema thực tế.
- [ ] Cả nhóm thống nhất dùng cùng phiên bản corpus trước khi chunking.

Chuẩn bị tiếp trước benchmark/CP5: thống nhất đúng 5 câu hỏi có đáp án trích từ corpus, trong đó ít nhất một câu cần `metadata_filter={"audience": "buyer"}` hoặc `seller`. Thử có/không có filter để ghi nhận tác dụng thật, không chỉ gán metadata hình thức.
