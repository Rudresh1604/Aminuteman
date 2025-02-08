// droneRouter.js
const express = require("express");
const router = express.Router();
const {
  getDroneData,
  getAllDroneData,
  registerDrone,
  recieveDroneData,
  DroneAuthenticator,
} = require("../Controller/droneController");

router.get("/get-drone", getDroneData);
router.post("/verify", DroneAuthenticator);

router.get("/get-all-drones", getAllDroneData);
router.post("/register-drone", registerDrone);
router.post("/receive-drone-data", recieveDroneData);

module.exports = router;
