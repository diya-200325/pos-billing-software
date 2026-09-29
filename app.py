from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
import math
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "pos-secret-key")


# ============================================================
# VALIDATION HELPERS
# ============================================================

def clean_text(value):
    """Remove unnecessary spaces from text input."""
    return value.strip() if value else ""


def is_valid_email(email):
    """Check whether an email has a basic valid format."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone):
    """Validate phone number if one is provided."""
    if not phone:
        return True

    digits = re.sub(r"\D", "", phone)

    return 10 <= len(digits) <= 15


def is_valid_non_negative_number(value):
    """Check for a valid number >= 0."""
    try:
        number = float(value)

        return (
            math.isfinite(number)
            and number >= 0
        )

    except (ValueError, TypeError):
        return False


def is_valid_non_negative_integer(value):
    """Check for a valid whole number >= 0."""
    try:
        number = int(value)

        return number >= 0

    except (ValueError, TypeError):
        return False


def is_valid_positive_integer(value):
    """Check for a valid whole number >= 1."""
    try:
        number = int(value)

        return number >= 1

    except (ValueError, TypeError):
        return False


# ============================================================
# DATABASE
# ============================================================

def create_database():

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            supplier TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            staff_id INTEGER NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            change_amount REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (staff_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            refund_amount REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# DEFAULT USERS
# ============================================================

def create_default_users():

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    admin_password = generate_password_hash("admin123")

    cursor.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, ("admin@pos.com",))

    admin = cursor.fetchone()

    if admin:

        cursor.execute("""
            UPDATE users
            SET password = ?,
                role = 'admin'
            WHERE email = ?
        """, (
            admin_password,
            "admin@pos.com"
        ))

    else:

        cursor.execute("""
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Admin",
            "admin@pos.com",
            admin_password,
            "admin"
        ))

    # --------------------------------------------------------
    # STAFF
    # --------------------------------------------------------

    staff_password = generate_password_hash("staff123")

    cursor.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, ("staff@pos.com",))

    staff = cursor.fetchone()

    if staff:

        cursor.execute("""
            UPDATE users
            SET password = ?,
                role = 'staff'
            WHERE email = ?
        """, (
            staff_password,
            "staff@pos.com"
        ))

    else:

        cursor.execute("""
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Staff",
            "staff@pos.com",
            staff_password,
            "staff"
        ))

    connection.commit()
    connection.close()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/admin-login")
def admin_login_page():

    return render_template("admin_login.html")


@app.route("/admin-login", methods=["POST"])
def admin_login():

    email = clean_text(
        request.form.get("email")
    ).lower()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:
        return "Email and password are required"

    if not is_valid_email(email):
        return "Please enter a valid email address"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email, password, role
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    connection.close()

    if user and user[4] == "admin":

        try:

            password_valid = check_password_hash(
                user[3],
                password
            )

        except Exception:

            password_valid = False

        if password_valid:

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_role"] = user[4]
            session["cart"] = []

            return redirect(
                url_for("admin_dashboard")
            )

    return "Invalid admin email or password"


# ============================================================
# MOBILE ADMIN
# ============================================================

@app.route("/admin-mobile")
def admin_mobile():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    return render_template(
        "admin_mobile.html"
    )


# ============================================================
# STAFF LOGIN
# ============================================================

@app.route("/staff-login")
def staff_login_page():

    return render_template(
        "staff_login.html"
    )


@app.route("/staff-login", methods=["POST"])
def staff_login():

    email = clean_text(
        request.form.get("email")
    ).lower()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:
        return "Email and password are required"

    if not is_valid_email(email):
        return "Please enter a valid email address"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email, password, role
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    connection.close()

    if user and user[4] == "staff":

        try:

            password_valid = check_password_hash(
                user[3],
                password
            )

        except Exception:

            password_valid = False

        if password_valid:

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_role"] = user[4]
            session["cart"] = []

            return redirect(
                url_for("staff_dashboard")
            )

    return "Invalid staff email or password"


# ============================================================
# ADMIN DASHBOARD
# ============================================================
@app.route("/admin/mobile")
def admin_mobile():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    return render_template("admin_mobile.html")
@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
    """)

    total_products = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role = 'staff'
    """)

    total_staff = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM suppliers
    """)

    total_suppliers = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
    """)

    total_transactions = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM transactions
    """)

    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE DATE(created_at) = DATE('now')
    """)

    today_transactions = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM transactions
        WHERE DATE(created_at) = DATE('now')
    """)

    today_sales = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "admin_dashboard.html",
        total_products=total_products,
        total_staff=total_staff,
        total_suppliers=total_suppliers,
        total_transactions=total_transactions,
        total_sales=total_sales,
        today_transactions=today_transactions,
        today_sales=today_sales
    )


