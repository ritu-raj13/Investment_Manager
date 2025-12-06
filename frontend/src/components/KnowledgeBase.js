import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  Tab,
  Tabs,
  Tooltip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  MenuItem
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Send as SendIcon,
  Delete as DeleteIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Refresh as RefreshIcon,
  Description as DocumentIcon,
  Clear as ClearIcon,
  AutoFixHigh as AiIcon,
  MenuBook as BookIcon
} from '@mui/icons-material';
import { knowledgeAPI } from '../services/api';
import BookView from './BookView';

// TabPanel component - MUST be outside to prevent remounting
const TabPanel = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ paddingTop: 16 }}>
    {value === index && children}
  </div>
);

function KnowledgeBase() {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [documents, setDocuments] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [books, setBooks] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatQuery, setChatQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [stats, setStats] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState([]);
  
  // Book selection for approving proposals
  const [approveDialog, setApproveDialog] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState(null);
  const [approveOption, setApproveOption] = useState('existing'); // 'existing' or 'new'
  const [selectedBookId, setSelectedBookId] = useState('');
  const [newBookTitle, setNewBookTitle] = useState('');
  
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const chatInputRef = useRef(null);
  const inputKey = useRef(0);

  // Load data on mount
  useEffect(() => {
    loadDocuments();
    loadProposals();
    loadStats();
    loadBooks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadDocuments = async () => {
    try {
      const docs = await knowledgeAPI.getDocuments();
      const docList = Array.isArray(docs) ? docs : [];
      console.log('Loaded documents:', docList.length);
      setDocuments(docList);
      return docList;
    } catch (err) {
      console.error('Failed to load documents:', err);
      setError('Failed to load documents. Please refresh the page.');
      return [];
    }
  };

  const loadProposals = async () => {
    try {
      const props = await knowledgeAPI.getOrganizationProposals();
      setProposals(Array.isArray(props) ? props : []);
    } catch (err) {
      console.error('Failed to load proposals:', err);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await knowledgeAPI.getStats();
      setStats(statsData || {});
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadBooks = async () => {
    try {
      const response = await knowledgeAPI.getBooks();
      const booksList = response?.books || [];
      setBooks(booksList);
    } catch (err) {
      console.error('Failed to load books:', err);
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      // Validate all files are PDFs
      const invalidFiles = files.filter(f => f.type !== 'application/pdf');
      if (invalidFiles.length > 0) {
        setError(`Please select only PDF files. Invalid: ${invalidFiles.map(f => f.name).join(', ')}`);
        return;
      }
      setSelectedFiles(files);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');
    
    // Initialize progress tracking
    const initialProgress = selectedFiles.map(file => ({
      filename: file.name,
      status: 'pending',
      message: 'Waiting...'
    }));
    setUploadProgress(initialProgress);

    try {
      const result = await knowledgeAPI.uploadMultiplePDFs(selectedFiles);
      
      // Update progress with results
      const finalProgress = result.results.map(r => ({
        filename: r.filename,
        status: r.status,
        message: r.status === 'success' 
          ? `Processed ${r.chunks_processed} chunks, ${r.proposals_generated} proposals`
          : r.message
      }));
      setUploadProgress(finalProgress);
      
      // Show summary message
      if (result.status === 'success') {
        setSuccess(`All ${result.total_files} PDFs uploaded successfully!`);
      } else if (result.status === 'partial') {
        setSuccess(`${result.successful} of ${result.total_files} PDFs uploaded successfully. Check details below.`);
        if (result.failed > 0) {
          setError(`${result.failed} PDFs failed to upload.`);
        }
      } else {
        setError(`All ${result.total_files} PDFs failed to upload.`);
      }
      
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Reload data to show newly uploaded documents
      await loadDocuments();
      await loadProposals();
      await loadStats();
      
      // Clear progress after 10 seconds if successful
      if (result.status === 'success') {
        setTimeout(() => setUploadProgress([]), 10000);
      }
    } catch (err) {
      setError(err.message || 'Failed to upload PDFs');
      setUploadProgress([]);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await knowledgeAPI.deleteDocument(docId);
      setSuccess('Document deleted successfully');
      loadDocuments();
      loadStats();
    } catch (err) {
      setError(err.message || 'Failed to delete document');
    }
  };

  const handleApproveClick = (proposal) => {
    setSelectedProposal(proposal);
    setApproveDialog(true);
    // Pre-select "Swing Trading Notes" if it exists
    const swingBook = books.find(b => b.title === 'Swing Trading Notes');
    if (swingBook) {
      setSelectedBookId(swingBook.id);
      setApproveOption('existing');
    } else {
      setNewBookTitle('Swing Trading Notes');
      setApproveOption('new');
    }
  };

  const handleConfirmApprove = async () => {
    if (!selectedProposal) return;
    
    setLoading(true);
    try {
      const payload = {};
      
      if (approveOption === 'new') {
        payload.create_new_book = true;
        payload.new_book_title = newBookTitle;
      } else {
        payload.book_id = parseInt(selectedBookId);
      }
      
      await knowledgeAPI.approveOrganization(selectedProposal.id, payload);
      setSuccess('Proposal approved and section added to book');
      setApproveDialog(false);
      setSelectedProposal(null);
      loadProposals();
      loadStats();
      loadBooks();
    } catch (err) {
      setError(err.message || 'Failed to approve proposal');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAll = async () => {
    if (proposals.length === 0) {
      setError('No proposals to approve');
      return;
    }
    
    // Find Swing Trading Notes book
    const swingBook = books.find(b => b.title === 'Swing Trading Notes');
    
    if (!swingBook) {
      setError('Swing Trading Notes book not found');
      return;
    }
    
    if (!window.confirm(`Auto-approve all ${proposals.length} proposals and add to "${swingBook.title}"?`)) {
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const result = await knowledgeAPI.approveAllProposals(swingBook.id);
      setSuccess(result.message || `Created ${result.sections_created} sections`);
      loadProposals();
      loadStats();
      loadBooks();
      loadDocuments();
    } catch (err) {
      setError(err.message || 'Failed to auto-approve proposals');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectProposal = async (proposalId) => {
    try {
      await knowledgeAPI.rejectOrganization(proposalId);
      setSuccess('Proposal rejected');
      loadProposals();
    } catch (err) {
      setError(err.message || 'Failed to reject proposal');
    }
  };

  const handleGenerateProposals = async (useLLM = true) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const result = await knowledgeAPI.generateProposals(useLLM);
      setSuccess(result.message || 'Proposals generated successfully');
      loadProposals();
      loadStats();
      loadDocuments();
    } catch (err) {
      setError(err.message || 'Failed to generate proposals');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    const query = chatInputRef.current?.value?.trim() || chatQuery.trim();
    if (!query) return;

    const userMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatQuery('');
    if (chatInputRef.current) {
      chatInputRef.current.value = '';
    }
    setSending(true);
    setError('');

    try {
      const response = await knowledgeAPI.sendChatMessage(query);
      
      const botMessage = {
        role: 'assistant',
        content: response.response,
        sources: response.sources || [],
        timestamp: new Date().toISOString(),
        responseTime: response.response_time
      };

      setChatMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setError(err.message || 'Failed to get response');
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure Ollama is running and try again.',
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
      if (chatInputRef.current) {
        chatInputRef.current.focus();
      }
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Clear chat history?')) {
      setChatMessages([]);
      setSuccess('Chat cleared');
    }
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleReindex = async () => {
    if (!window.confirm('Rebuild the entire knowledge base index? This may take a few minutes.')) {
      return;
    }

    setLoading(true);
    try {
      const result = await knowledgeAPI.reindex();
      setSuccess(`Reindexing complete! Processed ${result.processed} documents with ${result.total_chunks} chunks.`);
      loadStats();
    } catch (err) {
      setError(err.message || 'Reindexing failed');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box sx={{ maxWidth: 1400, margin: '0 auto', padding: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AiIcon fontSize="large" />
        Trading Notes Knowledge Base
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Statistics */}
      {stats && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={3}>
              <Typography variant="h6">{stats.total_documents}</Typography>
              <Typography variant="body2" color="text.secondary">Documents</Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="h6">{stats.total_pages}</Typography>
              <Typography variant="body2" color="text.secondary">Total Pages</Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="h6">{stats.vector_store?.total_chunks || 0}</Typography>
              <Typography variant="body2" color="text.secondary">Knowledge Chunks</Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="h6">{stats.pending_proposals}</Typography>
              <Typography variant="body2" color="text.secondary">Pending Reviews</Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
        <Tab label="Book View" icon={<BookIcon />} iconPosition="start" />
        <Tab label="Chatbot" />
        <Tab label="Documents" />
        <Tab label="Content Review" />
      </Tabs>

      {/* Book View Tab */}
      <TabPanel value={activeTab} index={0}>
        <BookView />
      </TabPanel>

      {/* Chatbot Tab */}
      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 2, height: 500, display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Ask About Your Trading Notes</Typography>
                <Button
                  size="small"
                  startIcon={<ClearIcon />}
                  onClick={handleClearChat}
                  disabled={chatMessages.length === 0}
                >
                  Clear
                </Button>
              </Box>

              {/* Chat messages */}
              <Box sx={{ flexGrow: 1, overflowY: 'auto', mb: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                {chatMessages.length === 0 && (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body1" sx={{ color: '#666' }} gutterBottom>
                      No messages yet. Start by asking a question about your trading notes!
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 2, color: '#666' }}>
                      Example questions:
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#666' }}>
                      • What is support and resistance?
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#666' }}>
                      • How do I identify a trend?
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#666' }}>
                      • Explain chart patterns
                    </Typography>
                  </Box>
                )}

                {chatMessages.map((msg, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      mb: 2,
                      p: 2,
                      bgcolor: msg.role === 'user' ? '#e3f2fd' : '#fff',
                      borderRadius: 2,
                      border: msg.role === 'assistant' ? '1px solid #ddd' : 'none'
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 600 }} gutterBottom>
                      {msg.role === 'user' ? 'You' : 'AI Assistant'}
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', color: '#333' }}>
                      {msg.content}
                    </Typography>

                    {/* Sources */}
                    {msg.sources && msg.sources.length > 0 && (
                      <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #ddd' }}>
                        <Typography variant="caption" sx={{ color: '#666', display: 'block', mb: 1 }}>
                          Sources:
                        </Typography>
                        {msg.sources.map((source, sidx) => (
                          <Chip
                            key={sidx}
                            label={`${source.document_name} - Page(s) ${source.pages.join(', ')}`}
                            size="small"
                            sx={{ mr: 1, mt: 1 }}
                          />
                        ))}
                      </Box>
                    )}

                    {msg.responseTime && (
                      <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#888' }}>
                        Response time: {msg.responseTime}s
                      </Typography>
                    )}
                  </Box>
                ))}

                {sending && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                    <CircularProgress size={20} />
                    <Typography variant="body2" sx={{ color: '#666' }}>
                      Thinking...
                    </Typography>
                  </Box>
                )}

                <div ref={chatEndRef} />
              </Box>

              {/* Input */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  inputRef={chatInputRef}
                  placeholder="Ask a question about your trading notes..."
                  defaultValue=""
                  onKeyDown={handleKeyDown}
                  disabled={sending}
                  helperText={sending ? 'Thinking...' : ''}
                  autoComplete="off"
                />
                <Button
                  variant="contained"
                  endIcon={<SendIcon />}
                  onClick={handleSendMessage}
                  disabled={sending}
                >
                  Send
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Documents Tab */}
      <TabPanel value={activeTab} index={2}>
        <Grid container spacing={3}>
          {/* Upload Section */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Upload Trading Notes PDFs
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Upload your scanned trading class notes (single or multiple PDFs). The system will extract text, organize content, and make it searchable via the chatbot.
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  multiple
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                  id="pdf-upload"
                />
                <label htmlFor="pdf-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<DocumentIcon />}
                  >
                    Choose PDF(s)
                  </Button>
                </label>

                {selectedFiles.length > 0 && (
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {selectedFiles.length} file(s) selected:
                    </Typography>
                    {selectedFiles.map((file, idx) => (
                      <Chip
                        key={idx}
                        label={`${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                )}

                <Button
                  variant="contained"
                  startIcon={uploading ? <CircularProgress size={20} /> : <UploadIcon />}
                  onClick={handleUpload}
                  disabled={selectedFiles.length === 0 || uploading}
                >
                  {uploading ? 'Processing...' : `Upload & Process ${selectedFiles.length > 0 ? `(${selectedFiles.length})` : ''}`}
                </Button>
              </Box>

              {uploading && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Processing PDFs sequentially... This may take a few minutes.
                  </Typography>
                  <LinearProgress sx={{ mb: 2 }} />
                </Box>
              )}

              {/* Upload Progress Details */}
              {uploadProgress.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom sx={{ color: 'text.primary' }}>
                    Upload Progress ({uploadProgress.filter(p => p.status === 'success').length}/{uploadProgress.length} completed):
                  </Typography>
                  <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
                    {uploadProgress.map((progress, idx) => (
                      <Box 
                        key={idx} 
                        sx={{ 
                          mb: 1, 
                          p: 1.5, 
                          bgcolor: progress.status === 'error' ? '#ffebee' : '#f5f5f5',
                          borderRadius: 1,
                          borderLeft: `4px solid ${
                            progress.status === 'success' ? '#4caf50' :
                            progress.status === 'error' ? '#f44336' :
                            '#2196f3'
                          }`
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                          <Typography variant="body2" sx={{ color: 'text.primary', fontWeight: 500 }}>
                            {progress.filename}
                          </Typography>
                          <Chip
                            label={progress.status.toUpperCase()}
                            size="small"
                            color={
                              progress.status === 'success' ? 'success' :
                              progress.status === 'error' ? 'error' :
                              'primary'
                            }
                          />
                        </Box>
                        {progress.status === 'processing' && (
                          <LinearProgress variant="indeterminate" sx={{ mt: 1 }} />
                        )}
                        {progress.message && (
                          <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
                            Error: {progress.message}
                          </Typography>
                        )}
                        {progress.status === 'success' && (
                          <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
                            {progress.total_pages || '?'} pages • {progress.chunks_processed || 0} chunks indexed
                          </Typography>
                        )}
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Documents List */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Uploaded Documents</Typography>
                <Tooltip title="Rebuild entire knowledge base index">
                  <Button
                    size="small"
                    startIcon={<RefreshIcon />}
                    onClick={handleReindex}
                    disabled={loading || documents.length === 0}
                  >
                    Reindex
                  </Button>
                </Tooltip>
              </Box>

              {documents.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  No documents uploaded yet
                </Typography>
              ) : (
                <Grid container spacing={2}>
                  {documents.map((doc) => (
                    <Grid item xs={12} md={6} key={doc.id}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            {doc.original_filename}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Size: {formatFileSize(doc.file_size)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Pages: {doc.total_pages}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Uploaded: {formatDate(doc.upload_date)}
                          </Typography>
                          <Chip
                            label={doc.status}
                            color={doc.status === 'ready' ? 'success' : 'default'}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        </CardContent>
                        <CardActions>
                          <Button
                            size="small"
                            color="error"
                            startIcon={<DeleteIcon />}
                            onClick={() => handleDeleteDocument(doc.id)}
                          >
                            Delete
                          </Button>
                        </CardActions>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Content Review Tab */}
      <TabPanel value={activeTab} index={3}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6">
                AI Content Organization Proposals
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {proposals.length > 0 
                  ? `${proposals.length} proposals ready - Auto-approve to add all to your book`
                  : 'Review AI-suggested organization of scattered topics across your notes.'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {proposals.length > 0 && (
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleApproveAll}
                  disabled={loading}
                  startIcon={<ApproveIcon />}
                >
                  Auto-Approve All ({proposals.length})
                </Button>
              )}
              <Button
                variant={proposals.length > 0 ? "outlined" : "contained"}
                onClick={() => handleGenerateProposals(true)}
                disabled={loading || documents.length === 0}
                startIcon={<RefreshIcon />}
              >
                Generate New Proposals
              </Button>
            </Box>
          </Box>

          {loading && <LinearProgress sx={{ mb: 2 }} />}

          {proposals.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary" paragraph>
                {documents.length === 0 
                  ? 'No documents uploaded yet. Upload PDFs first.' 
                  : 'No proposals yet. Click "Generate Proposals" to analyze your uploaded documents.'}
              </Typography>
              {documents.length > 0 && (
                <Button
                  variant="outlined"
                  onClick={handleGenerateProposals}
                  disabled={loading}
                >
                  Generate Proposals Now
                </Button>
              )}
            </Box>
          ) : (
            <List>
              {proposals.map((proposal, idx) => (
                <React.Fragment key={proposal.id}>
                  {idx > 0 && <Divider />}
                  <ListItem
                    sx={{ flexDirection: 'column', alignItems: 'stretch', py: 2 }}
                  >
                    <Box sx={{ width: '100%' }}>
                      <Typography variant="subtitle1" gutterBottom>
                        {proposal.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {proposal.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Chip
                          label={`Type: ${proposal.proposal_type}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                        <Chip
                          label={`Pages: ${proposal.affected_pages}`}
                          size="small"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          variant="contained"
                          color="success"
                          size="small"
                          startIcon={<ApproveIcon />}
                          onClick={() => handleApproveClick(proposal)}
                          disabled={loading}
                        >
                          Approve & Add to Book
                        </Button>
                        <Button
                          variant="outlined"
                          color="error"
                          size="small"
                          startIcon={<RejectIcon />}
                          onClick={() => handleRejectProposal(proposal.id)}
                          disabled={loading}
                        >
                          Reject
                        </Button>
                      </Box>
                    </Box>
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}
        </Paper>
      </TabPanel>

      {/* Approve Proposal Dialog with Book Selection */}
      <Dialog open={approveDialog} onClose={() => setApproveDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add to Book</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Where should this section be added?
          </Typography>

          <FormControl component="fieldset" fullWidth>
            <RadioGroup value={approveOption} onChange={(e) => setApproveOption(e.target.value)}>
              <FormControlLabel
                value="existing"
                control={<Radio />}
                label="Add to Existing Book"
              />
              {approveOption === 'existing' && (
                <TextField
                  select
                  fullWidth
                  label="Select Book"
                  value={selectedBookId}
                  onChange={(e) => setSelectedBookId(e.target.value)}
                  sx={{ ml: 4, mb: 2, mt: 1 }}
                  size="small"
                >
                  {books.map((book) => (
                    <MenuItem key={book.id} value={book.id}>
                      {book.title} ({book.section_count} sections)
                    </MenuItem>
                  ))}
                </TextField>
              )}

              <FormControlLabel
                value="new"
                control={<Radio />}
                label="Create New Book"
              />
              {approveOption === 'new' && (
                <TextField
                  fullWidth
                  label="New Book Title"
                  value={newBookTitle}
                  onChange={(e) => setNewBookTitle(e.target.value)}
                  sx={{ ml: 4, mb: 2, mt: 1 }}
                  size="small"
                  placeholder="Swing Trading Notes"
                />
              )}
            </RadioGroup>
          </FormControl>

          {selectedProposal && (
            <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Proposal Details:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {selectedProposal.title}
              </Typography>
              <Typography variant="caption">
                Pages: {selectedProposal.affected_pages}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApproveDialog(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmApprove}
            variant="contained"
            disabled={loading || (approveOption === 'existing' && !selectedBookId) || (approveOption === 'new' && !newBookTitle)}
          >
            {approveOption === 'existing' ? 'Add to Book' : 'Create Book & Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default KnowledgeBase;


