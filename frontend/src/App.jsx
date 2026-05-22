import React, { useEffect, useMemo, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Activity,
  Bot,
  CalendarPlus,
  Check,
  ChevronsLeft,
  ChevronsRight,
  ClipboardList,
  MessageSquareText,
  Pencil,
  Plus,
  Save,
  Search,
  Send,
  Stethoscope,
  X,
} from "lucide-react";
import {
  addUserChatMessage,
  clearError,
  clearSuccess,
  createHcp,
  createInteraction,
  fetchHcps,
  fetchInteractions,
  selectHcp,
  sendChatMessage,
  setActiveMode,
  updateInteraction,
} from "./features/crmSlice.js";

const emptyForm = {
  interaction_type: "visit",
  products_discussed: "",
  notes: "",
  logged_by: "Field Rep",
  followup_date: "",
  followup_notes: "",
};

const emptyHcpForm = {
  name: "",
  specialty: "",
  hospital: "",
  email: "",
  phone: "",
  territory: "",
};

// Typing indicator dots animation
function TypingIndicator() {
  return (
    <div className="chat-bubble assistant typing-indicator" aria-label="Agent is thinking">
      <Bot size={16} />
      <span className="dots">
        <span /><span /><span />
      </span>
    </div>
  );
}

// Edit interaction modal
function EditModal({ interaction, onSave, onClose }) {
  const [form, setForm] = useState({
    interaction_type: interaction.interaction_type,
    products_discussed: interaction.products_discussed || "",
    notes: interaction.notes || "",
    followup_date: interaction.followup_date
      ? new Date(interaction.followup_date).toISOString().slice(0, 16)
      : "",
    followup_notes: interaction.followup_notes || "",
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      ...form,
      followup_date: form.followup_date || null,
    });
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>Edit Interaction #{interaction.id}</h2>
          <button type="button" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="interaction-form">
          <div className="form-row">
            <label>
              Interaction type
              <select
                value={form.interaction_type}
                onChange={(e) => setForm({ ...form, interaction_type: e.target.value })}
              >
                <option value="visit">Visit</option>
                <option value="call">Call</option>
                <option value="email">Email</option>
                <option value="conference">Conference</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>
              Products discussed
              <input
                value={form.products_discussed}
                onChange={(e) => setForm({ ...form, products_discussed: e.target.value })}
                placeholder="CardioPlus, Respira"
              />
            </label>
          </div>
          <label>
            Notes
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              required
            />
          </label>
          <div className="form-row">
            <label>
              Follow-up date
              <input
                type="datetime-local"
                value={form.followup_date}
                onChange={(e) => setForm({ ...form, followup_date: e.target.value })}
              />
            </label>
            <label>
              Follow-up note
              <input
                value={form.followup_notes}
                onChange={(e) => setForm({ ...form, followup_notes: e.target.value })}
                placeholder="Send study abstract"
              />
            </label>
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button className="primary-action" type="submit">
              <Save size={16} /> Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function App() {
  const dispatch = useDispatch();
  const {
    hcps,
    interactions,
    selectedHcpId,
    activeMode,
    status,
    error,
    successMessage,
    chat,
    chatStatus,
    sessionId,
  } = useSelector((state) => state.crm);

  const [query, setQuery] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [hcpForm, setHcpForm] = useState(emptyHcpForm);
  const [showHcpForm, setShowHcpForm] = useState(false);
  const [chatText, setChatText] = useState("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [editingInteraction, setEditingInteraction] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => { dispatch(fetchHcps()); }, [dispatch]);

  useEffect(() => {
    if (selectedHcpId) dispatch(fetchInteractions(selectedHcpId));
  }, [dispatch, selectedHcpId]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, chatStatus]);

  // Auto-dismiss success toast
  useEffect(() => {
    if (!successMessage) return;
    const timer = setTimeout(() => dispatch(clearSuccess()), 3000);
    return () => clearTimeout(timer);
  }, [successMessage, dispatch]);

  // Refresh interactions after agent responds (it may have written to DB)
  useEffect(() => {
    if (chatStatus === "ready" && selectedHcpId) {
      dispatch(fetchInteractions(selectedHcpId));
    }
  }, [chatStatus, selectedHcpId, dispatch]);

  const filteredHcps = useMemo(() => {
    const needle = query.toLowerCase();
    return hcps.filter((hcp) =>
      [hcp.name, hcp.specialty, hcp.hospital, hcp.territory].join(" ").toLowerCase().includes(needle)
    );
  }, [hcps, query]);

  const selectedHcp = hcps.find((hcp) => hcp.id === selectedHcpId);

  const submitForm = async (e) => {
    e.preventDefault();
    if (!selectedHcpId) return;
    await dispatch(createInteraction({ ...form, hcp_id: selectedHcpId, followup_date: form.followup_date || null }));
    setForm(emptyForm);
  };

  const submitChat = (e) => {
    e.preventDefault();
    const message = chatText.trim();
    if (!message || chatStatus === "loading") return;
    dispatch(addUserChatMessage(message));
    dispatch(sendChatMessage({ message, sessionId, hcpContext: selectedHcp || null }));
    setChatText("");
  };

  const submitHcp = async (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(
      Object.entries(hcpForm).map(([k, v]) => [k, v.trim() || null])
    );
    if (!payload.name) return;
    const result = await dispatch(createHcp(payload));
    if (result.meta.requestStatus === "fulfilled") {
      setHcpForm(emptyHcpForm);
      setShowHcpForm(false);
    }
  };

  const saveEdit = async (payload) => {
    if (!editingInteraction) return;
    await dispatch(updateInteraction({ id: editingInteraction.id, payload, hcp_id: selectedHcpId }));
    setEditingInteraction(null);
  };

  return (
    <main className={`app-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>

      {/* ── SUCCESS TOAST ── */}
      {successMessage && (
        <div className="toast success" role="status">
          <Check size={16} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* ── EDIT MODAL ── */}
      {editingInteraction && (
        <EditModal
          interaction={editingInteraction}
          onSave={saveEdit}
          onClose={() => setEditingInteraction(null)}
        />
      )}

      {/* ── SIDEBAR ── */}
      <aside className="sidebar" aria-label="HCP navigation">
        <div className="sidebar-head">
          <div className="brand">
            <span className="brand-mark"><Stethoscope size={22} /></span>
            <div className="brand-copy">
              <p>Field CRM</p>
              <strong>HCP Interactions</strong>
            </div>
          </div>
          <button
            className="collapse-button"
            type="button"
            onClick={() => setSidebarCollapsed((v) => !v)}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <ChevronsRight size={18} /> : <ChevronsLeft size={18} />}
          </button>
        </div>

        <label className="search">
          <Search size={18} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search HCPs"
            aria-label="Search HCPs"
          />
        </label>

        <button
          className="new-hcp-button"
          type="button"
          onClick={() => { setShowHcpForm((v) => !v); if (sidebarCollapsed) setSidebarCollapsed(false); }}
          title="Register new HCP"
        >
          <Plus size={18} /><span>Register HCP</span>
        </button>

        {showHcpForm && !sidebarCollapsed && (
          <form className="hcp-create-form" onSubmit={submitHcp}>
            <label>Name<input value={hcpForm.name} onChange={(e) => setHcpForm({ ...hcpForm, name: e.target.value })} placeholder="Dr. Asha Rao" required /></label>
            <label>Specialty<input value={hcpForm.specialty} onChange={(e) => setHcpForm({ ...hcpForm, specialty: e.target.value })} placeholder="Cardiology" /></label>
            <label>Hospital<input value={hcpForm.hospital} onChange={(e) => setHcpForm({ ...hcpForm, hospital: e.target.value })} placeholder="City Heart Institute" /></label>
            <div className="compact-row">
              <label>Email<input type="email" value={hcpForm.email} onChange={(e) => setHcpForm({ ...hcpForm, email: e.target.value })} placeholder="doctor@hospital.com" /></label>
              <label>Phone<input value={hcpForm.phone} onChange={(e) => setHcpForm({ ...hcpForm, phone: e.target.value })} placeholder="+91..." /></label>
            </div>
            <label>Territory<input value={hcpForm.territory} onChange={(e) => setHcpForm({ ...hcpForm, territory: e.target.value })} placeholder="Hyderabad Central" /></label>
            <div className="hcp-form-actions">
              <button type="button" onClick={() => setShowHcpForm(false)}>Cancel</button>
              <button type="submit">Save HCP</button>
            </div>
          </form>
        )}

        <div className="hcp-list">
          {filteredHcps.map((hcp) => (
            <button
              className={`hcp-card ${hcp.id === selectedHcpId ? "selected" : ""}`}
              key={hcp.id}
              onClick={() => dispatch(selectHcp(hcp.id))}
              title={`${hcp.name} — ${hcp.specialty || "Specialty pending"}`}
            >
              <span className="hcp-initials">
                {hcp.name.replace("Dr. ", "").split(" ").map((p) => p[0]).slice(0, 2).join("")}
              </span>
              <span className="hcp-details">
                <span>{hcp.name}</span>
                <small>{hcp.specialty || "Specialty pending"}</small>
                <em>{hcp.territory || "No territory"}</em>
              </span>
            </button>
          ))}
        </div>
      </aside>

      {/* ── WORKSPACE ── */}
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Log Interaction Screen</p>
            <h1>{selectedHcp?.name || "Select an HCP"}</h1>
            <span>
              {selectedHcp
                ? `${selectedHcp.specialty || "Unknown specialty"} · ${selectedHcp.hospital || "Unknown hospital"}`
                : "Start the backend and seed HCP data to begin"}
            </span>
          </div>
          <div className="mode-switch" role="tablist" aria-label="Interaction logging mode">
            <button className={activeMode === "form" ? "active" : ""} onClick={() => dispatch(setActiveMode("form"))} title="Structured form">
              <ClipboardList size={18} /><span>Form</span>
            </button>
            <button className={activeMode === "chat" ? "active" : ""} onClick={() => dispatch(setActiveMode("chat"))} title="Conversational chat">
              <MessageSquareText size={18} /><span>Chat</span>
            </button>
          </div>
        </header>

        {error && (
          <div className="alert">
            {error}
            <button type="button" onClick={() => dispatch(clearError())} aria-label="Dismiss"><X size={14} /></button>
          </div>
        )}
        {status === "loading" && <div className="alert muted">Loading HCP data…</div>}

        <div className="content-grid">
          {/* ── LOG PANEL ── */}
          <section className="panel log-panel">
            {activeMode === "form" ? (
              <form onSubmit={submitForm} className="interaction-form">
                <div className="form-row">
                  <label>
                    Interaction type
                    <select value={form.interaction_type} onChange={(e) => setForm({ ...form, interaction_type: e.target.value })}>
                      <option value="visit">Visit</option>
                      <option value="call">Call</option>
                      <option value="email">Email</option>
                      <option value="conference">Conference</option>
                      <option value="other">Other</option>
                    </select>
                  </label>
                  <label>
                    Products discussed
                    <input value={form.products_discussed} onChange={(e) => setForm({ ...form, products_discussed: e.target.value })} placeholder="CardioPlus, Respira" />
                  </label>
                </div>
                <label>
                  Interaction notes
                  <textarea
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    placeholder="Capture objections, patient profile, brand interest, samples requested, and next steps."
                    required
                  />
                </label>
                <div className="form-row">
                  <label>
                    Follow-up date
                    <input type="datetime-local" value={form.followup_date} onChange={(e) => setForm({ ...form, followup_date: e.target.value })} />
                  </label>
                  <label>
                    Logged by
                    <input value={form.logged_by} onChange={(e) => setForm({ ...form, logged_by: e.target.value })} />
                  </label>
                </div>
                <label>
                  Follow-up note
                  <input value={form.followup_notes} onChange={(e) => setForm({ ...form, followup_notes: e.target.value })} placeholder="Send study abstract before next visit" />
                </label>
                <button className="primary-action" type="submit" disabled={!selectedHcpId}>
                  <Save size={18} /><span>Save Interaction</span>
                </button>
              </form>
            ) : (
              <div className="chat-mode">
                {selectedHcp && (
                  <div className="chat-context-bar">
                    <Bot size={14} />
                    <span>Agent context: <strong>{selectedHcp.name}</strong> (ID {selectedHcp.id}) · {selectedHcp.specialty || "unknown specialty"}</span>
                  </div>
                )}
                <div className="chat-stream">
                  {chat.map((msg, i) => (
                    <div className={`chat-bubble ${msg.role}`} key={`${msg.role}-${i}`}>
                      {msg.role === "assistant" && <Bot size={16} />}
                      <p>{msg.text}</p>
                    </div>
                  ))}
                  {chatStatus === "loading" && <TypingIndicator />}
                  <div ref={chatEndRef} />
                </div>
                <form onSubmit={submitChat} className="chat-input">
                  <input
                    value={chatText}
                    onChange={(e) => setChatText(e.target.value)}
                    placeholder={
                      selectedHcp
                        ? `Try: "Log a positive visit for ${selectedHcp.name} about CardioPlus"`
                        : "Select an HCP before using chat"
                    }
                    disabled={chatStatus === "loading"}
                  />
                  <button type="submit" disabled={chatStatus === "loading" || !chatText.trim()}>
                    <Send size={18} />
                  </button>
                </form>
              </div>
            )}
          </section>

          {/* ── INSIGHT PANEL ── */}
          <aside className="panel insight-panel">
            <div className="metric-row">
              <div>
                <Activity size={18} />
                <strong>{interactions.length}</strong>
                <span>Interactions</span>
              </div>
              <div>
                <CalendarPlus size={18} />
                <strong>{interactions.filter((i) => i.followup_date).length}</strong>
                <span>Follow-ups</span>
              </div>
            </div>

            <h2>Recent History</h2>
            <div className="timeline">
              {interactions.length === 0 ? (
                <p className="empty-state">No interactions logged yet.</p>
              ) : (
                interactions.map((item) => (
                  <article className="timeline-item" key={item.id}>
                    <div className="timeline-item-head">
                      <div>
                        <strong>{item.interaction_type}</strong>
                        <span className={`sentiment ${item.sentiment || "neutral"}`}>{item.sentiment || "neutral"}</span>
                      </div>
                      <button
                        className="edit-btn"
                        type="button"
                        title="Edit interaction"
                        onClick={() => setEditingInteraction(item)}
                      >
                        <Pencil size={13} />
                      </button>
                    </div>
                    <p>{item.summary || item.notes}</p>
                    {item.followup_date && (
                      <small className="followup-tag">
                        <CalendarPlus size={11} />
                        Follow-up: {new Date(item.followup_date).toLocaleDateString()}
                      </small>
                    )}
                    <small>{new Date(item.date).toLocaleString()}</small>
                  </article>
                ))
              )}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

export default App;
