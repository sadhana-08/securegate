# SecureGate

## Run locally

Use Git Bash from the project root. Create and activate the backend environment, install its dependencies, and create `.env`:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
if ! grep -qE '^SECRET_KEY=[^[:space:]]+' .env; then
  SECRET_KEY_VALUE="$(python -c 'import secrets; print(secrets.token_hex(32))')"
  sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY_VALUE/" .env
  unset SECRET_KEY_VALUE
fi
python backend/init_db.py
```

To load the optional synthetic demo accounts, set `SEED_PASSWORD` in `.env` to a throwaway password that meets the password rules, then run `python backend/seed.py`.

In one Git Bash terminal, start the backend:

```bash
cd "/c/Users/Sadhana S/OneDrive/Desktop/secureGate/securegate"
source .venv/Scripts/activate
python backend/run.py
```

In a second Git Bash terminal, install and start the frontend:

```bash
cd "/c/Users/Sadhana S/OneDrive/Desktop/secureGate/securegate/frontend"
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open `http://127.0.0.1:5173` in your browser. In VS Code, the **SecureGate: Start both** task starts both development servers after dependencies and `.env` are set up.

## Run backend security tests

From the project root in Git Bash, install the test dependencies and run the isolated backend security regression suite:

```bash
python -m pip install -r backend/requirements-test.txt
PYTHONPATH=backend python -m pytest backend/tests -q
```
