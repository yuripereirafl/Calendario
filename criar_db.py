import sqlite3

conn = sqlite3.connect('reservas.db')
cursor = conn.cursor()

# Criar tabela de reservas
cursor.execute('''
CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT NOT NULL,
    descricao TEXT
)
''')

conn.commit()
conn.close()
print("Banco de dados criado com sucesso!")