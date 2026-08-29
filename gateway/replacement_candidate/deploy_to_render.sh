#!/bin/bash
echo "========================================"
echo "VENNATTA CORE - DEPLOY TO RENDER"
echo "========================================"

# 1. Create GitHub repo (manual step)
echo -e "\n1. Create GitHub repo:"
echo "   - Go to https://github.com/new"
echo "   - Name: vennatta-core"
echo "   - Public or Private"
echo "   - Create"

# 2. Initialize git
echo -e "\n2. Initialize git:"
cd ~/vennatta_core
git init
git add .
git commit -m "Initial commit: Identity node + legacy protocol"

# 3. Push to GitHub
echo -e "\n3. Push to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/vennatta-core.git"
echo "   git push -u origin main"

# 4. Deploy to Render
echo -e "\n4. Deploy to Render:"
echo "   - Go to https://render.com"
echo "   - Sign up / Login"
echo "   - New → Web Service"
echo "   - Connect GitHub repo (vennatta-core)"
echo "   - Configure:"
echo "     * Name: vennatta-core"
echo "     * Runtime: Python 3"
echo "     * Build: pip install -r requirements.txt"
echo "     * Start: uvicorn app.identity_node:app --host 0.0.0.0 --port \$PORT"
echo "   - Add Environment Variables:"
echo "     * PRIVATE_KEY=your_key"
echo "     * USDC_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
echo "     * WALLET_ADDRESS=0xdadeFD58681C5C5df68681735752a40CaAE5E152"
echo "     * HEIR_ADDRESS=your_child_address"

echo -e "\n5. Test deployment:"
echo "   curl https://vennatta-core.onrender.com/health"

echo -e "\n========================================"
echo "✅ DEPLOYMENT READY!"
echo "========================================"
