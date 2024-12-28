# Telegram Expense Tracker Bot

A comprehensive Telegram bot for tracking personal expenses with detailed reporting, analytics capabilities, and flexible category management.

## Features

- **Smart Expense Tracking**
  - Quick expense recording with intuitive format
  - Interactive category selection via buttons
  - Support for custom categories
  - Optional expense descriptions
  - Automatic date parsing and validation

- **Category Management**
  - Default categories for new users
  - Add custom categories
  - Safe category deletion with expense reassignment
  - Change expense categories after creation
  - Category-based expense analysis

- **Reporting & Analytics**
  - Monthly expense reports with charts
  - Yearly expense summaries
  - Category-wise breakdowns
  - Visual representations using charts and graphs
  - Percentage calculations for better insights

- **Data Management**
  - View last 5 expenses
  - Delete individual expenses
  - Total spending overview
  - Date-wise expense filtering
  - Change expense categories

## Usage Guide

### Basic Commands
- `/start` - Initialize the bot and get instructions
- `/change DD.MM.YY` - Change category for expenses on specific date
- `/delete DD.MM.YY` - Delete expenses from specific date

### Recording Expenses
```
Format: DD.MM.YY amount description
Example: 26.12.24 500 coffee with friends

After sending, select a category from the provided buttons.
```

### Category Management
- Click "📝 Manage Categories" to:
  - View all categories
  - Add new categories
  - Delete categories (expenses will be moved to another category)
  - Change expense categories

### Reports
- Monthly Report: View expenses by category with charts
- Yearly Report: See yearly trends and category distribution
- Last 5 Expenses: Quick overview of recent spending
- Total Spent: Overall spending summary

## Technical Stack

- **Framework**: Python with aiogram 3.x
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy (async)
- **Visualization**: Matplotlib, Pandas
- **Additional Tools**: 
  - Alembic for database migrations
  - Python-dotenv for configuration
  - Logging for debugging

## Project Structure
```
Cost-Control/
├── app/
│   ├── db/
│   │   ├── models.py      # Database models and session management
│   │   └── requests.py    # Database queries and operations
│   ├── handlers.py        # Telegram message/callback handlers
│   ├── keyboards.py       # Telegram keyboard layouts
│   └── spendings.py       # Expense tracking logic
├── migration/             # Database migrations
│   ├── vesrsions/         # Migration version
│   ├── env.py             # Alembic environment variables
│   ├── README
│   └── script.py.mako
├── .env                   # Environment variables
├── .gitignore
├── alembic.ini           # Alembic configuration
├── config.py             # Application configuration
├── main.py               # Application entry point
└── requirements.txt
```

## Setup Guide

1. **Prerequisites**
   - Python 3.8+
   - PostgreSQL database
   - Telegram Bot Token (from @BotFather)

2. **Environment Setup**
   ```bash
   git clone https://github.com/TrippyFrenemy/Cost-Control
   cd Cost-Control
   python -m venv venv
   source venv/bin/activate  # Unix
   # or
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Configuration**
   Create a `.env` file:
   ```
   API_TOKEN=your_telegram_bot_token
   DB_DRIVER=postgresql+asyncpg
   DB_USER=your_db_user
   DB_PASS=your_db_password
   DB_HOST=localhost
   DB_NAME=your_db_name
   ```

4. **Database Setup**
   ```bash
   alembic upgrade head
   ```

5. **Running with Docker**
   ```bash
   docker-compose up -d
   ```

## Default Categories
New users get these default categories:
- Food
- Transport
- Entertainment
- Shopping
- Bills
- Other

You can add, delete, or modify categories through the bot interface.

## Error Handling

The bot includes comprehensive error handling for:
- Invalid date formats
- Incorrect amount inputs
- Category management errors
- Database connection issues
- Session management

## Logging

Detailed logging is implemented for:
- User actions
- Category operations
- Database queries
- Error tracking
- Performance monitoring

## Future Improvements

- Multiple currency support
- Budget setting and tracking
- Export functionality
- Category statistics and trends
- Backup and restore functionality
- Budget alerts and notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.