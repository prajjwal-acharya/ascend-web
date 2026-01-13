# Contributing to ascend

Welcome to the team! We follow a strict **"Governance-Based"** workflow to keep our history clean and our Jira board in sync. Please read these rules before pushing code.

---

## 🌟 The Golden Workflow
**Jira is our Source of Truth.**
1.  **Start in Jira:** Always create a ticket in Jira first. Our automation will handle creating the GitHub Issue.
2.  **Sync Status:**
    * **In Progress:** Move the ticket on the Jira board.
    * **In Review:** Opens automatically when you create a Pull Request.
    * **Done:** Moves automatically when the Pull Request is merged.

---

## 🌿 Branching Strategy
We use a strict naming convention to ensure our tools (and humans) stay organized.
**Always create new branches from `main`.**

### Naming Format
`type/JIRA-KEY-description-slug`

* `feat/`: For new features (Stories).
* `fix/`: For bug fixes.
* `docs/`: For documentation changes.

### Examples
✅ `feat/KAN-12-add-login-button`
✅ `fix/KAN-45-crash-on-safari`
❌ `login-button` (Missing type and key)
❌ `KAN-12` (Missing description)

---

## 📝 Commit Messages
We combine **Conventional Commits** with **Smart Commits**. Every commit must tell us *what* changed and *which* ticket it belongs to.

### Format
`type: description (KEY)`

### Types
* `feat:` New feature.
* `fix:` Bug fix.
* `docs:` Documentation only.
* `style:` Formatting, missing semi-colons, etc.
* `refactor:` Code change that neither fixes a bug nor adds a feature.

### Examples
✅ `feat: implement oauth login flow (KAN-12)`
✅ `fix: handle null user profile image (KAN-45)`
❌ `fixed bug` (Vague, no key)

---

## 🤝 Pull Requests (PRs)
1.  **Template:** You must fill out the PR template (Summary, Testing Steps, Screenshots).
2.  **Title:** Must follow the commit format: `feat: add login button (KAN-12)`.
3.  **Linking:** Ensure the Jira key (e.g., `KAN-12`) is in the PR title or body.
4.  **Review:** Do not merge your own PR. Wait for at least **1 approval**.
5.  **Merge Strategy:** We use **Squash and Merge** only. This keeps our `main` history linear and clean.

### 🧹 Cleanup
We use GitHub's **"Automatically delete head branches"** feature.
* Once your PR is merged, the remote branch is deleted automatically.
* **Action:** Please run `git fetch -p` regularly to prune your local branches.

---

## 🛡️ Protection Rules
* **No Direct Pushes:** You cannot push directly to `main`.
* **Status Checks:** All CI/CD tests must pass before merging.
* **Linear History:** We avoid merge commits; rebase or squash is required.
