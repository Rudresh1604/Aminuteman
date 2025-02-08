const mongoose = require("mongoose");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");

const clientSchema = new mongoose.Schema(
  {
    username: {
      type: String,
      unique: true,
      required: false,
    },
    email: {
      type: String,
      required: true,
    },
    password: {
      type: String,
      required: true,
      select: false,
    },
    role: {
      type: String,
      enum: ["JWO", "WO", "MWO"],
      required: true,
    },

    allActivity: [
      {
        type: mongoose.Schema.Types.Mixed,
      },
    ],
  },
  {
    timestamps: true,
  }
);

clientSchema.pre("save", async function (next) {
  const client = this;

  if (!client.isModified("password")) {
    return next();
  }

  if (client.password) {
    this.password = await bcrypt.hash(this.password, 10);
  }
});

clientSchema.methods.isPasswordValid = async function (password) {
  return await bcrypt.compare(password, this.password);
};

clientSchema.methods.generateToken = async function () {
  try {
    const key = process.env.JWT_SECRET;
    console.log(key);

    if (!key) {
      throw new Error("JWT_SECRET is not defined");
    }

    const payload = { _id: this._id, role: this.role };

    const token = jwt.sign(payload, key, { expiresIn: "7d" });
    return token;
  } catch (error) {
    console.error("Error while creating token:", error);
    throw error;
  }
};

const Client = mongoose.model("Client", clientSchema);

module.exports = Client;
