import React, { useState } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  TextField,
  Typography,
  Button,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  FormatBold as BoldIcon,
  FormatItalic as ItalicIcon,
  Code as CodeIcon,
  FormatListBulleted as ListIcon,
  Link as LinkIcon,
  Image as ImageIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function MarkdownEditor({ value, onChange, onSave, disabled = false }) {
  const [activeTab, setActiveTab] = useState(0);

  const insertMarkdown = (before, after = '') => {
    const textarea = document.getElementById('markdown-textarea');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    const newText = value.substring(0, start) + before + selectedText + after + value.substring(end);
    
    onChange(newText);
    
    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + before.length, start + before.length + selectedText.length);
    }, 0);
  };

  const handleBold = () => insertMarkdown('**', '**');
  const handleItalic = () => insertMarkdown('*', '*');
  const handleCode = () => insertMarkdown('`', '`');
  const handleList = () => {
    const textarea = document.getElementById('markdown-textarea');
    const start = textarea.selectionStart;
    const lineStart = value.lastIndexOf('\n', start - 1) + 1;
    const newText = value.substring(0, lineStart) + '- ' + value.substring(lineStart);
    onChange(newText);
  };
  const handleLink = () => insertMarkdown('[', '](url)');
  const handleImage = () => insertMarkdown('![alt text](', ')');

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Edit" />
          <Tab label="Preview" />
        </Tabs>
      </Box>

      {activeTab === 0 ? (
        <Box>
          {/* Toolbar */}
          <Paper sx={{ p: 1, mb: 1, display: 'flex', gap: 1 }} elevation={1}>
            <Tooltip title="Bold">
              <IconButton size="small" onClick={handleBold} disabled={disabled}>
                <BoldIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Italic">
              <IconButton size="small" onClick={handleItalic} disabled={disabled}>
                <ItalicIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Code">
              <IconButton size="small" onClick={handleCode} disabled={disabled}>
                <CodeIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="List">
              <IconButton size="small" onClick={handleList} disabled={disabled}>
                <ListIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Link">
              <IconButton size="small" onClick={handleLink} disabled={disabled}>
                <LinkIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Image">
              <IconButton size="small" onClick={handleImage} disabled={disabled}>
                <ImageIcon fontSize="small" />
              </IconButton>
            </Tooltip>

            <Box sx={{ flexGrow: 1 }} />
            
            {onSave && (
              <Button
                size="small"
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={onSave}
                disabled={disabled}
              >
                Save
              </Button>
            )}
          </Paper>

          {/* Editor */}
          <TextField
            id="markdown-textarea"
            multiline
            fullWidth
            rows={20}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder="Write your content in Markdown..."
            sx={{
              '& .MuiInputBase-input': {
                fontFamily: "'Courier New', monospace",
                fontSize: '14px'
              }
            }}
          />

          {/* Quick Reference */}
          <Paper sx={{ p: 2, mt: 2, bgcolor: '#f9f9f9' }} elevation={0}>
            <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', mb: 1 }}>
              Markdown Quick Reference:
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace' }}>
              **bold** | *italic* | `code` | [link](url) | ![image](url)
              <br />
              # Heading 1 | ## Heading 2 | - List item | &gt; Blockquote
            </Typography>
          </Paper>
        </Box>
      ) : (
        <Box>
          {/* Preview */}
          <Paper sx={{ p: 3, minHeight: 400 }} elevation={0} variant="outlined">
            {value ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({node, ...props}) => <Typography variant="h4" gutterBottom {...props} />,
                  h2: ({node, ...props}) => <Typography variant="h5" gutterBottom {...props} />,
                  h3: ({node, ...props}) => <Typography variant="h6" gutterBottom {...props} />,
                  p: ({node, ...props}) => <Typography variant="body1" paragraph {...props} />,
                  code: ({node, inline, ...props}) => inline ? (
                    <code style={{
                      background: '#f4f4f4',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontFamily: 'monospace'
                    }} {...props} />
                  ) : (
                    <pre style={{
                      background: '#f4f4f4',
                      padding: '15px',
                      borderRadius: '5px',
                      overflow: 'auto'
                    }}>
                      <code {...props} />
                    </pre>
                  ),
                  img: ({node, ...props}) => (
                    <img
                      {...props}
                      style={{
                        maxWidth: '100%',
                        height: 'auto',
                        display: 'block',
                        margin: '20px auto'
                      }}
                      alt={props.alt || 'Image'}
                    />
                  )
                }}
              >
                {value}
              </ReactMarkdown>
            ) : (
              <Typography color="text.secondary" align="center">
                Nothing to preview yet. Start writing in the Edit tab!
              </Typography>
            )}
          </Paper>
        </Box>
      )}
    </Box>
  );
}

export default MarkdownEditor;