# ============================================================
# STAFF DASHBOARD
# ============================================================

@app.route("/staff")
def staff_dashboard():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "staff":
        return "Access denied"

    return redirect(
        url_for("billing")
    )


# ============================================================
# BILLING
# ============================================================

@app.route("/billing")
def billing():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "staff":
        return "Access denied"

    search = clean_text(
        request.args.get("search", "")
    )

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    if search:

        cursor.execute("""
            SELECT *
            FROM products
            WHERE name LIKE ?
               OR category LIKE ?
            ORDER BY id DESC
        """, (
            "%" + search + "%",
            "%" + search + "%"
        ))

    else:

        cursor.execute("""
            SELECT *
            FROM products
            ORDER BY id DESC
        """)

    products = cursor.fetchall()

    connection.close()

    cart = session.get(
        "cart",
        []
    )

    cart_total = 0

    for item in cart:

        cart_total += (
            item["price"]
            * item["quantity"]
        )

    return render_template(
        "staff_dashboard.html",
        products=products,
        search=search,
        cart=cart,
        cart_total=cart_total
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# ADD TO CART
# ============================================================

@app.route("/cart/add", methods=["POST"])
def add_to_cart():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "staff":
        return "Access denied"

    try:

        product_id = int(
            request.form.get("product_id")
        )

        quantity = int(
            request.form.get("quantity")
        )

    except (ValueError, TypeError):

        return "Invalid product or quantity"

    if quantity < 1:
        return "Quantity must be at least 1"

    if quantity > 100000:
        return "Quantity is too large"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, price, stock
        FROM products
        WHERE id = ?
    """, (product_id,))

    product = cursor.fetchone()

    connection.close()

    if not product:
        return "Product not found"

    if product[2] < 0 or product[3] < 0:
        return "Product has invalid price or stock"

    if product[3] == 0:
        return "This product is out of stock"

    if quantity > product[3]:
        return "Not enough stock"

    cart = session.get(
        "cart",
        []
    )

    found = False

    for item in cart:

        if item["product_id"] == product[0]:

            new_quantity = (
                item["quantity"]
                + quantity
            )

            if new_quantity > product[3]:
                return "Not enough stock"

            item["quantity"] = new_quantity

            found = True

            break

    if not found:

        cart.append({
            "product_id": product[0],
            "name": product[1],
            "price": product[2],
            "quantity": quantity
        })

    session["cart"] = cart

    return redirect(
        url_for("billing")
    )


# ============================================================
# UPDATE CART
# ============================================================

@app.route("/cart/update", methods=["POST"])
def update_cart():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "staff":
        return "Access denied"

    try:

        product_id = int(
            request.form.get("product_id")
        )

        quantity = int(
            request.form.get("quantity")
        )

    except (ValueError, TypeError):

        return "Invalid product or quantity"

    if quantity < 1:
        return "Quantity must be at least 1"

    if quantity > 100000:
        return "Quantity is too large"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT stock
        FROM products
        WHERE id = ?
    """, (product_id,))

    product = cursor.fetchone()

    connection.close()

    if not product:
        return "Product not found"

    if product[0] < 0:
        return "Product has invalid stock"

    if quantity > product[0]:
        return "Not enough stock"

    cart = session.get(
        "cart",
        []
    )

    found = False

    for item in cart:

        if item["product_id"] == product_id:

            item["quantity"] = quantity
            found = True

            break

    if not found:
        return "Product is not in the cart"

    session["cart"] = cart

    return redirect(
        url_for("billing")
    )


# ============================================================
# REMOVE FROM CART
# ============================================================

