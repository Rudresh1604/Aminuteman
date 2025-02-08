const Client = require("../Models/userModel");
const jwt = require("jsonwebtoken");
class ErrorResponse extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
  }
}

class SuccessResponse {
  constructor(success, statusCode, message, data = null) {
    this.success = success;
    this.statusCode = statusCode;
    this.message = message;
    if (data) this.data = data;
  }
}

const signup = async (req, res, next) => {
  try {
    const { username, email, password, role } = req.body;
    console.log("Request Body:", req.body);

    if (!username || !email || !password || !role) {
      throw new ErrorResponse("Kindly Provide all arguments", 400);
    }

    const clientExist = await Client.findOne({ username: username });
    if (clientExist) {
      throw new ErrorResponse("Username already exists", 400);
    }

    const client = await Client.create({
      username,
      password,
      email,
      role,
    });

    console.log("Client Created:", client);
    await client.save();
    return res.json(
      new SuccessResponse(true, 200, "Account Created Successfully", client)
    );
  } catch (error) {
    console.error("Signup Error:", error);
    next(error);
  }
};

const signin = async (req, res, next) => {
  try {
    console.log(req.body);
    const { email, password } = req.body;

    if (!email || !password) {
      throw new ErrorResponse("Please Provide all fields", 400);
    }

    const client = await Client.findOne({ email }).select("+password");
    if (!client) {
      throw new ErrorResponse("User doesn't exist", 400);
    }

    const isMatch = await client.isPasswordValid(password);

    if (!isMatch) {
      throw new ErrorResponse("Incorrect Password", 400);
    }

    const token = await client.generateToken();
    console.log(token);

    const options = {
      sameSite: "Lax",
      secure: process.env.NODE_ENV === "production",
      httpOnly: true,
      maxAge: 7 * 24 * 60 * 60 * 1000,
    };

    res.cookie("token", token, options);
    console.log("Cookie options:", options);

    return res
      .status(200)
      .json(new SuccessResponse(true, 200, "Login Success", { token }));
  } catch (error) {
    next(error);
  }
};
const adminVerify = async (req, res, next) => {
  try {
    const token =
      req.headers.authorization && req.headers.authorization.split(" ")[1];

    if (!token) {
      throw new ErrorResponse("Please provide email, secret, and token", 400);
    }

    const JWT_SECRET = process.env.JWT_SECRET;
    if (!JWT_SECRET) {
      throw new Error("JWT_SECRET is not configured");
    }

    let decoded = await jwt.verify(token, JWT_SECRET);
    console.log(decoded);

    if (!decoded) {
      return res.status(401).send("Invalid or expired token");
    }

    const client = await Client.findById(decoded._id);

    if (!client) {
      throw new ErrorResponse("User doesn't exist", 400);
    }

    if (client.role === "MWO") {
      return res.status(400).send("Unauthorized access");
    }
    console.log("Heel");

    const users = await Client
      .find
      //   {
      //   _id: { $ne: decoded._id },
      // }
      ()
      .select("+password");
    console.log(users);

    return res.status(200).send(users);
  } catch (error) {
    next(error);
  }
};

const logout = async (req, res, next) => {
  try {
    res
      .clearCookie("token")
      .json(new SuccessResponse(true, 200, "Logout successfully"));
  } catch (error) {
    next(error);
  }
};

const IAM = async (req, res, next) => {
  try {
    const client = req.user;
    return res.json(
      new SuccessResponse(true, 200, "User fetched Sucess", client)
    );
  } catch (error) {
    next(error);
  }
};

module.exports = {
  signup,
  signin,
  logout,
  IAM,
  adminVerify,
  ErrorResponse,
  SuccessResponse,
};
