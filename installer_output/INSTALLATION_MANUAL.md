# PANN POS System – Installation Manual

This guide walks a Windows user through installing the PANN POS System from the packaged installer and performing the initial setup.

---

## 1. Prerequisites

- **Operating System:** Windows 10 or later (64-bit).
- **MongoDB Community Edition:** Required for data storage.
  - Download: <https://www.mongodb.com/try/download/community>
  - Install MongoDB as a Windows service and start it before running the POS.
- **Administrator Rights:** Needed to install MongoDB and the POS application.
- **Firewall/Antivirus:** Allow the application to listen on `http://localhost:8000`.

---

## 2. Files & Folders

After unzipping your delivery package you should see:

```
installer_output\
 ├── PANN_POS_System_Setup.exe      # Windows installer (run this)
 ├── PANN_POS_System.exe            # Standalone executable (optional direct run)
 └── INSTALLATION_MANUAL.md         # This document
```

> **Important:** Always install from `PANN_POS_System_Setup.exe`. The standalone executable is only for advanced scenarios.

---

## 3. Install MongoDB (if not already installed)

1. Run the MongoDB installer you downloaded.
2. Choose “Complete” setup, keep defaults.
3. Ensure **“Install MongoDB as a Service”** remains checked.
4. Finish the wizard and confirm the service is running:
   - Press `Win + R`, type `services.msc`, press Enter.
   - Locate “MongoDB” in the list and make sure the status is “Running”.

---

## 4. Install the PANN POS System

1. Open the `installer_output` folder.
2. Right-click `PANN_POS_System_Setup.exe` → **Run as administrator**.
3. Follow the wizard:
   - Accept the license terms.
   - Choose the installation directory (default is `C:\Program Files\PANN\POS_System`).
   - Optionally create desktop/start menu shortcuts (recommended).
4. Click **Install**. The installer drops an `Uninstall` script inside the install directory for future removal.

---

## 5. First Launch & Initial Data Sync

1. Launch the application via the desktop shortcut or Start Menu entry (“PANN POS System”).
2. A console window opens and performs initial checks:
   - Verifies MongoDB connection.
   - Runs any pending migrations.
   - If this is a fresh environment, it will pull data from the cloud database automatically.
3. Once the console displays `Starting server on http://localhost:8000`, open a browser and navigate to that URL.

> **Tip:** Keep the console window open; closing it stops the backend service.

---

## 6. Sign In & Verify Admin Account

1. Use your provided admin credentials (for example, `ngjameswinston@gmail.com`) to sign in.
2. If prompted, complete email verification. Verified admin accounts receive shift summary emails and other alerts.
3. Confirm data (users, products, settings) synced correctly from the cloud.

---

## 7. Shift Summary Emails (Optional Configuration)

To ensure shift summaries reach the right people:

- In `backend/.env`, set `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, and `SENDGRID_FROM_NAME`.
- Add `SHIFT_SUMMARY_ADMIN_EMAILS` with a comma-separated list of recipients (e.g., `SHIFT_SUMMARY_ADMIN_EMAILS=ngjameswinston@gmail.com`).
- Verified admin accounts in MongoDB (`email_verified=True`) also receive summaries automatically.

Restart the POS console after updating environment variables.

---

## 8. Troubleshooting

| Symptom | Resolution |
| --- | --- |
| Console cannot connect to MongoDB | Ensure MongoDB service is running; check firewall and credentials if using a remote cluster. |
| Email notifications fail | Confirm SendGrid credentials and sender address in `backend/.env`. |
| Data missing locally | Run `PANN_POS_System.exe` once to allow the initial cloud pull, or rerun the sync command from the console. |
| Need to delete or re-install | Run the `Uninstall.ps1` script located in the install directory, then rerun the installer. |

For detailed logs, monitor the console window while the POS system runs. Errors include timestamps and collection names to aid debugging.

---

## 9. Updating the Application

1. Stop the running POS system (close the console).
2. Install the new `PANN_POS_System_Setup.exe` (newer version).
3. Repeat the initial launch to let migrations and sync run automatically.

---

## 10. Support

For assistance, contact the PANN support team or the integrator who delivered the installer. Provide log excerpts from the console window when reporting issues.

---

**Enjoy using the PANN POS System!**