@app.route("/cart/remove", methods=["POST"])
def remove_from_cart():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "staff":
        return "Access denied"

    try:

        product_id = int(
            request.form.get("product_id")
        )

    except (ValueError, TypeError):

        return "Invalid product"

    cart = session.get(
        "cart",
        []
    )

    cart = [
        item
        for item in cart
        if item["product_id"] != product_id
    ]

    session["cart"] = cart

    return redirect(
        url_for("billing")
    )


# ============================================================
# CHECKOUT
# ============================================================

@app.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "staff":
        return "Access denied"

    cart = session.get(
        "cart",
        []
    )

    if not cart:
        return "Cart is empty"

    total = 0

    for item in cart:

        if item["quantity"] < 1:
            return "Invalid cart quantity"

        if item["price"] < 0:
            return "Invalid product price"

        total += (
            item["price"]
            * item["quantity"]
        )

    if not math.isfinite(total):
        return "Invalid transaction total"

    return render_template(
        "checkout.html",
        cart=cart,
        total=total
    )


# ============================================================
# PAYMENT
# ============================================================

@app.route("/payment", methods=["POST"])
def payment():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "staff":
        return "Access denied"

    cart = session.get(
        "cart",
        []
    )

    if not cart:
        return "Cart is empty"

    # --------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------

    payment_method = clean_text(
        request.form.get(
            "payment_method"
        )
    )

    allowed_payment_methods = [
        "Cash",
        "UPI",
        "Card"
    ]

    if payment_method not in allowed_payment_methods:
        return "Invalid payment method"

    # --------------------------------------------------------
    # AMOUNT PAID
    # --------------------------------------------------------

    amount_paid_text = clean_text(
        request.form.get(
            "amount_paid"
        )
    )

    try:

        amount_paid = float(
            amount_paid_text
        )

    except (ValueError, TypeError):

        return "Please enter a valid payment amount"

    if not math.isfinite(amount_paid):
        return "Invalid payment amount"

    if amount_paid < 0:
        return "Payment amount cannot be negative"

    # --------------------------------------------------------
    # CALCULATE TOTAL
    # --------------------------------------------------------

    total = 0

    for item in cart:

        if not is_valid_positive_integer(
            item.get("quantity")
        ):
            return "Invalid cart quantity"

        try:

            price = float(
                item.get("price")
            )

        except (ValueError, TypeError):

            return "Invalid product price"

        if not math.isfinite(price) or price < 0:
            return "Invalid product price"

        total += (
            price
            * item["quantity"]
        )

    if not math.isfinite(total) or total < 0:
        return "Invalid transaction total"

    # --------------------------------------------------------
    # PAYMENT CHECK
    # --------------------------------------------------------

    if amount_paid < total:
        return (
            "Amount paid is less than "
            "the total amount"
        )

    change_amount = (
        amount_paid - total
    )

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # RECHECK PRODUCTS AND STOCK
        # ----------------------------------------------------

        verified_cart = []

        for item in cart:

            product_id = item["product_id"]

            cursor.execute("""
                SELECT id, name, price, stock
                FROM products
                WHERE id = ?
            """, (product_id,))

            product = cursor.fetchone()

            if not product:

                connection.rollback()
                connection.close()

                return (
                    "Product no longer exists"
                )

            database_price = float(
                product[2]
            )

            database_stock = int(
                product[3]
            )

            if database_price < 0:
                connection.rollback()
                connection.close()

                return (
                    "Product has an invalid price"
                )

            if database_stock < 0:
                connection.rollback()
                connection.close()

                return (
                    "Product has invalid stock"
                )

            if item["quantity"] > database_stock:

                connection.rollback()
                connection.close()

                return (
                    "Not enough stock for "
                    + product[1]
                )

            # Use current database price.
            verified_cart.append({
                "product_id": product[0],
                "name": product[1],
                "price": database_price,
                "quantity": item["quantity"]
            })

        # ----------------------------------------------------
        # RECALCULATE TOTAL USING DATABASE PRICES
        # ----------------------------------------------------

        cart = verified_cart

        total = 0

        for item in cart:

            total += (
                item["price"]
                * item["quantity"]
            )

        if amount_paid < total:

            connection.rollback()
            connection.close()

            return (
                "Amount paid is less than "
                "the updated total amount"
            )

        change_amount = (
            amount_paid - total
        )

        # ----------------------------------------------------
        # CREATE UNIQUE INVOICE NUMBER
        # ----------------------------------------------------

        invoice_no = (
            "INV-"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            + "-"
            + uuid.uuid4().hex[:6].upper()
        )

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # ----------------------------------------------------
        # CREATE TRANSACTION
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO transactions
            (
                invoice_no,
                staff_id,
                total,
                payment_method,
                amount_paid,
                change_amount,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_no,
            session["user_id"],
            total,
            payment_method,
            amount_paid,
            change_amount,
            created_at
        ))

        transaction_id = cursor.lastrowid

        # ----------------------------------------------------
        # CREATE TRANSACTION ITEMS
        # ----------------------------------------------------

        for item in cart:

            line_total = (
                item["price"]
                * item["quantity"]
            )

            cursor.execute("""
                INSERT INTO transaction_items
                (
                    transaction_id,
                    product_id,
                    quantity,
                    price,
                    line_total
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                transaction_id,
                item["product_id"],
                item["quantity"],
                item["price"],
                line_total
            ))

            # ------------------------------------------------
            # REDUCE STOCK
            # ------------------------------------------------

            cursor.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
                AND stock >= ?
            """, (
                item["quantity"],
                item["product_id"],
                item["quantity"]
            ))

            if cursor.rowcount != 1:

                raise sqlite3.Error(
                    "Stock update failed"
                )

        # ----------------------------------------------------
        # COMMIT EVERYTHING
        # ----------------------------------------------------

        connection.commit()

    except sqlite3.Error as error:

        connection.rollback()
        connection.close()

        return (
            "Payment could not be completed: "
            + str(error)
        )

    except Exception as error:

        connection.rollback()
        connection.close()

        return (
            "Unexpected payment error: "
            + str(error)
        )

    connection.close()

    session["cart"] = []

    return render_template(
        "invoice.html",
        invoice_no=invoice_no,
        cart=cart,
        total=total,
        payment_method=payment_method,
        amount_paid=amount_paid,
        change_amount=change_amount,
        created_at=created_at
    )


