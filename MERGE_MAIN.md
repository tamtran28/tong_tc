# Hướng dẫn merge nhánh `work` vào `main`

Các bước bên dưới giúp hợp nhất thay đổi hiện tại vào nhánh `main` một cách an toàn.

1. Cập nhật remote và lấy nhánh `main` mới nhất (nếu có):
   ```bash
   git fetch origin
   git checkout main || git checkout -b main origin/main
   git pull
   ```

2. Merge nhánh làm việc vào `main`:
   ```bash
   git merge work
   ```
   - Nếu xảy ra conflict, mở từng file, tìm các đoạn `<<<<<<<` / `>>>>>>>` và chỉnh sửa lại nội dung mong muốn.
   - Sau khi sửa conflict, chạy `git add <file>` cho từng file đã chỉnh.

3. Kiểm tra nhanh trước khi push:
   ```bash
   python -m compileall module app.py db
   ```
   Đảm bảo lệnh chạy không báo lỗi cú pháp.

4. Đẩy kết quả lên remote:
   ```bash
   git push origin main
   ```

5. (Tuỳ chọn) Tạo Pull Request từ `main` nếu quy trình yêu cầu review.

Lưu ý: luôn đảm bảo bạn đang ở đúng repository/remote trước khi merge và push.
