import sqlite3
from pathlib import Path
from datetime import date

DB_FILE = Path(__file__).resolve().parent / 'shirley_financas.db'


def connect():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS debts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          description TEXT NOT NULL,
          category TEXT NOT NULL,
          due_date TEXT NOT NULL,
          amount REAL NOT NULL CHECK(amount>=0),
          notes TEXT NOT NULL DEFAULT '',
          origin TEXT NOT NULL DEFAULT 'mensal' CHECK(origin IN ('mensal','anterior')),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payments (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          debt_id INTEGER NOT NULL REFERENCES debts(id) ON DELETE CASCADE,
          paid_on TEXT NOT NULL,
          amount REAL NOT NULL CHECK(amount>0),
          notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS incomes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          description TEXT NOT NULL,
          received_on TEXT NOT NULL,
          amount REAL NOT NULL CHECK(amount>=0)
        );
        CREATE INDEX IF NOT EXISTS ix_debts_due ON debts(due_date);
        CREATE INDEX IF NOT EXISTS ix_payments_paid_on ON payments(paid_on);
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        if db.execute("SELECT value FROM metadata WHERE key='seeded'").fetchone():
            return
        # Estimativas extraídas do planejamento anterior; todos os valores são editáveis.
        for i in range(12):
            y = 2026 + (10 + i)//12
            m = (10 + i)%12 + 1
            period = f'{y}-{m:02d}'
            monthly = [
                ('Internet','Moradia e serviços',10,120),
                ('Energia do mês','Moradia e serviços',15,694),
                ('Moto do mês','Transporte',20,900),
                ('Cartão de crédito','Cartão',4,950 if i == 0 else 0),
            ]
            if i < 10: monthly.insert(0,('Empréstimo - parcela mensal','Empréstimos',5,907.52))
            for description, cat, day, value in monthly:
                if value:
                    db.execute('INSERT INTO debts(description,category,due_date,amount,origin,notes) VALUES(?,?,?,?,?,?)',
                               (description,cat,f'{period}-{day:02d}',value,'mensal','Previsão inicial editável'))
            income = 3415 + (1500 if i in (0,1) else 0)
            db.execute('INSERT INTO incomes(description,received_on,amount) VALUES(?,?,?)',
                       ('Renda prevista (editável)',f'{period}-01',income))
        # Parcela avulsa quitada em novembro, assumida no levantamento inicial.
        cursor = db.execute('INSERT INTO debts(description,category,due_date,amount,origin,notes) VALUES(?,?,?,?,?,?)',
          ('Última parcela do empréstimo (verificar)','Empréstimos','2026-11-05',755.92,'mensal','Pagamento presumido conforme informação fornecida; confirmar parcela'))
        db.execute('INSERT INTO payments(debt_id,paid_on,amount,notes) VALUES(?,?,?,?)',
                   (cursor.lastrowid,'2026-11-12',755.92,'Único pagamento registrado em novembro; confirmar valor'))
        for description,category,amount in [
            ('Moto atrasada 1','Transporte',900),('Moto atrasada 2','Transporte',900),('Moto atrasada 3','Transporte',900),
            ('Energia atrasada 1','Moradia e serviços',694),('Energia atrasada 2','Moradia e serviços',597.12),
        ]:
            db.execute('INSERT INTO debts(description,category,due_date,amount,origin,notes) VALUES(?,?,?,?,?,?)',
                       (description,category,'2026-10-31',amount,'anterior','Atraso anterior a novembro; data provisória'))
        db.execute("INSERT INTO metadata(key,value) VALUES('seeded','1')")


def fetch_debts():
    with connect() as db:
        return [dict(row) for row in db.execute('''
            SELECT d.*, COALESCE(SUM(p.amount),0) AS paid,
                   MAX(0,d.amount-COALESCE(SUM(p.amount),0)) AS remaining
            FROM debts d LEFT JOIN payments p ON p.debt_id=d.id
            GROUP BY d.id ORDER BY d.due_date,d.id''')]


def fetch_payments():
    with connect() as db:
        return [dict(row) for row in db.execute('''SELECT p.*,d.description FROM payments p
           JOIN debts d ON d.id=p.debt_id ORDER BY p.paid_on DESC,p.id DESC''')]


def fetch_incomes():
    with connect() as db:
        return [dict(row) for row in db.execute('SELECT * FROM incomes ORDER BY received_on,id')]


def add_debt(description,category,due_date,amount,origin,notes=''):
    with connect() as db:
        db.execute('INSERT INTO debts(description,category,due_date,amount,origin,notes) VALUES(?,?,?,?,?,?)',
                   (description,category,str(due_date),round(amount,2),origin,notes))


def update_debt(debt_id,description,category,due_date,amount,origin,notes):
    with connect() as db:
        already_paid = db.execute('SELECT COALESCE(SUM(amount),0) FROM payments WHERE debt_id=?',(debt_id,)).fetchone()[0]
        if round(amount,2) + 0.00001 < already_paid: raise ValueError('O valor da conta não pode ser menor que o já pago.')
        db.execute('UPDATE debts SET description=?,category=?,due_date=?,amount=?,origin=?,notes=? WHERE id=?',
                   (description,category,str(due_date),round(amount,2),origin,notes,debt_id))


def delete_debt(debt_id):
    with connect() as db: db.execute('DELETE FROM debts WHERE id=?',(debt_id,))


def add_payment(debt_id,paid_on,amount,notes=''):
    with connect() as db:
        row=db.execute('''SELECT d.amount-COALESCE(SUM(p.amount),0) FROM debts d
            LEFT JOIN payments p ON p.debt_id=d.id WHERE d.id=? GROUP BY d.id''',(debt_id,)).fetchone()
        if row is None: raise ValueError('Conta não encontrada.')
        if amount <= 0 or amount > row[0]+0.00001: raise ValueError('O pagamento deve ser maior que zero e não ultrapassar o saldo da conta.')
        db.execute('INSERT INTO payments(debt_id,paid_on,amount,notes) VALUES(?,?,?,?)',
                   (debt_id,str(paid_on),round(amount,2),notes))


def delete_payment(payment_id):
    with connect() as db: db.execute('DELETE FROM payments WHERE id=?',(payment_id,))


def add_income(description,received_on,amount):
    with connect() as db:
        db.execute('INSERT INTO incomes(description,received_on,amount) VALUES(?,?,?)',(description,str(received_on),round(amount,2)))


def update_income(income_id,description,received_on,amount):
    with connect() as db:
        db.execute('UPDATE incomes SET description=?, received_on=?,amount=? WHERE id=?',
                   (description,str(received_on),round(amount,2),income_id))


def delete_income(income_id):
    with connect() as db: db.execute('DELETE FROM incomes WHERE id=?',(income_id,))
