from flask import Flask, render_template, request, session, redirect, url_for
from ModelClass import RLModel, Student
import pandas as pd
import os
import random

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Initialize model and load questions
rl_model = RLModel()
rl_model.load_questions_from_csv("ml_maths_python_questions.csv")

STUDENT_DATA_FILE = "student_data.csv"

# Create student_data.csv if it doesn't exist
if not os.path.exists(STUDENT_DATA_FILE):
    df = pd.DataFrame(columns=["ID", "Name", "Proficiency", "Score", "Score_Quiz2"])
    df.to_csv(STUDENT_DATA_FILE, index=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        student_id = int(request.form["id"])
        name = request.form["name"]
        session["student_id"] = student_id
        session["name"] = name

        # Load or initialize student
        df = pd.read_csv(STUDENT_DATA_FILE)
        ids = list(df['ID'])
        if student_id in ids:
            proficiency = df.loc[df['ID'] == student_id]['Proficiency'].values[0]
        else:
            proficiency = 0.5

        student = Student(student_id, proficiency)
        session["proficiency"] = proficiency
        session["question_index"] = 0
        session["question_reports"] = []

        return redirect(url_for("quiz"))

    return render_template("login.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    student_id = session.get("student_id")
    name = session.get("name")
    proficiency = session.get("proficiency")
    reports = session.get("question_reports", [])
    q_index = session.get("question_index", 0)

    # Track how many questions from each topic were answered
    if "topics_left" not in session:
        session["topics_left"] = {
            "Math": 10,
            "Python": 10,
            "Machine Learning": 10
        }

    student = Student(student_id, proficiency)
    student.question_reports = reports

    if sum(session["topics_left"].values()) <= 0:
        return redirect(url_for("result"))

    if request.method == "POST":
        selected_option = request.form.get("option")
        current_question = session.get("current_question")
        correct = selected_option == current_question["answer"]

        student.question_reports.append((current_question["question_id"], correct))
        rl_model.update_proficiency(student, correct)

        # Reduce count for the topic
        topic = current_question.get('topic', 'Unknown')
        normalized_topic = topic.replace("(ML)", "").strip()

        if normalized_topic in session["topics_left"]:
            session["topics_left"][normalized_topic] -= 1

        session["question_reports"] = student.question_reports
        session["topics_left"] = session["topics_left"]
        session["proficiency"] = student.proficiency
        return redirect(url_for("quiz"))

    # Get next question based on remaining topics
    remaining_topics = [t for t, c in session["topics_left"].items() if c > 0]
    if not remaining_topics:
        return redirect(url_for("result"))

    # Pick one of the remaining topics
    topic = random.choice(remaining_topics)
    question = rl_model.select_question_from_topic(student, topic)

    if not question:
        return f"No more {topic} questions left."

    session["current_question"] = question
    question_num = len(student.question_reports) + 1  # Total answered so far
    total_questions = 30

    return render_template(
        "question.html",
        question=question,
        question_num=question_num,
        total_questions=total_questions,
        name=name
    )


@app.route("/result")
def result():
    student = Student(session["student_id"], session["proficiency"])
    student.question_reports = session["question_reports"]
    score = student.getScore()

    # Get topic-wise scores
    topic_scores = rl_model.get_topic_scores(student.question_reports)

    # Update CSV file
    df = pd.read_csv(STUDENT_DATA_FILE)
    student_row = df[df["ID"] == student.student_id]

    if not student_row.empty:
        df.loc[df["ID"] == student.student_id, "Proficiency"] = student.proficiency
        df.loc[df["ID"] == student.student_id, "Score"] = score
    else:
        new_row = pd.DataFrame([{
            "ID": student.student_id,
            "Name": session["name"],
            "Proficiency": student.proficiency,
            "Score": score
        }])
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(STUDENT_DATA_FILE, index=False)

    return render_template("result.html", 
                           proficiency=student.proficiency, 
                           score=score, 
                           topic_scores=topic_scores)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
