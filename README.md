# AI Knowledge Base Analyzer

A sophisticated AI-powered knowledge base analyzer that combines local document search with Gemini's web search capabilities to provide comprehensive answers to user questions.

## 🚀 Features

### Core Functionality
- **Local Knowledge Base Search**: Searches through your local markdown files for relevant information
- **AI-Powered Analysis**: Uses Google's Gemini AI for enhanced analysis and web search
- **Interactive Step-by-Step Flow**: Guided process for refining questions and selecting relevant documents
- **Web Search Integration**: Automatically searches the web when local context is insufficient
- **Beautiful UI**: Modern, responsive interface with formatted responses

### Key Capabilities
- **Document Selection**: Choose which files to include in your analysis
- **Message Refinement**: Modify your question before sending to AI
- **Structured Responses**: Color-coded sections showing local vs web search results
- **Source Tracking**: View which documents contributed to the answer
- **Modal Document Viewer**: Full-screen view of source documents

## 🏗️ Architecture

### Frontend
- **Next.js** with TypeScript
- **React** for UI components
- **CSS Modules** for styling
- **Axios** for API communication

### Backend
- **Python Flask** server
- **Google Generative AI** (Gemini) integration
- **Local file system** for knowledge base storage
- **CORS** enabled for frontend communication

## 📁 Project Structure

```
my_ai_project/
├── frontend/                 # Next.js React application
│   ├── components/          # React components
│   ├── pages/              # Next.js pages
│   ├── styles/             # CSS modules
│   └── types.ts            # TypeScript type definitions
├── knowledge_base/          # Your markdown documents
├── server.py               # Flask backend server
├── requirements.txt        # Python dependencies
└── .gitignore             # Git ignore rules
```

## 🛠️ Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Google AI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd my_ai_project
   ```

2. **Set up the backend**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

5. **Add your knowledge base documents**
   Place your markdown files in the `knowledge_base/` directory

## 🚀 Running the Application

### Start the backend server
```bash
# From the root directory
python server.py
```
The server will run on `http://localhost:5557`

### Start the frontend development server
```bash
# From the frontend directory
npm run dev
```
The frontend will run on `http://localhost:3000`

## 📖 Usage

### Basic Workflow

1. **Ask a Question**: Enter your question in the input field and click "Ask Question"

2. **Local Search**: The system first searches your local knowledge base for relevant information

3. **AI Analysis Decision**: Choose whether to use AI for enhanced analysis
   - **Yes**: Proceed with AI-powered analysis
   - **No**: Keep the local search results

4. **Document Selection** (if using AI): Select which files to include in the analysis

5. **Message Refinement** (optional): Modify your question before sending to AI

6. **Get Comprehensive Answer**: Receive a formatted response with:
   - Local knowledge base findings
   - Web search results (if needed)
   - Combined comprehensive answer
   - Source document references

### Response Format

The AI responses are formatted with color-coded sections:
- **🔵 Local Knowledge Base**: Information found in your markdown files
- **🟡 Web Search Results**: Information found through web search
- **🟢 Comprehensive Answer**: Final combined response

## 🔧 Configuration

### Knowledge Base
- Place your markdown files in the `knowledge_base/` directory
- Supported formats: `.md` files
- Files are automatically indexed and searchable

### API Configuration
- Update `GOOGLE_API_KEY` in your `.env` file
- The system uses Gemini 1.5 Flash for optimal performance

## 🎨 UI Features

### Responsive Design
- Works on desktop, tablet, and mobile devices
- Modern, clean interface with intuitive navigation

### Document Viewer
- Click "View Full Document" to see complete source files
- Modal overlay with proper formatting
- Easy close functionality

### Step-by-Step Flow
- Clear progress indicators
- Confirmation steps for important decisions
- Ability to go back and modify selections

## 🔒 Security

- API keys are stored in environment variables
- CORS is properly configured for local development
- No sensitive data is logged or stored

## 🐛 Troubleshooting

### Common Issues

1. **"Large files detected" error**
   - The repository has been cleaned of `node_modules`
   - Use the provided `.gitignore` to prevent future issues

2. **API key errors**
   - Ensure your `GOOGLE_API_KEY` is set in the `.env` file
   - Verify the API key has access to Gemini

3. **No documents found**
   - Check that your markdown files are in the `knowledge_base/` directory
   - Ensure files have `.md` extensions

4. **Frontend not connecting to backend**
   - Verify the Flask server is running on port 5557
   - Check CORS configuration if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Google Generative AI for providing the Gemini API
- Next.js team for the excellent React framework
- Flask team for the Python web framework

---

**Note**: This project is designed for personal knowledge base analysis. Ensure you have proper API usage limits and costs configured for your Google AI account.
