# Phòng trống BK

Web tĩnh cho biết phòng học nào đang có lớp, phòng nào trống, dựa trên file thời khóa biểu HUST.

## Cấu trúc

- `TKB*.xlsx`: file TKB gốc, là nguồn dữ liệu duy nhất. Dùng thẳng file xlsx, không chuyển qua CSV.
- `build_data.py`: đọc TKB (.xlsx, hoặc .csv) rồi ghi ra `data.js` (`window.TKB = {rooms, sessions}`). Chỉ dùng stdlib, không cần cài gì.
- `data.js`: file sinh ra, **không sửa tay**.
- `index.html`: toàn bộ UI (HTML, CSS và JS nằm chung một file, không build step). Mở trực tiếp bằng `file://` hoặc đưa lên GitHub Pages đều chạy.

## Cập nhật TKB

```sh
python3 build_data.py "TKB20261-FULL.xlsx"   # không truyền tham số thì lấy file TKB* mới nhất
```

Sang kỳ mới thì sửa 2 hằng số đầu `<script>` trong `index.html`: `WEEK1` (thứ Hai của tuần 1) và `SOURCE`.

## Dữ liệu TKB: những điểm cần biết

- Cột theo chỉ số (0-based): 2 Mã lớp, 4 Mã HP, 5 Tên HP, 10 Thứ (2–7, 8 = CN), 11 Thời gian `HHMM-HHMM`, 15 Tuần, 16 Phòng, 20 Trạng thái, 21 Loại lớp.
- Chỉ lấy dòng có cột 0 là số, tức là bỏ 2 dòng tiêu đề và dòng header.
- Tuần viết không thống nhất, ví dụ `2-9,11-18`, `15.17`, `4, 6, 13`, `4,7,11,13,`. Vì vậy `weeks()` parse bằng regex. Trong `data.js`, tuần được lưu thành bitmask (`1 << tuần`).
- Bỏ các lớp có trạng thái "Huỷ lớp" và các dòng có giá trị `NULL`.
- Chỉ tính phòng học khớp `ROOM_RE`, tức dạng `<tòa>-<số>` như D9-102, C7-E303, C10B-205, NhaT-KT-205, GĐ-B1. Sân, SVĐ, bể bơi, Online, `TTB4` và phòng không có số đều bị loại. Muốn xem danh sách phòng bị loại thì in các giá trị cột 16 không khớp regex. Tòa được lấy từ phần đứng trước dấu `-` cuối cùng.
- Script đọc được `.xlsx` bằng stdlib (`read_xlsx`, dò theo tham chiếu ô vì các ô trống bị bỏ qua). Nên ưu tiên file này.
- CSV hiện tại xuất ra Windows-1252 nên đã mất dấu tiếng Việt (có ký tự `?` thật ở trong file, không khôi phục được). Script thử UTF-8 trước, không được thì fallback sang cp1252. Khi tên có `?`, `name()` dùng tên tiếng Anh (cột 6) thay thế.
- Số tuần là tuần của năm học (kỳ 1: 2–18, kỳ hè: 45–49), được lưu thành bitmask và có thể vượt 2^31. Trong JS phải dùng `inWeek()`, không dùng `&`.

## Kiểm tra

- `python3 build_data.py` chạy các `assert` của `weeks()` / `minutes()` trước khi build.
- Kiểm tra tay: D9-102, thứ 2 tuần 2, 10:00 phải đang học AC2010 đến 11:45. Cùng giờ đó ở tuần 10 (tuần nghỉ) thì phải trống.

## UI

Thiết kế theo skill Hallmark: genre modern-minimal, theme Cobalt, macrostructure Catalogue. Stamp nằm đầu `<style>`.
- Màu và font chỉ dùng token trong `:root`, không hard-code giá trị. Dark mode khai báo lại các token màu ở hai chỗ, `@media (prefers-color-scheme: dark)` và `:root[data-theme="dark"]`, nên khi thêm token màu mới phải thêm vào cả 3 khối. Theme người dùng chọn được lưu trong `localStorage.theme`.
- Font: Space Grotesk (tiêu đề), Inter (nội dung), JetBrains Mono (mã phòng, nhãn).
- Accent cobalt chỉ dùng cho trạng thái "Trống" và focus ring. Trạng thái luôn có chữ đi kèm, không để màu tự báo nghĩa.
- Bố cục phải chạy được ở độ rộng 320px, không có scroll ngang.
