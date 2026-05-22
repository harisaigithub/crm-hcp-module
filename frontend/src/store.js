import { configureStore } from "@reduxjs/toolkit";
import crmReducer from "./features/crmSlice.js";

export const store = configureStore({
  reducer: {
    crm: crmReducer,
  },
});
