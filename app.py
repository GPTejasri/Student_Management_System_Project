import os
from datetime import date
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///student_performance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), default="")
    year = db.Column(db.String(20), default="")
    marks = db.Column(db.Float, default=0)
    attendance_total = db.Column(db.Integer, default=0)
    attendance_present = db.Column(db.Integer, default=0)

    @property
    def percentage(self):
        return round((self.marks / 100) * 100, 2)

    @property
    def grade(self):
        if self.marks >= 90: return "A+"
        if self.marks >= 80: return "A"
        if self.marks >= 70: return "B"
        if self.marks >= 60: return "C"
        if self.marks >= 50: return "D"
        return "F"

    @property
    def attendance_percentage(self):
        if not self.attendance_total:
            return 0
        return round(self.attendance_present / self.attendance_total * 100, 2)

    def to_dict(self):
        return {
            "id": self.id, "roll_no": self.roll_no, "name": self.name,
            "department": self.department, "year": self.year,
            "marks": self.marks, "grade": self.grade,
            "attendance_total": self.attendance_total,
            "attendance_present": self.attendance_present,
            "attendance_percentage": self.attendance_percentage
        }

with app.app_context():
    db.create_all()

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/students")
def list_students():
    q = request.args.get("q", "").strip()
    query = Student.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Student.name.ilike(like),
                                 Student.roll_no.ilike(like),
                                 Student.department.ilike(like)))
    students = query.order_by(Student.name).all()
    return jsonify([s.to_dict() for s in students])

@app.post("/api/students")
def add_student():
    data = request.get_json(silent=True) or {}
    try:
        roll_no = str(data.get("roll_no", "")).strip()
        name = str(data.get("name", "")).strip()
        marks = float(data.get("marks", 0))
        total = int(data.get("attendance_total", 0))
        present = int(data.get("attendance_present", 0))
        if not roll_no or not name:
            return jsonify(error="Roll number and student name are required."), 400
        if not 0 <= marks <= 100:
            return jsonify(error="Marks must be between 0 and 100."), 400
        if total < 0 or present < 0 or present > total:
            return jsonify(error="Attendance must satisfy 0 <= present <= total."), 400
        student = Student(
            roll_no=roll_no, name=name,
            department=str(data.get("department", "")).strip(),
            year=str(data.get("year", "")).strip(), marks=marks,
            attendance_total=total, attendance_present=present
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(student.to_dict()), 201
    except ValueError:
        return jsonify(error="Marks and attendance fields must be valid numbers."), 400
    except Exception:
        db.session.rollback()
        return jsonify(error="Could not save record. Check whether the roll number already exists."), 400

@app.put("/api/students/<int:student_id>")
def update_student(student_id):
    student = db.get_or_404(Student, student_id)
    data = request.get_json(silent=True) or {}
    try:
        marks = float(data.get("marks", student.marks))
        total = int(data.get("attendance_total", student.attendance_total))
        present = int(data.get("attendance_present", student.attendance_present))
        if not 0 <= marks <= 100 or total < 0 or present < 0 or present > total:
            return jsonify(error="Check marks (0–100) and attendance values."), 400
        student.marks = marks
        student.attendance_total = total
        student.attendance_present = present
        student.department = str(data.get("department", student.department)).strip()
        student.year = str(data.get("year", student.year)).strip()
        db.session.commit()
        return jsonify(student.to_dict())
    except ValueError:
        return jsonify(error="Marks and attendance must be numeric."), 400

@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify(message="Student deleted.")

@app.get("/api/report")
def report():
    students = Student.query.all()
    count = len(students)
    avg_marks = round(sum(s.marks for s in students) / count, 2) if count else 0
    avg_att = round(sum(s.attendance_percentage for s in students) / count, 2) if count else 0
    grade_counts = {g: sum(1 for s in students if s.grade == g) for g in ["A+", "A", "B", "C", "D", "F"]}
    return jsonify({
        "total_students": count, "average_marks": avg_marks,
        "average_attendance": avg_att, "grade_counts": grade_counts,
        "students": [s.to_dict() for s in students]
    })

def local_ai_answer(question):
    """Small rule-based natural-language query helper; it uses only this app's SQLite records."""
    q = question.lower().strip()
    students = Student.query.all()
    if not students:
        return "There are no student records yet. Add student records first, then ask about grades, marks, or attendance."
    if any(word in q for word in ["below 75", "attendance below", "low attendance", "attendance less"]):
        found = [s for s in students if s.attendance_percentage < 75]
        return "Students with attendance below 75%: " + (", ".join(f"{s.name} ({s.attendance_percentage}%)" for s in found) if found else "None.")
    if any(word in q for word in ["top", "highest", "best marks", "highest marks"]):
        top = sorted(students, key=lambda s: s.marks, reverse=True)[:5]
        return "Top students by marks: " + "; ".join(f"{s.name}: {s.marks}/100 ({s.grade})" for s in top)
    if any(word in q for word in ["fail", "failed", "below 50"]):
        found = [s for s in students if s.marks < 50]
        return "Students scoring below 50: " + (", ".join(f"{s.name} ({s.marks})" for s in found) if found else "None.")
    if "average" in q and ("attendance" in q or "present" in q):
        avg = round(sum(s.attendance_percentage for s in students) / len(students), 2)
        return f"Average attendance across {len(students)} students is {avg}%."
    if "average" in q or "mean marks" in q:
        avg = round(sum(s.marks for s in students) / len(students), 2)
        return f"Average marks across {len(students)} students is {avg}/100."
    if "count" in q or "how many" in q or "total students" in q:
        return f"There are {len(students)} student record(s)."
    # Try to match a student's name or roll number in the question.
    match = next((s for s in students if s.name.lower() in q or s.roll_no.lower() in q), None)
    if match:
        return (f"{match.name} (Roll No. {match.roll_no}) scored {match.marks}/100, grade {match.grade}, "
                f"and attendance is {match.attendance_percentage}%.")
    return ("Try questions like: 'Who has the highest marks?', 'Show students with attendance below 75%', "
            "'What is the average marks?', 'How many students are there?', or enter a student's name/roll number.")

@app.post("/api/ai")
def ai_query():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify(error="Please enter a question."), 400

    # Optional OpenAI-compatible API integration. The app still works without an API key.
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            report_data = report().get_json()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": (
                        "You are a student performance assistant. Answer only from the supplied student summary. "
                        "Do not invent records. Be concise and respectful. Student marks and attendance are educational data."
                    )},
                    {"role": "user", "content": f"Student summary JSON: {report_data}\nQuestion: {question}"}
                ],
                temperature=0.2,
                max_tokens=350
            )
            return jsonify(answer=response.choices[0].message.content or "No answer returned.", mode="LLM API")
        except Exception as exc:
            # Fall back safely if API is unavailable or the provider configuration is incorrect.
            return jsonify(answer=local_ai_answer(question) + f"\n\n(LLM API unavailable; using local helper.)", mode="Local fallback")
    return jsonify(answer=local_ai_answer(question), mode="Local helper")

if __name__ == "__main__":
    app.run(debug=True)
