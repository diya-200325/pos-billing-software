# POS Billing Software

A web-based Point of Sale (POS) and Billing Software designed for a textile/retail business.

The application provides separate **Admin** and **Staff Billing** portals for managing products, staff, suppliers, billing, payments, transactions, returns, reports, and sales ledger. It also includes a dedicated **mobile application-style Admin Portal** for accessing the complete administration functionality through a mobile-friendly interface.

---

## Project Overview

The POS Billing Software is designed to support the day-to-day operations of a retail/textile business.

The system provides:

- Product and stock management
- Staff management
- Supplier management
- Billing and checkout
- Payment processing
- Invoice generation
- Transaction management
- Product returns
- Sales reports
- Payment summaries
- Sales ledger
- Role-based access
- Mobile Admin Portal

The project follows a simple web-based architecture using Flask and SQLite.

---

# Features

## 1. Admin Portal

The Admin Portal provides centralized management of the POS system.

### Dashboard

The dashboard provides an overview of the business, including:

- Total products
- Total staff
- Total suppliers
- Total transactions
- Total sales
- Today's transactions
- Today's sales
- System status
- Quick management actions

### Product Management

Administrators can:

- Add products
- View products
- Edit products
- Delete products
- Manage product categories
- Manage product prices
- Manage stock quantities
- Associate products with suppliers

### Staff Management

Administrators can:

- Add staff accounts
- View staff
- Edit staff information
- Delete staff accounts
- Manage staff access

### Supplier Management

Administrators can:

- Add suppliers
- View suppliers
- Edit supplier information
- Delete suppliers
- Store supplier contact details

### Transaction Management

Administrators can:

- View completed transactions
- View invoice numbers
- View staff responsible for transactions
- View transaction totals
- View payment methods
- View transaction dates

### Product Returns

The system supports product return handling.

Administrators can:

- View return information
- Select products for return
- Specify return quantities
- Process returns
- Record refund amounts
- Update product stock

### Reports and Ledger

The Reports section provides:

- Total sales
- Total transactions
- Payment method summary
- Sales details
- Sales ledger

The sales ledger includes:

- Date
- Invoice number
- Description
- Payment method
- Amount

---

# 2. Billing Portal

The Billing Portal is designed for staff members to handle the complete billing process.

Staff can:

- Log in using staff credentials
- Search for products
- View product availability
- Add products to the cart
- Update quantities
- Remove products from the cart
- View cart totals
- Proceed to checkout
- Select payment method
- Enter payment amount
- Calculate change automatically
- Complete transactions
- Generate invoices
- Print bills

### Supported Payment Methods

- Cash
- UPI
- Card

### Stock Management

The system checks product availability before completing a transaction.

After a successful transaction:

- The transaction is stored in the database
- Transaction items are recorded
- Product stock is automatically reduced

---

# 3. Mobile Admin Portal

The project includes a dedicated **mobile application-style Admin Portal**.

The mobile interface provides access to the complete Admin functionality through a mobile-friendly layout.

The Mobile Admin Portal includes:

- Dashboard
- Products
- Staff
- Suppliers
- Transactions
- Returns
- Reports and Ledger
- Logout

No separate APK or native mobile application is required.

### Mobile Admin URL

For local testing:

```text
http://127.0.0.1:5000/admin/mobile
