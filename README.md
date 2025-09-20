# Bank Deposit Management System

A Flask-based web application for managing bank deposits, calculating interest rates, and tracking deposit maturity values with support for multiple users.
 

## Features
- Deposit CRUD: add, view, edit and delete deposits. Each deposit stores account holder name and number, principal, interest rate (can override bank default), deposit and maturity dates, and tax rate.
- Automatic interest calculations: computes interest before tax, tax amount, interest after tax, total maturity amount, daily interest, and the time period (in years) used for calculations.
- Bank management: create, edit and remove bank records; each bank can carry a default interest rate that is applied when creating new deposits.
- Summary dashboard: a summary page that aggregates deposits and shows totals/overview (see `templates/summary.html`).
- Authentication skeleton: login and admin user pages are included (`templates/login.html`, `templates/admin_users.html`) for simple access control in development.
- Settings page: update application defaults and tax rates via the web UI (`templates/settings.html`).
- JSON API: a lightweight API endpoint is available to fetch deposits as JSON (e.g. `GET /api/deposits`).
- Templated UI: server-rendered pages using Jinja2 templates located in the `templates/` folder for quick customization.
- Local persistence: application stores data in local files for easy backup and restore (see Data Storage below).

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Features Overview

### Adding Deposits
- Account holder name and number
- Bank selection (with default interest rates)
- Principal amount in Indonesian Rupiah (IDR)
- Interest rate (annual percentage, can override bank default)
- Deposit and maturity dates
- Tax rate

### Automatic Calculations
The system automatically calculates:
- Interest earned before tax
- Tax amount (if applicable)
- Interest earned after tax
- Total maturity amount
- Daily interest rates
- Time period in years

### Data Storage
- Primary storage: the app uses local database files in the `data/` folder (SQLite files such as `bank_deposits.db`). This keeps the app simple to run locally and to back up.
- Config & models: `models.py` contains the deposit and bank logic as well as the persistence layer used by `app.py`.
- Backups: copy the files in `data/` to create a quick backup; you can replace the storage with a proper RDBMS later for production.

### Bank Management
- Start with empty bank list - add banks through the web interface
- Each bank has its own default interest rate
- Add, edit, or remove banks as needed
- Interest rates can be overridden per deposit
- Supports any bank name (Indonesian or international)

### Multiuser 
- Simple user authentication with login page
- Admin user management page for adding/removing users

## Project Structure

```
bank_deposit_management/
├── app.py
├── models.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── add_deposit.html
│   ├── view_deposit.html
│   ├── edit_deposit.html
│   ├── summary.html
│   ├── banks.html
│   ├── login.html
│   ├── admin_users.html
│   ├── settings.html
│   └── footer.html
└── data/ 
   ├── bank_deposits.db (not included - automatically generated)
```

## API Endpoints

- `GET /` - Main dashboard showing all deposits
- `GET /add_deposit` - Form to add new deposit
- `POST /add_deposit` - Process new deposit
- `GET /deposit/<id>` - View specific deposit details
- `GET /edit_deposit/<id>` - Form to edit deposit
- `POST /edit_deposit/<id>` - Process deposit update
- `POST /delete_deposit/<id>` - Delete deposit
- `GET /summary` - Summary dashboard
- `GET /banks` - Bank management page
- `POST /add_bank` - Add new bank
- `POST /update_bank` - Update bank settings
- `POST /delete_bank` - Delete bank
- `GET /settings` - Application settings
- `POST /update_settings` - Update settings
- `GET /api/deposits` - JSON API for all deposits

## Interest Calculation Formula

The system uses the following formulas:

- **Interest Before Tax**: `Principal × Interest Rate × Time Period (years)`
- **Tax Amount**: `Interest Before Tax × Tax Rate / 100`
- **Interest After Tax**: `Interest Before Tax - Tax Amount`
- **Total Maturity Amount**: `Principal + Interest After Tax`
- **Daily Interest**: `Principal × (Interest Rate / 365.25)`

## Customization

You can customize the application by:
- Modifying the interest calculation logic in `models.py`
- Adding new fields to the deposit model
- Customizing the UI by editing the HTML templates
- Adding new API endpoints in `app.py`

## Security Note

This is a development application. For production use:
- Change the secret key in `app.py`
- Implement proper authentication
- Use a proper database instead of JSON files
- Add input validation and sanitization
- Implement proper error handling

## License

This project is open source and available under the MIT License.
