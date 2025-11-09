# 🚀 Quick Setup Guide

Follow these steps to get Alpaca Smart Trade running in minutes!

## Step 1: Get Alpaca API Credentials

1. Go to [https://alpaca.markets](https://alpaca.markets)
2. Sign up for a free account
3. Navigate to **Paper Trading** (for testing)
4. Click on "Generate API Keys"
5. Copy your API Key and Secret Key (keep these safe!)

## Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

**Add your Alpaca credentials to `.env`:**

```env
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

Save and close the file.

## Step 3: Frontend Setup

```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install
```

## Step 4: Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python app/api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

The app will automatically open at `http://localhost:3000`

## Step 5: Run Your First Analysis

1. The default stocks are already selected (NVDA, MSFT, AMZN, etc.)
2. Click the big **"Run Analysis"** button
3. Wait 10-30 seconds for the analysis to complete
4. Review the recommendations!

## Optional: Set Up Telegram Notifications

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy the **bot token**
5. Start a chat with your new bot (send any message)
6. Get your **chat ID**:
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id":123456789}`
7. Add both to your `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   ```
8. Restart the backend server

Now you can send analysis reports to Telegram!

## Quick Start Scripts

For convenience, you can use the startup scripts:

```bash
# Terminal 1
./run_backend.sh

# Terminal 2
./run_frontend.sh
```

## Troubleshooting

### "ModuleNotFoundError: No module named..."
**Solution:** Make sure virtual environment is activated and dependencies are installed
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Failed to get account info"
**Solution:** Check your API credentials in `.env`
- Verify ALPACA_API_KEY is correct
- Verify ALPACA_SECRET_KEY is correct
- Make sure you're using paper trading URL

### "Cannot connect to backend"
**Solution:** Ensure backend is running on port 5000
```bash
curl http://localhost:5000/api/health
```

### Frontend won't start
**Solution:** Delete node_modules and reinstall
```bash
cd frontend
rm -rf node_modules
npm install
npm start
```

## What's Next?

1. ✅ Run analysis on the default stocks
2. ✅ Review the recommendations
3. ✅ Try adding custom stocks
4. ✅ Execute a paper trade
5. ✅ Set up Telegram notifications
6. ✅ Customize configuration in `.env`

## Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review Alpaca API docs: https://docs.alpaca.markets
- Open an issue on GitHub

---

Happy Trading! 📈
