# Phòng trống HUST

Web tĩnh cho biết phòng học nào đang có lớp, phòng nào trống, dựa trên file thời khóa biểu HUST.

## Cấu trúc

- `TKB*.xlsx`: file TKB gốc, là nguồn dữ liệu duy nhất. Chỉ đọc .xlsx.
- `build_data.py`: đọc TKB (.xlsx) rồi ghi ra `data.js` (`window.TKB = {rooms, sessions}`). Chỉ dùng stdlib, không cần cài gì.
- `data.js`: file sinh ra, **không sửa tay**.
- `maps-hust.webp`: ảnh bản đồ trường, hiện trong popup `#map` khi bấm nút "Bản đồ" cạnh nút sáng/tối (icon mặt trời/mặt trăng). Ảnh gốc là PNG, đổi sang webp bằng `ffmpeg -i in.png -c:v libwebp -quality 80 maps-hust.webp` (máy không có cwebp).
- `index.html`: toàn bộ UI (HTML, CSS và JS nằm chung một file, không build step). Mở trực tiếp bằng `file://` hoặc đưa lên GitHub Pages đều chạy.

## Cập nhật TKB

```sh
python3 build_data.py "TKB20261-FULL.xlsx"   # không truyền tham số thì lấy file TKB* mới nhất
python3 build_data.py --week1 2027-09-06     # chỉ khi đổi năm học
```

Không còn cấu hình nào trong `index.html`. `data.js` chứa `term` và `updated` (regex bám vào số ở dòng tiêu đề) cùng `week1` (lấy từ `--week1`, không truyền thì dùng lại giá trị trong `data.js` cũ, và phải là thứ Hai). `index.html` tạo `WEEK1` và `SOURCE` từ các giá trị này. `weeks: [đầu, cuối]` là khoảng tuần có lớp. Ngoài khoảng này `render()` hiện `.notice` và không liệt kê phòng. `exam` là danh sách tuần thi, lấy từ `--exam-weeks` hoặc do `exam_weeks()` đoán (tuần có < 30% số lớp của tuần đông nhất, nằm sau tuần học đầu tiên). Tuần thi vẫn liệt kê phòng như thường nhưng thêm `.notice.exam` ở đầu danh sách. Khác với `week1`, `exam` không được giữ lại giữa các lần build.
- Đếm lượt truy cập: đặt hằng số `GOATCOUNTER` trong `index.html` (để trống thì tắt). Tổng lượt xem lấy từ `/counter/TOTAL.json` và hiện ở footer.

## Dữ liệu TKB: những điểm cần biết

- Cột được tìm theo tên ở dòng header (`COLS`, `columns()`), không theo vị trí: Mã_lớp, Mã_HP, Tên_HP, Thứ (2–7, 8 = CN), Thời_gian `HHMM-HHMM`, Tuần, Phòng, Trạng_thái, Loại_lớp. Thiếu cột nào thì script dừng và báo tên cột đó.
- Chỉ lấy dòng có Mã_lớp là số, tức là bỏ 2 dòng tiêu đề và dòng header.
- Tuần viết không thống nhất, ví dụ `2-9,11-18`, `15.17`, `4, 6, 13`, `4,7,11,13,`. Vì vậy `weeks()` parse bằng regex. Trong `data.js`, tuần được lưu thành bitmask (`1 << tuần`).
- Bỏ các lớp có trạng thái "Huỷ lớp" và các dòng có giá trị `NULL`.
- Chỉ tính phòng học khớp `ROOM_RE`, tức dạng `<tòa>-<số>` như D9-102, C7-E303, C10B-205, NhaT-KT-205, GĐ-B1. Sân, SVĐ, bể bơi, Online, `TTB4` và phòng không có số đều bị loại. Muốn xem danh sách phòng bị loại thì in các giá trị cột Phòng không khớp regex. Tòa được lấy từ phần đứng trước dấu `-` cuối cùng.
- Script đọc được `.xlsx` bằng stdlib (`read_xlsx`, dò theo tham chiếu ô vì các ô trống bị bỏ qua).
- Số tuần là tuần của năm học (kỳ 1: 2–18, kỳ hè: 45–49), được lưu thành bitmask và có thể vượt 2^31. Trong JS phải dùng `inWeek()`, không dùng `&`.

## Kiểm tra

- `python3 build_data.py` chạy các `assert` của `weeks()` / `minutes()` trước khi build.
- Kiểm tra tay: D9-102, thứ 2 tuần 2, 10:00 phải đang học AC2010 đến 11:45. Cùng giờ đó ở tuần 10 (tuần nghỉ) thì phải trống.

## UI

Thiết kế theo skill Hallmark. Genre là editorial (thiên về công cụ), macrostructure Map / Diagram, theme tự chọn với giấy ấm và vạch "bây giờ" màu đỏ son. Stamp nằm đầu `<style>`. Mỗi tòa là một khối dòng thời gian: mỗi phòng là một dòng `.row` gồm mã phòng, trạng thái và `.bar` từ 6:00 đến 22:00 (`T0`/`T1`, hàm `pct()`). Khối `.bar i` là các buổi học. `--now` (đặt trên `.rows`) quyết định vị trí vạch đỏ và phần đã qua. Trong mỗi tòa, phòng trống lâu nhất lên đầu (`rank`). Tòa có tên bắt đầu bằng số (cơ sở ngoài) xếp cuối.
- Màu và font chỉ dùng token trong `:root`, không hard-code giá trị. Dark mode khai báo lại các token màu ở hai chỗ, `@media (prefers-color-scheme: dark)` và `:root[data-theme="dark"]`, nên khi thêm token màu mới phải thêm vào cả 3 khối. Theme người dùng chọn được lưu trong `localStorage.theme`.
- Font: Be Vietnam Pro (toàn bộ chữ), JetBrains Mono (mã phòng, giờ). Không dùng nhãn mono in hoa giãn chữ.
- Accent đỏ son chỉ dùng cho vạch giờ đang xem, số phòng trống, viền thông báo và focus ring. Trạng thái luôn có chữ đi kèm, không để màu tự báo nghĩa.
- Ô "Mã học phần" (`#hp`): có nội dung thì `render()` gọi `renderCourse()` thay cho danh sách phòng. Hàm này liệt kê các lớp có mã HP (`s[5]`) bắt đầu bằng chuỗi đã gõ, không phân biệt hoa thường, tối đa 30 lớp, gom theo mã lớp (`byClass`, mã lớp là `s[8]`). Mỗi buổi hiện thứ, giờ, phòng và tuần (`weekText()` đổi bitmask thành `2-9, 11-18`). Các bộ lọc tòa, phòng và trạng thái không áp dụng khi tìm HP.
- Popup dùng `<dialog>` + `.dlg-head` chung: `#dlg` là lịch cả ngày của một phòng, `#map` là bản đồ (rộng hơn, tối đa 960px). Cả hai đóng bằng nút Đóng, Esc hoặc bấm ra ngoài.
- Bố cục phải chạy được ở độ rộng 320px, không có scroll ngang.
