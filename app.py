from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import MySQLdb
import csv
import io
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # required for session and flash

# MySQL connection
conn = MySQLdb.connect(
    host='localhost',
    user='root',         # your MySQL username
    password='M@njeethsai#2005',         # your MySQL password
    database='students_db'
)
cursor = conn.cursor()

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Routes
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    course = request.form['course']

    if not (name and email and phone and course):
        flash('All fields are required!', 'error')
        return redirect('/')

    cursor.execute("INSERT INTO students (name, email, phone, course) VALUES (%s, %s, %s, %s)", (name, email, phone, course))
    conn.commit()
    flash('Student registered successfully!', 'success')
    return redirect('/students')

@app.route('/students')
def students():
    if not session.get('logged_in'):
        return redirect('/login')

    search = request.args.get('search')
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))
    limit = 5
    offset = (page - 1) * limit

    query = "SELECT * FROM students"
    params = []

    if search:
        query += " WHERE name LIKE %s OR course LIKE %s"
        params.extend(['%' + search + '%', '%' + search + '%'])

    query += f" ORDER BY {sort_by} {order.upper()} LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    students = cursor.fetchall()

    # total count for pagination
    count_query = "SELECT COUNT(*) FROM students"
    if search:
        count_query += " WHERE name LIKE %s OR course LIKE %s"
        cursor.execute(count_query, ('%' + search + '%', '%' + search + '%'))
    else:
        cursor.execute(count_query)
    total_students = cursor.fetchone()[0]
    total_pages = math.ceil(total_students / limit)

    return render_template('students.html', students=students, page=page, total_pages=total_pages, search=search, sort_by=sort_by, order=order)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('logged_in'):
        return redirect('/login')
    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    conn.commit()
    flash('Student deleted successfully!', 'success')
    return redirect('/students')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not session.get('logged_in'):
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        course = request.form['course']

        if not (name and email and phone and course):
            flash('All fields are required!', 'error')
            return redirect(f'/edit/{id}')

        cursor.execute("UPDATE students SET name=%s, email=%s, phone=%s, course=%s WHERE id=%s", (name, email, phone, course, id))
        conn.commit()
        flash('Student updated successfully!', 'success')
        return redirect('/students')

    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()
    return render_template('edit.html', student=student)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect('/')
        else:
            flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect('/login')

@app.route('/export')
def export():
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Course'])
    for student in students:
        writer.writerow(student)

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='students.csv'
    )

if __name__ == "__main__":
    app.run(debug=True)
