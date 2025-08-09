import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os
import uuid
import shutil

# File upload constants
ALLOWED_FILE_TYPES = ['pdf', 'doc', 'docx', 'txt']
MAX_FILE_SIZE_MB = 10
UPLOADS_DIR = Path("uploads")

def validate_upload_form(title, description, files):
    """Validate the upload form inputs"""
    errors = []
    
    # Validate required fields
    if not title or not title.strip():
        errors.append("📝 Plan title is required")
    
    if not description or not description.strip():
        errors.append("📝 Plan description is required")
    
    if not files:
        errors.append("📁 At least one file must be uploaded")
    
    # Validate files if provided
    if files:
        for file in files:
            # Check file size (convert bytes to MB)
            file_size_mb = file.size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                errors.append(f"📁 File '{file.name}' is too large ({file_size_mb:.1f}MB). Maximum size is {MAX_FILE_SIZE_MB}MB")
            
            # Check file type
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in ALLOWED_FILE_TYPES:
                errors.append(f"📁 File '{file.name}' has unsupported format. Allowed formats: {', '.join(ALLOWED_FILE_TYPES).upper()}")
    
    return errors

def create_uploads_directory():
    """Create uploads directory if it doesn't exist"""
    try:
        UPLOADS_DIR.mkdir(exist_ok=True)
        return True
    except Exception as e:
        st.error(f"Failed to create uploads directory: {str(e)}")
        return False

def save_uploaded_file(uploaded_file, plan_id):
    """Save uploaded file to the uploads directory"""
    try:
        # Create uploads directory if it doesn't exist
        if not create_uploads_directory():
            return None
        
        # Generate unique filename to avoid conflicts
        file_extension = uploaded_file.name.split('.')[-1].lower()
        safe_filename = f"{plan_id}_{uploaded_file.name}"
        file_path = UPLOADS_DIR / safe_filename
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return str(file_path)
    
    except Exception as e:
        st.error(f"Failed to save file '{uploaded_file.name}': {str(e)}")
        return None

def generate_unique_plan_id():
    """Generate a unique ID for a development plan"""
    return str(uuid.uuid4())[:8]

def save_plan_metadata(title, description, plan_type, start_date, files):
    """Save plan metadata after successful upload"""
    try:
        # Generate unique ID for the plan
        plan_id = generate_unique_plan_id()
        
        # Save uploaded files
        saved_files = []
        for file in files:
            file_path = save_uploaded_file(file, plan_id)
            if file_path:
                saved_files.append({
                    'original_name': file.name,
                    'file_path': file_path,
                    'file_size': file.size
                })
            else:
                # If any file fails to save, clean up and return failure
                cleanup_failed_upload(saved_files)
                return None
        
        # Create development plan data structure according to design document
        plan_data = {
            'id': plan_id,
            'title': title.strip(),
            'description': description.strip(),
            'plan_type': plan_type,
            'proposed_start_date': start_date.isoformat() if start_date else None,
            'upload_date': datetime.now(),
            'files': saved_files,
            'upvotes': 0,
            'downvotes': 0
        }
        
        # Initialize session state if needed
        if 'development_plans' not in st.session_state:
            st.session_state.development_plans = []
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = {}
        
        # Add to session state
        st.session_state.development_plans.append(plan_data)
        st.session_state.uploaded_files[plan_id] = saved_files
        
        return plan_data
    
    except Exception as e:
        st.error(f"Failed to save plan metadata: {str(e)}")
        return None

def get_all_development_plans():
    """Retrieve all stored development plans"""
    if 'development_plans' not in st.session_state:
        st.session_state.development_plans = []
    return st.session_state.development_plans

def get_plan_files(plan_id):
    """Retrieve files associated with a development plan"""
    if 'uploaded_files' not in st.session_state:
        return []
    return st.session_state.uploaded_files.get(plan_id, [])

