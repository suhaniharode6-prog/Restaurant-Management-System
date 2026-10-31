# Restaurant Management System (Python)

A desktop Restaurant Management System with two interfaces:
- **GUI application** built with Tkinter (`gui_app.py`)
- **Console application** (`console_app.py`)

Both interfaces use the same local SQLite database (`restaurant.db`).

## Features

- Manager login and logout
- Dashboard statistics
- Table management (free/occupied status)
- Menu management (add, edit, delete, availability)
- Order creation and order history
- Billing with discount and tax calculation
- Payment method selection (Cash, UPI, Card)
- Customer management
- Inventory / stock tracking
- Sales report and top-selling items

## Requirements

- Python 3.8 or newer
- Tkinter (included with the standard Windows Python installer)
- No third-party Python packages are required

On Ubuntu/Debian, install Tkinter if needed:

```bash
sudo apt-get install python3-tk
```

## First-time setup (Windows PowerShell)

Open PowerShell in this project folder. Before the first run, set a manager password:

```powershell
$env:ADMIN_PASSWORD = "Choose-A-Strong-Password"
python run.py
```

The first run creates the SQLite database and a manager account:
- **Username:** `admin`
- **Password:** the value you set in `ADMIN_PASSWORD`

Choose a password of at least 10 characters. The password is not stored in this project. The environment variable applies only to the current PowerShell window; set it again in a new terminal session if you start with a fresh database.

For Command Prompt, use:

```bat
set ADMIN_PASSWORD=Choose-A-Strong-Password
python run.py
```

On macOS/Linux:

```bash
export ADMIN_PASSWORD='Choose-A-Strong-Password'
python3 run.py
```

If a manager account already exists in `restaurant.db`, changing `ADMIN_PASSWORD` will not reset that account's password.

## Run the application

From this folder:

```bash
python run.py
```

Select `1` for Console or `2` for GUI.

You can also launch either interface directly:

```bash
python console_app.py
python gui_app.py
```

The database is created automatically beside `database.py`. It is intentionally excluded from Git so your local restaurant data is not uploaded.

## Project structure

```text
restaurant_management_system/
├── .gitignore
├── README.md
├── console_app.py
├── database.py
├── gui_app.py
├── login.py
├── requirements.txt
└── run.py
```

## GitHub safety

- `restaurant.db` and Python cache files are excluded by `.gitignore`.
- Local environment files and virtual environments are excluded.
- Do not commit real passwords, customer records, or business data.
