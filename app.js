let rawRows = [];
let dataByDayAndWeek = {};

window.addEventListener("DOMContentLoaded", () => {
  const xhr = new XMLHttpRequest();
  xhr.open("GET", "tkb.xlsx", true);
  xhr.responseType = "arraybuffer";

  xhr.onload = function () {
    const data = new Uint8Array(xhr.response);
    const workbook = XLSX.read(data, { type: "array" });
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const raw = XLSX.utils.sheet_to_json(sheet, { header: 1 });
    const headers = raw[2];

    rawRows = XLSX.utils.sheet_to_json(sheet, {
      header: headers,
      range: 3
    }).map(row => {
      const needed = {};
      ["Phòng", "Thời_gian", "Thứ", "Tuần", "Tên_HP"].forEach(k => needed[k] = row[k]);
      return needed;
    });

    window.allRoomsSet = new Set();
    rawRows.forEach(r => {
      if (r["Phòng"]) window.allRoomsSet.add(r["Phòng"]);
    });

    indexData(rawRows);

    document.getElementById("status").textContent = "Dữ liệu đã sẵn sàng!";
    updateRooms();
    setInterval(updateRooms, 60000);
  };

  xhr.send();
});

function parseTimeString(str) {
  if (!str || typeof str !== "string") return [null, null];
  const match = str.match(/(\d{3,4})-(\d{3,4})/);
  if (!match) return [null, null];
  const start = parseInt(match[1]);
  const end = parseInt(match[2]);
  return [convertToMinutes(start), convertToMinutes(end)];
}

function convertToMinutes(timeInt) {
  const h = Math.floor(timeInt / 100);
  const m = timeInt % 100;
  return h * 60 + m;
}

function getCurrentTimeInMinutes() {
  const now = new Date();
  return now.getHours() * 60 + now.getMinutes();
}

function getCurrentWeek() {
  const start = new Date("2025-06-23");
  const now = new Date();
  const diff = Math.floor((now - start) / (1000 * 60 * 60 * 24));
  return Math.floor(diff / 7) + 1;
}

function indexData(rows) {
  dataByDayAndWeek = {};
  for (let row of rows) {
    const thu = Number(row["Thứ"]);
    const tuanStr = String(row["Tuần"] || "");
    if (!thu || !tuanStr) continue;

    const tuans = tuanStr.split(/[^0-9]+/).filter(Boolean).map(Number);
    for (let tuan of tuans) {
      if (!dataByDayAndWeek[thu]) dataByDayAndWeek[thu] = {};
      if (!dataByDayAndWeek[thu][tuan]) dataByDayAndWeek[thu][tuan] = [];
      dataByDayAndWeek[thu][tuan].push(row);
    }
  }
}

function getCurrentClasses() {
  const nowMinutes = getCurrentTimeInMinutes();
  const jsDay = new Date().getDay();
  if (jsDay === 0) return [];
  const weekday = jsDay + 1;
  const currentWeek = getCurrentWeek();
  const result = [];

  const todayData = (dataByDayAndWeek[weekday] || {})[currentWeek] || [];

  for (let row of todayData) {
    const phong = row["Phòng"];
    const ten = row["Tên_HP"];
    const thoigian = row["Thời_gian"];
    const [startMinutes, endMinutes] = parseTimeString(thoigian);

    if (!startMinutes || !endMinutes || !phong) continue;
    if (nowMinutes >= startMinutes && nowMinutes <= endMinutes) {
      result.push(`${phong} (${ten})`);
    }
  }

  return result;
}

function getPhongTrong() {
  const nowMinutes = getCurrentTimeInMinutes();
  const jsDay = new Date().getDay();
  if (jsDay === 0) return [];
  const weekday = jsDay + 1;
  const week = getCurrentWeek();
  const todayRows = (dataByDayAndWeek[weekday] || {})[week] || [];

  const occupiedRooms = new Set();
  for (let row of todayRows) {
    const phong = row["Phòng"];
    const [bd, kt] = parseTimeString(row["Thời_gian"]);
    if (!bd || !kt || !phong) continue;
    if (nowMinutes >= bd && nowMinutes <= kt) {
      occupiedRooms.add(phong);
    }
  }

  return Array.from(window.allRoomsSet).filter(p => !occupiedRooms.has(p));
}

function updateList(id, data, emptyText) {
  const ul = document.getElementById(id);
  const current = ul.dataset.lastRender || "";
  const next = JSON.stringify(data);

  if (current !== next) {
    ul.innerHTML = data.length === 0
      ? `<li><em>${emptyText}</em></li>`
      : data.map(r => `<li>${r}</li>`).join("");
    ul.dataset.lastRender = next;
  }
}

function updateRooms() {
  const oc = getCurrentClasses().slice(0, 100);
  const av = getPhongTrong().slice(0, 100);

  updateList("occupied", oc, "Không có lớp học");
  updateList("available", av, "Không có phòng trống");
}
