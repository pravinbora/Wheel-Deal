from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bcrypt import Bcrypt
from functools import wraps
import math, random
from database import SQLiteDatabase

app = Flask(__name__)
app.config.from_object('config.Config')

database = SQLiteDatabase(app)
bcrypt = Bcrypt(app)

# ─── Auth helpers ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Auth routes ─────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role     = request.form['role']
        cur = database.connection.cursor()
        if role == 'admin':
            cur.execute("SELECT * FROM admin WHERE username = %s", (username,))
            user = cur.fetchone()
            if user and bcrypt.check_password_hash(user['password'], password):
                session['user_id']  = user['id']
                session['username'] = user['username']
                session['role']     = 'admin'
                return redirect(url_for('admin_home'))
        else:
            cur.execute("SELECT * FROM user WHERE username = %s", (username,))
            user = cur.fetchone()
            if user and bcrypt.check_password_hash(user['password'], password):
                session['user_id']  = user['user_id']
                session['username'] = user['username']
                session['role']     = 'user'
                return redirect(url_for('user_home'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        age  = int(data['age'])
        lic  = data['driving_license'].lower()
        if lic != 'yes' or age < 18:
            flash('You must be 18+ and have a driving license.', 'danger')
            return render_template('signup.html')
        hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        cur = database.connection.cursor()
        try:
            cur.execute("""INSERT INTO user
                (name, username, password, email, father_name, phone,
                 qualification, city, gender, blood, age, dob,
                 driving_license, address)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (data['name'], data['username'], hashed, data['email'],
                 data['father_name'], data['phone'], data['qualification'],
                 data['city'], data['gender'], data['blood'], age,
                 data['dob'], data['driving_license'], data['address']))
            database.connection.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Username already exists or error: {e}', 'danger')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Home pages ──────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_home():
    return render_template('admin_home.html')

@app.route('/user')
@login_required
def user_home():
    return render_template('user_home.html')

# ─── Bike Brand ──────────────────────────────────────────────────────────────

@app.route('/brands')
@login_required
def view_brands():
    cur = database.connection.cursor()
    cur.execute("SELECT * FROM bike_brand")
    brands = cur.fetchall()
    return render_template('view_brand.html', brands=brands)

@app.route('/brands/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_brand():
    if request.method == 'POST':
        name  = request.form['brand_name']
        model = request.form['brand_model']
        year  = request.form['year']
        cur   = database.connection.cursor()
        cur.execute("INSERT INTO bike_brand (brand_name, brand_model, year) VALUES (%s,%s,%s)",
                    (name, model, year))
        database.connection.commit()
        flash('Brand added successfully!', 'success')
        return redirect(url_for('view_brands'))
    return render_template('add_brand.html')

@app.route('/brands/delete/<int:brand_id>')
@login_required
@admin_required
def delete_brand(brand_id):
    cur = database.connection.cursor()
    cur.execute("SELECT brand_name, brand_model FROM bike_brand WHERE brand_id = %s", (brand_id,))
    brand = cur.fetchone()
    cur.execute("SELECT 1 FROM bike WHERE brand_name=%s AND brand_model=%s",
                (brand['brand_name'], brand['brand_model']))
    if cur.fetchone():
        flash('Cannot delete — bikes exist under this brand. Delete those bikes first.', 'danger')
    else:
        cur.execute("DELETE FROM bike_brand WHERE brand_id = %s", (brand_id,))
        database.connection.commit()
        flash('Brand deleted.', 'success')
    return redirect(url_for('view_brands'))

# ─── Bikes ───────────────────────────────────────────────────────────────────

@app.route('/bikes')
@login_required
def view_bikes():
    cur = database.connection.cursor()
    cur.execute("SELECT * FROM bike")
    bikes = cur.fetchall()
    return render_template('view_bike.html', bikes=bikes)

@app.route('/bikes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_bike():
    cur = database.connection.cursor()
    if request.method == 'POST':
        d = request.form
        cur.execute("""INSERT INTO bike VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Available')""",
            (d['bike_no'], d['brand_name'], d['brand_model'], d['bike_name'],
             d['bike_seat'], d['bike_engine'], d['bike_category'],
             d['bike_mileage'], d['bike_mirror'], d['bike_rent']))
        database.connection.commit()
        flash('Bike added!', 'success')
        return redirect(url_for('view_bikes'))
    cur.execute("SELECT DISTINCT brand_name FROM bike_brand")
    brands = cur.fetchall()
    return render_template('add_bike.html', brands=brands)

@app.route('/bikes/delete/<bike_no>')
@login_required
@admin_required
def delete_bike(bike_no):
    cur = database.connection.cursor()
    cur.execute("SELECT 1 FROM booking WHERE bike_no=%s AND booking_status='Booked'", (bike_no,))
    if cur.fetchone():
        flash('Cannot delete — bike is currently booked.', 'danger')
    else:
        cur.execute("DELETE FROM bike WHERE bike_no = %s", (bike_no,))
        database.connection.commit()
        flash('Bike deleted.', 'success')
    return redirect(url_for('view_bikes'))

@app.route('/api/models/<brand_name>')
@login_required
def get_models(brand_name):
    cur = database.connection.cursor()
    cur.execute("SELECT DISTINCT brand_model FROM bike_brand WHERE brand_name=%s", (brand_name,))
    models = [r['brand_model'] for r in cur.fetchall()]
    return jsonify(models)

@app.route('/api/bike_nos/<brand_name>/<brand_model>')
@login_required
def get_bike_nos(brand_name, brand_model):
    cur = database.connection.cursor()
    cur.execute("SELECT bike_no FROM bike WHERE brand_name=%s AND brand_model=%s AND bike_status='Available'",
                (brand_name, brand_model))
    nos = [r['bike_no'] for r in cur.fetchall()]
    return jsonify(nos)

@app.route('/api/bike_details/<bike_no>')
@login_required
def get_bike_details(bike_no):
    cur = database.connection.cursor()
    cur.execute("SELECT * FROM bike WHERE bike_no=%s", (bike_no,))
    return jsonify(cur.fetchone())

# ─── Users ───────────────────────────────────────────────────────────────────

@app.route('/users')
@login_required
@admin_required
def view_users():
    cur = database.connection.cursor()
    cur.execute("SELECT * FROM user")
    users = cur.fetchall()
    return render_template('view_users.html', users=users)

@app.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    cur = database.connection.cursor()
    cur.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
    database.connection.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('view_users'))

@app.route('/users/update', methods=['GET', 'POST'])
@login_required
def update_user():
    cur = database.connection.cursor()
    if session['role'] == 'admin':
        cur.execute("SELECT username, user_id FROM user")
        users = cur.fetchall()
    else:
        cur.execute("SELECT username, user_id FROM user WHERE user_id=%s", (session['user_id'],))
        users = cur.fetchall()

    selected_user = None
    if request.method == 'POST' and 'load' in request.form:
        uid = request.form['user_id']
        cur.execute("SELECT * FROM user WHERE user_id=%s", (uid,))
        selected_user = cur.fetchone()

    if request.method == 'POST' and 'save' in request.form:
        d = request.form
        cur.execute("""UPDATE user SET name=%s, email=%s, father_name=%s,
            phone=%s, qualification=%s, city=%s, gender=%s, blood=%s,
            age=%s, dob=%s, address=%s WHERE user_id=%s""",
            (d['name'], d['email'], d['father_name'], d['phone'],
             d['qualification'], d['city'], d['gender'], d['blood'],
             d['age'], d['dob'], d['address'], d['user_id']))
        database.connection.commit()
        flash('User updated!', 'success')
        return redirect(url_for('update_user'))

    return render_template('update_user.html', users=users, selected_user=selected_user)

# ─── Bookings ────────────────────────────────────────────────────────────────

@app.route('/bookings')
@login_required
def view_bookings():
    cur = database.connection.cursor()
    if session['role'] == 'admin':
        cur.execute("SELECT * FROM booking ORDER BY booking_date DESC")
    else:
        cur.execute("SELECT * FROM booking WHERE customer_username=%s ORDER BY booking_date DESC",
                    (session['username'],))
    bookings = cur.fetchall()
    return render_template('view_bookings.html', bookings=bookings)

@app.route('/bookings/add', methods=['GET', 'POST'])
@login_required
def add_booking():
    cur = database.connection.cursor()
    if request.method == 'POST':
        d = request.form
        days       = int(d['total_days'])
        total_rent = days * int(d['bike_rent'])
        cur.execute("""INSERT INTO booking
            (customer_username, customer_name, customer_phone,
             brand_name, brand_model, bike_no, bike_name,
             bike_category, bike_mileage, bike_rent, total_days, booking_status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Booked')""",
            (d['customer_username'], d['customer_name'], d['customer_phone'],
             d['brand_name'], d['brand_model'], d['bike_no'], d['bike_name'],
             d['bike_category'], d['bike_mileage'], total_rent, days))
        cur.execute("UPDATE bike SET bike_status='Booked' WHERE bike_no=%s", (d['bike_no'],))
        database.connection.commit()
        flash('Bike booked successfully!', 'success')
        return redirect(url_for('view_bookings'))

    cur.execute("SELECT DISTINCT brand_name FROM bike")
    brands = cur.fetchall()
    if session['role'] == 'admin':
        cur.execute("SELECT username, user_id, name, phone FROM user")
    else:
        cur.execute("SELECT username, user_id, name, phone FROM user WHERE user_id=%s",
                    (session['user_id'],))
    users = cur.fetchall()
    return render_template('add_booking.html', brands=brands, users=users)

@app.route('/bookings/complete/<int:booking_id>')
@login_required
@admin_required
def complete_booking(booking_id):
    cur = database.connection.cursor()
    cur.execute("SELECT bike_no FROM booking WHERE booking_id=%s", (booking_id,))
    b = cur.fetchone()
    cur.execute("UPDATE booking SET booking_status='Complete' WHERE booking_id=%s", (booking_id,))
    cur.execute("UPDATE bike SET bike_status='Available' WHERE bike_no=%s", (b['bike_no'],))
    database.connection.commit()
    flash('Booking marked as complete.', 'success')
    return redirect(url_for('view_bookings'))

@app.route('/bookings/cancel/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    cur = database.connection.cursor()
    cur.execute("SELECT bike_no, customer_username FROM booking WHERE booking_id=%s", (booking_id,))
    b = cur.fetchone()
    if not b:
        flash('Booking not found.', 'danger')
        return redirect(url_for('view_bookings'))
    # users can only cancel their own bookings
    if session['role'] != 'admin' and b['customer_username'] != session['username']:
        flash('You can only cancel your own bookings.', 'danger')
        return redirect(url_for('view_bookings'))
    cur.execute("UPDATE booking SET booking_status='Cancelled' WHERE booking_id=%s", (booking_id,))
    cur.execute("UPDATE bike SET bike_status='Available' WHERE bike_no=%s", (b['bike_no'],))
    database.connection.commit()
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('view_bookings'))

# ─── Billing ─────────────────────────────────────────────────────────────────

@app.route('/bill')
@login_required
def check_bill():
    cur = database.connection.cursor()
    if session['role'] == 'admin':
        cur.execute("SELECT DISTINCT customer_username FROM booking")
    else:
        cur.execute("SELECT DISTINCT customer_username FROM booking WHERE customer_username=%s",
                    (session['username'],))
    customers = cur.fetchall()
    return render_template('check_bill.html', customers=customers)

@app.route('/api/bill/<customer_username>/<int:booking_id>')
@login_required
def get_bill(customer_username, booking_id):
    cur = database.connection.cursor()
    cur.execute("SELECT * FROM booking WHERE customer_username=%s AND booking_id=%s",
                (customer_username, booking_id))
    b = cur.fetchone()
    if b:
        gross = b['bike_rent']
        tax   = round(gross * 0.021, 2)
        b['tax']   = tax
        b['total'] = round(gross + tax, 2)
        b['booking_date'] = str(b['booking_date'])
    return jsonify(b)

@app.route('/api/bookings_for_user/<customer_username>')
@login_required
def bookings_for_user(customer_username):
    cur = database.connection.cursor()
    cur.execute("SELECT booking_id FROM booking WHERE customer_username=%s", (customer_username,))
    ids = [r['booking_id'] for r in cur.fetchall()]
    return jsonify(ids)

if __name__ == '__main__':
    app.run(debug=True)