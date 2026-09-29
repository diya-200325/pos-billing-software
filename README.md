# POS Billing System

A web-based Point of Sale (POS) Billing Software designed for a textile/retail business. The system provides separate Admin and Staff portals for managing products, staff, suppliers, billing, transactions, returns, reports, and stock.

## Project Features

### Admin Portal

- Admin login and authentication
- Product management
  - Add products
  - Edit products
  - Delete products
  - View products
  - Manage stock
- Staff management
  - Add staff
  - Edit staff
  - Delete staff
- Supplier management
  - Add suppliers
  - Edit suppliers
  - Delete suppliers
- Transaction management
- Product returns
- Sales reports
- Payment summary
- Sales ledger
- Dashboard with business statistics
- Mobile-friendly Admin Portal

### Billing Portal

- Staff login
- Product search
- Add products to cart
- Update cart quantities
- Remove products from cart
- Stock availability checking
- Checkout
- Cash, UPI and Card payment options
- Payment amount validation
- Automatic change calculation
- Invoice generation
- Automatic stock reduction after successful billing

### Security and Validation

- Separate Admin and Staff access
- Password hashing
- Role-based access control
- Input validation
- Email validation
- Phone number validation
- Quantity and stock validation
- Payment validation
- Duplicate email prevention
- Transaction rollback on database errors
- Protection against deleting products with transaction history
- Protection against deleting staff with transaction history
- Custom 404 and 500 error handling

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, Flask
- Database: SQLite
- Authentication: Flask Sessions
- Password Security: Werkzeug Password Hashing
- Development Environment: Visual Studio Code
- Version Control: Git and GitHub

## Database

The application uses SQLite.

The database contains the following main tables:

- users
- products
- suppliers
- transactions
- transaction_items
- returns

The database file is created automatically when the application is started.

## How to Run the Project

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL