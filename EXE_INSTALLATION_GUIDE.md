# PANN POS System Installation Guide

## Overview
This guide will help you install and run the PANN POS System as a standalone Windows executable for individual cashier terminals with offline capability.

## Prerequisites

### 1. MongoDB Community Edition (Required)
The POS system requires MongoDB to store your data locally for offline operations.

**Download and Install:**
1. Visit: https://www.mongodb.com/try/download/community
2. Download the latest version for Windows
3. Run the installer with the following settings:
   - **Setup Type:** Complete
   - **Service Configuration:** Install MongoDB as a Service (Recommended)
   - **Default Data Directory:** C:\Program Files\MongoDB\Server\[version]\data
   - **Default Log Directory:** C:\Program Files\MongoDB\Server\[version]\log

**Note:** If MongoDB is installed as a Windows Service, it will start automatically with Windows. The POS system can also auto-start MongoDB if needed.

### 2. Windows Requirements
- Windows 10 or later
- At least 4GB RAM (8GB recommended)
- Administrator privileges for first-time installation

## Installation Steps

### Step 1: Run the Executable
1. Double-click `PANN_POS_System.exe`
2. On first run, Windows Defender or antivirus may ask for permission - click "Allow" or "Run anyway"
3. The application will:
   - Check if MongoDB is running
   - Auto-start MongoDB if needed
   - Launch the web interface on port 8000

### Step 2: Access the Application
1. Open your web browser
2. Navigate to: `http://localhost:8000`
3. You should see the login screen

### Step 3: First-Time Setup
1. Log in with your credentials
2. For cashiers/employees: Start a shift before processing sales
3. Begin using the POS system!

## Data Storage

### Local Data Directory
Your data is stored in: `C:\Users\[YourUsername]\PANN_POS_Data\`
- **Database files:** `PANN_POS_Data\mongodb\`
- **Application logs:** `PANN_POS_Data\logs\`

### Data Backup
To backup your data:
1. Stop the POS application
2. Copy the entire `PANN_POS_Data` folder to a safe location
3. Restore by copying the backup back to the same location

## Offline Mode

### How It Works
- **Online:** Syncs data to cloud database (MongoDB Atlas) in real-time
- **Offline:** Stores data locally, queues transactions
- **Auto-sync:** When internet connection is restored, all offline data syncs automatically

### Testing Offline Mode
1. Start the POS system (ensure internet is connected initially)
2. Make a sale to sync initial data
3. Disconnect internet (disable Wi-Fi/Ethernet)
4. Make sales offline - they will queue locally
5. Reconnect internet
6. Data syncs automatically within 30 seconds

## Troubleshooting

### Issue: "MongoDB not found"
**Solution:**
1. Ensure MongoDB Community Edition is installed
2. Check installation path: `C:\Program Files\MongoDB\Server\[version]\bin\`
3. Reinstall MongoDB if necessary

### Issue: "Port 8000 already in use"
**Solution:**
1. Close other applications using port 8000
2. Check if another instance of PANN POS is running
3. Restart the application

### Issue: Cannot connect to cloud database
**Solution:**
1. Check your internet connection
2. Verify cloud database credentials in `.env` file (if editable)
3. The system will work offline - data will sync when connection is restored

### Issue: Application won't start
**Solution:**
1. Check logs in: `C:\Users\[YourUsername]\PANN_POS_Data\logs\app.log`
2. Ensure MongoDB is installed correctly
3. Try running as Administrator
4. Check Windows Event Viewer for errors

### Issue: Slow performance
**Solution:**
1. Close other resource-heavy applications
2. Increase system RAM if possible
3. Clear old log files periodically
4. Check database size - consider cleanup if very large

## Updates

### Updating the POS System
1. Download the latest `PANN_POS_System.exe`
2. Stop the current application
3. Replace the old .exe with the new one
4. Launch the new version
5. Data is automatically migrated

**Note:** Always backup your data before updating!

## Uninstallation

### To Remove the POS System
1. Close the application
2. Delete `PANN_POS_System.exe`
3. Optionally delete data: `C:\Users\[YourUsername]\PANN_POS_Data\`
4. Optionally uninstall MongoDB (if not used by other applications)

## Security Notes

- The application runs on `localhost` only - not accessible from network by default
- Data is encrypted during cloud sync
- Local data is stored in user's home directory
- Regular backups are recommended
- Don't share your MongoDB connection credentials

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Contact system administrator
4. Report bugs with relevant log files

## Additional Features

### Auto-Start with Windows
To have the POS start automatically:
1. Create a shortcut to `PANN_POS_System.exe`
2. Press Win+R, type `shell:startup`
3. Copy the shortcut to the Startup folder

### Multiple Terminals
Each terminal runs independently:
- Each has its own local database
- All sync to the same cloud database
- No conflicts - system handles concurrent operations

## Version Information
- Current Version: 1.0.0
- Last Updated: January 2025
- Minimum MongoDB Version: 5.0
- Windows Version: 10 or later


