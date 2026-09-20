from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "projects.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            task_name TEXT NOT NULL,
            assigned_to TEXT,
            status TEXT NOT NULL,
            progress INTEGER NOT NULL,
            deadline TEXT,
            update_date TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- AGENTS ----------------

class ProjectManagerAgent:

    def process_update(self, update):

        if not update.strip():
            return "No project update was provided."

        return (
            "Project Manager Agent\n\n"
            "Project update received successfully.\n\n"
            f"Update: {update}\n\n"
            "The project information has been processed "
            "for further analysis."
        )


class ProjectProgressAnalystAgent:

    def analyze(self):

        conn = get_db()

        tasks = conn.execute(
            "SELECT * FROM project_tasks"
        ).fetchall()

        conn.close()

        if not tasks:

            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "delayed": 0,
                "progress": 0
            }

        total = len(tasks)
        completed = 0
        in_progress = 0
        pending = 0
        delayed = 0

        progress_values = []

        today = datetime.now().date()

        for task in tasks:

            status = task["status"].lower()
            progress = task["progress"]

            progress_values.append(progress)

            if status == "completed":
                completed += 1

            elif status == "in progress":
                in_progress += 1

            elif status == "pending":
                pending += 1

            try:

                deadline = datetime.strptime(
                    task["deadline"],
                    "%Y-%m-%d"
                ).date()

                if deadline < today and status != "completed":
                    delayed += 1

            except:
                pass

        overall_progress = round(
            sum(progress_values) / len(progress_values),
            2
        )

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "delayed": delayed,
            "progress": overall_progress
        }


class ProjectAdvisorAgent:

    def generate_advice(self, analysis):

        if analysis["total"] == 0:

            return (
                "No tasks are available. "
                "Add project tasks to receive recommendations."
            )

        recommendations = []

        if analysis["delayed"] > 0:

            recommendations.append(
                "Review delayed tasks and prioritize them."
            )

        if analysis["pending"] > 0:

            recommendations.append(
                "Assign pending tasks to team members."
            )

        if analysis["in_progress"] > 0:

            recommendations.append(
                "Monitor in-progress tasks regularly."
            )

        if analysis["progress"] < 50:

            recommendations.append(
                "Project progress is below 50%. "
                "Increase task monitoring."
            )

        elif analysis["progress"] >= 80:

            recommendations.append(
                "Project progress is good. "
                "Continue monitoring deadlines."
            )

        if not recommendations:

            recommendations.append(
                "Continue regular project monitoring."
            )

        return "\n".join(
            "• " + item
            for item in recommendations
        )


class AgenticProjectSystem:

    def __init__(self):

        self.project_manager = ProjectManagerAgent()
        self.progress_analyst = ProjectProgressAnalystAgent()
        self.project_advisor = ProjectAdvisorAgent()

    def run(self, update):

        manager_result = (
            self.project_manager.process_update(update)
        )

        analysis = self.progress_analyst.analyze()

        advice = (
            self.project_advisor.generate_advice(
                analysis
            )
        )

        return {
            "manager": manager_result,
            "analysis": analysis,
            "advice": advice
        }


# ---------------- INITIALIZE ----------------

create_database()

system = AgenticProjectSystem()


# ---------------- ROUTES ----------------

@app.route("/")
def home():

    analysis = system.progress_analyst.analyze()

    conn = get_db()

    tasks = conn.execute(
        "SELECT * FROM project_tasks ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        tasks=tasks,
        analysis=analysis,
        result=None
    )


@app.route("/add", methods=["POST"])
def add_task():

    project_name = request.form["project_name"]
    task_name = request.form["task_name"]
    assigned_to = request.form["assigned_to"]
    status = request.form["status"]
    progress = int(request.form["progress"])
    deadline = request.form["deadline"]

    conn = get_db()

    conn.execute("""
        INSERT INTO project_tasks
        (
            project_name,
            task_name,
            assigned_to,
            status,
            progress,
            deadline,
            update_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        project_name,
        task_name,
        assigned_to,
        status,
        progress,
        deadline,
        datetime.now().strftime("%Y-%m-%d")
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>")
def delete_task(task_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM project_tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


@app.route("/analyze", methods=["POST"])
def analyze():

    update = request.form["project_update"]

    result = system.run(update)

    analysis = result["analysis"]

    conn = get_db()

    tasks = conn.execute(
        "SELECT * FROM project_tasks ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        tasks=tasks,
        analysis=analysis,
        result=result
    )


# ---------------- RUN ----------------

if __name__ == "__main__":

    import os

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )