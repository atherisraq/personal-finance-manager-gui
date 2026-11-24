# Personal Finance Manager (Python + Tkinter)

Offline desktop app. Data is stored in `finance.db` (SQLite) next to the scripts.

    pip install -r requirements.txt
    python main.py

- First launch seeds a Guest account with sample incomes, expenses, budgets and savings goals.
- "Continue as Guest (Demo Mode)" opens it instantly. Registered users start empty;
  use Profile & Settings > Reset to Demo Data to load samples.
- Delete `finance.db` to start completely fresh.

Layout: `main.py` (window + navigation), `database.py` (all storage), `utils.py` (currency formatter, parsing),
`theme.py` (styles), `views/` (one module per screen).
