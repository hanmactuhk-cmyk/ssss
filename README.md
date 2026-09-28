# G-Labs Flow Automation v4

Tool Windows desktop quản lý nhiều Chrome profile đã đăng nhập Google và chạy hàng đợi Flow Image/Video.

## Chức năng
- Quản lý tối đa nhiều Chrome profile/tài khoản Google; đăng nhập một lần trong từng profile.
- Flow Video: prompt, ảnh đầu/cuối, tỉ lệ, model, thời lượng, hàng chờ, chạy/dừng/tạm dừng.
- Flow Ảnh: prompt, tỉ lệ, model, hàng chờ.
- Nhân vật: thư viện ảnh tham chiếu.
- Workflow: lưu JSON workflow.
- Dựng Video: ghép video bằng ffmpeg nếu có.
- Nâng cấp ảnh: mở công cụ/đường dẫn xử lý ngoài; không giả mạo upscale nếu chưa có engine.
- Log và Cài đặt.
- Có tab Webhook API tùy chọn, nhưng đường chính là Browser/Chrome profile.

## Cài đặt
1. Cài Python 3.11+.
2. `pip install -r requirements.txt`
3. `python -m playwright install chromium`
4. `python -m app.main`

## Đóng gói EXE
Chạy `build.bat`. EXE nằm trong `dist`.

## Đăng nhập
Trong Tài khoản Flow, chọn **Thêm tài khoản**, đặt tên profile, sau đó tool mở Chromium profile riêng. Tự đăng nhập Google trong cửa sổ đó. Tool không yêu cầu và không lưu mật khẩu Gmail.

## Lưu ý về Google Flow
Giao diện Google Flow có thể thay đổi. Bộ điều khiển dùng nhiều locator dự phòng và có file `data/flow_selectors.json` để chỉnh selector nếu giao diện thay đổi. Không có cơ chế vượt CAPTCHA, giới hạn, hoặc quota; khi Flow yêu cầu xác minh/đăng nhập lại, task sẽ dừng và ghi log.
