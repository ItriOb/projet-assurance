from flask import Flask, render_template, request, redirect, url_for, session, flash
import config
import mysql.connector as connector
from werkzeug.utils import secure_filename
import os
from ultralytics import YOLO
import bcrypt
from collections import Counter
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


def connect_to_db():
    try:
        # Added buffered=True to automatically consume results
        connection = connector.connect(**config.mysql_credentials, buffered=True)
        return connection
    except connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        email = request.form.get('email')
        vehicle_id = request.form.get('vehicleId')
        contact_number = request.form.get('phoneNumber')
        address = request.form.get('address')
        car_brand = request.form.get('carBrand')
        model = request.form.get('carModel')

        # Debug: Print all form data
        print(f"Form data: {request.form}")

        if not all([name, password, email, vehicle_id, contact_number, address, car_brand, model]):
            flash("All fields are required!", "error")
            return render_template('signup.html')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        connection = None
        try:
            connection = connect_to_db()
            if not connection:
                flash("Database connection failed. Please try again later.", "error")
                return render_template('signup.html')

            cursor = connection.cursor()
            query = '''
            INSERT INTO user_info (name, password, email, vehicle_id, contact_number, address, car_brand, model)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, (name, hashed_password, email, vehicle_id, contact_number, address, car_brand, model))
            connection.commit()

            # Verify the insertion by checking if the user was created
            verify_query = "SELECT * FROM user_info WHERE email = %s"
            cursor.execute(verify_query, (email,))
            user = cursor.fetchone()

            if user:
                # Store user email in session
                session['user_email'] = email
                flash("Signup successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Failed to create user. Please try again.", "error")

        except connector.IntegrityError as e:
            print(f"IntegrityError: {e}")
            if 'Duplicate entry' in str(e):
                flash("Email already exists. Please use a different email.", "error")
            else:
                flash(f"Database integrity error: {str(e)}", "error")

        except connector.Error as e:
            print(f"MySQL Error: {e}")
            flash(f"Database error: {str(e)}", "error")

        finally:
            if connection:
                if 'cursor' in locals():
                    cursor.close()
                connection.close()

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Login attempt - Email: {email}")

        if not email or not password:
            flash("Email and password are required!", "error")
            return render_template('login.html')

        connection = None
        try:
            connection = connect_to_db()
            if not connection:
                flash("Database connection failed. Please try again later.", "error")
                return render_template('login.html')

            cursor = connection.cursor(buffered=True)
            query = "SELECT password FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()

            if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
                session['user_email'] = email  # Store user email in session
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password.", "error")

        except connector.Error as e:
            print(f"Error executing query: {e}")
            flash("An error occurred during login. Please try again.", "error")

        finally:
            if connection:
                if 'cursor' in locals():
                    cursor.close()
                connection.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_email', None)  # Remove user email from session
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


# Load YOLO model
model_path = "/Users/itri.obanni/Documents/Projects/Python/accident-damage-detection/models/best.pt"
model = YOLO(model_path)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_email' not in session:
        flash("Please login to access the dashboard.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('image')
        if not file:
            flash('Please upload an image.', 'error')
            return render_template('dashboard.html')

        filename = secure_filename(file.filename)
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            flash('Invalid file type. Please upload an image.', 'error')
            return render_template('dashboard.html')

        # Save the uploaded image
        image_path = os.path.join('/Users/itri.obanni/Documents/Projects/Python/accident-damage-detection/static', 'uploaded_image.jpg')
        print("File uploaded successfully")

        file.save(image_path)

        # Make predictions using YOLO
        result = model(image_path)
        print(result)
        detected_objects = result[0].boxes
        class_ids = [box.cls.item() for box in detected_objects]
        class_counts = Counter(class_ids)

        # Save the image with detections
        detected_image_path = os.path.join('/Users/itri.obanni/Documents/Projects/Python/accident-damage-detection/static', 'detected_image.jpg')
        detected_image_path = result[0].save(detected_image_path)
        print(f"Detected image path: {detected_image_path}")

        # Get the user's email from session
        user_email = session.get('user_email')
        if not user_email:
            flash('You need to log in to get an estimate.', 'error')
            return redirect(url_for('login'))

        # Fetch part prices from the database
        part_prices = get_part_prices(user_email, class_counts)
        return render_template('estimate.html', original_image='uploaded_image.jpg', detected_image='detected_image.jpg', part_prices=part_prices)

    return render_template('dashboard.html')


def get_part_prices(email, class_counts):
    connection = None
    try:
        connection = connect_to_db()
        if not connection:
            print("Database connection failed")
            return {}

        cursor = connection.cursor(dictionary=True, buffered=True)

        # Get user's car brand and model
        cursor.execute("SELECT car_brand, model FROM user_info WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        if not user_data:
            print(f"User with email {email} not found")
            return {}

        car_brand = user_data['car_brand']
        car_model = user_data['model']
        print(f"User car: {car_brand} {car_model}")

        # Fetch part prices
        prices = {}
        for class_id, count in class_counts.items():
            part_name = get_part_name_from_id(class_id)
            print(f"Parts name: {part_name}")

            if part_name:
                cursor.execute(
                    "SELECT price FROM car_models WHERE brand = %s AND model = %s AND part = %s",
                    (car_brand, car_model, part_name)
                )
                price_data = cursor.fetchone()
                print(f"Price data: {price_data}")

                if price_data:
                    price_per_part = price_data['price']
                    total_price = price_per_part * count
                    prices[part_name] = {'count': count, 'price': price_per_part, 'total': total_price}

        return prices

    except connector.Error as e:
        print(f"Error executing query: {e}")
        return {}

    finally:
        if connection:
            if 'cursor' in locals():
                cursor.close()
            connection.close()


def get_part_name_from_id(class_id):
    class_names = ['Bonnet', 'Bumper', 'Dickey', 'Door', 'Fender', 'Light', 'Windshield']
    if 0 <= class_id < len(class_names):
        return class_names[int(class_id)]
    return None


@app.route('/view_profile')
def view_profile():
    if 'user_email' not in session:
        flash('You need to login to view your profile.', 'error')
        return redirect(url_for('login'))

    connection = None
    try:
        connection = connect_to_db()
        if not connection:
            flash("Database connection failed. Please try again later.", "error")
            return redirect(url_for('dashboard'))

        cursor = connection.cursor(dictionary=True)

        # Fetch current user information
        cursor.execute("SELECT * FROM user_info WHERE email = %s", (session['user_email'],))
        user_info = cursor.fetchone()

        if not user_info:
            flash('User not found.', 'error')
            return redirect(url_for('dashboard'))

        return render_template('view_profile.html', user_info=user_info)

    except connector.Error as e:
        print(f"Error executing query: {e}")
        flash("An error occurred while fetching your profile. Please try again.", "error")
        return redirect(url_for('dashboard'))

    finally:
        if connection:
            if 'cursor' in locals():
                cursor.close()
            connection.close()


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_email' not in session:
        flash('You need to login to edit your profile.', 'error')
        return redirect(url_for('login'))

    connection = None
    try:
        connection = connect_to_db()
        if not connection:
            flash("Database connection failed. Please try again later.", "error")
            return redirect(url_for('dashboard'))

        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':
            # Debug: Print all form data
            print(f"Edit profile form data: {request.form}")

            # Store the old email to check if it was changed
            old_email = session['user_email']
            new_email = request.form['email']

            # Update user information
            query = '''
            UPDATE user_info
            SET name = %s, email = %s, vehicle_id = %s, contact_number = %s, 
                address = %s, car_brand = %s, model = %s
            WHERE email = %s
            '''

            params = (
                request.form['name'],
                new_email,
                request.form['vehicleId'],
                request.form['phoneNumber'],
                request.form['address'],
                request.form['carBrand'],
                request.form['carModel'],
                old_email
            )

            print(f"Update query: {query}")
            print(f"Parameters: {params}")

            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            connection.commit()

            print(f"Rows affected: {affected_rows}")

            if affected_rows > 0:
                # Verify the update
                verify_query = "SELECT * FROM user_info WHERE email = %s"
                cursor.execute(verify_query, (new_email,))
                user = cursor.fetchone()

                if user:
                    # Update session if email changed
                    session['user_email'] = new_email
                    flash('Profile updated successfully!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Profile update failed. Please try again.', 'error')
            else:
                flash('No changes were made or user not found.', 'warning')

            return redirect(url_for('edit_profile'))

        # Fetch current user information for GET request
        cursor.execute("SELECT * FROM user_info WHERE email = %s", (session['user_email'],))
        user_info = cursor.fetchone()

        if not user_info:
            flash('User not found.', 'error')
            return redirect(url_for('dashboard'))

        return render_template('edit_profile.html', user_info=user_info)

    except connector.Error as e:
        print(f"Error executing query: {e}")
        flash(f"An error occurred while updating your profile: {str(e)}", "error")
        return redirect(url_for('dashboard'))

    finally:
        if connection:
            if 'cursor' in locals():
                cursor.close()
            connection.close()


if __name__ == '__main__':
    app.run(debug=True)