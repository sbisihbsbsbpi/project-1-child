// @ts-nocheck
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// ✅ FIX: Disabled React.StrictMode to prevent double-invocation of event handlers
// React.StrictMode was causing deleteSelectedSessions to be called twice per click,
// which showed the confirmation dialog twice and caused it to be cancelled on the second call
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <App />
);
