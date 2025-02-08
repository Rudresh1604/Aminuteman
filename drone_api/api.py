from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import clr
import time
from typing import Optional
import uvicorn
from command_matcher import CommandMatcher  # Your existing command matcher class

# Add Mission Planner references
try:
    clr.AddReference("MissionPlanner")
    clr.AddReference("MissionPlanner.Utilities")
    from MissionPlanner import MainV2
    MISSION_PLANNER_AVAILABLE = True
except:
    print("Warning: Mission Planner libraries not found. Running in test mode.")
    MISSION_PLANNER_AVAILABLE = False

app = FastAPI(title="Drone Command API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize command matcher
matcher = CommandMatcher()

class UserMessage(BaseModel):
    message: str

class CommandGenerateResponse(BaseModel):
    success: bool
    original_message: str
    generated_command: str

class CommandExecuteResponse(BaseModel):
    success: bool
    original_message: str
    interpreted_command: str
    execution_status: str
    details: Optional[dict] = None

def execute_mavlink_command(command_str: str) -> dict:
    """Execute MAVLink command and return result"""
    if not MISSION_PLANNER_AVAILABLE:
        return {"success": False, "status": "Mission Planner not available"}
    
    try:
        mavlink = MainV2.comPort
        if not mavlink.BaseStream.IsOpen:
            return {"success": False, "status": "Not connected to vehicle"}

        commands = command_str.split(';')
        execution_results = []
        
        for cmd in commands:
            cmd = cmd.strip()
            
            if cmd.startswith('arm'):
                mavlink.doARM(True)
                time.sleep(1)
                execution_results.append({"command": "arm", "status": "executed"})
                
            elif cmd.startswith('disarm'):
                mavlink.doARM(False)
                execution_results.append({"command": "disarm", "status": "executed"})
                
            elif cmd.startswith('mode'):
                mode = cmd.split()[1].upper()
                mavlink.setMode(mode)
                execution_results.append({"command": f"mode {mode}", "status": "executed"})
                
            elif cmd.startswith('takeoff'):
                altitude = float(cmd.split()[1]) if len(cmd.split()) > 1 else 10.0
                mavlink.doCommand(mavlink.MAV_CMD.TAKEOFF, 0, 0, 0, 0, 0, 0, altitude)
                execution_results.append({"command": f"takeoff {altitude}m", "status": "executed"})
                
            elif cmd.startswith('wp'):
                # Handle waypoint command
                parts = cmd.split()
                if parts[1] == 'seq':
                    wp_num = parts[2]
                    mavlink.setWPCurrent(int(wp_num))
                    execution_results.append({"command": f"waypoint {wp_num}", "status": "executed"})
                else:
                    lat, lon = float(parts[1]), float(parts[2])
                    alt = float(parts[3]) if len(parts) > 3 else 10.0
                    mavlink.setGuidedModeWP(lat, lon, alt)
                    execution_results.append({"command": f"waypoint {lat},{lon},{alt}", "status": "executed"})
            
            time.sleep(0.5)
            
        return {
            "success": True,
            "status": "All commands executed",
            "details": execution_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": f"Error executing command: {str(e)}"
        }

@app.post("/generate-command", response_model=CommandGenerateResponse)
async def generate_command(user_message: UserMessage):
    """Generate command without execution (for testing)"""
    try:
        generated_command = matcher.process_command(user_message.message)
        
        return CommandGenerateResponse(
            success=generated_command != "No commands recognized. Please try again.",
            original_message=user_message.message,
            generated_command=generated_command
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating command: {str(e)}"
        )

@app.post("/execute-command", response_model=CommandExecuteResponse)
async def execute_command(user_message: UserMessage):
    """Generate and execute command"""
    try:
        # Convert natural language to command
        mavlink_command = matcher.process_command(user_message.message)
        
        # Check if command was recognized
        if mavlink_command == "No commands recognized. Please try again.":
            return CommandExecuteResponse(
                success=False,
                original_message=user_message.message,
                interpreted_command=mavlink_command,
                execution_status="Command not recognized",
                details={"error": "Could not interpret command"}
            )
        
        # Execute command
        execution_result = execute_mavlink_command(mavlink_command)
        
        return CommandExecuteResponse(
            success=execution_result["success"],
            original_message=user_message.message,
            interpreted_command=mavlink_command,
            execution_status=execution_result["status"],
            details=execution_result.get("details")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing command: {str(e)}"
        )

@app.get("/status")
async def get_status():
    """Check system status"""
    return {
        "api_status": "online",
        "mission_planner_available": MISSION_PLANNER_AVAILABLE,
        "vehicle_connected": MainV2.comPort.BaseStream.IsOpen if MISSION_PLANNER_AVAILABLE else False
    }

if __name__ == "__main__":
    print("\nStarting Drone Command API...")
    print("Endpoints:")
    print("  /generate-command - Test command generation only")
    print("  /execute-command - Generate and execute commands")
    print("  /status - Check system status")
    print("\n1. API is running on http://localhost:8000")
    print("2. To use with ngrok: ngrok http 8000")
    print("3. Swagger docs available at /docs endpoint\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")