import csv
from ModelClass import RLModel, Student
import pandas as pd
import os

# Initialize RL model
rl_model = RLModel()

# Load questions from CSV
rl_model.load_questions_from_csv("ml_maths_python_questions.csv")

# File to store student data
STUDENT_DATA_FILE = "student_data.csv"

# Create student_data.csv if it doesn't exist
if not os.path.exists(STUDENT_DATA_FILE):
    df = pd.DataFrame(columns=["ID", "Name", "Proficiency", "Score"])
    df.to_csv(STUDENT_DATA_FILE, index=False)

num_students = int(input("How many students? "))
bacche = []

for _ in range(num_students):
    stu_id = int(input("Enter ID: "))
    name = input("Enter Name: ")
    bacche.append({'id': stu_id, 'name': name})

# Read existing student data
df = pd.read_csv(STUDENT_DATA_FILE)
ids = df['ID'].tolist()

# Open file for appending new students
with open(STUDENT_DATA_FILE, mode='a', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)

    for stu in bacche:
        print(f"\nTesting for Student {stu['id']}:\n")
        proficiency = 0.5

        if stu['id'] in ids:
            proficiency = df.loc[df['ID'] == stu['id']]['Proficiency'].values[0]
        student = Student(stu['id'], proficiency)

        num_questions_to_answer = 10
        for q_num in range(num_questions_to_answer):
            question = rl_model.select_question(student)
            if question is None:
                print("No more available questions.")
                break

            print(f"Q{q_num + 1}) {question['prompt']}")
            print(f"A) {question['A']}")
            print(f"B) {question['B']}")
            print(f"C) {question['C']}")
            print(f"D) {question['D']}")
            print(f"E) {question['E']}")

            option_selected = input("\nEnter the option selected (A-E): ").strip().upper()
            correct_answer = (option_selected == question['answer'])
            student.question_reports.append((question['question_id'], correct_answer))
            rl_model.update_proficiency(student, correct_answer)

        print("---------------------------------------------------------------")
        print(f"Name: {stu['name']} | ID: {stu['id']}")
        print(f"Final Proficiency: {student.proficiency:.3f}")
        print(f"Final Score: {student.getScore():.1f}")
        print("---------------------------------------------------------------\n")

        # Update or append student data
        df = pd.read_csv(STUDENT_DATA_FILE)
        if stu['id'] in df['ID'].values:
            df.loc[df['ID'] == stu['id'], ['Proficiency', 'Score']] = [student.proficiency, student.getScore()]
            df.to_csv(STUDENT_DATA_FILE, index=False)
        else:
            writer.writerow([stu['id'], stu['name'], student.proficiency, student.getScore()])
            print("Data added successfully.")

print("\nTesting complete.")