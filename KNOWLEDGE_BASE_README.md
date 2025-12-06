# Trading Notes Knowledge Base - RAG Chatbot Feature

## Overview

Upload your scanned handwritten notes or any PDFs and create a searchable knowledge base with:
- **PDF upload** (single or batch) with text and image extraction
- **ChromaDB vector storage** for semantic search
- **Book organization** with chapters and sections
- **Markdown editor** for manual content editing
- **RAG chatbot** for accurate Q&A from your notes
- **Export to PDF/HTML** for sharing or offline reading
- **Local & Private** - All processing on your machine with Ollama

> **Note:** This is a separate feature from the core investment manager. All RAG-related data is stored independently in `backend/chroma_db/` and `backend/uploads/`.

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements-minimal.txt
pip install chromadb sentence-transformers langchain ollama pdfplumber PyPDF2 nltk markdown Pillow
```

Optional (for PDF export):
```bash
pip install reportlab  # Simple PDF export
# OR
pip install weasyprint  # Advanced PDF with full CSS support
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 3. Configure Your Models
Add to `backend/.env`:
```bash
OLLAMA_LLM_MODEL=gpt-oss:20b
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
LLM_TEMPERATURE=0.15
```

### 4. Start Application
```bash
scripts\dev\start_dev.bat
```

### 5. Use Features
1. Navigate to "Trading Notes" tab
2. **Book View**: Create books, organize chapters, edit in markdown
3. **Chatbot**: Ask questions - get answers with source citations
4. **Documents**: Upload PDFs (single or batch)
5. **Content Review**: Approve AI-suggested organization

## Features

### 1. Book View & Organization
- **Create books**: Organize your notes into structured books
- **Chapter navigation**: Collapsible table of contents with nested sections
- **Markdown editing**: Full markdown editor with live preview
- **Image support**: Images extracted from PDFs display inline in chapters
- **Drag & reorder**: Organize sections in any order
- **Export**: Download as PDF or standalone HTML

### 2. PDF Processing
- **Multiple file upload**: Batch upload and process PDFs sequentially
- **Image extraction**: Automatically extracts all images from PDFs
- **Text extraction**: Handles handwritten notes (OCR-ready PDFs)
- **Progress tracking**: Real-time status for each uploaded file
- **Error recovery**: Robust handling of problematic PDFs

### 3. Content Organization
- **Automatic section creation**: Creates sections from uploaded PDF pages
- **Manual organization**: Reorder sections, create chapters, group content
- **Book management**: Create multiple books for different topics
- **Auto-approve**: Batch approve all organization proposals
- **Image support**: Images extracted and linked to sections

### 4. RAG Chatbot
- **Accurate answers**: Temperature=0.15 for factual, deterministic responses
- **Source citations**: Shows exact page numbers from your notes
- **Semantic search**: Understands meaning, not just keyword matching
- **Context-aware**: Retrieves relevant chunks before answering
- **Local & private**: Everything runs on your machine (no cloud API calls)

## Configuration

### Your Models (from `ollama list`)
```
gpt-oss:20b (13 GB)           - Language model for responses
nomic-embed-text:latest (274 MB) - Embedding model for search
```

### Settings File
All configurable via `backend/.env`:

```bash
# Models
OLLAMA_LLM_MODEL=gpt-oss:20b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
EMBEDDING_PROVIDER=ollama

# Response Quality
LLM_TEMPERATURE=0.15      # Very factual (0.0-1.0)
RAG_TOP_K_RESULTS=5       # Context chunks to retrieve
LLM_MAX_TOKENS=500        # Response length

# Processing
CHUNK_SIZE=500            # Characters per chunk
CHUNK_OVERLAP=100         # Overlap for context
```

**Template:** See `backend/knowledge_base.env.example`

### View/Validate Config
- **View config**: http://127.0.0.1:5000/api/knowledge/config
- **Validate models**: http://127.0.0.1:5000/api/knowledge/config/validate

## Common Issues & Fixes

### Issue 1: Portfolio Transaction Error (Empty buy_step/sell_step)
**Error:** `ValueError: invalid literal for int() with base 10: ''`

**Fix:** ✅ Updated to handle empty strings properly

### Issue 2: Chat Text Not Visible
**Error:** White text on white background

