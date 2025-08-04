# BMO Documentation Analysis Tool

A powerful document analysis tool built with FastAPI and Streamlit, featuring configurable file upload validation, comprehensive error handling, and AI-powered document analysis.

## Features

- **File Upload Validation**: 10MB size limit, supports .doc, .docx, .xlsx, .csv, .pdf
- **Configurable Settings**: All settings managed through config.yaml
- **Comprehensive Error Handling**: Structured error responses with correlation IDs
- **Session Management**: Automatic and manual session cleanup
- **Real-time Chat Interface**: Interactive document analysis and Q&A

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone/Download the project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Option 1: Using Scripts (Recommended)

**Terminal 1 - Start Backend:**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**Terminal 2 - Start Frontend:**
```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

#### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
python main.py
```

**Terminal 2 - Frontend:**
```bash
streamlit run app.py
```

### Access the Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Configuration

Edit `config.yaml` to customize:

- File upload limits and allowed types
- AI processing settings
- Session management options
- API settings
- Logging configuration

## Usage

1. **Upload Files**: Use the sidebar to upload documents (max 10MB)
2. **Set File Roles**: Choose "Content" or "Template" for each file
3. **Chat**: Ask questions or request document analysis
4. **Session Management**: Use "Clear Session" to reset

## Project Structure

```
├── app.py              # Streamlit frontend
├── main.py             # FastAPI backend
├── config.py           # Configuration management
├── models.py           # Pydantic data models
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── start_backend.sh    # Backend startup script
├── start_frontend.sh   # Frontend startup script
└── README.md          # This file
```

## API Endpoints

- `POST /upload` - Upload and validate files
- `POST /chat` - Process chat messages
- `GET /download/{session_id}/{filename}` - Download generated files
- `DELETE /session/{session_id}` - Clean up session
- `GET /health` - Health check

## Error Handling

The application features comprehensive error handling:

- **File Upload**: Size and type validation with specific error codes
- **API Errors**: Structured JSON responses with correlation IDs
- **Network Issues**: Connection error handling and retries
- **Session Cleanup**: Automatic cleanup on errors

## Next Steps

This is Sprint 1 foundation. Upcoming features:
- Mock data service integration
- LangGraph agent implementation  
- Document processing and analysis
- File export capabilities
- Multi-document analysis

## Development

To modify configuration, edit `config.yaml`. The application will automatically load the new settings on restart.

For development, use the `/health` endpoint to verify backend connectivity.