# ============================================================
# TRANSACTIONS
# ============================================================

@app.route("/transactions")
def transactions():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            transactions.id,
            transactions.invoice_no,
            users.name,
            transactions.total,
            transactions.payment_method,
            transactions.amount_paid,
            transactions.change_amount,
            transactions.created_at
        FROM transactions
        JOIN users
        ON transactions.staff_id = users.id
        ORDER BY transactions.id DESC
    """)

    transaction_list = cursor.fetchall()

    connection.close()

    return render_template(
        "transactions.html",
        transactions=transaction_list
    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM transactions
    """)

    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
    """)

    total_transactions = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            payment_method,
            COUNT(*),
            COALESCE(SUM(total), 0)
        FROM transactions
        GROUP BY payment_method
        ORDER BY payment_method
    """)

    payment_summary = cursor.fetchall()

    cursor.execute("""
        SELECT
            transactions.invoice_no,
            users.name,
            transactions.total,
            transactions.payment_method,
            transactions.created_at
        FROM transactions
        JOIN users
            ON transactions.staff_id = users.id
        ORDER BY transactions.id DESC
    """)

    sales = cursor.fetchall()

    cursor.execute("""
        SELECT
            transactions.created_at,
            transactions.invoice_no,
            'Sales' AS description,
            transactions.payment_method,
            transactions.total
        FROM transactions
        ORDER BY transactions.id DESC
    """)

    ledger = cursor.fetchall()

    connection.close()

    return render_template(
        "reports.html",
        total_sales=total_sales,
        total_transactions=total_transactions,
        payment_summary=payment_summary,
        sales=sales,
        ledger=ledger
    )


# ============================================================
# RETURNS
# ============================================================

