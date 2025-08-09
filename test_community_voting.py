"""
Unit tests for Community Voting Page core functionality
Tests file upload validation, vote counting, state management, data models, and error handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
from datetime import datetime
import uuid
import sys

# Add the pages directory to the path so we can import the module
sys.path.append('pages')

# Import the functions we want to test
# Note: Import from 4_Community_Voting (the actual filename)
import importlib.util
import sys

# Load the module dynamically since it has a number prefix
spec = importlib.util.spec_from_file_location("community_voting", "pages/4_Community_Voting.py")
community_voting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(community_voting)

# Import the functions we want to test
from community_voting import (
    validate_upload_form,
    create_uploads_directory,
    save_uploaded_file,
    generate_unique_plan_id,
    save_plan_metadata,
    get_all_development_plans,
    get_development_plan_by_id,
    get_plan_files,
    process_plan_upload,
    cleanup_failed_upload,
    format_upload_date,
    get_plan_summary_stats,
    filter_and_sort_plans,
    cast_vote,
    validate_plan_data_model,
    initialize_community_data,
    ALLOWED_FILE_TYPES,
    MAX_FILE_SIZE_MB
)


class TestFileUploadValidation(unittest.TestCase):
    """Test file upload validation functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_file_valid = Mock()
        self.mock_file_valid.name = "test_plan.pdf"
        self.mock_file_valid.size = 1024 * 1024  # 1MB
        
        self.mock_file_large = Mock()
        self.mock_file_large.name = "large_plan.pdf"
        self.mock_file_large.size = 15 * 1024 * 1024  # 15MB (exceeds limit)
        
        self.mock_file_invalid_type = Mock()
        self.mock_file_invalid_type.name = "plan.exe"
        self.mock_file_invalid_type.size = 1024 * 1024  # 1MB
    
    def test_validate_upload_form_valid_input(self):
        """Test validation with valid form inputs"""
        title = "Test Development Plan"
        description = "A comprehensive development plan for testing"
        files = [self.mock_file_valid]
        
        errors = validate_upload_form(title, description, files)
        self.assertEqual(len(errors), 0, "Valid input should not produce errors")
    
    def test_validate_upload_form_missing_title(self):
        """Test validation with missing title"""
        title = ""
        description = "A comprehensive development plan for testing"
        files = [self.mock_file_valid]
        
        errors = validate_upload_form(title, description, files)
        self.assertGreater(len(errors), 0, "Missing title should produce error")
        self.assertTrue(any("title is required" in error for error in errors))
    
    def test_validate_upload_form_missing_description(self):
        """Test validation with missing description"""
        title = "Test Development Plan"
        description = ""
        files = [self.mock_file_valid]
        
        errors = validate_upload_form(title, description, files)
        self.assertGreater(len(errors), 0, "Missing description should produce error")
        self.assertTrue(any("description is required" in error for error in errors))
    
    def test_validate_upload_form_no_files(self):
        """Test validation with no files uploaded"""
        title = "Test Development Plan"
        description = "A comprehensive development plan for testing"
        files = []
        
        errors = validate_upload_form(title, description, files)
        self.assertGreater(len(errors), 0, "No files should produce error")
        self.assertTrue(any("file must be uploaded" in error for error in errors))
    
    def test_validate_upload_form_file_too_large(self):
        """Test validation with file exceeding size limit"""
        title = "Test Development Plan"
        description = "A comprehensive development plan for testing"
        files = [self.mock_file_large]
        
        errors = validate_upload_form(title, description, files)
        self.assertGreater(len(errors), 0, "Large file should produce error")
        self.assertTrue(any("too large" in error for error in errors))
    
    def test_validate_upload_form_invalid_file_type(self):
        """Test validation with invalid file type"""
        title = "Test Development Plan"
        description = "A comprehensive development plan for testing"
        files = [self.mock_file_invalid_type]
        
        errors = validate_upload_form(title, description, files)
        self.assertGreater(len(errors), 0, "Invalid file type should produce error")
        self.assertTrue(any("unsupported format" in error for error in errors))
    
    def test_validate_upload_form_whitespace_only_inputs(self):
        """Test validation with whitespace-only inputs"""
        title = "   "
        description = "   "
        files = [self.mock_file_valid]
        
        errors = validate_upload_form(title, description, files)
        self.assertGreaterEqual(len(errors), 2, "Whitespace-only inputs should produce errors")


