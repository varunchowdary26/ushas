import csv
import io
import random
from datetime import datetime
from flask import Flask, Response, jsonify, send_from_directory, request
import psycopg2
from psycopg2.extras import RealDictCursor

# Configured to read HTML/JS directly from root directory instead of templates/
app = Flask(__name__, template_folder='.', static_folder='.')

# --- POSTGRESQL CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "database": "ushas_beauty_db",
    "user": "postgres",
    "password": "your_password",  # Update with your PostgreSQL password
    "port": 5432,
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(15) NOT NULL,
                email VARCHAR(100),
                service VARCHAR(100) NOT NULL,
                price NUMERIC(10, 2) DEFAULT 0,
                date DATE NOT NULL,
                time TIME NOT NULL,
                notes TEXT,
                status VARCHAR(20) DEFAULT 'Confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("PostgreSQL Database initialized successfully.")
    except Exception as e:
        print("Warning: Database initialization failed:", e)


# --- ROUTING FOR ROOT-LEVEL HTML FILES ---


@app.route("/")
def home():
    return send_from_directory('.', 'index.html')


@app.route("/my-bookings")
def my_bookings():
    return send_from_directory('.', 'my-bookings.html')


@app.route("/admin")
def admin_dashboard():
    return send_from_directory('.', 'admin.html')


@app.route("/admin-login")
@app.route("/login")
def admin_login():
    return send_from_directory('.', 'admin-login.html')


@app.route("/feedbackindex")
def feedback_index():
    return send_from_directory('.', 'feedbackindex.html')


@app.route("/feedbackdash")
def feedback_dash():
    return send_from_directory('.', 'feedbackdash.html')


# Catch-all to serve static assets like script.js directly from root
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


# --- API ENDPOINTS ---


@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.json or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    service = data.get("service", "")
    price = float(data.get("price", 0))
    date = data.get("date", "")
    time = data.get("time", "")
    notes = data.get("notes", "").strip()

    if not all([name, phone, service, date, time]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for duplicate time slot
        cursor.execute(
            "SELECT id FROM bookings WHERE date = %s AND time = %s",
            (date, time),
        )
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "This time slot is already booked."}), 409

        booking_id = f"USH-{random.randint(100000, 999999)}"

        cursor.execute(
            """
            INSERT INTO bookings (id, name, phone, email, service, price, date, time, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                booking_id,
                name,
                phone,
                email,
                service,
                price,
                date,
                time,
                notes,
            ),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "success": True,
                    "booking": {
                        "id": booking_id,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "service": service,
                        "price": price,
                        "date": str(date),
                        "time": str(time),
                        "notes": notes,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/bookings/search", methods=["GET"])
def search_bookings():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT id, name, phone, email, service, price, 
                   to_char(date, 'YYYY-MM-DD') as date, 
                   to_char(time, 'HH24:MI') as time, 
                   notes, status 
            FROM bookings 
            WHERE phone LIKE %s OR id ILIKE %s
            ORDER BY date DESC, time DESC
        """,
            (f"%{query}%", f"%{query}%"),
        )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify([dict(row) for row in rows])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/bookings", methods=["GET"])
def get_all_bookings():
    month = request.args.get("month", "")
    search = request.args.get("search", "").lower().strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT id, name, phone, email, service, price, 
                   to_char(date, 'YYYY-MM-DD') as date, 
                   to_char(time, 'HH24:MI') as time, 
                   notes, status 
            FROM bookings 
            ORDER BY date DESC, time DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        result = []
        for row in rows:
            b = dict(row)
            b["price"] = float(b["price"]) if b["price"] is not None else 0
            matches_month = not month or b["date"].startswith(month)
            matches_search = not search or (
                search in b["name"].lower()
                or search in b["phone"]
                or search in b["service"].lower()
                or search in b["id"].lower()
            )
            if matches_month and matches_search:
                result.append(b)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, phone, email, service, price, 
                   to_char(date, 'YYYY-MM-DD'), to_char(time, 'HH24:MI'), notes 
            FROM bookings 
            ORDER BY date DESC, time DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Booking ID",
                "Customer",
                "Phone",
                "Email",
                "Service",
                "Price",
                "Date",
                "Time",
                "Notes",
            ]
        )
        writer.writerows(rows)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-disposition": f"attachment; filename=bookings-{datetime.now().strftime('%Y-%m-%d')}.csv"
            },
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)