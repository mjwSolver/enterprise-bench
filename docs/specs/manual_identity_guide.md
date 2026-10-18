# Human Guide: Updating Project Team & Client Names Manually

This guide is for Project Managers, PMO assistants, or secretaries who need to fill in or update team and client names **without using the terminal or running console commands**.

---

## 📍 Where the Identity Files Live

All identities are kept in simple JSON text files on your local computer. Open them directly in your preferred editor (VS Code, TextEdit, Notepad, etc.):

| Scope | File Path | Who / What It Contains | Git Status |
| :--- | :--- | :--- | :--- |
| **Global Vault** | `presets/staff_vault.local.json` | Default consulting team members & default client officers | 🔒 Gitignored (Stays only on your machine) |
| **Project Vault** | `clean_workspace/projects/<project_id>/team_vault.local.json` | Project-specific assignments (e.g. Cloud Data Platform) | 🔒 Gitignored (Stays only on your machine) |
| **Public Roster Archetypes** | `presets/staff_roster.json` | Anonymized generic roles (`ROLE_PROJECT_MANAGER`, etc.) | 🌐 Safe to commit |

> [!IMPORTANT]
> Files ending in `.local.json` are strictly ignored by Git. Any names, emails, and phone numbers you type into these files will **never** be pushed to GitHub or shared outside your computer.

---

## ✏️ How to Edit Names Manually (Step-by-Step)

### 1. Open the File
In VS Code, double-click `presets/staff_vault.local.json`.

### 2. Update the Staff Members
Locate the `"staff_bindings"` block. Replace the `"full_name"` and `"official_position"` fields with the actual person:

```json
"ROLE_PROJECT_MANAGER": {
  "full_name": "Project Manager A",
  "official_position": "Senior Project Manager",
  "email": "pm.lead@enterprise-bench.local",
  "phone": "+6281200000001"
},
"ROLE_STREAMLIT_DEV": {
  "full_name": "Analytics Engineer A",
  "official_position": "Analytics & UI Engineer",
  "email": "analytics.dev@enterprise-bench.local",
  "phone": "+6281200000002"
}
```

* **Leaving someone unassigned:** Set `"full_name": null`. The system will warn you if a document needs this role before client delivery.

### 3. Update the Client Representatives
Scroll down to the `"client_bindings"` block. Fill in the client's company name and executive stakeholders:

```json
"client_bindings": {
  "CLIENT_COMPANY": "PT Nusantara Global Logistics Tbk",
  "CLIENT_COMPANY_SHORT": "Nusantara Global",
  "CLIENT_ABBR": "NGL",
  "CLIENT_STEERING_COMMITTEE": {
    "full_name": "Client Executive A",
    "position": "CFO & Vice President"
  },
  "CLIENT_PROJECT_MANAGER": {
    "full_name": "Client PM Lead",
    "position": "Enterprise Data – Project Manager"
  }
}
```

### 4. Save the File
Press `Cmd + S` (macOS) or `Ctrl + S` (Windows). That's it!

---

## 🔄 How the System Uses Your Changes

1. **Working with Clean Templates:** All sanitized files in `clean_workspace/` use placeholders like `{{ ROLE_PROJECT_MANAGER }}` or `ROLE_PROJECT_MANAGER`.
2. **Exporting Documents:** When you or an agent exports a deliverable (Word BAST, PowerPoint status deck, or Excel milestone sheet), the system reads your `*.local.json` file and replaces the placeholders with real names automatically.
3. **Double-Check Before Sending:** If you ever want to verify whether any role is missing before sending files to the client, you can ask the agent: *"Verify all aliases are filled"* or run `uv run bench check-aliases`.
