# MedTrack

A Django app for managing patients, medication plans, and daily medication rounds.

## Requirements

- Python 3.12 or newer
- MySQL server
- Internet access to load Tailwind CSS from its CDN

## Install

From the repository root, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the Python packages:

```bash
python -m pip install Django mysqlclient
```

Create a MySQL database named `MedTrack`. Then update the `DATABASES` settings in `MedTrack/MedTrack/settings.py` with your database name, user, password, host, and port.

## Run

From the repository root, run migrations and create a staff account:

```bash
cd MedTrack
python manage.py migrate
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and sign in with the staff account you created. Use `/admin/` to manage Django users and administration records.