**Fix:** ✅ Changed to explicit dark colors (#333) on light background (#f5f5f5)

### Issue 3: Chat Input Cursor Disappears
**Error:** Can only type one character at a time

**Fix:** ✅ Used `useCallback` to prevent re-renders + stable event handlers

### Issue 4: PDF Color Value Error
**Error:** `Cannot set gray non-stroke color because /'P1' is an invalid float value`

**Fix:** ✅ Added warning suppression + per-page error handling for problematic PDFs

### Issue 5: ChromaDB Embedding Conflict
**Error:** `ValueError: Embedding function conflict: new: ollama vs persisted: default`

**Fix:** ✅ Uses existing collection instead of trying to recreate

**Manual fix if needed:**
```bash
cd backend
rmdir /s chroma_db  # Windows
# OR
rm -rf chroma_db    # Linux/Mac
# Then restart and re-upload PDFs
```

### Issue 6: Only First PDF Processes (Batch Upload)
**Error:** Subsequent files fail silently

**Fix:** ✅ Added `file.seek(0)` before each file + detailed error handling

### Issue 7: Ollama Not Running
**Check:**
```bash
ollama list  # Should show your models
ollama run gpt-oss:20b "test"  # Test LLM
```

**Fix:** Start Ollama (should auto-start on Windows)

### Issue 8: Missing Dependencies
**Error:** `ModuleNotFoundError: No module named 'chromadb'`

**Fix:**
```bash
cd backend
venv\Scripts\activate
pip install chromadb sentence-transformers langchain ollama pdfplumber PyPDF2 nltk
```

### Issue 9: Python 3.13 Compatibility
**Error:** `psycopg2-binary` or `pandas` won't install

**Fix:** ✅ Use `requirements-minimal.txt` (PostgreSQL removed for local dev)

## API Endpoints

### Upload
- `POST /api/knowledge/upload` - Single PDF
- `POST /api/knowledge/upload-multiple` - Multiple PDFs (batch)

### Documents
- `GET /api/knowledge/documents` - List all
- `DELETE /api/knowledge/documents/<id>` - Delete one

### Organization
- `GET /api/knowledge/proposals` - Get AI suggestions
- `POST /api/knowledge/proposals/<id>/approve` - Apply suggestion
- `POST /api/knowledge/proposals/<id>/reject` - Reject suggestion

### Chat
- `POST /api/knowledge/chat` - Ask question
- `GET /api/knowledge/chat/history` - Get history
- `DELETE /api/knowledge/chat/history` - Clear history

### Management
- `GET /api/knowledge/config` - View configuration
- `GET /api/knowledge/config/validate` - Validate models
- `GET /api/knowledge/stats` - Statistics
- `POST /api/knowledge/reindex` - Rebuild vector DB
- `GET /api/knowledge/sections` - Get organized sections

## Files Structure

```
backend/
├── config/
│   └── knowledge_base.py          # Configuration class
├── services/
│   ├── knowledge_base.py          # PDF processing, ChromaDB
│   ├── content_organizer.py       # AI organization
│   └── rag_chatbot.py             # RAG implementation
├── utils/
│   └── ollama_client.py           # Ollama integration
├── uploads/pdfs/                  # Uploaded PDFs
├── chroma_db/                     # Vector database
└── knowledge_base.env.example     # Config template

frontend/src/components/
└── KnowledgeBase.js               # UI component
```

## Performance Tips

**For faster responses:**
- Lower RAG_TOP_K_RESULTS (3-4)
- Lower CHUNK_SIZE (400)
- Smaller model (if available)

**For better quality:**
- Your gpt-oss:20b is excellent
- Increase RAG_TOP_K_RESULTS (6-7)
- Lower temperature (0.1)

## All Fixed Issues Summary

✅ SQLAlchemy reserved keyword (`metadata` → `section_metadata`)
✅ PostgreSQL dependency (removed for local dev)
✅ Python 3.13 compatibility (upgraded SQLAlchemy to 2.0.44)
✅ Portfolio transaction empty string handling
✅ Chat text visibility (dark text on light background)
✅ Chat input cursor issue (useCallback to prevent re-renders)
✅ PDF color value errors (suppressed warnings + robust page extraction)
✅ ChromaDB embedding conflict (use existing collection)
✅ Batch upload file pointer issue (file.seek(0))
✅ Model configuration (fully configurable via .env)

**Everything is now working! Restart your backend and try uploading PDFs.** 🚀