@app.route("/returns")
def returns():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect("pos.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            returns.id,
            transactions.invoice_no,
            products.name,
            returns.quantity,
            returns.refund_amount,
            returns.created_at
        FROM returns
        JOIN transactions
            ON returns.transaction_id = transactions.id
        JOIN products
            ON returns.product_id = products.id
        ORDER BY returns.id DESC
    """)

    return_list = cursor.fetchall()

    cursor.execute("""
        SELECT
            transaction_items.transaction_id,
            transaction_items.product_id,
            transactions.invoice_no,
            products.name,
            transaction_items.quantity,
            transaction_items.price,
            COALESCE(
                (
                    SELECT SUM(returns.quantity)
                    FROM returns
                    WHERE returns.transaction_id =
                          transaction_items.transaction_id
                    AND returns.product_id =
                          transaction_items.product_id
                ),
                0
            ) AS returned_quantity
        FROM transaction_items
        JOIN transactions
            ON transaction_items.transaction_id =
               transactions.id
        JOIN products
            ON transaction_items.product_id =
               products.id
        ORDER BY transaction_items.id DESC
    """)

    return_items = cursor.fetchall()

    connection.close()

    return render_template(
        "returns.html",
        returns=return_list,
        return_items=return_items
    )


# ============================================================
# PROCESS RETURN
# ============================================================

@app.route("/returns/process", methods=["POST"])
def process_return():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    try:

        transaction_id = int(
            request.form.get(
                "transaction_id"
            )
        )

        product_id = int(
            request.form.get(
                "product_id"
            )
        )

        quantity = int(
            request.form.get(
                "quantity"
            )
        )

    except (ValueError, TypeError):

        return "Invalid return information"

    if quantity < 1:
        return (
            "Return quantity must "
            "be at least 1"
        )

    if quantity > 100000:
        return "Return quantity is too large"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            transaction_items.quantity,
            transaction_items.price,
            products.name
        FROM transaction_items
        JOIN products
            ON transaction_items.product_id =
               products.id
        WHERE transaction_items.transaction_id = ?
        AND transaction_items.product_id = ?
    """, (
        transaction_id,
        product_id
    ))

    item = cursor.fetchone()

    if not item:

        connection.close()

        return (
            "Product not found in "
            "this transaction"
        )

    sold_quantity = item[0]
    price = item[1]

    if sold_quantity < 1:
        connection.close()

        return "Invalid sold quantity"

    if price < 0:
        connection.close()

        return "Invalid product price"

    cursor.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM returns
        WHERE transaction_id = ?
        AND product_id = ?
    """, (
        transaction_id,
        product_id
    ))

    already_returned = (
        cursor.fetchone()[0]
    )

    remaining_quantity = (
        sold_quantity
        - already_returned
    )

    if remaining_quantity <= 0:

        connection.close()

        return (
            "This product has already "
            "been completely returned"
        )

    if quantity > remaining_quantity:

        connection.close()

        return (
            "Return quantity cannot "
            "exceed remaining quantity: "
            + str(remaining_quantity)
        )

    refund_amount = (
        price * quantity
    )

    if not math.isfinite(
        refund_amount
    ):

        connection.close()

        return "Invalid refund amount"

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:

        cursor.execute("""
            INSERT INTO returns
            (
                transaction_id,
                product_id,
                quantity,
                refund_amount,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            transaction_id,
            product_id,
            quantity,
            refund_amount,
            created_at
        ))

        cursor.execute("""
            UPDATE products
            SET stock = stock + ?
            WHERE id = ?
        """, (
            quantity,
            product_id
        ))

        if cursor.rowcount != 1:
            raise sqlite3.Error(
                "Stock could not be restored"
            )

        connection.commit()

    except sqlite3.Error as error:

        connection.rollback()
        connection.close()

        return (
            "Return could not be processed: "
            + str(error)
        )

    except Exception as error:

        connection.rollback()
        connection.close()

        return (
            "Unexpected return error: "
            + str(error)
        )

    connection.close()

    return redirect(
        url_for("returns")
    )


# ============================================================
# PRODUCTS
# ============================================================

@app.route("/products")
def products():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    product_list = cursor.fetchall()

    connection.close()

    return render_template(
        "products.html",
        products=product_list
    )


# ============================================================
# ADD PRODUCT
# ============================================================

