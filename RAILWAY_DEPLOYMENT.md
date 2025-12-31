# Deploy to Railway

## Quick Deploy (5 minutes)

### 1. Sign Up for Railway
1. Go to https://railway.app
2. Click "Login" and sign in with GitHub
3. Authorize Railway to access your repositories

### 2. Create New Project from GitHub

**Option A: Deploy from this local repo**
1. Push this repo to GitHub first:
   ```bash
   # Create a new repo on GitHub (https://github.com/new)
   # Then run:
   git remote add origin https://github.com/YOUR_USERNAME/lead-capture.git
   git branch -M main
   git push -u origin main
   ```

2. In Railway:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `lead-capture` repository
   - Click "Deploy Now"

**Option B: Deploy with Railway CLI**
1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   # or
   brew install railway
   ```

2. Login and deploy:
   ```bash
   railway login
   railway init
   railway up
   ```

### 3. Add Environment Variables

In your Railway project dashboard:

1. Go to "Variables" tab
2. Add these variables:
   ```
   CLOSE_API_KEY=api_5OqWQfjcZT8Js2HBSD8G8G.6qamc1fRqQCuWV3QSwtObS
   PORT=5000
   ```

3. Click "Deploy" to restart with new variables

### 4. Get Your Webhook URL

After deployment:
1. Go to "Settings" → "Networking"
2. Click "Generate Domain"
3. Your webhook URL will be: `https://YOUR-APP.up.railway.app`

Copy this URL - you'll need it for Calendly!

### 5. Update Calendly Webhook

Run this locally:
```bash
# Update .env with your Railway URL
CALENDLY_WEBHOOK_URL=https://YOUR-APP.up.railway.app

# Update the webhook
cd execution
python update_webhook.py
```

### 6. Test It!

1. Go to `https://YOUR-APP.up.railway.app/health`
   - Should return: `{"status":"healthy","service":"Calendly Lead Capture"}`

2. Book a test meeting on Calendly

3. Check Railway logs:
   - Click "Deployments" → "View Logs"
   - You should see webhook processing

4. Check Close.io for the new lead!

## Troubleshooting

### View Logs
```bash
railway logs
```

Or in the Railway dashboard: Deployments → View Logs

### Redeploy
```bash
railway up --detach
```

### Check Environment Variables
```bash
railway variables
```

## Cost

- Railway Free Tier: $5/month credit (plenty for webhooks)
- Your usage: ~$0.10/month (webhook processing is very light)

## Architecture

```
Calendly Booking
    ↓
Railway Webhook (Flask)
    ↓
Close.io API
    ↓
Lead Created/Updated
```

Railway runs 24/7, no cold starts, very reliable for webhooks!
