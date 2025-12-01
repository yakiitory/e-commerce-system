# E-commerce System

A full-featured e-commerce platform built with Python and Flask. It provides a complete online shopping experience with separate functionalities for customers and merchants.

## 🚀 Getting Started

Follow these steps to get your local development environment set up and running.

### Prerequisites

- Python 3.10+
- MariaDB (or MySQL)
- `pip` and `venv`

### 1. Clone the Repository

First, clone the project to your local machine:

```bash
git clone <https://github.com/yakiitory/e-commerce-system.git>
cd e-commerce-system
```

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
```

*Note: Depending on your system, you might need to use `python3` instead of `python`.*

### 2. Activate the Virtual Environment

Before you install dependencies or run the application, you need to activate the virtual environment.

**On Windows:**
```bash
.\venv\Scripts\activate
```

**On macOS and Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

If this is your first time setting up the project, install all the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Create the Environment File

Create a `.env` file in the root directory of the project. This file will hold your environment-specific configurations, like your database connection string and a secret key for the application.

```
DATABASE_URL="loremipsumdolorsitamet"
FLASK_SECRET_KEY="loremipsumdolorsitamet"
DB_HOST="loremipsum"
DB_PORT=3306
DB_USER="loremipsum"
DB_PASSWORD="loremipsum"
DB_NAME="loremipsum"
DB_POOL_SIZE=5
```

### 5. Set Up the Database

This project uses MariaDB as its database.

1.  **Start the MariaDB service** on your machine. The command for this varies depending on your operating system (e.g., `sudo systemctl start mariadb` on Linux or through the XAMPP/MAMP control panel).
2.  **Create the database.** Log in to your MariaDB client and run the following SQL command. The recommended name is `ecommerce`.

    ```sql
    CREATE DATABASE ecommerce;
    ```

## Running the Application

Once the setup is complete, you can run the Flask application with the following command from the root directory:

```bash
python src/app.py
```

The application will be available at `http://127.0.0.1:5000`.