@app.route(
    "/products/add",
    methods=["GET", "POST"]
)
def add_product():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    if request.method == "POST":

        name = clean_text(
            request.form.get("name")
        )

        category = clean_text(
            request.form.get("category")
        )

        price = clean_text(
            request.form.get("price")
        )

        stock = clean_text(
            request.form.get("stock")
        )

        supplier = clean_text(
            request.form.get("supplier")
        )

        if not name:
            return "Product name is required"

        if not category:
            return "Product category is required"

        if len(name) > 100:
            return "Product name is too long"

        if len(category) > 100:
            return "Product category is too long"

        if not is_valid_non_negative_number(
            price
        ):
            return (
                "Price must be a valid "
                "number greater than or equal to 0"
            )

        if not is_valid_non_negative_integer(
            stock
        ):
            return (
                "Stock must be a valid "
                "whole number greater than or equal to 0"
            )

        connection = sqlite3.connect(
            "pos.db"
        )

        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO products
                (name, category, price, stock, supplier)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                category,
                float(price),
                int(stock),
                supplier
            ))

            connection.commit()

        except sqlite3.Error as error:

            connection.rollback()
            connection.close()

            return (
                "Product could not be added: "
                + str(error)
            )

        connection.close()

        return redirect(
            url_for("products")
        )

    return render_template(
        "add_product.html"
    )


# ============================================================
# EDIT PRODUCT
# ============================================================

@app.route(
    "/products/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_product(id):

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (id,))

    product = cursor.fetchone()

    if not product:

        connection.close()

        return "Product not found"

    if request.method == "POST":

        name = clean_text(
            request.form.get("name")
        )

        category = clean_text(
            request.form.get("category")
        )

        price = clean_text(
            request.form.get("price")
        )

        stock = clean_text(
            request.form.get("stock")
        )

        supplier = clean_text(
            request.form.get("supplier")
        )

        if not name:
            connection.close()

            return "Product name is required"

        if not category:
            connection.close()

            return "Product category is required"

        if len(name) > 100:
            connection.close()

            return "Product name is too long"

        if len(category) > 100:
            connection.close()

            return "Product category is too long"

        if not is_valid_non_negative_number(
            price
        ):
            connection.close()

            return (
                "Price must be a valid "
                "number greater than or equal to 0"
            )

        if not is_valid_non_negative_integer(
            stock
        ):
            connection.close()

            return (
                "Stock must be a valid "
                "whole number greater than or equal to 0"
            )

        try:

            cursor.execute("""
                UPDATE products
                SET name = ?,
                    category = ?,
                    price = ?,
                    stock = ?,
                    supplier = ?
                WHERE id = ?
            """, (
                name,
                category,
                float(price),
                int(stock),
                supplier,
                id
            ))

            if cursor.rowcount != 1:

                connection.rollback()
                connection.close()

                return "Product could not be updated"

            connection.commit()

        except sqlite3.Error as error:

            connection.rollback()
            connection.close()

            return (
                "Product could not be updated: "
                + str(error)
            )

        connection.close()

        return redirect(
            url_for("products")
        )

    connection.close()

    return render_template(
        "edit_product.html",
        product=product
    )


# ============================================================
# DELETE PRODUCT
# ============================================================

@app.route(
    "/products/delete/<int:id>"
)
def delete_product(id):

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    try:

        # Check whether the product exists.
        cursor.execute("""
            SELECT id
            FROM products
            WHERE id = ?
        """, (id,))

        product = cursor.fetchone()

        if not product:

            connection.close()

            return "Product not found"

        # Do not delete a product already used in sales.
        cursor.execute("""
            SELECT id
            FROM transaction_items
            WHERE product_id = ?
            LIMIT 1
        """, (id,))

        used_product = cursor.fetchone()

        if used_product:

            connection.close()

            return (
                "This product cannot be deleted "
                "because it has transaction history"
            )

        cursor.execute("""
            DELETE FROM products
            WHERE id = ?
        """, (id,))

        connection.commit()

    except sqlite3.Error as error:

        connection.rollback()
        connection.close()

        return (
            "Product could not be deleted: "
            + str(error)
        )

    connection.close()

    return redirect(
        url_for("products")
    )


# ============================================================
# STAFF MANAGEMENT
# ============================================================

