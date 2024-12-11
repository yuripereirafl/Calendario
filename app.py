from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para gerenciar sessões

# Função para conectar ao banco de dados
def connect_db():
    return sqlite3.connect('reservas.db')

# Criar tabela de usuários (execute uma vez para inicializar o banco)
def create_user_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data_inicio TEXT NOT NULL,
            data_fim TEXT NOT NULL,
            descricao TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Função para obter todas as reservas
def get_reservas():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reservas')
    reservas = cursor.fetchall()
    conn.close()
    return reservas

# Página inicial com login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]  # Salvar o ID do usuário na sessão
            return redirect(url_for('agenda'))
        else:
            return render_template('login.html', error='Usuário ou senha inválidos!')

    return render_template('login.html')

# Rota para registrar um novo usuário (apenas para testes ou admins)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Usuário já existe!')
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Página de agenda (protegida)
@app.route('/agenda')
def agenda():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('index.html')

# Rota para gerenciar contas (protegida)
@app.route('/gerenciar_contas', methods=['GET', 'POST'])
def gerenciar_contas():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        excluir_usuario_id = request.form.get('excluir_usuario_id')
        if excluir_usuario_id:
            try:
                cursor.execute('DELETE FROM usuarios WHERE id = ?', (excluir_usuario_id,))
                conn.commit()
            except Exception as e:
                return render_template('gerenciar_contas.html', error=f'Erro ao excluir usuário: {str(e)}')

    cursor.execute('SELECT id, username FROM usuarios')
    usuarios = cursor.fetchall()
    conn.close()

    return render_template('gerenciar_contas.html', usuarios=usuarios)

# API para listar reservas
@app.route('/api/reservas', methods=['GET'])
def reservas():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autorizado!'}), 401

    reservas = get_reservas()
    eventos = []
    for reserva in reservas:
        eventos.append({
            'id': reserva[0],     # ID da reserva
            'title': reserva[4],  # Descrição do evento
            'start': reserva[2],  # Data e hora de início
            'end': reserva[3]     # Data e hora de término
        })
    return jsonify(eventos)

# Rota para criar uma reserva
@app.route('/reservar', methods=['POST'])
def reservar():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autorizado!'}), 401

    usuario_id = session['user_id']  # Pegar o ID do usuário autenticado
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')
    descricao = request.form.get('descricao')
    sala = request.form.get('sala')  # Adicionando o campo de seleção da sala

    if not all([data_inicio, data_fim, descricao, sala]):
        return jsonify({'error': 'Todos os campos são obrigatórios!'}), 400

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM reservas
    WHERE descricao LIKE ? AND (
        (data_inicio <= ? AND data_fim > ?)
        OR (data_inicio < ? AND data_fim >= ?)
        OR (data_inicio >= ? AND data_fim <= ?)
    )
    ''', (f'%{sala}%', data_fim, data_inicio, data_fim, data_inicio, data_inicio, data_fim))

    conflito = cursor.fetchone()

    if conflito:
        conn.close()
        return jsonify({'error': f'Conflito de horários com outra reserva na {sala}!'}), 400

    descricao_com_sala = f'{descricao} - {sala}'
    cursor.execute('''
    INSERT INTO reservas (usuario_id, data_inicio, data_fim, descricao)
    VALUES (?, ?, ?, ?)
    ''', (usuario_id, data_inicio, data_fim, descricao_com_sala))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Reserva criada com sucesso na {sala}!'}), 201

# Rota para excluir uma reserva
@app.route('/excluir_reserva/<int:reserva_id>', methods=['POST'])
def excluir_reserva(reserva_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Não autorizado!'}), 401

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM reservas WHERE id = ?', (reserva_id,))
        reserva = cursor.fetchone()

        if not reserva:
            return jsonify({'error': 'Reserva não encontrada!'}), 404

        cursor.execute('DELETE FROM reservas WHERE id = ?', (reserva_id,))
        conn.commit()
        return jsonify({'message': 'Reserva excluída com sucesso!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    create_user_table()
    app.run(debug=True, host='0.0.0.0')