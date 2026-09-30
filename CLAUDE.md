# Phòng trống BK

Web tĩnh cho biết phòng học nào đang có lớp, phòng nào trống, dựa trên file thời khóa biểu HUST.

## Cấu trúc

- `TKB*.csv`: file TKB xuất từ Excel, là nguồn dữ liệu duy nhất.
- `build_data.py`: đọc CSV rồi ghi ra `data.js` (`window.TKB = {rooms, sessions}`). Chỉ dùng stdlib, không cần cài gì.
- `data.js`: file sinh ra, **không sửa tay**.
- `index.html`: toàn bộ UI (HTML, CSS và JS nằm chung một file, không build step). Mở trực tiếp bằng `file://` hoặc đưa lên GitHub Pages đều chạy.

## Cập nhật TKB

```sh
python3 build_data.py "TKB20261-FULL.csv"   # không truyền tham số thì lấy TKB*.csv đầu tiên
```

Sang kỳ mới thì sửa 2 hằng số đầu `<script>` trong `index.html`: `WEEK1` (thứ Hai của tuần 1) và `SOURCE`.

## Dữ liệu CSV: những điểm cần biết

- Cột theo chỉ số (0-based): 2 Mã lớp, 4 Mã HP, 5 Tên HP, 10 Thứ (2–7, 8 = CN), 11 Thời gian `HHMM-HHMM`, 15 Tuần, 16 Phòng, 20 Trạng thái, 21 Loại lớp.
- Chỉ lấy dòng có cột 0 là số, tức là bỏ 2 dòng tiêu đề và dòng header.
- Tuần viết không thống nhất, ví dụ `2-9,11-18`, `15.17`, `4, 6, 13`, `4,7,11,13,`. Vì vậy `weeks()` parse bằng regex. Trong `data.js`, tuần được lưu thành bitmask (`1 << tuần`).
- Bỏ các lớp có trạng thái "Huỷ lớp" và các dòng có giá trị `NULL`.
- Chỉ tính phòng học khớp `ROOM_RE` (D9-102, D3-5-301, TC-301, …). Sân, SVD, bể bơi, xưởng như `TTB4` đều bị loại. Tòa được lấy từ phần đứng trước dấu `-` cuối cùng.
- File hiện tại xuất ra Windows-1252 nên đã mất dấu tiếng Việt (có ký tự `?` thật ở trong file). Script thử UTF-8 trước, không được thì fallback sang cp1252. Muốn sửa tên môn bị lỗi dấu thì phải xuất lại CSV ở dạng UTF-8.

## Kiểm tra

- `python3 build_data.py` chạy các `assert` của `weeks()` / `minutes()` trước khi build.
- Kiểm tra tay: D9-102, thứ 2 tuần 2, 10:00 phải đang học AC2010 đến 11:45. Cùng giờ đó ở tuần 10 (tuần nghỉ) thì phải trống.

## UI

Thiết kế theo skill Hallmark: genre modern-minimal, theme Cobalt, macrostructure Catalogue. Stamp nằm đầu `<style>`.
- Màu và font chỉ dùng token trong `:root`, không hard-code giá trị. Dark mode khai báo lại các token màu ở hai chỗ, `@media (prefers-color-scheme: dark)` và `:root[data-theme="dark"]`, nên khi thêm token màu mới phải thêm vào cả 3 khối. Theme người dùng chọn được lưu trong `localStorage.theme`.
- Font: Space Grotesk (tiêu đề), Inter (nội dung), JetBrains Mono (mã phòng, nhãn).
- Accent cobalt chỉ dùng cho trạng thái "Trống" và focus ring. Trạng thái luôn có chữ đi kèm, không để màu tự báo nghĩa.
- Bố cục phải chạy được ở độ rộng 320px, không có scroll ngang.
