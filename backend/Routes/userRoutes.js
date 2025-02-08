const express = require("express");
const router = express.Router();
const {
  signup,
  signin,
  logout,
  IAM,
  adminVerify,
} = require("../Controller/userController");
const { authMiddleware } = require("../Middleware/authMiddleware");

router.post("/signup", signup);
router.post("/signin", signin);
router.get("/logout", logout);
router.get("/admin/get-users", adminVerify);

module.exports = router;
