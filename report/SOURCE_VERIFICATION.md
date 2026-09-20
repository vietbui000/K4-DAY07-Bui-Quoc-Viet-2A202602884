# Kiểm tra nguồn Lazada — 2026-09-20

> **C?p nh?t:** Vi?t ?? x?c nh?n ngu?n l? ??ng. ?? ?i?n 5 gold answer b?ng ?o?n tr?ch trong corpus, ghi tr?ng th?i `user_confirmed_source`; ??y l? x?c nh?n c?a ng??i d?ng, kh?ng ph?i x?c minh ??c l?p c?a tr? l?. C?c ghi ch? ch?a x?c minh ph?a d??i l? l?ch s? tr??c x?c nh?n. C?n c? quy?n s? d?ng v? phi?n b?n ch?a ???c x?c nh?n ri?ng.


**Kết luận: chưa xác minh được nội dung của cả 5 nguồn. Chưa chốt gold answer.** Không truy cập được qua công cụ không đồng nghĩa trang không tồn tại hoặc nội dung chắc chắn sai.

| Tài liệu | URL đã thử mở | Những khẳng định cần bằng chứng | Kết quả |
|---|---|---|---|
| lazada-buyer-return | https://www.lazada.vn/helpcenter/chinh-sach-tra-hang-hoan-tien-lazada.html | 30/7 ngày trả hàng; 3–5 và 7–14 ngày hoàn tiền; phiên bản 3.0 | Công cụ không lấy được nội dung |
| lazada-buyer-protection-claim | https://www.lazada.vn/helpcenter/cam-ket-hang-chinh-hang-lazmall.html | Đền 200%; 14 ngày khiếu nại; phản hồi 48 giờ; phiên bản 2.0 | Công cụ không lấy được nội dung |
| lazada-electronic-warranty | https://www.lazada.vn/helpcenter/huong-dan-bao-hanh-san-pham.html | Hình thức bảo hành, ngoại lệ; phiên bản 1.5 | Công cụ không lấy được nội dung |
| lazada-seller-return-process | https://university.lazada.vn/course/view.htm?id=1204 | 7–10 ngày; hạn khiếu nại 3 ngày; bồi thường 100%; phiên bản 2.1 | Công cụ không lấy được nội dung |
| lazada-seller-fee-and-claim | https://university.lazada.vn/course/view.htm?id=3055 | Phí 3.973%, 2–8%; tự động bồi thường; phiên bản 4.0 | Công cụ không lấy được nội dung |

Đã mở [trang chính sách và quy tắc bán hàng](https://www.lazada.vn/chinh-sach-va-quy-tac-ban-hang). Nội dung nhận được chủ yếu là menu, không đủ đối chiếu điều khoản. Liên kết [Returns & Refunds](https://www.lazada.vn/helpcenter/returns/) chuyển tới [Help Center](https://helpcenter.lazada.vn/s/faq), công cụ nhận 0 dòng nội dung. Tìm kiếm nguồn thay thế chưa cung cấp được bài chính thức đầy đủ để xác nhận các con số trên. Không dùng bài blog hoặc snippet tìm kiếm làm gold answer.

[robots.txt của www.lazada.vn](https://www.lazada.vn/robots.txt) đọc được, nhưng không phải bằng chứng quyền sử dụng mọi nội dung; quy tắc ở tên miền này không tự áp dụng cho university.lazada.vn.

Đã thêm file_path đúng vào sources.csv. Cột license_or_permission để trống vì chưa xác minh căn cứ sử dụng; không tự điền public-source để vượt checklist. Các phiên bản hiện giữ nguyên như thông tin nhóm cung cấp, được ghi là claimed_document_version trong source_verification.json; chưa xác nhận là phiên bản do Lazada công bố. Chỉ đổi sang not-stated sau khi đối chiếu trang nguồn và thấy không công bố phiên bản.

Để hoàn tất: cung cấp nội dung trang công khai thực tế đọc được hoặc tìm URL chính sách chính thức thay thế; đối chiếu phạm vi, điều kiện, ngoại lệ và từng con số. Lưu ngày kiểm tra, tiêu đề mục và bằng chứng. Cập nhật Markdown/CSV rồi mới thống nhất gold answer với nhóm. Không dùng dữ liệu sau đăng nhập hoặc vượt hạn chế truy cập.
