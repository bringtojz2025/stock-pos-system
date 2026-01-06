#!/bin/bash

echo ""
echo "===================================="
echo "  Stock POS AI Features Installer"
echo "===================================="
echo ""

echo "Installing base packages..."
pip install -r requirements.txt

echo ""
echo "===================================="
echo "  AI Service Selection"
echo "===================================="
echo ""
echo "1. OpenAI (ChatGPT)"
echo "2. Anthropic (Claude)"
echo "3. Skip (use offline mode)"
echo ""

read -p "Select an option (1-3): " choice

case $choice in
  1)
    echo "Installing OpenAI package..."
    pip install openai
    echo "Done! Remember to set your OpenAI API Key in the app."
    ;;
  2)
    echo "Installing Anthropic package..."
    pip install anthropic
    echo "Done! Remember to set your Anthropic API Key in the app."
    ;;
  3)
    echo "Skipping AI service installation. You can use offline mode."
    ;;
  *)
    echo "Invalid choice!"
    ;;
esac

echo ""
echo "===================================="
echo "  Installation Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Copy ai_config_example.json to ai_config.json"
echo "2. Add your API keys to ai_config.json"
echo "3. Run: python app_stock.py"
echo ""
