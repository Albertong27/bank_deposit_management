# Bank Deposit Management System

A Flask-based web application for managing bank deposits, calculating interest rates, and tracking deposit maturity values.

## Features

- **Deposit Management**: Add, view, edit, and delete bank deposits
- **Bank Management**: Add and configure banks with default interest rates
- **IDR Currency Support**: Full support for Indonesian Rupiah with proper formatting
- **Interest Calculations**: Automatic calculation of interest before and after tax
- **Daily Interest Tracking**: Calculate daily interest earned
- **Maturity Tracking**: Track total amount expected at maturity
- **Summary Dashboard**: Overview of all deposits with financial statistics
- **Configurable Tax Rates**: Default Indonesian tax rate (20%) with override capability
- **Bank-Specific Rates**: Each bank can have its own default interest rate
- **Data Persistence**: Store data in JSON format for easy backup and portability

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Flask application:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Start by adding your first deposit using the "Add Deposit" button

## Features Overview

### Adding Deposits
- Account holder name and number
- Bank selection (with default interest rates)
- Principal amount in Indonesian Rupiah (IDR)
- Interest rate (annual percentage, can override bank default)
- Deposit and maturity dates
- Tax rate (defaults to Indonesian tax rate of 20%)

### Automatic Calculations
The system automatically calculates:
- Interest earned before tax
- Tax amount (if applicable)
- Interest earned after tax
- Total maturity amount
- Daily interest rates
- Time period in years

### Data Storage
- All data is stored in `data/deposits.json`
- Bank configurations stored in `data/config.json`
- Easy to backup and restore
- Human-readable JSON format

### Bank Management
- Start with empty bank list - add banks through the web interface
- Each bank has its own default interest rate
- Add, edit, or remove banks as needed
- Interest rates can be overridden per deposit
- Supports any bank name (Indonesian or international)

## Project Structure

```
bank_deposit_management/
├── app.py                 # Main Flask application
├── models.py              # Deposit management logic & configuration
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Main dashboard
│   ├── add_deposit.html  # Add new deposit form
│   ├── view_deposit.html # View deposit details
│   ├── edit_deposit.html # Edit deposit form
│   ├── summary.html      # Summary dashboard
│   ├── banks.html        # Bank management
│   └── settings.html     # Application settings
└── data/                 # Data storage directory
    ├── deposits.json     # Deposit data (created automatically)
    └── config.json       # Configuration data (created automatically)
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
