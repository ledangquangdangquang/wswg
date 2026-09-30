"""CSV thời khóa biểu -> data.js (window.TKB) cho index.html.

Chạy: python3 build_data.py [file.csv]   (mặc định: file TKB*.csv đầu tiên trong thư mục)
"""
import csv, glob, json, re, sys

ROOM_RE = re.compile(r"^[A-Z]+\d*(-\d+)*-\d+[A-Z]?$")  # D9-102, D3-5-301, TC-301, T-512, C1-419A


def weeks(s):
    """'2-9,11-18' -> [2..9, 11..18]; chịu được '15.17', '4, 6, 13', '4,7,11,13,'"""
    out = []
    for a, b in re.findall(r"(\d+)(?:\s*-\s*(\d+))?", s):
        out += range(int(a), int(b or a) + 1)
    return out


def minutes(hhmm):
    return int(hhmm[:2]) * 60 + int(hhmm[2:])


def read_rows(path):
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")  # bản xuất cũ, mất dấu
    return [r for r in csv.reader(text.splitlines()) if r and r[0].isdigit()]  # bỏ tiêu đề, dòng trống


def build(rows):
    rooms, sessions = {}, []
    for r in rows:
        if len(r) < 22:
            continue
        thu, time, wk, room, status = r[10], r[11], r[15], r[16].strip(), r[20]
        if not ROOM_RE.match(room) or "NULL" in (thu, time, wk) or status.startswith("Hu"):  # bỏ lớp Huỷ
            continue
        start, _, end = time.partition("-")
        idx = rooms.setdefault(room, len(rooms))
        sessions.append([idx, int(thu), minutes(start), minutes(end), sum(1 << w for w in set(weeks(wk))), r[4], r[5], r[21], r[2]])
    names = sorted(rooms, key=rooms.get)
    return {"rooms": names, "sessions": sessions}


if __name__ == "__main__":
    assert weeks("2-9,11-18") == [*range(2, 10), *range(11, 19)]
    assert weeks("15.17") == [15, 17] and weeks("4,7, 13,") == [4, 7, 13]
    assert minutes("0645") == 405
    path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob("TKB*.csv"))[0]
    data = build(read_rows(path))
    with open("data.js", "w", encoding="utf-8") as f:
        f.write("window.TKB=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{path}: {len(data['rooms'])} phòng, {len(data['sessions'])} buổi -> data.js")