@app.route("/staff-management")
def staff_management():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email, role
        FROM users
        WHERE role = 'staff'
        ORDER BY id DESC
    """)

    staff_members = cursor.fetchall()

    connection.close()

    return render_template(
        "staff.html",
        staff=staff_members
    )


# ============================================================
# ADD STAFF
# ============================================================

@app.route(
    "/staff/add",
    methods=["GET", "POST"]
)
def add_staff():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    if request.method == "POST":

        name = clean_text(
            request.form.get("name")
        )

        email = clean_text(
            request.form.get("email")
        ).lower()

        raw_password = request.form.get(
            "password",
            ""
        )

        if not name:
            return "Staff name is required"

        if not email:
            return "Staff email is required"

        if not raw_password:
            return "Password is required"

        if len(name) > 100:
            return "Staff name is too long"

        if not is_valid_email(email):
            return "Please enter a valid email address"

        if len(raw_password) < 6:
            return (
                "Password must contain "
                "at least 6 characters"
            )

        password = generate_password_hash(
            raw_password
        )

        connection = sqlite3.connect(
            "pos.db"
        )

        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (name, email, password, role)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                password,
                "staff"
            ))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.rollback()
            connection.close()

            return "Email already exists"

        except sqlite3.Error as error:

            connection.rollback()
            connection.close()

            return (
                "Staff member could not be added: "
                + str(error)
            )

        connection.close()

        return redirect(
            url_for("staff_management")
        )

    return render_template(
        "add_staff.html"
    )


# ============================================================
# EDIT STAFF
# ============================================================

@app.route(
    "/staff/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_staff(id):

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email, password
        FROM users
        WHERE id = ?
        AND role = 'staff'
    """, (id,))

    staff = cursor.fetchone()

    if not staff:

        connection.close()

        return "Staff member not found"

    if request.method == "POST":

        name = clean_text(
            request.form.get("name")
        )

        email = clean_text(
            request.form.get("email")
        ).lower()

        raw_password = request.form.get(
            "password",
            ""
        )

        if not name:
            connection.close()

            return "Staff name is required"

        if not email:
            connection.close()

            return "Staff email is required"

        if len(name) > 100:
            connection.close()

            return "Staff name is too long"

        if not is_valid_email(email):
            connection.close()

            return "Please enter a valid email address"

        # If password is empty while editing,
        # keep the existing password.
        if raw_password:

            if len(raw_password) < 6:

                connection.close()

                return (
                    "Password must contain "
                    "at least 6 characters"
                )

            password = generate_password_hash(
                raw_password
            )

        else:

            password = staff[3]

        try:

            cursor.execute("""
                UPDATE users
                SET name = ?,
                    email = ?,
                    password = ?
                WHERE id = ?
                AND role = 'staff'
            """, (
                name,
                email,
                password,
                id
            ))

            if cursor.rowcount != 1:

                connection.rollback()
                connection.close()

                return (
                    "Staff member could not be updated"
                )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.rollback()
            connection.close()

            return "Email already exists"

        except sqlite3.Error as error:

            connection.rollback()
            connection.close()

            return (
                "Staff member could not be updated: "
                + str(error)
            )

        connection.close()

        return redirect(
            url_for("staff_management")
        )

    connection.close()

    return render_template(
        "edit_staff.html",
        staff=staff
    )


# ============================================================
# DELETE STAFF
# ============================================================

@app.route(
    "/staff/delete/<int:id>"
)
def delete_staff(id):

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    # Prevent deleting the currently logged-in user.
    if session.get("user_id") == id:
        return (
            "You cannot delete the currently "
            "logged-in account"
        )

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT id
            FROM users
            WHERE id = ?
            AND role = 'staff'
        """, (id,))

        staff = cursor.fetchone()

        if not staff:

            connection.close()

            return "Staff member not found"

        # Do not delete staff with transaction history.
        cursor.execute("""
            SELECT id
            FROM transactions
            WHERE staff_id = ?
            LIMIT 1
        """, (id,))

        has_transactions = cursor.fetchone()

        if has_transactions:

            connection.close()

            return (
                "This staff member cannot be deleted "
                "because they have transaction history"
            )

        cursor.execute("""
            DELETE FROM users
            WHERE id = ?
            AND role = 'staff'
        """, (id,))

        connection.commit()

    except sqlite3.Error as error:

        connection.rollback()
        connection.close()

        return (
            "Staff member could not be deleted: "
            + str(error)
        )

    connection.close()

    return redirect(
        url_for("staff_management")
    )


# ============================================================
# SUPPLIERS
# ============================================================

@app.route("/suppliers")
def suppliers():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM suppliers
        ORDER BY id DESC
    """)

    suppliers_list = cursor.fetchall()

    connection.close()

    return render_template(
        "suppliers.html",
        suppliers=suppliers_list
    )


