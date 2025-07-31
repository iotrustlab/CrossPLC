/*
 * Sample TXT Control Logic
 * 
 * This file demonstrates common patterns found in Fischertechnik TXT C++ control logic
 * based on the txt_training_factory repository.
 */

#include <iostream>
#include <thread>
#include <chrono>
#include <string>

// Global variables (internal tags)
int motor_speed = 512;
int current_position = 0;
bool is_running = false;
int error_code = 0;
std::string status = "IDLE";

// TXT-specific patterns
FISH_X1_TRANSFER* pTArea = NULL;

// Input functions (sensor readings)
bool isSwitchPressed(uint8_t switch_id) {
    // Simulate switch reading
    return (switch_id % 2 == 0);
}

bool read_sensor(int sensor_id) {
    // Simulate sensor reading
    return (sensor_id % 3 == 0);
}

bool get_input(int input_pin) {
    return read_sensor(input_pin);
}

// Output functions (actuator control)
void setMotorOff() {
    if (pTArea) {
        pTArea->ftX1out.duty[0] = 0;
        pTArea->ftX1out.duty[1] = 0;
    }
    std::cout << "Motor turned off" << std::endl;
}

void setMotorLeft() {
    if (pTArea) {
        pTArea->ftX1out.duty[0] = -motor_speed;
        pTArea->ftX1out.duty[1] = 0;
    }
    std::cout << "Motor turned left" << std::endl;
}

void setMotorRight() {
    if (pTArea) {
        pTArea->ftX1out.duty[0] = motor_speed;
        pTArea->ftX1out.duty[1] = 0;
    }
    std::cout << "Motor turned right" << std::endl;
}

void setSpeed(int16_t speed) {
    motor_speed = speed;
    std::cout << "Speed set to: " << speed << std::endl;
}

void set_output(int output_pin, bool value) {
    if (pTArea) {
        pTArea->ftX1out.duty[output_pin] = value ? 1 : 0;
    }
    std::cout << "Output " << output_pin << " set to " << value << std::endl;
}

// Main control loop
void main_control_loop() {
    std::cout << "Starting TXT control loop..." << std::endl;
    is_running = true;
    
    while (is_running) {
        // Read inputs
        bool sensor1 = read_sensor(1);
        bool sensor2 = get_input(2);
        bool switch1 = isSwitchPressed(3);
        
        // Control logic
        if (switch1) {
            // Switch is pressed, start motor
            setMotorRight();
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        } else {
            // Switch not pressed, stop motor
            setMotorOff();
        }
        
        // Check for emergency stop
        if (sensor1 && sensor2) {
            // Emergency condition detected
            setMotorOff();
            error_code = 1;
            std::cout << "Emergency stop activated!" << std::endl;
            break;
        }
        
        // Update position
        if (is_running) {
            current_position += 1;
        }
        
        // Sleep for control cycle
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    std::cout << "TXT control loop stopped." << std::endl;
}

// State machine example (similar to TXT FSM patterns)
enum State_t {
    IDLE,
    RUNNING,
    STOPPED,
    ERROR,
    FAULT
};

void state_machine() {
    State_t currentState = IDLE;
    State_t newState = IDLE;
    
    while (true) {
        // Entry activities
        if (newState != currentState) {
            switch (newState) {
                case IDLE:
                    std::cout << "State: IDLE" << std::endl;
                    setSpeed(512);
                    status = "IDLE";
                    break;
                case RUNNING:
                    std::cout << "State: RUNNING" << std::endl;
                    setMotorRight();
                    status = "RUNNING";
                    break;
                case STOPPED:
                    std::cout << "State: STOPPED" << std::endl;
                    setMotorOff();
                    status = "STOPPED";
                    break;
                case ERROR:
                    std::cout << "State: ERROR" << std::endl;
                    setMotorOff();
                    error_code = 2;
                    status = "ERROR";
                    break;
                case FAULT:
                    std::cout << "State: FAULT" << std::endl;
                    setMotorOff();
                    error_code = 3;
                    status = "FAULT";
                    break;
            }
            currentState = newState;
        }
        
        // Do activities
        switch (currentState) {
            case IDLE:
                if (isSwitchPressed(1)) {
                    newState = RUNNING;
                }
                break;
            case RUNNING:
                if (isSwitchPressed(2)) {
                    newState = STOPPED;
                } else if (read_sensor(1)) {
                    newState = ERROR;
                }
                break;
            case STOPPED:
                if (isSwitchPressed(1)) {
                    newState = IDLE;
                }
                break;
            case ERROR:
                std::this_thread::sleep_for(std::chrono::milliseconds(1000));
                newState = IDLE;
                break;
            case FAULT:
                // Stay in fault state
                break;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

// Function calls with parameters
void process_workpiece(int workpiece_id) {
    std::cout << "Processing workpiece " << workpiece_id << std::endl;
    
    // Move to position
    setMotorRight();
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    setMotorOff();
    
    // Check sensor
    if (read_sensor(workpiece_id)) {
        set_output(1, true);
        std::cout << "Workpiece processed successfully" << std::endl;
    } else {
        set_output(2, true);
        std::cout << "Workpiece rejected" << std::endl;
    }
}

int main() {
    // Start control logic
    try {
        main_control_loop();
    } catch (const std::exception& e) {
        std::cout << "Control loop interrupted: " << e.what() << std::endl;
        is_running = false;
    }
    
    return 0;
} 