class TestFileStorage(unittest.TestCase):
    """Test file storage and retrieval functionality"""
    
    def setUp(self):
        """Set up test fixtures with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_uploads_dir = Path("uploads")
        
        # Mock uploaded file
        self.mock_file = Mock()
        self.mock_file.name = "test_plan.pdf"
        self.mock_file.getbuffer.return_value = b"test file content"
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('community_voting.UPLOADS_DIR')
    def test_create_uploads_directory_success(self, mock_uploads_dir):
        """Test successful creation of uploads directory"""
        mock_uploads_dir.mkdir = Mock()
        result = create_uploads_directory()
        self.assertTrue(result, "Should successfully create uploads directory")
        mock_uploads_dir.mkdir.assert_called_once_with(exist_ok=True)
    
    @patch('community_voting.UPLOADS_DIR')
    def test_create_uploads_directory_failure(self, mock_uploads_dir):
        """Test failure to create uploads directory"""
        mock_uploads_dir.mkdir.side_effect = Exception("Permission denied")
        
        with patch('streamlit.error'):
            result = create_uploads_directory()
            self.assertFalse(result, "Should return False on directory creation failure")
    
    @patch('community_voting.create_uploads_directory')
    @patch('community_voting.UPLOADS_DIR')
    @patch('builtins.open', create=True)
    def test_save_uploaded_file_success(self, mock_open, mock_uploads_dir, mock_create_dir):
        """Test successful file saving"""
        mock_create_dir.return_value = True
        mock_uploads_dir.__truediv__ = Mock(return_value=Path("uploads/test_id_test_plan.pdf"))
        
        plan_id = "test_id"
        result = save_uploaded_file(self.mock_file, plan_id)
        
        self.assertIsNotNone(result, "Should return file path on successful save")
        mock_open.assert_called_once()
    
    @patch('community_voting.create_uploads_directory')
    def test_save_uploaded_file_directory_creation_failure(self, mock_create_dir):
        """Test file saving when directory creation fails"""
        mock_create_dir.return_value = False
        
        plan_id = "test_id"
        result = save_uploaded_file(self.mock_file, plan_id)
        
        self.assertIsNone(result, "Should return None when directory creation fails")
    
    def test_generate_unique_plan_id(self):
        """Test unique plan ID generation"""
        id1 = generate_unique_plan_id()
        id2 = generate_unique_plan_id()
        
        self.assertIsInstance(id1, str, "Should return string")
        self.assertIsInstance(id2, str, "Should return string")
        self.assertNotEqual(id1, id2, "Should generate unique IDs")
        self.assertEqual(len(id1), 8, "Should return 8-character ID")


class TestDataModelValidation(unittest.TestCase):
    """Test data model validation and structure"""
    
    def setUp(self):
        """Set up test data models"""
        self.valid_plan_data = {
            'id': 'test123',
            'title': 'Test Plan',
            'description': 'Test Description',
            'upload_date': datetime.now(),
            'files': [],
            'upvotes': 0,
            'downvotes': 0
        }
    
    def test_validate_plan_data_model_valid(self):
        """Test validation of valid plan data model"""
        is_valid, message = validate_plan_data_model(self.valid_plan_data)
        self.assertTrue(is_valid, "Valid plan data should pass validation")
        self.assertEqual(message, "Valid")
    
    def test_validate_plan_data_model_missing_field(self):
        """Test validation with missing required field"""
        invalid_data = self.valid_plan_data.copy()
        del invalid_data['title']
        
        is_valid, message = validate_plan_data_model(invalid_data)
        self.assertFalse(is_valid, "Missing field should fail validation")
        self.assertIn("Missing required field", message)
    
    def test_validate_plan_data_model_invalid_vote_type(self):
        """Test validation with invalid vote count types"""
        invalid_data = self.valid_plan_data.copy()
        invalid_data['upvotes'] = "not_a_number"
        
        is_valid, message = validate_plan_data_model(invalid_data)
        self.assertFalse(is_valid, "Invalid vote type should fail validation")
        self.assertIn("Vote counts must be integers", message)
    
    def test_validate_plan_data_model_invalid_files_type(self):
        """Test validation with invalid files type"""
        invalid_data = self.valid_plan_data.copy()
        invalid_data['files'] = "not_a_list"
        
        is_valid, message = validate_plan_data_model(invalid_data)
        self.assertFalse(is_valid, "Invalid files type should fail validation")
        self.assertIn("Files must be a list", message)


class TestVotingSystem(unittest.TestCase):
    """Test voting system functionality"""
    
    def setUp(self):
        """Set up test voting data"""
        self.test_plans = [
            {
                'id': 'plan1',
                'title': 'Plan 1',
                'description': 'Description 1',
                'upload_date': datetime.now(),
                'files': [],
                'upvotes': 5,
                'downvotes': 2
            },
            {
                'id': 'plan2',
                'title': 'Plan 2',
                'description': 'Description 2',
                'upload_date': datetime.now(),
                'files': [],
                'upvotes': 3,
                'downvotes': 4
            }
        ]
    
    @patch('streamlit.session_state', {'development_plans': []})
    def test_cast_vote_upvote(self):
        """Test casting an upvote"""
        import streamlit as st
        st.session_state.development_plans = self.test_plans.copy()
        
        result = cast_vote('plan1', 'upvote')
        
        self.assertTrue(result, "Should successfully cast upvote")
        self.assertEqual(st.session_state.development_plans[0]['upvotes'], 6)
        self.assertEqual(st.session_state.development_plans[0]['downvotes'], 2)
    
    @patch('streamlit.session_state', {'development_plans': []})
    def test_cast_vote_downvote(self):
        """Test casting a downvote"""
        import streamlit as st
        st.session_state.development_plans = self.test_plans.copy()
        
        result = cast_vote('plan1', 'downvote')
        
        self.assertTrue(result, "Should successfully cast downvote")
        self.assertEqual(st.session_state.development_plans[0]['upvotes'], 5)
        self.assertEqual(st.session_state.development_plans[0]['downvotes'], 3)
    
    @patch('streamlit.session_state', {'development_plans': []})
    def test_cast_vote_invalid_plan_id(self):
        """Test casting vote for non-existent plan"""
        import streamlit as st
        st.session_state.development_plans = self.test_plans.copy()
        
        result = cast_vote('nonexistent', 'upvote')
        
        self.assertFalse(result, "Should fail for non-existent plan")
    
    def test_get_plan_summary_stats(self):
        """Test calculation of plan summary statistics"""
        with patch('pages.community_voting.get_all_development_plans', return_value=self.test_plans):
            stats = get_plan_summary_stats()
            
            self.assertEqual(stats['total_plans'], 2)
            self.assertEqual(stats['total_votes'], 14)  # 5+2+3+4
            self.assertEqual(stats['most_popular']['id'], 'plan1')  # Higher net votes


class TestStateManagement(unittest.TestCase):
    """Test session state management functionality"""
    
    @patch('streamlit.session_state', {})
    def test_initialize_community_data(self):
        """Test initialization of community data in session state"""
        import streamlit as st
        
        initialize_community_data()
        
        self.assertIn('development_plans', st.session_state)
        self.assertIn('uploaded_files', st.session_state)
        self.assertIn('vote_history', st.session_state)
        self.assertIsInstance(st.session_state.development_plans, list)
        self.assertIsInstance(st.session_state.uploaded_files, dict)
        self.assertIsInstance(st.session_state.vote_history, dict)
    
    @patch('streamlit.session_state', {'development_plans': []})
    def test_get_all_development_plans_empty(self):
        """Test retrieving development plans when none exist"""
        import streamlit as st
        
        plans = get_all_development_plans()
        
        self.assertIsInstance(plans, list)
        self.assertEqual(len(plans), 0)
    
    @patch('streamlit.session_state', {})
    def test_get_all_development_plans_uninitialized(self):
        """Test retrieving development plans when session state is uninitialized"""
        import streamlit as st
        
        plans = get_all_development_plans()
        
        self.assertIsInstance(plans, list)
        self.assertEqual(len(plans), 0)
        self.assertIn('development_plans', st.session_state)
    
    def test_get_development_plan_by_id_found(self):
        """Test retrieving specific plan by ID when it exists"""
        test_plans = [
            {'id': 'plan1', 'title': 'Plan 1'},
            {'id': 'plan2', 'title': 'Plan 2'}
        ]
        
        with patch('pages.community_voting.get_all_development_plans', return_value=test_plans):
            plan = get_development_plan_by_id('plan1')
            
            self.assertIsNotNone(plan)
            self.assertEqual(plan['id'], 'plan1')
            self.assertEqual(plan['title'], 'Plan 1')
    
    def test_get_development_plan_by_id_not_found(self):
        """Test retrieving specific plan by ID when it doesn't exist"""
        test_plans = [
            {'id': 'plan1', 'title': 'Plan 1'},
            {'id': 'plan2', 'title': 'Plan 2'}
        ]
        
        with patch('pages.community_voting.get_all_development_plans', return_value=test_plans):
            plan = get_development_plan_by_id('nonexistent')
            
            self.assertIsNone(plan)


