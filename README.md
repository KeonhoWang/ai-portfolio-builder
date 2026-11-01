# ✨ AI Portfolio Builder

**Build a professional portfolio website with the power of AI.**

AI Portfolio Builder is a web application that allows users to create, customize, and publish responsive personal portfolio websites without writing code. Through a guided building experience and AI-powered tools, users can generate professional content, customize their design, receive portfolio feedback, and export a complete standalone HTML website.

Built with **Python, Flask, Vanilla JavaScript, and Groq AI**.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey) ![AI](https://img.shields.io/badge/AI-Groq-orange) ![License](https://img.shields.io/badge/License-MIT-brightgreen)

---

## ✨ Key Features

- 🧭 **Guided Portfolio Builder** — Create a portfolio through four simple steps: personal information, skills, projects, and visual customization.
- 🎨 **Flexible Customization** — Choose from 12 color themes and 4 typography styles.
- 👀 **Real-Time Preview** — Preview your portfolio instantly with desktop, tablet, and mobile layouts.
- 🤖 **AI-Powered Editing** — Customize your portfolio using natural language instructions without manually editing code.
- 📊 **AI Portfolio Analyzer** — Receive recruiter-style feedback, content evaluations, scores, and suggestions for improvement.
- 📝 **AI Cover Letter Generator** — Generate tailored cover letters based on your profile, target company, position, and preferred tone.
- 🎥 **AI Video Script Generator** — Create personalized self-introduction scripts for 30–120 second videos.
- 💾 **Portfolio Management** — Save, load, and manage up to 20 portfolio versions.
- 📥 **One-Click HTML Export** — Download a complete, responsive, self-contained HTML portfolio ready for deployment.

---

## 🧠 AI Integration & Architecture

AI Portfolio Builder combines deterministic template generation with AI-assisted content creation and customization.

Rather than allowing AI to generate an entire website from scratch, the application uses a structured Python template to ensure consistent layouts, valid HTML, responsive styling, and reliable output.

Groq AI is integrated into specific features where intelligent assistance provides the most value.

| Feature | AI Functionality |
|---|---|
| Tagline Generation | Creates personalized professional introductions. |
| Natural Language Editing | Converts user instructions into validated portfolio customization settings. |
| Portfolio Analysis | Evaluates portfolio content and provides structured feedback and improvement recommendations. |
| Cover Letter Generation | Produces role-specific and company-aware cover letters. |
| Video Script Generation | Creates personalized professional introduction scripts. |

### How AI Editing Works

1. The user describes a desired change in natural language.
2. The AI interprets the request and returns structured customization settings.
3. Python validates the returned values against predefined rules.
4. The portfolio template is rebuilt using the validated settings.
5. The updated portfolio is displayed in the live preview.

This approach minimizes unpredictable AI-generated code and helps maintain the stability of the generated website.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend logic and portfolio generation |
| Flask | Web application and API development |
| Flask-CORS | Cross-origin request handling |
| Groq API | AI-powered functionality |
| OpenAI GPT-OSS 120B | Language model for AI features |
| JavaScript | Interactive frontend and application logic |
| HTML5 | Application interface and generated portfolios |
| CSS3 | Responsive design and visual customization |
| python-dotenv | Environment variable management |
| Requests | HTTP communication with the AI API |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager
- A Groq API key (required only for AI functionality)

Get your API key from [Groq Console](https://console.groq.com/).

### 1. Clone the Repository

```bash
git clone https://github.com/KeonhoWang/ai-portfolio-builder.git

cd ai-portfolio-builder
```

### 2. Install Dependencies

```bash
pip3 install flask flask-cors python-dotenv requests
```

### 3. Configure Environment Variables

Create a `.env` file in the project root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Start the Application

```bash
python3 app.py
```

### 5. Open the Application

Navigate to:

```text
http://localhost:5002
```

**Note:** The portfolio builder, customization tools, and HTML export work without an API key. AI-powered features require a valid Groq API key.

---

## 📁 Project Structure

```text
ai-portfolio-builder/
│
├── app.py                  # Flask backend and AI API routes
├── index.html              # Portfolio builder interface
├── style.css               # Frontend styling
├── script.js               # Frontend interactions and logic
│
├── .env                    # API configuration (not committed)
├── saved_portfolios.json   # Locally saved portfolios (auto-created)
│
└── README.md               # Project documentation
```

---

## 🔌 API Endpoints

The Flask backend provides endpoints for portfolio generation, AI assistance, portfolio management, and HTML export.

| Endpoint | Method | Description |
|---|---|---|
| `/generate` | POST | Generates a portfolio from user-provided information. |
| `/edit` | POST | Applies AI-interpreted customization settings. |
| `/score` | POST | Analyzes portfolio content and returns feedback. |
| `/cover-letter` | POST | Generates a personalized cover letter. |
| `/video-script` | POST | Generates a professional introduction script. |
| `/saves` | GET / POST | Retrieves or saves portfolio versions. |
| `/saves/<id>` | GET / DELETE | Loads or deletes a saved portfolio. |
| `/download` | POST | Exports the generated portfolio as an HTML file. |

---

## 🌐 Deployment

One of the main advantages of AI Portfolio Builder is that exported portfolios are completely self-contained HTML files.

No Flask server or backend hosting is required to publish a generated portfolio.

### Supported Deployment Options

- **Netlify Drop:** Upload your exported HTML file using [Netlify](https://app.netlify.com/drop).
- **GitHub Pages:** Host your portfolio through a GitHub repository.
- **Static Web Hosting:** Deploy the generated HTML file to any hosting provider that supports static websites.

---

## 🔒 Security & Data Management

- API credentials are stored in environment variables rather than hardcoded into the application.
- `.env` files should never be committed to version control.
- Saved portfolios are stored locally in `saved_portfolios.json`.
- The generated portfolio does not require a continuously running backend.
- The contact section uses the visitor's default email application rather than a server-side contact processing system.

---

## 🔮 Future Improvements

Potential areas for future development include:

- Additional portfolio templates and layout variations.
- More advanced AI-driven content recommendations.
- Custom domain integration.
- Enhanced accessibility and SEO optimization.
- Additional export and publishing options.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👨‍💻 Author

**Keonho Wang**

Software Engineering Student | Full-Stack Developer | AI/ML Enthusiast

- **GitHub:** [KeonhoWang](https://github.com/KeonhoWang)
- **Portfolio:** [keonho-portfolio.netlify.app](https://keonho-portfolio.netlify.app)

*Designed and developed as a software engineering project exploring the integration of AI, web development, and automated portfolio generation.*
