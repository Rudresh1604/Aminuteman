require("dotenv").config();
const mongoose = require("mongoose");
const dbUrl = process.env.MONGO_DB_URL;

const dbConnect = async () => {
  try {
    console.log(dbUrl);

    await mongoose.connect(dbUrl).then(() => {
      console.log("DB Connected ..");
    });
  } catch (error) {
    console.log(error.message);
  }
};
dbConnect();