class TestFilteringAndSorting(unittest.TestCase):
    """Test plan filtering and sorting functionality"""
    
    def setUp(self):
        """Set up test plans for filtering and sorting"""
        self.test_plans = [
            {
                'id': 'plan1',
                'title': 'Residential Complex',
                'description': 'A modern residential development',
                'plan_type': 'Residential',
                'upload_date': datetime(2024, 1, 1),
                'upvotes': 10,
                'downvotes': 2
            },
            {
                'id': 'plan2',
                'title': 'Commercial Center',
                'description': 'Shopping and office complex',
                'plan_type': 'Commercial',
                'upload_date': datetime(2024, 2, 1),
                'upvotes': 5,
                'downvotes': 3
            },
            {
                'id': 'plan3',
                'title': 'Mixed Use Building',
                'description': 'Residential and commercial mixed use',
                'plan_type': 'Mixed-Use',
                'upload_date': datetime(2024, 3, 1),
                'upvotes': 15,
                'downvotes': 1
            }
        ]
    
    def test_filter_and_sort_plans_no_filters(self):
        """Test filtering and sorting with no filters applied"""
        result = filter_and_sort_plans(self.test_plans, "", "All", "Upload Date")
        
        self.assertEqual(len(result), 3)
        # Should be sorted by upload date (newest first)
        self.assertEqual(result[0]['id'], 'plan3')
        self.assertEqual(result[1]['id'], 'plan2')
        self.assertEqual(result[2]['id'], 'plan1')
    
    def test_filter_and_sort_plans_search_filter(self):
        """Test filtering by search term"""
        result = filter_and_sort_plans(self.test_plans, "residential", "All", "Upload Date")
        
        self.assertEqual(len(result), 2)  # Should match "Residential Complex" and "Mixed Use" (description)
        plan_ids = [plan['id'] for plan in result]
        self.assertIn('plan1', plan_ids)
        self.assertIn('plan3', plan_ids)
    
    def test_filter_and_sort_plans_type_filter(self):
        """Test filtering by plan type"""
        result = filter_and_sort_plans(self.test_plans, "", "Commercial", "Upload Date")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'plan2')
        self.assertEqual(result[0]['plan_type'], 'Commercial')
    
    def test_filter_and_sort_plans_sort_by_votes(self):
        """Test sorting by most votes"""
        result = filter_and_sort_plans(self.test_plans, "", "All", "Most Votes")
        
        # Should be sorted by total votes (upvotes + downvotes) descending
        self.assertEqual(result[0]['id'], 'plan3')  # 16 total votes
        self.assertEqual(result[1]['id'], 'plan1')  # 12 total votes
        self.assertEqual(result[2]['id'], 'plan2')  # 8 total votes
    
    def test_filter_and_sort_plans_sort_by_title(self):
        """Test sorting by title alphabetically"""
        result = filter_and_sort_plans(self.test_plans, "", "All", "Title")
        
        # Should be sorted alphabetically by title
        self.assertEqual(result[0]['title'], 'Commercial Center')
        self.assertEqual(result[1]['title'], 'Mixed Use Building')
        self.assertEqual(result[2]['title'], 'Residential Complex')


