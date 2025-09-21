
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- Database ----------------
def get_db_connection():
    conn = sqlite3.connect('study.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chapters(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            chapter TEXT,
            status TEXT DEFAULT 'Not Done',
            last_study DATE,
            note TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER,
            question TEXT,
            answer TEXT,
            FOREIGN KEY(chapter_id) REFERENCES chapters(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------- Helper ----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- Routes ----------------
@app.route('/')
def index():
    conn = get_db_connection()
    chapters = conn.execute("SELECT * FROM chapters").fetchall()
    conn.close()
    return render_template('index.html', chapters=chapters)

@app.route('/add_chapter', methods=['GET','POST'])
def add_chapter():
    if request.method=='POST':
        subject = request.form['subject']
        chapter = request.form['chapter']
        note_file = request.files.get('note')
        filename = None
        if note_file and allowed_file(note_file.filename):
            filename = secure_filename(note_file.filename)
            note_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db_connection()
        conn.execute("INSERT INTO chapters(subject, chapter, note) VALUES (?, ?, ?)", (subject, chapter, filename))
        conn.commit()
        conn.close()
        flash("Chapter added successfully!")
        return redirect(url_for('index'))
    return render_template('add_chapter.html')

@app.route('/add_question', methods=['GET','POST'])
def add_question():
    conn = get_db_connection()
    chapters = conn.execute("SELECT * FROM chapters").fetchall()
    conn.close()
    if request.method=='POST':
        chapter_id = request.form['chapter_id']
        question = request.form['question']
        answer = request.form['answer']
        conn = get_db_connection()
        conn.execute("INSERT INTO questions(chapter_id, question, answer) VALUES (?, ?, ?)", (chapter_id, question, answer))
        conn.commit()
        conn.close()
        flash("Question added successfully!")
        return redirect(url_for('index'))
    return render_template('add_question.html', chapters=chapters)

@app.route('/take_test/<int:chapter_id>', methods=['GET','POST'])
def take_test(chapter_id):
    conn = get_db_connection()
    questions = conn.execute("SELECT * FROM questions WHERE chapter_id=?", (chapter_id,)).fetchall()
    chapter = conn.execute("SELECT * FROM chapters WHERE id=?", (chapter_id,)).fetchone()
    conn.close()
    
    if request.method == 'POST':
        score = 0
        for q in questions:
            user_ans = request.form.get(f'answer_{q["id"]}')
            if user_ans and user_ans.strip().lower() == q['answer'].lower():
                score += 1
        conn = get_db_connection()
        if score == len(questions):
            flash("All answers correct! Chapter completed.")
            conn.execute("UPDATE chapters SET status='Done', last_study=? WHERE id=?", (datetime.today(), chapter_id))
        else:
            flash(f"{score}/{len(questions)} correct. Study again!")
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('take_test.html', chapter=chapter, questions=questions)

@app.route('/progress')
def progress():
    conn = get_db_connection()
    chapters = conn.execute("SELECT * FROM chapters").fetchall()
    conn.close()
    return render_template('progress.html', chapters=chapters)

@app.route('/reminder')
def reminder():
    conn = get_db_connection()
    subjects = conn.execute("SELECT subject, MAX(last_study) as last_study FROM chapters GROUP BY subject").fetchall()
    conn.close()
    today = datetime.today()
    reminders = []
    for s in subjects:
        if s['last_study']:
            last_date = datetime.strptime(s['last_study'], "%Y-%m-%d %H:%M:%S.%f")
            if today - last_date > timedelta(days=2):
                reminders.append(f"You did not study {s['subject']} for 3 days")
    return "<br>".join(reminders) if reminders else "No reminders!"

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return redirect(url_for('static', filename='uploads/' + filename))

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
