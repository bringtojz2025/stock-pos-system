# Copilot AI Agent Instructions for Stock POS System

## Project Overview
- This is a Python-based POS (Point of Sale) and inventory management system with integrated AI content generation and Facebook posting features.
- The main application is `app_stock.py`, which provides the GUI and core logic using `customtkinter`.
- AI and social media features are implemented in `ai_content_generator.py` and configured via `ai_config.json`.

## Key Components
- `app_stock.py`: Main entry point, handles POS, inventory, sales history, dashboard, and integrates AI features.
- `ai_content_generator.py`: Handles AI-powered content creation (Google Gemini API) and Facebook posting.
- `requirements.txt`: Lists all dependencies. Use `install.bat` on Windows for setup.
- `ai_config.json`: Stores API keys and tokens (not in git). Use `ai_config_example.json` as a template.
- `FACEBOOK_SETUP.md`, `README_AI_FEATURES.md`: Guides for Facebook and AI features.

## Developer Workflows
- **Install dependencies:**
  - `pip install -r requirements.txt` or run `install.bat` (Windows).
- **Run the app:**
  - `python app_stock.py`
- **Configure APIs:**
  - Place Google OAuth credentials as `client_secret.json`.
  - Set up Gemini API key and Facebook tokens in `ai_config.json`.
- **Testing:**
  - Tests are in `test_ai_module.py` (run with `python test_ai_module.py`).

## Patterns & Conventions
- Uses `customtkinter` for a modern, themed GUI.
- Google Sheets integration via `gspread`.
- AI content via `google-generativeai` (Gemini API).
- Facebook posting requires valid access tokens.
- Sensitive config files (`ai_config.json`, credentials) are not tracked in git.
- Output images (ads) are saved in `ads_output/`.

## Integration Points
- Google APIs: Sheets, Gemini (API keys required).
- Facebook Graph API: Posting content/images (token required).

## Examples
- To add a new AI content style, update logic in `ai_content_generator.py`.
- To add new POS features, extend `app_stock.py`.

## References
- See `README.md` for setup, features, and troubleshooting.
- See `README_AI_FEATURES.md` and `FACEBOOK_SETUP.md` for integration details.

---
For questions, contact bringtojz@gmail.com
