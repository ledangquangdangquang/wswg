"""Thời khóa biểu (.xlsx hoặc .csv) -> data.js (window.TKB) cho index.html.

Chạy: python3 build_data.py [file.xlsx|file.csv] [--week1 YYYY-MM-DD]
  file     mặc định: file TKB* mới nhất trong thư mục
  --week1  thứ Hai của tuần 1; bỏ trống thì giữ giá trị trong data.js cũ
Kỳ và ngày cập nhật lấy tự động từ dòng tiêu đề của file.
Nên dùng .xlsx: chữ luôn là Unicode, không bị mất dấu như CSV xuất sai encoding.
"""
import argparse, csv, datetime, glob, json, os, re, zipfile
import xml.etree.ElementTree as ET

# Phòng học = <tòa>-<số phòng>: D9-102, D3-5-301, C7-E303, C10B-205, NhaT-KT-205, GĐ-B1, Nha A-101.
# Không khớp (bị loại): NULL, Online, SVD/SVĐ 1, SanB13, San KTX, Sân Pickleball, NTD, TTB4, D2B.
ROOM_RE = re.compile(r"^[\w ]+(-[\w ]+)*-[A-Z]*\d+[A-Z]?$")


def weeks(s):
    """'2-9,11-18' -> [2..9, 11..18]; chịu được '15.17', '4, 6, 13', '4,7,11,13,'"""
    out = []
    for a, b in re.findall(r"(\d+)(?:\s*-\s*(\d+))?", s):
        out += range(int(a), int(b or a) + 1)
    return out


def minutes(hhmm):
    return int(hhmm[:2]) * 60 + int(hhmm[2:])


def read_xlsx(path):
    """Sheet đầu tiên của .xlsx -> list các dòng (chỉ dùng stdlib)."""
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        shared = ["".join(t.text or "" for t in si.iter(M + "t")) for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
    sheet = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
    rows = []
    for row in ET.fromstring(z.read(sheet)).iter(M + "row"):
        vals = {}
        for c in row.findall(M + "c"):
            col = 0
            for ch in re.match(r"[A-Z]+", c.get("r")).group():  # ô trống bị bỏ qua nên phải theo tên cột
                col = col * 26 + ord(ch) - 64
            v = c.find(M + "v")
            if c.get("t") == "s":
                vals[col - 1] = shared[int(v.text)]
            elif c.get("t") == "inlineStr":
                vals[col - 1] = "".join(t.text or "" for t in c.iter(M + "t"))
            elif v is not None:
                vals[col - 1] = v.text.removesuffix(".0")
        rows.append([vals.get(i, "") for i in range(max(vals, default=-1) + 1)])
    return rows


def read_table(path):
    """Mọi dòng của file (cả tiêu đề)."""
    if path.lower().endswith(".xlsx"):
        return read_xlsx(path)
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")  # bản xuất cũ, mất dấu
    return list(csv.reader(text.splitlines()))


def title_info(table):
    """'THỜI KHÓA BIỂU KỲ 20261 - CẬP NHẬT NGÀY 11.09.2026' -> ('20261', '11.09.2026').
    Chỉ bám vào số nên vẫn đọc được tiêu đề CSV mất dấu."""
    title = next((r[0] for r in table if r and r[0].strip()), "")
    m = re.search(r"(\d{5})\D+?(\d{1,2}\.\d{1,2}\.\d{4})", title)
    if not m:
        raise SystemExit(f"Không đọc được kỳ / ngày cập nhật từ dòng tiêu đề: {title!r}")
    return m.groups()


def old_week1(path="data.js"):
    try:
        return json.loads(open(path, encoding="utf-8").read()[len("window.TKB="):-2]).get("week1")
    except (OSError, ValueError):
        return None


def name(r):
    """Tên HP; nếu đã mất dấu (CSV xuất sai encoding) thì dùng tên tiếng Anh."""
    vi = r[5]
    return r[6] if ("?" in vi or "\ufffd" in vi) and r[6] else vi


def build(rows):
    rooms, sessions = {}, []
    for r in rows:
        if len(r) < 22 or not r[0].isdigit():  # bỏ tiêu đề, header, dòng trống
            continue
        thu, time, wk, room, status = r[10], r[11], r[15], r[16].strip(), r[20]
        if not ROOM_RE.match(room) or "NULL" in (thu, time, wk) or status.startswith("Hu"):  # bỏ lớp Huỷ
            continue
        start, _, end = time.partition("-")
        idx = rooms.setdefault(room, len(rooms))
        sessions.append([idx, int(thu), minutes(start), minutes(end), sum(1 << w for w in set(weeks(wk))), r[4], name(r), r[21], r[2]])
    names = sorted(rooms, key=rooms.get)
    mask = 0
    for s in sessions:
        mask |= s[4]
    weeks_range = [(mask & -mask).bit_length() - 1, mask.bit_length() - 1]  # tuần đầu / cuối có lớp
    return {"weeks": weeks_range, "rooms": names, "sessions": sessions}


if __name__ == "__main__":
    assert weeks("2-9,11-18") == [*range(2, 10), *range(11, 19)]
    assert weeks("15.17") == [15, 17] and weeks("4,7, 13,") == [4, 7, 13]
    assert minutes("0645") == 405
    assert all(ROOM_RE.match(r) for r in ["D9-102", "D3-5-301", "C7-E303", "C10B-205", "NhaT-KT-205", "GĐ-B1"])
    assert not any(ROOM_RE.match(r) for r in ["NULL", "Online", "SVĐ 1", "SanB13", "San KTX", "TTB4", "D2B"])
    assert title_info([[""], ["THỜI KHÓA BIỂU KỲ 20261 - CẬP NHẬT NGÀY 11.09.2026"]]) == ("20261", "11.09.2026")
    assert title_info([["TH?I KH\ufffdA BI?U K? 20261 - C?P NH?T NG\ufffdY 1.9.2026"]]) == ("20261", "1.9.2026")

    ap = argparse.ArgumentParser(description="Thời khóa biểu -> data.js")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--week1", help="thứ Hai của tuần 1, dạng YYYY-MM-DD")
    args = ap.parse_args()
    path = args.file or max(glob.glob("TKB*.xlsx") + glob.glob("TKB*.csv"), key=os.path.getmtime)

    week1 = args.week1 or old_week1()
    if not week1:
        raise SystemExit("Chưa có ngày tuần 1: chạy lại với --week1 YYYY-MM-DD")
    if datetime.date.fromisoformat(week1).weekday() != 0:
        raise SystemExit(f"--week1 {week1} không phải thứ Hai")

    table = read_table(path)
    term, updated = title_info(table)
    data = {"term": term, "updated": updated, "week1": week1, **build(table)}
    with open("data.js", "w", encoding="utf-8") as f:
        f.write("window.TKB=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{path}: kỳ {term}, cập nhật {updated}, tuần 1 = {week1}, có lớp tuần {data['weeks'][0]}–{data['weeks'][1]}")
    print(f"{len(data['rooms'])} phòng, {len(data['sessions'])} buổi -> data.js")
