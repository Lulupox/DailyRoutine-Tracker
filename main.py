import sqlite3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Chemin de la base de données SQLite
DB_PATH = "daily_tasks.db"

# Fonction pour créer la table "tasks" dans la base de données
def create_tasks_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    is_done INTEGER NOT NULL
                 )''')
    conn.commit()
    conn.close()

# Fonction pour créer la table "daily_score" dans la base de données
def create_daily_score_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS daily_score (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    score INTEGER NOT NULL
                 )''')
    conn.commit()
    conn.close()

# Fonction pour ajouter une tâche quotidienne
def add_task(task_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (task_name, is_done) VALUES (?, ?)", (task_name, 0))
    conn.commit()
    conn.close()

# Fonction pour supprimer une tâche quotidienne
def delete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# Fonction pour cocher ou décocher une tâche quotidienne
def check_task(task_id, is_done):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tasks SET is_done = ? WHERE id=?", (is_done, task_id))
    conn.commit()

    # Mettre à jour le daily score en fonction de la tâche cochée/décochée
    c.execute("SELECT EXISTS(SELECT 1 FROM daily_score WHERE date = DATE('now'))")
    result = c.fetchone()[0]
    if result:
        if is_done:
            c.execute("UPDATE daily_score SET score = score + 1 WHERE date = DATE('now')")
        else:
            c.execute("UPDATE daily_score SET score = score - 1 WHERE date = DATE('now')")
    else:
        if is_done:
            c.execute("INSERT INTO daily_score (date, score) VALUES (DATE('now'), 1)")
        else:
            c.execute("INSERT INTO daily_score (date, score) VALUES (DATE('now'), -1)")

    conn.commit()
    conn.close()

# Fonction pour récupérer le score quotidien
def get_daily_scores():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM daily_score ORDER BY date")
    daily_scores = [{'date': row[1], 'score': row[2]} for row in c.fetchall()]
    conn.close()
    return daily_scores

# API Endpoint pour récupérer toutes les tâches
@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    tasks = [{'id': row[0], 'task_name': row[1], 'is_done': row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify(tasks)

# API Endpoint pour ajouter une tâche
@app.route('/tasks', methods=['POST'])
def add_task_endpoint():
    data = request.json
    task_name = data.get('task_name')
    if task_name:
        add_task(task_name)
        return jsonify({'message': 'Tâche ajoutée avec succès'}), 201
    return jsonify({'error': 'Le nom de la tâche est manquant'}), 400

# API Endpoint pour supprimer une tâche
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task_endpoint(task_id):
    delete_task(task_id)
    return jsonify({'message': 'Tâche supprimée avec succès'}), 200

# API Endpoint pour cocher ou décocher une tâche
@app.route('/tasks/<int:task_id>', methods=['PATCH'])
def check_task_endpoint(task_id):
    data = request.json
    is_done = data.get('is_done')
    if is_done is not None:
        check_task(task_id, is_done)
        return jsonify({'message': 'Tâche mise à jour avec succès'}), 200
    return jsonify({'error': 'Le statut de la tâche est manquant'}), 400

# API Endpoint pour récupérer les scores quotidiens
@app.route('/daily_scores', methods=['GET'])
def get_daily_scores_endpoint():
    daily_scores = get_daily_scores()
    return jsonify(daily_scores)

if __name__ == '__main__':
    create_tasks_table()
    create_daily_score_table()
    app.run(host='127.0.0.1', port=8000)
