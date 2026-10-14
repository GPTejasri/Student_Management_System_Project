let gradeChart, marksChart;
const $ = (id) => document.getElementById(id);

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function safe(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  })[c]);
}
async function refresh() {
  const q = $("search").value.trim();
  const [students, report] = await Promise.all([
    api("/api/students?q=" + encodeURIComponent(q)),
    api("/api/report")
  ]);
  $("total").textContent = report.total_students;
  $("avgMarks").textContent = report.average_marks + "/100";
  $("avgAttendance").textContent = report.average_attendance + "%";
  $("empty").style.display = students.length ? "none" : "block";
  $("studentsBody").innerHTML = students.map(s => `
    <tr>
      <td>${safe(s.roll_no)}</td><td>${safe(s.name)}</td><td>${safe(s.department)}</td>
      <td>${s.marks}</td><td><span class="grade">${safe(s.grade)}</span></td>
      <td>${s.attendance_percentage}% (${s.attendance_present}/${s.attendance_total})</td>
      <td><button class="delete" onclick="deleteStudent(${s.id})">Delete</button></td>
    </tr>`).join("");
  drawCharts(report.students, report.grade_counts);
}
function drawCharts(students, grades) {
  if (gradeChart) gradeChart.destroy();
  if (marksChart) marksChart.destroy();
  gradeChart = new Chart($("gradeChart"), {
    type: "doughnut",
    data: { labels: Object.keys(grades), datasets: [{ data: Object.values(grades) }] },
    options: { responsive: true, plugins: { legend: { position: "bottom" } } }
  });
  marksChart = new Chart($("marksChart"), {
    type: "bar",
    data: { labels: students.map(s => s.name), datasets: [{ label: "Marks / 100", data: students.map(s => s.marks) }] },
    options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } }, plugins: { legend: { display: false } } }
  });
}
$("studentForm").addEventListener("submit", async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  const data = Object.fromEntries(f.entries());
  for (const key of ["marks", "attendance_total", "attendance_present"]) data[key] = Number(data[key]);
  try {
    await api("/api/students", { method: "POST", body: JSON.stringify(data) });
    e.target.reset();
    e.target.elements.marks.value = 0;
    e.target.elements.attendance_total.value = 0;
    e.target.elements.attendance_present.value = 0;
    $("formMessage").textContent = "Student saved successfully.";
    $("formMessage").className = "message success";
    await refresh();
  } catch (err) {
    $("formMessage").textContent = err.message;
    $("formMessage").className = "message error";
  }
});
$("search").addEventListener("input", () => refresh().catch(err => console.error(err)));
async function deleteStudent(id) {
  if (!confirm("Delete this student record?")) return;
  try { await api("/api/students/" + id, { method: "DELETE" }); await refresh(); }
  catch (err) { alert(err.message); }
}
$("aiForm").addEventListener("submit", async e => {
  e.preventDefault();
  $("aiAnswer").textContent = "Thinking…";
  try {
    const result = await api("/api/ai", { method: "POST", body: JSON.stringify({ question: $("question").value }) });
    $("aiAnswer").textContent = result.answer + "\n\nMode: " + result.mode;
  } catch (err) { $("aiAnswer").textContent = err.message; }
});
refresh().catch(err => alert("Could not load the dashboard: " + err.message));
