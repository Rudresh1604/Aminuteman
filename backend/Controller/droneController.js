const DroneModel = require("../Models/droneModel");
const Client = require("../Models/userModel");
const jwt = require("jsonwebtoken");
const DroneAuthenticator = async (req, res, next) => {
  try {
    const { email, secret, token } = req.body;

    if (!email || !secret || !token) {
      return res.status(400).send("All fields are required");
    }

    // Find user
    const user = await Client.findOne({ email });
    console.log(user);

    if (!user) {
      return res.status(400).send("Invalid credentials");
    }
    if (user.role === "MWO") {
      return res.status(403).send("Access denied");
    }
    if (secret !== "DroneIP" && secret !== "Admin11") {
      return res.status(403).send("Access denied");
    }
    let action;
    if (secret == "DroneIP") {
      action = "Login And Requested for Drone Access ";
    } else {
      action = "Login And Requested for Admin Access";
    }
    user.allActivity.push({
      action: action,
      timestamp: new Date(),
      ipAddress: req.ip,
    });

    await user.save();

    return res.status(200).send("Authentication successful");
  } catch (error) {
    console.error("Authentication Error:", error);
    return res.status(400).send(error.message);
  }
};

const getDroneData = async (req, res, next) => {
  try {
    const { droneName, token } = req.query;

    // Validate inputs
    if (!droneName || !token) {
      return res.status(400).send("Drone name and token are required");
    }

    // Verify token first
    const JWT_SECRET = process.env.JWT_SECRET;
    if (!JWT_SECRET) {
      throw new Error("JWT_SECRET is not configured");
    }

    let decoded = await jwt.verify(token, JWT_SECRET);
    console.log(decoded);

    if (!decoded) {
      return res.status(401).send("Invalid or expired token");
    }

    // Find drone and user
    const drone = await DroneModel.findOne({ droneName });
    const user = await Client.findById(decoded._id);
    console.log(user);

    if (!drone) {
      return res.status(404).send("Drone not found");
    }

    if (!user) {
      return res.status(404).send("User not found");
    }

    // Log activity
    user.allActivity.push({
      action: `Accessed Drone ${drone.droneName}`,
      timestamp: new Date(),
      droneName: drone.droneName,
      ipAddress: req.ip,
    });

    await user.save();

    return res.status(200).send(drone);
  } catch (error) {
    console.error("Drone Data Error:", error);
    next(error);
  }
};

const getAllDroneData = async (req, res, next) => {
  try {
    const getDrone = await DroneModel.find();

    if (!getDrone) {
      return res.status(400).send("Invalid Drone");
    }

    return res.status(200).send(getDrone);
  } catch (error) {
    console.error("Signup Error:", error);
    next(error);
  }
};

const registerDrone = async (req, res, next) => {
  try {
    const { droneName } = req.body;
    if (!droneName) {
      return res.json("Invalid Drone");
    }

    const Drone = await DroneModel.create({ droneName });
    console.log(Drone);
    return res.status(200).send(Drone);
  } catch (error) {
    console.error("Signup Error:", error);
    next(error);
  }
};

const recieveDroneData = async (req, res, next) => {
  try {
    const {
      droneName,
      longitude,
      latitude,
      height,
      anomalyObject,
      anomalyReason,
    } = req.body;

    if (!droneName) {
      return res.json("Invalid Drone");
    }

    let getDrone = await DroneModel.findOne({ droneName });
    console.log("Drone is ", getDrone);

    if (!getDrone) {
      return res.status(400).send("Invalid Drone");
    }

    getDrone.longitude = longitude;
    getDrone.latitude = latitude;
    getDrone.height = height;

    if (anomalyObject) {
      getDrone.anomalyObject = anomalyObject;
    }

    if (anomalyReason) {
      getDrone.anomalyReason = anomalyReason;
    }

    getDrone.positionHistory.push({
      latitude: latitude,
      longitude: longitude,
      height: height,
    });

    await getDrone.save();
    return res.status(200).send(getDrone.positionHistory);
  } catch (error) {
    console.error("Signup Error:", error);
    next(error);
  }
};

module.exports = {
  getDroneData,
  getAllDroneData,
  DroneAuthenticator,
  registerDrone,
  recieveDroneData,
};
