<<<<<<< HEAD
# Math Question Bank V0.1
Localhost prototype for a Grade 9 multiple-choice math question bank.

Requirements: Python 3.11+, Node.js 20+.

Backend:
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. SQLite is created automatically at `data/math_question_bank.sqlite`.

V0.1 deliberately keeps Word Equation export out of the first executable prototype. The next iteration should implement and test the LibreOffice Math -> OMML conversion before claiming editable Word equations.
=======
# Math-Question-Bank
>>>>>>> aa05a8fc38325cf28352e174125a0ef4cbc49848
