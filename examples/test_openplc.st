VAR
    Tank_Level : REAL := 0.0;
    Pump_Status : BOOL := FALSE;
    Temperature : REAL := 25.0;
    Alarm_Active : BOOL := FALSE;
    Setpoint : REAL := 50.0;
END_VAR

VAR_INPUT
    Start_Button : BOOL;
    Stop_Button : BOOL;
    Level_Sensor : REAL;
    Temp_Sensor : REAL;
END_VAR

VAR_OUTPUT
    Pump_Control : BOOL;
    Alarm_Light : BOOL;
    Status_LED : BOOL;
END_VAR

PROGRAM Tank_Control
    // Main control logic
    IF Start_Button AND NOT Stop_Button THEN
        Pump_Control := TRUE;
        Status_LED := TRUE;
    END_IF;
    
    IF Stop_Button THEN
        Pump_Control := FALSE;
        Status_LED := FALSE;
    END_IF;
    
    // Update tank level
    Tank_Level := Level_Sensor;
    
    // Check temperature
    Temperature := Temp_Sensor;
    
    // Alarm logic
    IF Temperature > Setpoint THEN
        Alarm_Active := TRUE;
        Alarm_Light := TRUE;
    ELSE
        Alarm_Active := FALSE;
        Alarm_Light := FALSE;
    END_IF;
    
    // Pump status
    Pump_Status := Pump_Control;
END_PROGRAM 