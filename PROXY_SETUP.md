# PANN POS System - Proxy Setup Guide

This guide explains how to use the custom domain `pos.panntech` instead of `localhost:8000`.

## Quick Setup

### Step 1: Update Hosts File

Run the hosts file updater script as Administrator:

```bash
python backend/update_hosts.py
```

Or manually add this line to `C:\Windows\System32\drivers\etc\hosts`:

```
127.0.0.1    pos.panntech
```

**Note:** You need Administrator privileges to edit the hosts file.

### Step 2: Start the Proxy Server

The proxy server forwards requests from `pos.panntech` to `localhost:8000`.

**Option A: Run on port 8080 (no admin required)**
```bash
python backend/proxy_server.py
```

**Option B: Run on port 80 (requires admin)**
```bash
python backend/proxy_server.py --port-80
```

### Step 3: Start Django Server

In a separate terminal, start your Django server:

```bash
cd backend
python manage.py runserver
```

### Step 4: Access the Application

Open your browser and navigate to:

```
http://pos.panntech
```

Or if using port 8080:

```
http://pos.panntech:8080
```

## How It Works

1. **Hosts File**: Maps `pos.panntech` to `127.0.0.1` (localhost)
2. **Proxy Server**: Listens on port 80 (or 8080) and forwards requests to Django on port 8000
3. **Django**: Serves the application and API on port 8000
4. **Frontend**: Configured to use `http://pos.panntech/api/v1` as the API base URL

## Troubleshooting

### Port 80 Already in Use

If port 80 is already in use:
- Use port 8080 instead (run without `--port-80` flag)
- Or close the application using port 80
- Or run as Administrator to use port 80

### Permission Denied

If you get permission errors:
- Run the proxy server as Administrator
- Or use port 8080 instead

### Hosts File Not Working

- Make sure you saved the hosts file correctly
- Clear your browser cache
- Try accessing `http://127.0.0.1` to verify Django is running
- Check that the hosts file entry is correct (no typos)

### Connection Refused

- Make sure Django server is running on port 8000
- Check that the proxy server is running
- Verify firewall isn't blocking the ports

## For Standalone Executable

When using the standalone executable:

1. The proxy server can be bundled with the executable
2. The hosts file update can be done during installation
3. The proxy server will start automatically with the application

## Benefits

- ✅ Clean URL: `pos.panntech` instead of `localhost:8000`
- ✅ No port number in URL
- ✅ Professional domain name
- ✅ Easy to remember
- ✅ Works with all browsers

