import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { api } from "../services/api.js";

export const fetchHcps = createAsyncThunk("crm/fetchHcps", api.listHcps);

export const createHcp = createAsyncThunk("crm/createHcp", api.createHcp);

export const fetchInteractions = createAsyncThunk(
  "crm/fetchInteractions",
  async (hcpId) => api.listInteractions(hcpId)
);

export const createInteraction = createAsyncThunk(
  "crm/createInteraction",
  async (payload, { dispatch }) => {
    const interaction = await api.createInteraction(payload);
    dispatch(fetchInteractions(payload.hcp_id));
    return interaction;
  }
);

export const updateInteraction = createAsyncThunk(
  "crm/updateInteraction",
  async ({ id, payload, hcp_id }, { dispatch }) => {
    const interaction = await api.updateInteraction(id, payload);
    dispatch(fetchInteractions(hcp_id));
    return interaction;
  }
);

// Prepend selected HCP context so the agent always knows who we're talking about
export const sendChatMessage = createAsyncThunk(
  "crm/sendChatMessage",
  async ({ message, sessionId, hcpContext }) => {
    const fullMessage = hcpContext
      ? `[Context: Currently selected HCP is ${hcpContext.name} (ID: ${hcpContext.id}), specialty: ${hcpContext.specialty || "unknown"}, hospital: ${hcpContext.hospital || "unknown"}]\n\n${message}`
      : message;
    return api.chat({ message: fullMessage, session_id: sessionId });
  }
);

const crmSlice = createSlice({
  name: "crm",
  initialState: {
    hcps: [],
    interactions: [],
    selectedHcpId: null,
    activeMode: "form",
    status: "idle",
    error: "",
    successMessage: "",
    chat: [
      {
        role: "assistant",
        text: "Choose an HCP, then ask me to log an interaction, edit one, schedule a follow-up, pull a profile, or analyze sentiment.",
      },
    ],
    chatStatus: "idle",
    sessionId: "demo-session",
  },
  reducers: {
    selectHcp(state, action) {
      state.selectedHcpId = action.payload;
    },
    setActiveMode(state, action) {
      state.activeMode = action.payload;
    },
    addUserChatMessage(state, action) {
      state.chat.push({ role: "user", text: action.payload });
    },
    clearError(state) {
      state.error = "";
    },
    clearSuccess(state) {
      state.successMessage = "";
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.status = "ready";
        state.hcps = action.payload;
        if (!state.selectedHcpId && action.payload.length > 0) {
          state.selectedHcpId = action.payload[0].id;
        }
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message;
      })
      .addCase(createHcp.fulfilled, (state, action) => {
        state.hcps.push(action.payload);
        state.selectedHcpId = action.payload.id;
        state.interactions = [];
        state.status = "ready";
        state.successMessage = `HCP "${action.payload.name}" registered successfully.`;
      })
      .addCase(createHcp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message;
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.interactions = action.payload;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.interactions.unshift(action.payload);
        state.successMessage = "Interaction saved successfully.";
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.error = action.error.message;
      })
      .addCase(updateInteraction.fulfilled, (state) => {
        state.successMessage = "Interaction updated successfully.";
      })
      .addCase(updateInteraction.rejected, (state, action) => {
        state.error = action.error.message;
      })
      .addCase(sendChatMessage.pending, (state) => {
        state.chatStatus = "loading";
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.chatStatus = "ready";
        state.sessionId = action.payload.session_id;
        state.chat.push({ role: "assistant", text: action.payload.response });
        // Refresh interactions if agent may have written to DB
        // (handled in App.jsx after response)
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.chatStatus = "error";
        state.chat.push({
          role: "assistant",
          text: `I could not reach the agent: ${action.error.message}`,
        });
      });
  },
});

export const { selectHcp, setActiveMode, addUserChatMessage, clearError, clearSuccess } = crmSlice.actions;
export default crmSlice.reducer;
