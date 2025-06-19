import csv
import random
import math
from collections import defaultdict

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

class RLModel:
    def __init__(self):
        self.questions = []
        self.difficulties = {}
        self.responses = {}
        self.learning_rate = 0.07
        self.learning_rate_decay = 1.00

    def load_questions_from_csv(self, file_name="ml_maths_python_questions.csv"):
        with open(file_name, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            self.questions = list(reader)

        # Ensure topic column exists
        for question in self.questions:
            if 'topic' not in question:
                prompt = question['prompt'].lower()
                if any(kw in prompt for kw in ['machine learning', 'ml']):
                    question['topic'] = 'Machine Learning'
                elif any(kw in prompt for kw in ['math', 'derivative', 'equation', 'value of f(x)']):
                    question['topic'] = 'Math'
                elif any(kw in prompt for kw in ['python', 'def', 'list', 'dictionary', 'module']):
                    question['topic'] = 'Python'
                else:
                    question['topic'] = 'Unknown'

        # Build difficulty map
        for question in self.questions:
            q_id = question['question_id']
            self.difficulties[q_id] = float(question.get('difficulty', 0.5))
            self.responses[q_id] = {'total': 0, 'correct': 0}

    def _filter_available_questions(self, student):
        answered_ids = [report[0] for report in student.question_reports]
        return [q for q in self.questions if q['question_id'] not in answered_ids]

    def _calculate_proficiency_distance(self, student_proficiency, question_difficulty):
        return abs(student_proficiency - question_difficulty)

    def select_question(self, student):
        epsilon = 0.1 * self.learning_rate
        explore = random.uniform(0, 1) < epsilon

        available_questions = self._filter_available_questions(student)
        if not available_questions:
            print("No more questions.")
            return None

        if explore:
            return random.choice(available_questions)
        else:
            selected_question = min(
                available_questions,
                key=lambda q: self._calculate_proficiency_distance(student.proficiency, self.difficulties[q['question_id']])
            )
            self.learning_rate *= self.learning_rate_decay
            return selected_question

    def update_proficiency(self, student, answer):
        correctness = int(answer == True)
        question_id = student.question_reports[-1][0]

        try:
            phat = sigmoid(student.proficiency - self.difficulties[question_id])
            reward = correctness - phat

            new_proficiency = student.proficiency + self.learning_rate * reward
            new_proficiency = max(0, min(1, new_proficiency))
            student.proficiency = new_proficiency
        except Exception as e:
            print(f"Error updating proficiency: {e}")
            raise

    def get_topic_scores(self, question_reports):
        from collections import defaultdict
        topic_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

        for qid, correct in question_reports:
            question = next((q for q in self.questions if q['question_id'] == qid), None)
            if question:
                topic = question.get('topic', 'Unknown')
                topic_stats[topic]['total'] += 1
                if correct:
                    topic_stats[topic]['correct'] += 1

        topic_scores = {}
        for topic, stats in topic_stats.items():
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            topic_scores[topic] = round(accuracy * 100, 1)

        return topic_scores

    def get_weak_topics(self, student):
        topic_scores = self.get_topic_scores(student.question_reports)
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1])  # Lowest score first
        return [t for t, s in sorted_topics if topic_scores[t] < 70]

    def get_questions_by_topic(self, topic):
        return [q for q in self.questions if q.get('topic', '').lower() == topic.lower()]

    def select_question_from_topic(self, student, topic):
        available_questions = [
            q for q in self.questions
            if q.get('topic', 'Unknown').lower() == topic.lower() and q['question_id'] not in [r[0] for r in student.question_reports]
        ]

        if not available_questions:
            return None

        selected_question = min(
            available_questions,
            key=lambda q: abs(student.proficiency - self.difficulties[q['question_id']])
        )
        return selected_question

class Student:
    def __init__(self, student_id, proficiency=0.5):
        self.student_id = student_id
        self.proficiency = proficiency
        self.question_reports = []

    def getScore(self):
        total_questions = len(self.question_reports)
        if total_questions == 0:
            return 0
        correct_answers = sum([int(ans) for _, ans in self.question_reports])
        correctness_score = (correct_answers / total_questions) * 100
        proficiency_score = self.proficiency * 100
        final_score = (proficiency_score + correctness_score) / 2
        return round(final_score, 1)