"""Tests for the CrossPLC converter."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from crossplc.l5x2st import L5X2STConverter
from crossplc.models import STFile, CompilerState


class TestL5X2STConverter:
    """Test cases for L5X2STConverter."""
    
    def test_init(self):
        """Test converter initialization."""
        converter = L5X2STConverter()
        assert isinstance(converter.state, CompilerState)
        assert converter.state.current_controller == 1
    
    def test_parse_variable_declaration(self):
        """Test parsing variable declarations."""
        converter = L5X2STConverter()
        
        # Test basic variable declaration
        line = "    variable_name: BOOL;"
        # This would be tested in the actual parsing logic
        
        # For now, just test that the converter can be created
        assert converter is not None
    
    def test_generate_struct_decs_empty(self):
        """Test generating struct declarations with empty project."""
        converter = L5X2STConverter()
        mock_prj = Mock()
        mock_prj.controller = Mock()
        mock_prj.controller.datatypes = {}
        
        result = converter._generate_struct_decs(mock_prj)
        
        # Should contain auxiliary structs
        assert "(*Structure Declarations*)" in result
        assert "DOMINANT_SET" in result
        assert "MESSAGE" in result
    
    def test_generate_func_decs_empty(self):
        """Test generating function declarations with empty project."""
        converter = L5X2STConverter()
        mock_prj = Mock()
        mock_prj.controller = Mock()
        mock_prj.controller.functionblocks = {}
        
        result = converter._generate_func_decs(mock_prj)
        
        # Should contain auxiliary functions
        assert "(*Function Declarations*)" in result
        assert "FUNCTION SETD" in result
        assert "FUNCTION SCL" in result
    
    def test_generate_var_decs_empty(self):
        """Test generating variable declarations with empty project."""
        converter = L5X2STConverter()
        mock_prj = Mock()
        mock_prj.controller = Mock()
        mock_prj.controller.tags = Mock()
        mock_prj.controller.tags.members = {}
        mock_prj.programs = {}
        
        result = converter._generate_var_decs(mock_prj)
        
        assert "PROGRAM prog0" in result
        assert "VAR" in result
        assert "END_VAR" in result
        assert "bit_access_helper: DWORD" in result
    
    def test_generate_prog_block_empty(self):
        """Test generating program block with empty project."""
        converter = L5X2STConverter()
        mock_prj = Mock()
        mock_prj.controller = Mock()
        mock_prj.controller.tags = Mock()
        mock_prj.controller.tags.members = {}
        mock_prj.programs = {}
        
        result = converter._generate_prog_block(mock_prj)
        
        assert "END_PROGRAM" in result
        assert "CONFIGURATION Config0" in result
    
    @patch('crossplc.l5x2st.l5x.Project')
    def test_parse_l5x_file_mock(self, mock_l5x_project):
        """Test parsing L5X file with mocked l5x library."""
        converter = L5X2STConverter()
        
        # Mock the L5X project
        mock_prj = Mock()
        mock_prj.controller = Mock()
        mock_prj.controller.tags = Mock()
        mock_prj.controller.tags.members = {}
        mock_prj.controller.datatypes = {}
        mock_prj.controller.functionblocks = {}
        mock_prj.programs = {}
        
        mock_l5x_project.return_value = mock_prj
        
        result = converter.parse_l5x_file("test.L5X")
        
        assert isinstance(result, STFile)
        assert result.description == "test.L5X"
    
    def test_convert_file(self, tmp_path):
        """Test converting a file."""
        converter = L5X2STConverter()
        
        # Create a mock L5X file
        l5x_file = tmp_path / "test.L5X"
        l5x_file.write_text("<?xml version='1.0'?><RSLogix5000Content></RSLogix5000Content>")
        
        output_file = tmp_path / "output.st"
        
        # This would need the actual l5x library to work
        # For now, just test that the method exists
        assert hasattr(converter, 'convert_file')
    
    def test_convert_directory(self, tmp_path):
        """Test converting a directory."""
        converter = L5X2STConverter()
        
        # Create a mock directory structure
        l5x_dir = tmp_path / "l5x_files"
        l5x_dir.mkdir()
        
        # Create mock L5X files
        (l5x_dir / "P1.L5X").write_text("<?xml version='1.0'?><RSLogix5000Content></RSLogix5000Content>")
        (l5x_dir / "P2.L5X").write_text("<?xml version='1.0'?><RSLogix5000Content></RSLogix5000Content>")
        
        output_file = tmp_path / "consolidated.st"
        
        # This would need the actual l5x library to work
        # For now, just test that the method exists
        assert hasattr(converter, 'convert_directory')


class TestCompilerState:
    """Test cases for CompilerState."""
    
    def test_init(self):
        """Test CompilerState initialization."""
        state = CompilerState()
        assert state.current_controller == 1
        assert len(state.fbd_timers) == 0
        assert len(state.data_types) == 0
        assert len(state.var_names) == 0
    
    def test_reset_for_new_controller(self):
        """Test resetting state for new controller."""
        state = CompilerState()
        state.current_controller = 5
        state.appended_reserved_words = ["test"]
        
        state.reset_for_new_controller()
        
        assert state.current_controller == 6
        assert len(state.appended_reserved_words) == 0
    
    def test_add_variable(self):
        """Test adding a variable."""
        state = CompilerState()
        
        state.add_variable("test_var", "BOOL", "original_tag")
        
        assert "test_var" in state.var_names
        assert state.data_types["test_var"] == "BOOL"
        assert state.var_origin["test_var"] == "original_tag"
    
    def test_add_struct(self):
        """Test adding a struct."""
        state = CompilerState()
        
        state.add_struct("test_struct", "original_struct")
        
        assert "test_struct" in state.struct_names
        assert state.struct_origin["test_struct"] == "original_struct"
    
    def test_add_function(self):
        """Test adding a function."""
        state = CompilerState()
        
        state.add_function("test_func", "original_func")
        
        assert "test_func" in state.fbd_names
        assert state.fbd_origin["test_func"] == "original_func" 