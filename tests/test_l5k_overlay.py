"""
Tests for L5K overlay functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from l5x_st_compiler.l5k_overlay import (
    L5KOverlay, L5KTag, L5KTask, L5KProgram, L5KModule
)
from l5x_st_compiler.models import (
    IRProject, IRController, IRProgram, IRRoutine, IRTag, IRDataType,
    TagScope, RoutineType
)


class TestL5KOverlay:
    """Test cases for L5K overlay functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_l5k_content = """
	TAG
		System_Ready : BOOL (RADIX := Decimal) := FALSE;
		Process_Value : REAL (RADIX := Decimal) := 0.0;
		Alarm_Array : BOOL[10] (RADIX := Decimal) := FALSE;
		Status_Word : DINT (RADIX := Decimal) := 0;
		Temperature : REAL (RADIX := Decimal, DESCRIPTION := "Process temperature sensor") := 25.0;
	END_TAG

	TASK MainTask (Type := CONTINUOUS,
	               Rate := 10,
	               Priority := 10,
	               Watchdog := 500,
	               DisableUpdateOutputs := No,
	               InhibitTask := No)
		MainProgram;
	END_TASK

	TASK PeriodicTask (Type := PERIODIC,
	                   Rate := 100,
	                   Priority := 5,
	                   Watchdog := 1000,
	                   DisableUpdateOutputs := No,
	                   InhibitTask := No)
		AlarmProgram;
	END_TASK

	PROGRAM MainProgram (MAIN := "MainRoutine",
	                     MODE := 0,
	                     DisableFlag := 0,
	                     SynchronizeRedundancyDataAfterExecution := 1)
		TAG
			Local_Tag : BOOL (RADIX := Decimal) := FALSE;
		END_TAG
	END_PROGRAM

	PROGRAM AlarmProgram (MAIN := "AlarmRoutine",
	                      MODE := 0,
	                      DisableFlag := 0,
	                      SynchronizeRedundancyDataAfterExecution := 1)
		TAG
			Alarm_Local_Tag : BOOL (RADIX := Decimal) := FALSE;
		END_TAG
	END_PROGRAM

	MODULE Analog_Input (Parent := "Local",
	                     CatalogNumber := "1756-IF8",
	                     Slot := 1,
	                     CommFormat := "Data-INT",
	                     Inhibited := No,
	                     MajorFault := No,
	                     ElectronicKeying := "Compatible Module",
	                     CompatibleModule := 0)
	END_MODULE

	MODULE Digital_Output (Parent := "Local",
	                       CatalogNumber := "1756-OB16D",
	                       Slot := 2,
	                       CommFormat := "Data-INT",
	                       Inhibited := No,
	                       MajorFault := No,
	                       ElectronicKeying := "Compatible Module",
	                       CompatibleModule := 0)
	END_MODULE
"""
    
    def test_l5k_tag_creation(self):
        """Test L5KTag dataclass creation."""
        tag = L5KTag(
            name="Test_Tag",
            data_type="BOOL",
            scope="Controller",
            value="TRUE",
            description="Test tag description"
        )
        
        assert tag.name == "Test_Tag"
        assert tag.data_type == "BOOL"
        assert tag.scope == "Controller"
        assert tag.value == "TRUE"
        assert tag.description == "Test tag description"
    
    def test_l5k_task_creation(self):
        """Test L5KTask dataclass creation."""
        task = L5KTask(
            name="TestTask",
            task_type="PERIODIC",
            priority=5,
            watchdog=1000,
            interval="T#100ms"
        )
        
        assert task.name == "TestTask"
        assert task.task_type == "PERIODIC"
        assert task.priority == 5
        assert task.watchdog == 1000
        assert task.interval == "T#100ms"
    
    def test_l5k_program_creation(self):
        """Test L5KProgram dataclass creation."""
        program = L5KProgram(
            name="TestProgram",
            main_routine="TestRoutine",
            task_name="TestTask"
        )
        
        assert program.name == "TestProgram"
        assert program.main_routine == "TestRoutine"
        assert program.task_name == "TestTask"
    
    def test_l5k_module_creation(self):
        """Test L5KModule dataclass creation."""
        module = L5KModule(
            name="TestModule",
            module_type="1756-IF8",
            slot=1,
            configuration={"Channel": "0"}
        )
        
        assert module.name == "TestModule"
        assert module.module_type == "1756-IF8"
        assert module.slot == 1
        assert module.configuration["Channel"] == "0"
    
    def test_l5k_overlay_initialization(self):
        """Test L5KOverlay initialization with valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(self.sample_l5k_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            assert overlay.l5k_file_path == Path(temp_file)
            assert overlay.content == self.sample_l5k_content
        finally:
            os.unlink(temp_file)
    
    def test_l5k_overlay_file_not_found(self):
        """Test L5KOverlay initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            L5KOverlay("nonexistent_file.L5K")
    
    def test_parse_tags(self):
        """Test parsing of TAG sections from L5K content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(self.sample_l5k_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            
            # Check that tags were parsed
            assert len(overlay.tags) >= 4
            
            # Check specific tags
            tag_names = [tag.name for tag in overlay.tags]
            assert "System_Ready" in tag_names
            assert "Process_Value" in tag_names
            assert "Alarm_Array" in tag_names
            assert "Status_Word" in tag_names
            
            # Check tag properties
            system_ready = next(tag for tag in overlay.tags if tag.name == "System_Ready")
            assert system_ready.data_type == "BOOL"
            assert system_ready.value == "FALSE"
            
            process_value = next(tag for tag in overlay.tags if tag.name == "Process_Value")
            assert process_value.data_type == "REAL"
            assert process_value.value == "0.0"
            
            alarm_array = next(tag for tag in overlay.tags if tag.name == "Alarm_Array")
            assert alarm_array.data_type == "BOOL"
            assert alarm_array.array_dimensions == [10]
            
            temperature = next(tag for tag in overlay.tags if tag.name == "Temperature")
            assert temperature.data_type == "REAL"
            assert temperature.description == "Process temperature sensor"
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_tasks(self):
        """Test parsing of TASK sections from L5K content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(self.sample_l5k_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            
            # Check that tasks were parsed
            assert len(overlay.tasks) >= 2
            
            # Check specific tasks
            task_names = [task.name for task in overlay.tasks]
            assert "MainTask" in task_names
            assert "PeriodicTask" in task_names
            
            # Check task properties
            main_task = next(task for task in overlay.tasks if task.name == "MainTask")
            assert main_task.task_type == "CONTINUOUS"
            assert main_task.priority == 10
            assert main_task.watchdog == 500
            
            periodic_task = next(task for task in overlay.tasks if task.name == "PeriodicTask")
            assert periodic_task.task_type == "PERIODIC"
            assert periodic_task.priority == 5
            assert periodic_task.interval == "T#100ms"
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_programs(self):
        """Test parsing of PROGRAM sections from L5K content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(self.sample_l5k_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            
            # Check that programs were parsed
            assert len(overlay.programs) >= 2
            
            # Check specific programs
            program_names = [prog.name for prog in overlay.programs]
            assert "MainProgram" in program_names
            assert "AlarmProgram" in program_names
            
            # Check program properties
            main_program = next(prog for prog in overlay.programs if prog.name == "MainProgram")
            assert main_program.main_routine == "MainRoutine"
            assert main_program.task_name == "MainTask"
            
            alarm_program = next(prog for prog in overlay.programs if prog.name == "AlarmProgram")
            assert alarm_program.main_routine == "AlarmRoutine"
            assert alarm_program.task_name == "PeriodicTask"
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_modules(self):
        """Test parsing of MODULE sections from L5K content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(self.sample_l5k_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            
            # Check that modules were parsed
            assert len(overlay.modules) >= 2
            
            # Check specific modules
            module_names = [mod.name for mod in overlay.modules]
            assert "Analog_Input" in module_names
            assert "Digital_Output" in module_names
            
            # Check module properties
            analog_input = next(mod for mod in overlay.modules if mod.name == "Analog_Input")
            assert analog_input.module_type == "1756-IF8"
            assert analog_input.slot == 1
            
            digital_output = next(mod for mod in overlay.modules if mod.name == "Digital_Output")
            assert digital_output.module_type == "1756-OB16D"
            assert digital_output.slot == 2
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_array_dimensions(self):
        """Test parsing of array dimensions."""
        overlay = L5KOverlay.__new__(L5KOverlay)  # Create instance without calling __init__
        
        # Test single dimension
        dims = overlay._parse_array_dimensions("10")
        assert dims == [10]
        
        # Test multiple dimensions
        dims = overlay._parse_array_dimensions("5,10,15")
        assert dims == [5, 10, 15]
        
        # Test invalid dimensions
        dims = overlay._parse_array_dimensions("invalid")
        assert dims == []
    
    def test_apply_to_ir(self):
        """Test applying L5K overlay to IR project."""
        # Create a mock IR project
        controller = IRController(
            name="TestController",
            tags=[],
            data_types=[],
            function_blocks=[]
        )
        
        ir_project = IRProject(
            controller=controller,
            programs=[],
            modules=[],
            tasks=[],
            metadata={}
        )
        
        # Create L5K overlay with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(self.sample_l5k_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            augmented_project = overlay.apply_to_ir(ir_project)
            
            # Check that tags were added
            assert len(augmented_project.controller.tags) >= 4
            
            # Check that tasks were added
            assert len(augmented_project.tasks) >= 2
            
            # Check that programs were added
            assert len(augmented_project.programs) >= 2
            
            # Check that modules were added
            assert len(augmented_project.modules) >= 2
            
            # Check metadata
            assert augmented_project.metadata['l5k_overlay_applied'] is True
            assert augmented_project.metadata['l5k_source_file'] == temp_file
            assert augmented_project.metadata['l5k_tags_added'] >= 4
            assert augmented_project.metadata['l5k_tasks_added'] >= 2
            assert augmented_project.metadata['l5k_programs_added'] >= 2
            assert augmented_project.metadata['l5k_modules_added'] >= 2
            
        finally:
            os.unlink(temp_file)
    
    def test_merge_tag_info(self):
        """Test merging L5K tag information into existing IR tag."""
        overlay = L5KOverlay.__new__(L5KOverlay)  # Create instance without calling __init__
        
        # Create existing IR tag
        ir_tag = IRTag(
            name="TestTag",
            data_type="BOOL",
            scope=TagScope.CONTROLLER,
            description=None,
            external_access=None,
            radix=None,
            initial_value=None
        )
        
        # Create L5K tag with additional information
        l5k_tag = L5KTag(
            name="TestTag",
            data_type="BOOL",
            description="Updated description",
            external_access="Read/Write",
            radix="Decimal",
            initial_value="TRUE"
        )
        
        # Merge information
        overlay._merge_tag_info(ir_tag, l5k_tag)
        
        # Check that information was merged
        assert ir_tag.description == "Updated description"
        assert ir_tag.external_access == "Read/Write"
        assert ir_tag.radix == "Decimal"
        assert ir_tag.initial_value == "TRUE"
    
    def test_get_summary(self):
        """Test getting summary of parsed L5K data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(self.sample_l5k_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            summary = overlay.get_summary()
            
            assert summary['source_file'] == temp_file
            assert summary['tags_count'] >= 4
            assert summary['tasks_count'] >= 2
            assert summary['programs_count'] >= 2
            assert summary['modules_count'] >= 2
            
            assert "System_Ready" in summary['tags']
            assert "MainTask" in summary['tasks']
            assert "MainProgram" in summary['programs']
            assert "Analog_Input" in summary['modules']
            
        finally:
            os.unlink(temp_file)
    
    def test_complex_l5k_content(self):
        """Test parsing of more complex L5K content."""
        complex_content = """
	TAG
		Complex_Tag : DINT[5,10] (RADIX := Decimal, DESCRIPTION := "Complex array tag", ExternalAccess := "Read Only") := 0;
		Alias_Tag : BOOL (RADIX := Decimal, ALIAS_FOR := "Original_Tag") := FALSE;
		Constant_Tag : REAL (RADIX := Decimal, CONSTANT := TRUE) := 3.14159;
	END_TAG

	TASK EventTask (Type := EVENT,
	                Priority := 1,
	                Watchdog := 1000,
	                DisableUpdateOutputs := No,
	                InhibitTask := No)
		ComplexProgram;
	END_TASK

	PROGRAM ComplexProgram (MAIN := "ComplexRoutine",
	                        MODE := 0,
	                        DisableFlag := 0,
	                        SynchronizeRedundancyDataAfterExecution := 1)
		TAG
			Complex_Local_Tag : BOOL (RADIX := Decimal) := FALSE;
		END_TAG
	END_PROGRAM

	MODULE ComplexModule (Parent := "Local",
	                      CatalogNumber := "1756-EN2T",
	                      Slot := 3,
	                      CommFormat := "Data-INT",
	                      Inhibited := No,
	                      MajorFault := No,
	                      ElectronicKeying := "Compatible Module",
	                      CompatibleModule := 0)
	END_MODULE
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(complex_content)
            temp_file = f.name
        
        try:
            overlay = L5KOverlay(temp_file)
            
            # Check complex tag
            complex_tag = next(tag for tag in overlay.tags if tag.name == "Complex_Tag")
            assert complex_tag.data_type == "DINT"
            assert complex_tag.array_dimensions == [5, 10]
            assert complex_tag.description == "Complex array tag"
            assert complex_tag.external_access == "Read Only"
            
            # Check alias tag
            alias_tag = next(tag for tag in overlay.tags if tag.name == "Alias_Tag")
            assert alias_tag.alias_for == "Original_Tag"
            
            # Check constant tag
            constant_tag = next(tag for tag in overlay.tags if tag.name == "Constant_Tag")
            assert constant_tag.constant is True
            assert constant_tag.value == "3.14159"
            
            # Check event task
            event_task = next(task for task in overlay.tasks if task.name == "EventTask")
            assert event_task.task_type == "EVENT"
            assert event_task.priority == 1
            assert event_task.watchdog == 1000
            
            # Check complex program
            complex_program = next(prog for prog in overlay.programs if prog.name == "ComplexProgram")
            assert complex_program.main_routine == "ComplexRoutine"
            assert complex_program.task_name == "EventTask"
            # Note: No description in the L5K content, so it should be None
            
            # Check complex module
            complex_module = next(mod for mod in overlay.modules if mod.name == "ComplexModule")
            assert complex_module.module_type == "1756-EN2T"
            assert complex_module.slot == 3
            # Note: No description in the L5K content, so it should be None
            
        finally:
            os.unlink(temp_file)
    
    def test_error_handling(self):
        """Test error handling in L5K parsing."""
        # Test with malformed content
        malformed_content = """
TAG "Malformed_Tag" : INVALID_TYPE;
TASK "Malformed_Task" : INVALID_TYPE;
PROGRAM "Malformed_Program" : INVALID_DEFINITION;
MODULE "Malformed_Module" : INVALID_TYPE;
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.L5K', delete=False) as f:
            f.write(malformed_content)
            temp_file = f.name
        
        try:
            # Should not raise exception, but should log warnings
            overlay = L5KOverlay(temp_file)
            
            # Should still have empty lists
            assert len(overlay.tags) == 0
            assert len(overlay.tasks) == 0
            assert len(overlay.programs) == 0
            assert len(overlay.modules) == 0
            
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__]) 