class TestErrorHandling(unittest.TestCase):
    """Test error handling functionality"""
    
    def setUp(self):
        """Set up test files for cleanup testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = [
            {
                'original_name': 'test1.pdf',
                'file_path': os.path.join(self.temp_dir, 'test1.pdf')
            },
            {
                'original_name': 'test2.pdf',
                'file_path': os.path.join(self.temp_dir, 'test2.pdf')
            }
        ]
        
        # Create test files
        for file_info in self.test_files:
            with open(file_info['file_path'], 'w') as f:
                f.write("test content")
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cleanup_failed_upload_success(self):
        """Test successful cleanup of failed upload files"""
        # Verify files exist before cleanup
        for file_info in self.test_files:
            self.assertTrue(os.path.exists(file_info['file_path']))
        
        with patch('streamlit.warning'):
            cleanup_failed_upload(self.test_files)
        
        # Verify files are deleted after cleanup
        for file_info in self.test_files:
            self.assertFalse(os.path.exists(file_info['file_path']))
    
    def test_cleanup_failed_upload_file_not_found(self):
        """Test cleanup when files don't exist"""
        non_existent_files = [
            {
                'original_name': 'nonexistent.pdf',
                'file_path': '/nonexistent/path/file.pdf'
            }
        ]
        
        with patch('streamlit.warning') as mock_warning:
            cleanup_failed_upload(non_existent_files)
            # Should not raise exception, but may log warning
    
    @patch('streamlit.session_state', {'development_plans': []})
    @patch('streamlit.error')
    def test_cast_vote_exception_handling(self, mock_error):
        """Test vote casting with exception handling"""
        import streamlit as st
        
        # Create a plan that will cause an exception when accessing
        problematic_plans = [{'id': 'plan1'}]  # Missing required fields
        st.session_state.development_plans = problematic_plans
        
        result = cast_vote('plan1', 'upvote')
        
        self.assertFalse(result, "Should return False on exception")
        mock_error.assert_called_once()


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_format_upload_date_datetime_object(self):
        """Test formatting datetime object"""
        test_date = datetime(2024, 1, 15, 14, 30, 0)
        formatted = format_upload_date(test_date)
        
        self.assertEqual(formatted, "2024-01-15 14:30")
    
    def test_format_upload_date_string_input(self):
        """Test formatting ISO string input"""
        test_date_str = "2024-01-15T14:30:00"
        formatted = format_upload_date(test_date_str)
        
        self.assertEqual(formatted, "2024-01-15 14:30")
    
    @patch('streamlit.session_state', {'uploaded_files': {}})
    def test_get_plan_files_empty(self):
        """Test getting files for plan with no files"""
        import streamlit as st
        
        files = get_plan_files('nonexistent_plan')
        
        self.assertIsInstance(files, list)
        self.assertEqual(len(files), 0)
    
    @patch('streamlit.session_state', {'uploaded_files': {'plan1': [{'name': 'test.pdf'}]}})
    def test_get_plan_files_with_files(self):
        """Test getting files for plan with files"""
        import streamlit as st
        
        files = get_plan_files('plan1')
        
        self.assertIsInstance(files, list)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['name'], 'test.pdf')


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestFileUploadValidation,
        TestFileStorage,
        TestDataModelValidation,
        TestVotingSystem,
        TestStateManagement,
        TestFilteringAndSorting,
        TestErrorHandling,
        TestUtilityFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\\n')[-2]}")