def process_plan_upload(title, description, plan_type, start_date, files):
    """Process the development plan upload"""
    try:
        plan_data = save_plan_metadata(title, description, plan_type, start_date, files)
        return plan_data is not None
    except Exception as e:
        st.error(f"Failed to process upload: {str(e)}")
        return False

def cleanup_failed_upload(saved_files):
    """Clean up files if upload fails partway through"""
    for file_info in saved_files:
        try:
            file_path = Path(file_info['file_path'])
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            st.warning(f"Failed to clean up file {file_info['original_name']}: {str(e)}")

def format_upload_date(upload_date):
    """Format upload date for display"""
    if isinstance(upload_date, str):
        upload_date = datetime.fromisoformat(upload_date)
    return upload_date.strftime('%Y-%m-%d %H:%M')

def get_plan_summary_stats():
    """Get summary statistics for all development plans"""
    plans = get_all_development_plans()
    total_plans = len(plans)
    total_votes = sum(plan['upvotes'] + plan['downvotes'] for plan in plans)
    
    # Find most popular plan (highest upvote ratio)
    most_popular = None
    if plans:
        most_popular = max(plans, key=lambda p: p['upvotes'] - p['downvotes'])
    
    return {
        'total_plans': total_plans,
        'total_votes': total_votes,
        'most_popular': most_popular
    }

def filter_and_sort_plans(plans, search_term, plan_type_filter, sort_by):
    """Filter and sort development plans based on user criteria"""
    filtered_plans = plans.copy()
    
    # Apply search filter
    if search_term and search_term.strip():
        search_lower = search_term.lower().strip()
        filtered_plans = [
            plan for plan in filtered_plans
            if search_lower in plan['title'].lower() or search_lower in plan['description'].lower()
        ]
    
    # Apply type filter
    if plan_type_filter and plan_type_filter != "All":
        filtered_plans = [
            plan for plan in filtered_plans
            if plan.get('plan_type', '') == plan_type_filter
        ]
    
    # Apply sorting
    if sort_by == "Upload Date":
        filtered_plans.sort(key=lambda p: p['upload_date'], reverse=True)
    elif sort_by == "Most Votes":
        filtered_plans.sort(key=lambda p: p['upvotes'] + p['downvotes'], reverse=True)
    elif sort_by == "Title":
        filtered_plans.sort(key=lambda p: p['title'].lower())
    
    return filtered_plans

def cast_vote(plan_id, vote_type):
    """Cast a vote for a development plan and update session state"""
    try:
        # Find the plan in session state
        plans = st.session_state.development_plans
        for i, plan in enumerate(plans):
            if plan['id'] == plan_id:
                # Update vote count based on vote type
                if vote_type == 'upvote':
                    st.session_state.development_plans[i]['upvotes'] += 1
                elif vote_type == 'downvote':
                    st.session_state.development_plans[i]['downvotes'] += 1
                
                # Track vote in vote history (optional for preventing duplicate votes)
                if 'vote_history' not in st.session_state:
                    st.session_state.vote_history = {}
                
                if plan_id not in st.session_state.vote_history:
                    st.session_state.vote_history[plan_id] = []
                
                st.session_state.vote_history[plan_id].append({
                    'vote_type': vote_type,
                    'timestamp': datetime.now()
                })
                
                return True
        
        return False
    except Exception as e:
        st.error(f"Failed to cast vote: {str(e)}")
        return False