# ============================================================
# ADD SUPPLIER
# ============================================================

@app.route(
    "/suppliers/add",
    methods=["GET", "POST"]
)
def add_supplier():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    if request.method == "POST":

        name = clean_text(
            request.form.get("name")
        )

        phone = clean_text(
            request.form.get("phone")
        )

        email = clean_text(
            request.form.get("email")
        ).lower()

        address = clean_text(
            request.form.get("address")
        )

        if not name:
            return "Supplier name is required"

        if len(name) > 100:
            return "Supplier name is too long"

        if email and not is_valid_email(email):
            return (
                "Please enter a valid "
                "supplier email"
            )

        if phone and not is_valid_phone(phone):
            return (
                "Please enter a valid "
                "phone number"
            )

        connection = sqlite3.connect(
            "pos.db"
        )

        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO suppliers
                (name, phone, email, address)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                phone,
                email,
                address
            ))

            connection.commit()

        except sqlite3.Error as error:

            connection.rollback()
            connection.close()

            return (
                "Supplier could not be added: "
                + str(error)
            )

        connection.close()

        return redirect(
            url_for("suppliers")
        )

    return render_template(
        "add_supplier.html"
    )


# ============================================================
# EDIT SUPPLIER
# ============================================================

@app.route(
    "/suppliers/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_supplier(id):

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM suppliers
        WHERE id = ?
    """, (id,))

    supplier = cursor.fetchone()

    if not supplier:

        connection.close()

        return "Supplier not found"

    if request.method == "POST":

        name = clean_text(
            request.form.get("name")
        )

        phone = clean_text(
            request.form.get("phone")
        )

        email = clean_text(
            request.form.get("email")
        ).lower()

        address = clean_text(
            request.form.get("address")
        )

        if not name:
            connection.close()

            return "Supplier name is required"

        if len(name) > 100:
            connection.close()

            return "Supplier name is too long"

        if email and not is_valid_email(email):
            connection.close()

            return (
                "Please enter a valid "
                "supplier email"
            )

        if phone and not is_valid_phone(phone):
            connection.close()

            return (
                "Please enter a valid "
                "phone number"
            )

        try:

            cursor.execute("""
                UPDATE suppliers
                SET name = ?,
                    phone = ?,
                    email = ?,
                    address = ?
                WHERE id = ?
            """, (
                name,
                phone,
                email,
                address,
                id
            ))

            if cursor.rowcount != 1:

                connection.rollback()
                connection.close()

                return (
                    "Supplier could not be updated"
                )

            connection.commit()

        except sqlite3.Error as error:

            connection.rollback()
            connection.close()

            return (
                "Supplier could not be updated: "
                + str(error)
            )

        connection.close()

        return redirect(
            url_for("suppliers")
        )

    connection.close()

    return render_template(
        "edit_supplier.html",
        supplier=supplier
    )


# ============================================================
# DELETE SUPPLIER
# ============================================================

@app.route(
    "/suppliers/delete/<int:id>"
)
def delete_supplier(id):

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("user_role") != "admin":
        return "Access denied"

    connection = sqlite3.connect(
        "pos.db"
    )

    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT id
            FROM suppliers
            WHERE id = ?
        """, (id,))

        supplier = cursor.fetchone()

        if not supplier:

            connection.close()

            return "Supplier not found"

        cursor.execute("""
            DELETE FROM suppliers
            WHERE id = ?
        """, (id,))

        connection.commit()

    except sqlite3.Error as error:

        connection.rollback()
        connection.close()

        return (
            "Supplier could not be deleted: "
            + str(error)
        )

    connection.close()

    return redirect(
        url_for("suppliers")
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
        <h2>Page Not Found</h2>
        <p>The requested page does not exist.</p>
        <a href="/">Go to Home</a>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):

    return """
        <h2>Something went wrong</h2>
        <p>An unexpected server error occurred.</p>
        <a href="/">Go to Home</a>
    """, 500


# ============================================================
# START APPLICATION
# ============================================================
create_database()
create_default_users()
if __name__ == "__main__":

    create_database()
    create_default_users()

    app.run(
        debug=True,
        use_reloader=False
    )