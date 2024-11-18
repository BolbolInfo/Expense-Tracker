from flask import Flask, render_template, request, redirect, url_for
import sqlite3 as sq
import os
import matplotlib.pyplot as plt

app = Flask(__name__)

CHARTS_DIR = os.path.join(os.path.dirname(__file__), 'static', 'charts')
if not os.path.exists(CHARTS_DIR):
    os.makedirs(CHARTS_DIR)


def createDB(CAT):
    con = sq.connect(os.path.join(os.path.dirname(__file__), "data", "dataBase.db"))
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS category(
                name VARCHAR(20) PRIMARY KEY
                )
    """)
    con.commit()

    for category in CAT:
        try:
            cur.execute("INSERT INTO category VALUES(?)", (category,))
            con.commit()
        except sq.IntegrityError:
            pass

    cur.execute("""
    CREATE TABLE IF NOT EXISTS data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATETIME,
                category VARCHAR(20),
                amount INT DEFAULT 0,
                description TEXT,
                FOREIGN KEY (category) REFERENCES category (name) ON DELETE CASCADE ON UPDATE CASCADE
                )
    """)
    con.commit()
    
    con.close()

def get_categories():
    con = sq.connect(os.path.join(os.path.dirname(__file__), "data", "dataBase.db"))
    cur = con.cursor()
    cur.execute("SELECT name FROM category")
    categories = [row[0] for row in cur.fetchall()]
    con.close()
    return categories

def get_expenses_by_category(start_date,end_date):
    con = sq.connect(os.path.join(os.path.dirname(__file__), "data", "dataBase.db"))
    cur = con.cursor()
    query = "SELECT category, SUM(amount) FROM data WHERE date BETWEEN ? AND ? GROUP BY category"
    cur.execute(query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
    expenses = cur.fetchall()
    con.close()
    return expenses


def get_expenses_details(start_date, end_date):
    con = sq.connect(os.path.join(os.path.dirname(__file__), "data", "dataBase.db"))
    cur = con.cursor()
    query = """
    SELECT date, category, amount, description 
    FROM data 
    WHERE date BETWEEN ? AND ?
    """
    cur.execute(query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
    expenses = cur.fetchall()
    con.close()
    return expenses


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add_expense')
def add_expense():
    categories = get_categories()
    return render_template('index.html', categories=categories)

@app.route('/submit', methods=['POST'])
def submit():
    category = request.form['category']
    amount = request.form['amount']
    description = request.form['description']

    con = sq.connect(os.path.join(os.path.dirname(__file__), "data", "dataBase.db"))
    cur = con.cursor()
    cur.execute("INSERT INTO data (date, category, amount, description) VALUES (datetime('now'), ?, ?, ?)", (category, amount, description))
    con.commit()
    con.close()

    return redirect('/')



@app.route('/view_chart', methods=['GET', 'POST'])
def view_chart():
    start_date = request.form.get('start_date', None)
    end_date = request.form.get('end_date', None)

    
    expenses_by_category = get_expenses_by_category(start_date, end_date)
    categories = [row[0] for row in expenses_by_category]
    amounts = [row[1] for row in expenses_by_category]


    detailed_expenses = get_expenses_details(start_date, end_date)


    total_amount = sum(amounts)


    fig, ax = plt.subplots()
    labels = [f"{category}: {amount}" for category, amount in zip(categories, amounts)]
    ax.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    ax.set_title(f"Total Expenses: {total_amount}")


    chart_filename = "expense_pie_chart.png"
    chart_filepath = os.path.join(CHARTS_DIR, chart_filename)
    fig.savefig(chart_filepath)
    plt.close(fig)

    return render_template(
        'chart_page.html',
        chart_filename=chart_filename,
        detailed_expenses=detailed_expenses,
        total_amount=total_amount
    )



@app.route('/chart_page/<filename>')
def chart_page(filename):

    return render_template('chart_page.html', chart_filename=filename)

if __name__ == '__main__':
    CAT = ["food", "transport", "smoke", "coffee"]
    createDB(CAT)
    app.run(debug=True)
