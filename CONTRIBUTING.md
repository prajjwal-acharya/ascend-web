# Contributing to ascend

Welcome to the team! To maintain a high-velocity, production-grade workflow, we follow a strict set of rules for version control and task management. 

**Please read this document before pushing any code.**

---

## 🛠 The Core Stack

* **Project Management:** [Linear](https://linear.app/)
* **Version Control:** GitHub
* **CI/CD:** GitHub Actions

---

## 🚫 The Golden Rule

**NEVER push directly to `main`.**
The `main` branch is protected. All changes must go through a Pull Request (PR) and pass automated status checks.

---

## 🌊 The Workflow (Linear + GitHub)

We use an automated workflow where your **Branch Name** controls your **Linear Ticket**.

### Step 1: Pick a Ticket 🎫
* Go to our **Linear Board**.
* Assign a ticket to yourself.
* Note the Ticket ID (e.g., `EXT-12`).

### Step 2: Create a Branch 🌿
Your branch name **must** follow this format:
`[type]/[Linear-ID]-[short-description]`

**Types:**
* `feat` → New feature (e.g., login, new API)
* `fix` → Bug fix
* `chore` → Maintenance (deps, configs)
* `docs` → Documentation only

**Examples:**
✅ `feat/EXT-12-add-login-page` (Good)
✅ `fix/EXT-45-sync-crash` (Good)
❌ `add-login` (Bad - No ID)
❌ `EXT-12` (Bad - No description)

**Why?** When you use the ID, Linear automatically moves the ticket to "In Progress".

### Step 3: Commit & Push 💾
* Write clear commit messages.
* Push your branch: `git push origin feat/EXT-12-add-login-page`

### Step 4: Open a Pull Request (PR) 📝
* Open a PR against `main`.
* **Title:** Use the same format as the branch or a clear human-readable title: `feat: Add Login Page`
* **Description:** The repo is configured with a PR Template. **Fill it out.**
    * Link the Linear Ticket (e.g., "Fixes EXT-12").
    * Explain the "Why".
    * Attach screenshots if it's a UI change.

**Automation:** Opening a PR automatically moves the Linear ticket to **"In Review"**.

### Step 5: Review & Merge 🟢
1.  **Status Checks:** GitHub Actions will run automatically (Linter/Tests). If these fail, you cannot merge. Fix the errors and push again.
2.  **Review:** Wait for approval (if required).
3.  **Merge:** Click "Squash and Merge".
    * **Automation:** Merging automatically moves the Linear ticket to **"Done"**.

---

## 🎨 Coding Standards

We use automated linting to keep code clean.
* **Python:** `black` and `flake8`
* **JS/TS:** `Prettier` and `ESLint`

**Before you push:**
Run the linter locally to save time:
```bash
# Example for Python
black .
flake8 .
