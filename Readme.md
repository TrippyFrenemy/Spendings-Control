# Telegram Expense Tracker Bot

A comprehensive Telegram bot for tracking personal expenses with detailed reporting and analytics capabilities.

## Features

- **Expense Tracking**
  - Quick expense recording with date, amount, and category
  - Support for different expense categories
  - Automatic date parsing and validation

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
project/
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
   # Clone the repository
   git clone https://github.com/TrippyFrenemy/Cost-Control
   cd Cost-Control

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Unix
   # or
   .\venv\Scripts\activate  # Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   Create a `.env` file with the following variables:
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
   # Initialize migrations
   alembic init alembic

   # Create initial migration
   alembic revision --autogenerate -m "Initial migration"

   # Apply migrations
   alembic upgrade head
   ```

5. **Running the Bot**
   ```bash
   python main.py
   ```

## Usage

1. **Start the Bot**
   - Send `/start` to initialize the bot
   - You'll receive a welcome message with basic instructions

2. **Recording Expenses**
   ```
   Format: DD.MM.YY amount category
   Example: 26.12.23 500 coffee
   ```

3. **View Reports**
   - Use the keyboard buttons to access different reports:
     - 📊 Monthly Report
     - 📅 Yearly Report
     - 💰 Total Spent
     - 🔍 Last 5 Expenses

4. **Delete Expenses**
   - Use ❌ Delete Expense button for today's expenses
   - Use `/delete DD.MM.YY` for specific dates

## Error Handling

The bot includes comprehensive error handling for:
- Invalid date formats
- Incorrect amount inputs
- Database connection issues
- Invalid categories
- Session management

## Logging

Detailed logging is implemented for:
- User actions
- Database operations
- Error tracking
- Performance monitoring

## Future Improvements

- Multiple currency support
- Budget setting and tracking
- Export functionality
- Category customization
- Expense statistics and trends
- Backup and restore functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [aiogram](https://docs.aiogram.dev/) for the Telegram Bot framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the ORM
- [Matplotlib](https://matplotlib.org/) for data visualization

This README provides a comprehensive overview of the project, including its features, setup instructions, usage guidelines, and future improvements. It helps new users and contributors understand the project structure and get started quickly.