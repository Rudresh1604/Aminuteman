require("dotenv").config();
const express = require("express");
const app = express();
const cors = require("cors");
const cookieParser = require("cookie-parser");
const userRoutes = require("./Routes/userRoutes");
const droneRoutes = require("./Routes/droneRouter");
const PORT = 5000;
require("./Config/dbConfig");

app.use(express.json());
app.use(cookieParser());
app.use(cors("*"));
app.use("/api/v1/user", userRoutes);
app.use("/api/v1/drone", droneRoutes);

app.listen(PORT, () => {
  console.log(`Server started on ${PORT} ...`);
});
