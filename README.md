# YouTube Downloader

A free web-based media downloader project built with **React** and **Python**. The goal is to provide a simple interface for processing supported video URLs and offering available download formats.

> **Status:** Under Development

## Features

- [x] React frontend with Vite
- [x] Separate frontend and backend structure
- [ ] URL validation
- [ ] Video metadata extraction
- [ ] Available format selection
- [ ] Audio and video download support
- [ ] Download progress and error handling
- [ ] Responsive user interface

*Features are planned and may not be implemented yet.*

## Tech Stack

### Frontend
- React
- Vite
- JavaScript
- CSS

### Backend
- Python
- Additional libraries to be documented as development progresses

## Project Structure

```text
youtube_downloader/
├── backend/
│   ├── myvenv/             # Local Python environment
│   ├── main.py             # Backend entry point
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   └── api.js      # API communication
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Install the following before running the project:

- Python 3.10 or newer
- Node.js and npm

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd youtube_downloader
```

Replace `YOUR_REPOSITORY_URL` with your Git repository URL.

### 2. Set Up the Backend

Open a terminal in the project root:

```bash
cd backend
python -m venv myvenv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\myvenv\Scripts\Activate.ps1
```

**Windows CMD:**

```cmd
myvenv\Scripts\activate.bat
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the backend using the command appropriate for the framework configured in `main.py`.

### 3. Set Up the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in your terminal.

## Usage

1. Open the web application.
2. Enter a supported video URL.
3. Validate the URL.
4. Retrieve the available media metadata and formats.
5. Select an available format and start the download.

*The workflow above describes the intended functionality and depends on implementation progress.*

## Security and Privacy

- Validate URLs on the backend rather than relying only on frontend validation.
- Do not expose environment variables, API credentials, or other secrets in the frontend.
- Restrict backend processing to supported sources and formats.
- Apply appropriate limits to file size, processing time, and concurrent downloads.

## Legal Notice

This project is intended for educational purposes and lawful personal use. Users are responsible for ensuring that their downloads comply with applicable laws, copyright requirements, and the terms of service of the relevant platforms.

Do not download copyrighted content without authorization.

## License

No license has been specified yet. All rights are reserved by default until a license is added to the repository.

---

**Project Status:** Actively in development.
