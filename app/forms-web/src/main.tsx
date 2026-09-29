import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { Gate } from "./Gate";
import "./styles/app.css";
import "./styles/paper.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Gate />
  </StrictMode>,
);