def display_development_plans_cards(plans, key_suffix=""):
    """Display development plans in card-based layout with voting functionality"""
    for plan in plans:
        # Create card container with styling
        with st.container():
            # Card styling with border and padding
            st.markdown(f"""
            <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='margin-bottom: 1rem;'>
                    <h4 style='margin: 0 0 0.5rem 0; color: #1f1f1f;'>🏗️ {plan['title']}</h4>
                    <p style='margin: 0; color: #666; font-size: 0.9rem;'>
                        <strong>Type:</strong> {plan.get('plan_type', 'N/A')} | 
                        <strong>Uploaded:</strong> {format_upload_date(plan['upload_date'])}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Plan description
            st.markdown(f"**Description:** {plan['description']}")
            
            # Display proposed start date if available
            if plan.get('proposed_start_date'):
                st.markdown(f"**Proposed Start:** {plan['proposed_start_date']}")
            
            # Voting section with buttons and real-time vote counts
            st.markdown("### 🗳️ Community Voting")
            
            # Create columns for voting interface
            vote_col1, vote_col2, vote_col3, vote_col4 = st.columns([1, 1, 1, 2])
            
            with vote_col1:
                # Upvote button with unique key
                if st.button(
                    f"👍 Upvote", 
                    key=f"upvote_{plan['id']}{key_suffix}", 
                    help="Vote in favor of this development plan",
                    use_container_width=True
                ):
                    if cast_vote(plan['id'], 'upvote'):
                        st.success("✅ Upvote recorded!")
                        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
                    else:
                        st.error("❌ Failed to record vote")
            
            with vote_col2:
                # Downvote button with unique key
                if st.button(
                    f"👎 Downvote", 
                    key=f"downvote_{plan['id']}{key_suffix}", 
                    help="Vote against this development plan",
                    use_container_width=True
                ):
                    if cast_vote(plan['id'], 'downvote'):
                        st.success("✅ Downvote recorded!")
                        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
                    else:
                        st.error("❌ Failed to record vote")
            
            with vote_col3:
                # Display current upvotes with styling
                st.metric(
                    label="👍 Upvotes", 
                    value=plan['upvotes'],
                    help="Number of community members who support this plan"
                )
            
            with vote_col4:
                # Display current downvotes with styling
                st.metric(
                    label="👎 Downvotes", 
                    value=plan['downvotes'],
                    help="Number of community members who oppose this plan"
                )
            
            # Calculate and display vote ratio
            total_votes = plan['upvotes'] + plan['downvotes']
            if total_votes > 0:
                approval_rate = (plan['upvotes'] / total_votes) * 100
                st.progress(approval_rate / 100, text=f"Community Approval: {approval_rate:.1f}% ({total_votes} total votes)")
            else:
                st.info("No votes yet - be the first to vote!")
            
            # Display files and download links
            plan_files = get_plan_files(plan['id'])
            if plan_files:
                st.markdown("**📁 Attached Files:**")
                
                # Create download links for each file
                file_cols = st.columns(min(len(plan_files), 3))  # Max 3 files per row
                
                for idx, file_info in enumerate(plan_files):
                    col_idx = idx % 3
                    with file_cols[col_idx]:
                        file_size_kb = file_info['file_size'] / 1024
                        
                        # Check if file exists before creating download link
                        file_path = Path(file_info['file_path'])
                        if file_path.exists():
                            try:
                                with open(file_path, "rb") as file:
                                    file_data = file.read()
                                
                                st.download_button(
                                    label=f"📥 {file_info['original_name']}",
                                    data=file_data,
                                    file_name=file_info['original_name'],
                                    mime="application/octet-stream",
                                    help=f"Download {file_info['original_name']} ({file_size_kb:.1f} KB)",
                                    key=f"download_{plan['id']}_{idx}{key_suffix}"
                                )
                            except Exception as e:
                                st.error(f"Error loading file: {file_info['original_name']}")
                        else:
                            st.warning(f"⚠️ File not found: {file_info['original_name']}")
            else:
                st.markdown("**📁 Files:** No files attached")
            
            # Add separator between cards
            st.markdown("---")

def display_upload_section():
    """Display the file upload section for development plans"""
    st.header("📤 Upload Development Plan")
    st.markdown("Share your development proposal with the community for feedback and voting.")
    
    # Upload form with actual functionality
    with st.form("upload_plan_form", clear_on_submit=True):
        st.subheader("📋 Plan Details")
        
        # Form inputs
        col1, col2 = st.columns(2)
        
        with col1:
            plan_title = st.text_input(
                "Plan Title *", 
                placeholder="Enter a descriptive title for your development plan",
                help="Provide a clear, concise title that describes your development project"
            )
            plan_type = st.selectbox(
                "Plan Type *", 
                ["Residential", "Commercial", "Mixed-Use", "Infrastructure", "Other"],
                help="Select the primary type of development"
            )
        
        with col2:
            plan_description = st.text_area(
                "Description *", 
                placeholder="Provide a detailed description of your development plan",
                help="Include key features, benefits, and any environmental considerations",
                height=100
            )
            proposed_start_date = st.date_input(
                "Proposed Start Date",
                help="When do you plan to begin construction?"
            )
        
        # File upload with validation
        st.subheader("📁 Upload Documents")
        st.markdown("*Upload your development plan documents (PDF, DOC, DOCX, TXT)*")
        
        uploaded_files = st.file_uploader(
            "Choose development plan files",
            type=['pdf', 'doc', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Upload PDF, DOC, DOCX, or TXT files containing your development plan details"
        )
        
        # Show file preview if files are uploaded
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")
            with st.expander("📄 File Details"):
                for file in uploaded_files:
                    st.write(f"• **{file.name}** ({file.size / 1024:.1f} KB)")
        
        # Submit button with actual functionality
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("📤 Submit Development Plan", type="primary", use_container_width=True)
            
            if submitted:
                # Validate form inputs
                validation_errors = validate_upload_form(plan_title, plan_description, uploaded_files)
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                else:
                    # Process the upload
                    try:
                        success = process_plan_upload(
                            plan_title, 
                            plan_description, 
                            plan_type, 
                            proposed_start_date, 
                            uploaded_files
                        )
                        
                        if success:
                            st.success("🎉 Development plan uploaded successfully!")
                            st.markdown("*Your plan is now available for community voting.*")
                            st.rerun()
                        else:
                            st.error("❌ Failed to upload development plan. Please try again.")
                    
                    except Exception as e:
                        st.error(f"❌ Upload failed: {str(e)}")
                        st.markdown("*Please check your files and try again.*")

def display_plans_section():
    """Display all uploaded development plans"""
    st.header("📋 Development Plans")
    st.markdown("Browse and review all submitted development plans.")
    
    # Get all development plans using the retrieval function
    all_plans = get_all_development_plans()
    
    # Filter and search options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search plans", placeholder="Search by title or description...")
    with col2:
        plan_type_filter = st.selectbox("Filter by Type", ["All", "Residential", "Commercial", "Mixed-Use", "Infrastructure", "Other"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Upload Date", "Most Votes", "Title"])
    
    # Check if there are any plans - implement empty state message
    if not all_plans:
        # Empty state message as required
        st.info("📝 No development plans have been uploaded yet. Be the first to share your proposal!")
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background-color: #f8f9fa; border-radius: 8px; margin: 1rem 0;'>
            <h3>🏗️ Ready to Share Your Development Plan?</h3>
            <p>Upload your development proposal to get community feedback and votes.</p>
            <p><em>Switch to the "Upload Plan" tab to get started!</em></p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Filter plans based on search and type filter
    filtered_plans = filter_and_sort_plans(all_plans, search_term, plan_type_filter, sort_by)
    
    # Show summary statistics
    stats = get_plan_summary_stats()
    st.success(f"📋 {len(filtered_plans)} of {stats['total_plans']} development plan(s) displayed")
    
    # Display plans in card-based layout with voting functionality
    display_development_plans_cards(filtered_plans, key_suffix="_plans")

def display_voting_section():
    """Display voting results and analytics"""
    st.header("📊 Voting Results & Analytics")
    st.markdown("View community voting statistics and analytics.")
    
    # Get current statistics
    stats = get_plan_summary_stats()
    all_plans = get_all_development_plans()
    
    if not all_plans:
        st.info("📊 No plans available for voting analysis yet.")
        return
    
    # Display voting statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Plans", stats['total_plans'], help="Total number of development plans")
    with col2:
        st.metric("Total Votes", stats['total_votes'], help="Total votes cast by community")
    with col3:
        most_popular_title = stats['most_popular']['title'][:20] + "..." if stats['most_popular'] and len(stats['most_popular']['title']) > 20 else (stats['most_popular']['title'] if stats['most_popular'] else "N/A")
        st.metric("Most Popular", most_popular_title, help="Plan with highest approval rating")
    with col4:
        participation_rate = f"{(stats['total_votes'] / max(stats['total_plans'], 1)):.1f}" if stats['total_plans'] > 0 else "0"
        st.metric("Avg Votes/Plan", participation_rate, help="Average votes per plan")
    
    # Show voting analytics
    st.markdown("### 📈 Voting Analytics")
    
    # Calculate voting statistics
    if all_plans:
        # Most controversial plan (closest to 50/50 split)
        controversial_plan = None
        min_difference = float('inf')
        
        for plan in all_plans:
            total_votes = plan['upvotes'] + plan['downvotes']
            if total_votes > 0:
                approval_rate = plan['upvotes'] / total_votes
                difference = abs(approval_rate - 0.5)
                if difference < min_difference:
                    min_difference = difference
                    controversial_plan = plan
        
        # Most supported plan
        most_supported = max(all_plans, key=lambda p: p['upvotes']) if all_plans else None
        
        # Display analytics
        col1, col2 = st.columns(2)
        
        with col1:
            if most_supported and most_supported['upvotes'] > 0:
                st.success(f"**🏆 Most Supported Plan:**")
                st.write(f"• {most_supported['title']}")
                st.write(f"• {most_supported['upvotes']} upvotes")
                total_votes = most_supported['upvotes'] + most_supported['downvotes']
                if total_votes > 0:
                    approval = (most_supported['upvotes'] / total_votes) * 100
                    st.write(f"• {approval:.1f}% approval rate")
            else:
                st.info("No votes cast yet")
        
        with col2:
            if controversial_plan and (controversial_plan['upvotes'] + controversial_plan['downvotes']) > 0:
                st.warning(f"**⚖️ Most Debated Plan:**")
                st.write(f"• {controversial_plan['title']}")
                total_votes = controversial_plan['upvotes'] + controversial_plan['downvotes']
                approval = (controversial_plan['upvotes'] / total_votes) * 100
                st.write(f"• {approval:.1f}% approval rate")
                st.write(f"• {total_votes} total votes")
            else:
                st.info("No controversial plans yet")

def initialize_community_data():
    """Initialize community voting data in session state"""
    # Initialize development plans list if not exists
    if 'development_plans' not in st.session_state:
        st.session_state.development_plans = []
    
    # Initialize uploaded files tracking if not exists
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    
    # Initialize vote history tracking if not exists
    if 'vote_history' not in st.session_state:
        st.session_state.vote_history = {}

def main():
    """Main function for the Community Voting page"""
    st.title("🗳️ Community Voting")
    st.markdown("---")
    
    # Page description with consistent styling
    st.markdown("""
    **Welcome to the Community Voting platform!** This space allows contractors to share development plans 
    and enables community members to vote on proposed developments.
    
    📋 **For Contractors**: Upload your development plans and get community feedback  
    🗳️ **For Community**: Review and vote on proposed developments in your area  
    📊 **For Everyone**: View voting results and community sentiment
    """)
    
    # Create main layout with tabs for better organization
    tab1, tab2, tab3 = st.tabs(["📤 Upload Plan", "📋 View Plans", "📊 Voting Results"])
    
    with tab1:
        display_upload_section()
    
    with tab2:
        display_plans_section()
    
    with tab3:
        display_voting_section()

if __name__ == "__main__":
    # Initialize community data
    initialize_community_data()
    
    # Run main function
    main()