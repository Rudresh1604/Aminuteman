const jwt = require("jsonwebtoken");
const Client = require("../Models/userModel");
// const Client = require("../models/user.model");

class ErrorResponse extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
  }
}

const authMiddleware = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      throw new ErrorResponse("Unauthenticated: No token provided", 401);
    }

    const token = authHeader.split(" ")[1];

    if (!token) {
      throw new ErrorResponse("Unauthenticated: Invalid token format", 401);
    }

    const JWT_SECRET = process.env.JWT_SECRET;
    if (!JWT_SECRET) {
      throw new Error("JWT_SECRET is not defined in the environment variables");
    }

    const decoded = jwt.verify(token, JWT_SECRET);

    const { _id } = decoded;
    if (!_id) {
      throw new ErrorResponse("Unauthenticated: Invalid token payload", 401);
    }

    const client = await Client.findById(_id);

    if (!client) {
      throw new ErrorResponse("User not found", 404);
    }

    req.user = client;
    next();
  } catch (error) {
    console.error("Auth Middleware Error:", error);
    next(error);
  }
};

module.exports = { authMiddleware, ErrorResponse };
