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
  - Three types of reports:
    - Daily breakdown with detailed expense tracking
    - Monthly reports with category breakdown
    - Yearly summaries with trends analysis
  - Visual representations using charts and graphs
  - Category-wise spending analysis
  - Percentage calculations for better insights

- **Data Management**
  - View last 5 expenses and incomes
  - Delete individual expenses or incomes
  - Total spending and income overviews
  - Date-wise expense filtering
  - Change expense categories
  - Scheduled database backups with Celery

- **Income Tracking**
  - Record incomes with /income command
  - View total income and last 5 incomes
  - Check balance between income and expenses
  - Visual graphs comparing incomes and expenses

## Usage Guide

### Basic Commands
- `/start` - Initialize the bot and get instructions
- `/change DD.MM.YY` - Change category for expenses on specific date
- `/delete DD.MM.YY` - Delete expenses from specific date
- `/delete_income DD.MM.YY` - Delete incomes from specific date
- `/income [DD.MM.YY] amount description` - Record an income
- `/expenses` - Show last 5 expenses
- `/graph_day MM.YYYY` - Show daily income/expense graph (optional date)
- `/graph_month YYYY` - Show monthly income/expense graph (optional year)

### Recording Expenses
```
Format: DD.MM.YY amount description
Example: 26.12.24 500 coffee with friends

Alternative format (uses today's date):
Format: amount description
Example: 500 coffee with friends

After sending, select a category from the provided buttons.
```

### Recording Incomes
```
Format: /income DD.MM.YY amount description
Example: /income 26.12.24 500 salary

Alternative format (uses today's date):
Format: /income amount description
Example: /income 500 salary
```

### Accessing Reports
The bot provides three main types of reports accessible from the main menu:
- 📈 Daily Breakdown: Detailed day-by-day expense tracking
- 📊 Monthly Report: Category-wise breakdown for chosen month
- 📅 Yearly Report: Annual overview with trends

Each report type offers:
- Interactive year/month selection
- Visual charts and graphs
- Detailed breakdowns and statistics
- Total spent calculations

### Category Management
Use "📝 Manage Categories" to:
- View all categories
- Add new categories
- Delete categories (expenses will be moved to another category)
- Change expense categories

### Quick Actions
- ➕ Add Expense: Start guided expense entr6y
- ➕ Add Income: Start guided income entry
- 💰 Total Spent: View total expenses across all time
- 🔍 Last 5 Expenses: Quick overview of recent spending (or use `/expenses`)
- 💵 Total Income: View total recorded income
- 🔍 Last 5 Incomes: Overview of recent income entries
- 📊 Balance: Compare income and expenses
- ❌ Delete Expense: Remove specific expenses
- ❌ Delete Income: Remove specific incomes
- `/graph_day` and `/graph_month`: Visualize incomes vs expenses

## Default Categories
New users get these default categories:
- Продукты (Groceries)
- Бензин (Fuel)
- Кофе (Coffee)
- Рестораны (Restaurants)
- Обучение (Education)
- Other

## Technical Stack

- **Framework**: Python with aiogram 3.x
- **Database**: PostgreSQL with asyncpg
- **Cache & Broker**: Redis
- **Task Queue**: Celery for scheduled backups
- **ORM**: SQLAlchemy (async)
- **Visualization**: Matplotlib, Pandas
- **Additional Tools**:
  - Alembic for database migrations
  - Python-dotenv for configuration
  - Docker for containerization

## Project Structure
```
Spendings-Control/
├── app/
│   ├── db/
│   │   ├── models.py                  # Database models
│   │   ├── repositories/              # DB operations
│   │   └── redis/                     # Redis helpers
│   ├── handlers/                      # Telegram handlers
│   ├── keyboards/                     # Keyboard layouts
│   ├── tasks/                         # Celery app & scheduled jobs
│   └── spendings.py                   # Report generation helpers
├── migration/                         # Database migrations
│   ├── versions/                      # Migration versions
│   ├── env.py                         # Alembic environment
│   └── script.py.mako                 # Migration template
├── scripts/                           # Utility scripts
├── .dockerignore                      # Docker ignore rules
├── .env                               # Environment variables
├── .gitignore                         # Git ignore rules
├── alembic.ini                        # Alembic configuration
├── config.py                          # Application configuration
├── docker-compose.yml                 # Docker compose configuration
├── Dockerfile                         # Docker build instructions
├── main.py                            # Application entry point
├── README.md                          # Project documentation
└── requirements.txt                   # Python dependencies
```

## Setup Guide

1. **Prerequisites**
   - Python 3.8+
   - PostgreSQL database
   - Redis server
   - Telegram Bot Token (from @BotFather)
   - Docker and Docker Compose (optional)

2. **Environment Setup**
   ```bash
   git clone https://github.com/TrippyFrenemy/Spendings-Control
   cd Spendings-Control
   python -m venv venv
   source venv/bin/activate  # Unix
   # or
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Configuration**
   Create a `.env` file:
   ```env
   API_TOKEN=your_telegram_bot_token
   DB_DRIVER=postgresql+asyncpg
   DB_USER=your_db_user
   DB_PASS=your_db_password
   DB_HOST=localhost
   DB_NAME=your_db_name
   REDIS_HOST=your_redis_host
   REDIS_PORT=your_redis_port
   REDIS_PASSWORD=your_redis_password
   ```

4. **Running the Bot**

   With Docker:
   ```bash
   docker-compose up -d
   ```
   This launches the bot, Celery worker, and Celery beat for scheduled backups.

   Without Docker:
   ```bash
   python main.py
   celery -A app.celery_app.celery_app worker -l info
   celery -A app.celery_app.celery_app beat -l info
   ```
   Backups will be stored in the `backups/` directory.

## Error Handling

The bot includes comprehensive error handling for:
- Invalid date formats
- Incorrect amount inputs
- Category management errors
- Database connection issues
- API communication errors

## Logging

Detailed logging is implemented for:
- User actions
- Category operations
- Database queries
- Error tracking
- Performance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
