const mongoose = require("mongoose");

const droneSchema = new mongoose.Schema(
  {
    droneName: {
      type: String,
      required: true,
    },
    longitude: {
      type: Number,
      required: false,
    },
    latitude: {
      type: Number,
      required: false,
    },
    height: {
      type: Number,
      required: false,
    },
    anomalyObject: {
      type: String,
      required: false,
    },
    anomalyReason: {
      type: String,
      required: false,
    },
    positionHistory: {
      type: [
        {
          latitude: {
            type: String,
            required: true,
          },
          longitude: {
            type: String,
            required: true,
          },
          anomalyObject: {
            type: String,
          },
          height: {
            type: String,
            required: false,
          },
          time: {
            type: Date,
            default: Date.now,
          },
        },
      ],
      required: false,
    },
  },
  {
    timestamps: true,
  }
);

const DroneModel = mongoose.model("DroneModel", droneSchema);

module.exports = DroneModel;
