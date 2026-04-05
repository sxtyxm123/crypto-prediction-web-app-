# Quick Start Guide

## Starting the Application

### For PowerShell (Recommended):

```powershell
cd web_app
.\start_servers.ps1
```

### For Command Prompt:

```cmd
cd web_app
start_servers.bat
```

### Manual Start (Alternative):

**Terminal 1** - API Server:
```powershell
cd web_app
python prediction_api.py
```

**Terminal 2** - Web Server:
```powershell
cd web_app
python -m http.server 8000
```

Then open: http://localhost:8000

## What You'll See

- **API Server**: Running on http://localhost:5000
- **Web App**: Running on http://localhost:8000
- Browser will open automatically

## Features

✅ Real LSTM predictions (not simulated)  
✅ Multi-timeframe forecasts (1h, 4h, 24h)  
✅ Confidence intervals  
✅ Model comparison  
✅ Interactive charts  
✅ Theme toggle (Dark/Light)  
✅ Simple authentication  

## Troubleshooting

**PowerShell Execution Policy Error**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Port Already in Use**:
- Close any existing Python servers
- Or change ports in the scripts

**Models Not Found**:
- Ensure trained models exist in `../lstm_models/`
- Check data files in `../crypto_data/`

## Toggle Real/Simulated Predictions

In `app.js` line 7:
```javascript
const USE_REAL_API = true;  // Set to false for simulated data
```

---

**Ready to predict!** 🚀
