# Design Document

## Overview

The Community Voting Page will be a new Streamlit page integrated into the existing environmental analysis application. It provides a minimalistic interface for contractors to upload development plans and for community members to vote on these proposals. The design emphasizes simplicity, clean UI, and seamless integration with the existing application architecture.

## Architecture

### Component Structure
```
Community Voting Page
├── File Upload Section
│   ├── Upload Form (title, description, file)
│   └── File Validation & Storage
├── Development Plans Display
│   ├── Plan List View
│   ├── Plan Details
│   └── Download Links
└── Voting System
    ├── Vote Buttons (upvote/downvote)
    ├── Vote Counter Display
    └── Vote State Management
```

### Data Flow
1. **Upload Flow**: Contractor → Upload Form → File Storage → Plan Display
2. **Voting Flow**: Community Member → Vote Action → State Update → UI Refresh
3. **Display Flow**: Page Load → Fetch Plans → Render List → Show Votes

## Components and Interfaces

### 1. File Upload Component
- **Purpose**: Handle development plan uploads
- **Interface**: Streamlit file uploader with form inputs
- **Validation**: File type checking (PDF, DOC, DOCX, TXT)
- **Storage**: Session state for temporary storage, file system for persistence

### 2. Plan Display Component
- **Purpose**: Show all uploaded development plans
- **Interface**: Card-based layout with plan details
- **Data**: Title, description, upload date, file info, vote counts

### 3. Voting Component
- **Purpose**: Handle upvote/downvote functionality
- **Interface**: Simple button pair with vote counters
- **State Management**: Session state for vote tracking

### 4. File Management Component
- **Purpose**: Handle file storage and retrieval
- **Interface**: Download links for uploaded files
- **Storage**: Local file system with organized directory structure

## Data Models

### Development Plan Model
```python
{
    "id": str,              # Unique identifier
    "title": str,           # Plan title
    "description": str,     # Plan description
    "filename": str,        # Original filename
    "file_path": str,       # Stored file path
    "upload_date": datetime, # Upload timestamp
    "upvotes": int,         # Upvote count
    "downvotes": int        # Downvote count
}
```

### Session State Structure
```python
st.session_state = {
    "development_plans": List[Dict],  # List of all plans
    "uploaded_files": Dict,          # File storage mapping
    "vote_history": Dict             # User vote tracking (optional)
}
```

## Error Handling

### File Upload Errors
- **Invalid file type**: Display clear error message with supported formats
- **File too large**: Show size limit and current file size
- **Upload failure**: Generic error message with retry option

### Voting Errors
- **State corruption**: Reset vote counts with warning message
- **Concurrent voting**: Handle race conditions gracefully

### Display Errors
- **No plans available**: Show friendly empty state message
- **File not found**: Handle missing files with appropriate messaging

## Testing Strategy

### Unit Testing
- File upload validation functions
- Vote counting logic
- Data model validation
- Error handling functions

### Integration Testing
- End-to-end upload workflow
- Voting system functionality
- File download process
- Session state management

### User Acceptance Testing
- Upload different file types
- Vote on multiple plans
- Navigate between pages
- Test error scenarios

## Implementation Details

### File Storage Strategy
- Create `uploads/` directory in project root
- Use timestamp-based naming to avoid conflicts
- Store metadata in session state
- Implement cleanup for old files (optional)

### UI Design Principles
- Consistent with existing application styling
- Minimal, clean interface
- Clear visual hierarchy
- Responsive design for different screen sizes

### Performance Considerations
- Limit file upload size (e.g., 10MB)
- Efficient session state management
- Lazy loading for large plan lists
- Optimized file serving

### Security Considerations
- File type validation
- Filename sanitization
- Path traversal prevention
- Basic input validation for forms

## Integration with Existing Application

### Navigation Integration
- Add new page to `app.py` navigation
- Use consistent icon and naming convention
- Maintain existing page structure

### Styling Integration
- Leverage existing CSS from `assets/styles.css`
- Use consistent color scheme and typography
- Apply existing component styling patterns

### Session State Integration
- Extend existing session state initialization
- Maintain separation from other page data
- Use consistent naming conventions