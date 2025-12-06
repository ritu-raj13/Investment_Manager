import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Menu,
  MenuItem,
  Collapse,
  Chip,
  Alert
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  FileDownload as ExportIcon,
  MenuBook as BookIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import MarkdownEditor from './MarkdownEditor';
import { knowledgeAPI } from '../services/api';

function BookView() {
  const [books, setBooks] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [sections, setSections] = useState([]);
  const [expandedSections, setExpandedSections] = useState({});
  const [editDialog, setEditDialog] = useState(false);
  const [newBookDialog, setNewBookDialog] = useState(false);
  const [newSectionDialog, setNewSectionDialog] = useState(false);
  const [editingSection, setEditingSection] = useState(null);
  const [exportMenu, setExportMenu] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Form states
  const [bookTitle, setBookTitle] = useState('');
  const [bookDescription, setBookDescription] = useState('');
  const [sectionTitle, setSectionTitle] = useState('');
  const [sectionContent, setSectionContent] = useState('');
  const [sectionType, setSectionType] = useState('section');
  
  // Use ref to prevent infinite loops
  const loadingBooks = useRef(false);
  const loadingSections = useRef(false);

  const loadBooks = async (autoSelect = false) => {
    if (loadingBooks.current) return;
    loadingBooks.current = true;
    
    try {
      const response = await knowledgeAPI.getBooks();
      const booksList = response?.data?.books || response?.books || [];
      setBooks(booksList);
      
      // Only auto-select on first load if requested
      if (autoSelect && booksList.length > 0) {
        setSelectedBook(prevBook => prevBook || booksList[0]);
      }
    } catch (err) {
      console.error('Failed to load books:', err);
      setError(err.message || 'Failed to load books');
      setBooks([]);
    } finally {
      loadingBooks.current = false;
    }
  };

  const loadBookSections = async (bookId) => {
    if (loadingSections.current) return;
    loadingSections.current = true;
    
    try {
      const response = await knowledgeAPI.getBook(bookId);
      const bookData = response?.data?.book || response?.book || {};
      setSections(bookData.sections || []);
    } catch (err) {
      console.error('Failed to load sections:', err);
      setError(err.message || 'Failed to load sections');
      setSections([]);
    } finally {
      loadingSections.current = false;
    }
  };

  // Load books only once on mount - NO DEPENDENCIES
  useEffect(() => {
    loadBooks(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty array - run only once

  // Load sections when book ID changes
  useEffect(() => {
    if (selectedBook?.id) {
      loadBookSections(selectedBook.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBook?.id]); // Only re-run when ID changes

  const handleCreateBook = async () => {
    setLoading(true);
    try {
      await knowledgeAPI.createBook({ title: bookTitle, description: bookDescription });
      setSuccess('Book created successfully');
      setNewBookDialog(false);
      setBookTitle('');
      setBookDescription('');
      loadBooks();
    } catch (err) {
      setError(err.message || 'Failed to create book');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSection = async () => {
    setLoading(true);
    try {
      await knowledgeAPI.createSection({
        book_id: selectedBook.id,
        title: sectionTitle,
        content: sectionContent,
        content_markdown: sectionContent,
        section_type: sectionType
      });
      setSuccess('Section created successfully');
      setNewSectionDialog(false);
      setSectionTitle('');
      setSectionContent('');
      loadBookSections(selectedBook.id);
    } catch (err) {
      setError(err.message || 'Failed to create section');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSection = async () => {
    if (!editingSection) return;
    
    setLoading(true);
    try {
      await knowledgeAPI.updateSection(editingSection.id, {
        title: sectionTitle,
        content: sectionContent,
        content_markdown: sectionContent
      });
      setSuccess('Section updated successfully');
      setEditDialog(false);
      setEditingSection(null);
      setSectionTitle('');
      setSectionContent('');
      loadBookSections(selectedBook.id);
      
      if (selectedSection && selectedSection.id === editingSection.id) {
        setSelectedSection(null);
      }
    } catch (err) {
      setError(err.message || 'Failed to update section');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSection = async (sectionId) => {
    if (!window.confirm('Delete this section?')) return;
    
    try {
      await knowledgeAPI.deleteSection(sectionId);
      setSuccess('Section deleted');
      loadBookSections(selectedBook.id);
      
      if (selectedSection && selectedSection.id === sectionId) {
        setSelectedSection(null);
      }
    } catch (err) {
      setError(err.message || 'Failed to delete section');
    }
  };

  const handleEditSection = (section) => {
    setEditingSection(section);
    setSectionTitle(section.title);
    setSectionContent(section.content_markdown || section.content);
    setEditDialog(true);
  };

  const handleReorganize = async () => {
    if (!window.confirm('Reorganize this book into logical chapters? This will group sections by topic.')) {
      return;
    }
    
    setLoading(true);
    try {
      const result = await knowledgeAPI.reorganizeBook(selectedBook.id);
      setSuccess(result.message || 'Book reorganized successfully');
      loadBooks();
      if (selectedBook) {
        loadBookSections(selectedBook.id);
      }
    } catch (err) {
      setError(err.message || 'Reorganization failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSynthesize = async () => {
    if (!window.confirm('Transform raw notes into clean, readable book content? This uses AI to rewrite sections as coherent prose. This may take 5-10 minutes.')) {
      return;
    }
    
    setLoading(true);
    setSuccess('Synthesizing content... This will take several minutes. Please wait.');
    
    try {
      const result = await knowledgeAPI.synthesizeBookContent(selectedBook.id);
      setSuccess(result.message || 'Content synthesized successfully! Your book is now readable.');
      loadBooks();
      if (selectedBook) {
        loadBookSections(selectedBook.id);
      }
    } catch (err) {
      setError(err.message || 'Synthesis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const blob = await knowledgeAPI.exportBook(selectedBook.id, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedBook.title}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setSuccess(`Book exported as ${format.toUpperCase()}`);
    } catch (err) {
      setError(err.message || 'Export failed');
    }
    setExportMenu(null);
  };

  const toggleExpand = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const renderSectionTree = (section, level = 0) => (
    <Box key={section.id} sx={{ pl: level * 2 }}>
      <ListItem
        disablePadding
        secondaryAction={
          <Box>
            <IconButton size="small" onClick={() => handleEditSection(section)}>
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => handleDeleteSection(section.id)}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        }
      >
        <ListItemButton onClick={() => setSelectedSection(section)}>
          {section.subsections && section.subsections.length > 0 && (
            <IconButton size="small" onClick={(e) => {
              e.stopPropagation();
              toggleExpand(section.id);
            }}>
              {expandedSections[section.id] ? <CollapseIcon /> : <ExpandIcon />}
            </IconButton>
          )}
          <ListItemText
            primary={section.title}
            secondary={
              <Box>
                <Chip label={section.section_type} size="small" sx={{ mr: 1, mt: 0.5 }} />
                {section.page_numbers && (
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    Pages: {section.page_numbers}
                  </Typography>
                )}
              </Box>
            }
          />
        </ListItemButton>
      </ListItem>
      
      {section.subsections && section.subsections.length > 0 && (
        <Collapse in={expandedSections[section.id]}>
          {section.subsections.map(sub => renderSectionTree(sub, level + 1))}
        </Collapse>
      )}
    </Box>
  );

  return (
    <Box sx={{ height: '100%', display: 'flex', gap: 2 }}>
      {/* Left Sidebar - Book TOC */}
      <Paper sx={{ width: 300, p: 2, overflowY: 'auto' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Books</Typography>
          <IconButton size="small" onClick={() => setNewBookDialog(true)}>
            <AddIcon />
          </IconButton>
        </Box>

        {books.map(book => (
          <Box
            key={book.id}
            sx={{
              p: 1,
              mb: 1,
              cursor: 'pointer',
              bgcolor: selectedBook?.id === book.id ? 'primary.light' : 'transparent',
              borderRadius: 1,
              '&:hover': { bgcolor: 'action.hover' }
            }}
            onClick={() => setSelectedBook(book)}
          >
            <Typography variant="subtitle1">{book.title}</Typography>
            <Typography variant="caption" color="text.secondary">
              {book.section_count} sections
            </Typography>
          </Box>
        ))}

        {selectedBook && (
          <>
            <Box sx={{ mt: 3, mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle2">Chapters</Typography>
              <IconButton size="small" onClick={() => setNewSectionDialog(true)}>
                <AddIcon />
              </IconButton>
            </Box>

            <List dense>
              {sections.map(section => renderSectionTree(section))}
            </List>
          </>
        )}
      </Paper>

      {/* Main Content Area */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
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

        {selectedBook && (
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h5">{selectedBook.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedBook.description}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  onClick={handleReorganize}
                  disabled={loading || sections.length === 0}
                  size="small"
                >
                  1. Organize
                </Button>
                <Button
                  variant="contained"
                  onClick={handleSynthesize}
                  disabled={loading || sections.length === 0}
                  size="small"
                >
                  2. Synthesize Content
                </Button>
                <Button
                  startIcon={<ExportIcon />}
                  onClick={(e) => setExportMenu(e.currentTarget)}
                  size="small"
                >
                  3. Export
                </Button>
              </Box>
              <Menu
                anchorEl={exportMenu}
                open={Boolean(exportMenu)}
                onClose={() => setExportMenu(null)}
              >
                <MenuItem onClick={() => handleExport('html')}>Export as HTML</MenuItem>
                <MenuItem onClick={() => handleExport('pdf')}>Export as PDF</MenuItem>
              </Menu>
            </Box>
          </Paper>
        )}

        {selectedSection ? (
          <Paper sx={{ p: 3, overflowY: 'auto', flexGrow: 1 }}>
            <Typography variant="h4" gutterBottom>{selectedSection.title}</Typography>
            
            {selectedSection.page_numbers && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                Source Pages: {selectedSection.page_numbers}
              </Typography>
            )}

            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({node, ...props}) => <Typography variant="h4" gutterBottom {...props} />,
                h2: ({node, ...props}) => <Typography variant="h5" gutterBottom {...props} />,
                h3: ({node, ...props}) => <Typography variant="h6" gutterBottom {...props} />,
                p: ({node, ...props}) => <Typography variant="body1" paragraph {...props} />
              }}
            >
              {selectedSection.content_markdown || selectedSection.content}
            </ReactMarkdown>

            {selectedSection.images && selectedSection.images.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>Images</Typography>
                {selectedSection.images.map((img, idx) => (
                  <Box key={idx} sx={{ mb: 2 }}>
                    <img
                      src={`/${img.image_path}`}
                      alt={img.caption || 'Image'}
                      style={{ maxWidth: '100%', height: 'auto' }}
                    />
                    {img.caption && (
                      <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', color: 'text.secondary' }}>
                        {img.caption}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        ) : (
          <Paper sx={{ p: 3, flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Box sx={{ textAlign: 'center' }}>
              <BookIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                {selectedBook ? 'Select a section to view' : 'Create or select a book to start'}
              </Typography>
            </Box>
          </Paper>
        )}
      </Box>

      {/* New Book Dialog */}
      <Dialog open={newBookDialog} onClose={() => setNewBookDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Book</DialogTitle>
        <DialogContent>
          <TextField
            label="Title"
            fullWidth
            value={bookTitle}
            onChange={(e) => setBookTitle(e.target.value)}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={bookDescription}
            onChange={(e) => setBookDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewBookDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateBook} variant="contained" disabled={!bookTitle || loading}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* New Section Dialog */}
      <Dialog open={newSectionDialog} onClose={() => setNewSectionDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Section</DialogTitle>
        <DialogContent>
          <TextField
            label="Title"
            fullWidth
            value={sectionTitle}
            onChange={(e) => setSectionTitle(e.target.value)}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            select
            label="Type"
            fullWidth
            value={sectionType}
            onChange={(e) => setSectionType(e.target.value)}
            sx={{ mb: 2 }}
          >
            <MenuItem value="chapter">Chapter</MenuItem>
            <MenuItem value="section">Section</MenuItem>
            <MenuItem value="subsection">Subsection</MenuItem>
          </TextField>
          <MarkdownEditor
            value={sectionContent}
            onChange={setSectionContent}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewSectionDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateSection} variant="contained" disabled={!sectionTitle || loading}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Section Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Section</DialogTitle>
        <DialogContent>
          <TextField
            label="Title"
            fullWidth
            value={sectionTitle}
            onChange={(e) => setSectionTitle(e.target.value)}
            sx={{ mt: 2, mb: 2 }}
          />
          <MarkdownEditor
            value={sectionContent}
            onChange={setSectionContent}
            onSave={handleUpdateSection}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={handleUpdateSection} variant="contained" disabled={!sectionTitle || loading}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default BookView;

