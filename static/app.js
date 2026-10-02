/**
 * Sigma Web Development Course - RAG Assistant Frontend Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const sidebar = document.getElementById("sidebar");
  const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
  const sidebarCloseBtn = document.getElementById("sidebar-close-btn");
  const newChatBtn = document.getElementById("new-chat-btn");
  const restartChatBtn = document.getElementById("restart-chat-btn");
  const welcomeView = document.getElementById("welcome-view");
  const messagesContainer = document.getElementById("messages-container");
  const chatMessages = document.getElementById("chat-messages");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const modelSelect = document.getElementById("model-select");
  const topKSelect = document.getElementById("top-k-select");
  const typingIndicator = document.getElementById("typing-indicator");
  const typingStatusText = document.getElementById("typing-status-text");
  const courseTopicsList = document.getElementById("course-topics-list");
  const chatHistoryList = document.getElementById("chat-history-list");
  const clearHistoryBtn = document.getElementById("clear-history-btn");
  const ollamaDot = document.getElementById("ollama-dot");
  const geminiDot = document.getElementById("gemini-dot");
  const courseCountBadge = document.getElementById("course-count-badge");

  // State
  let isGenerating = false;
  let chatHistory = JSON.parse(localStorage.getItem("course_rag_history") || "[]");

  // Initialize marked options
  if (window.marked) {
    marked.setOptions({
      breaks: true,
      gfm: true,
      highlight: function (code, lang) {
        if (window.hljs && lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        }
        return window.hljs ? hljs.highlightAuto(code).value : code;
      }
    });
  }

  // --- Initial Loaders ---
  fetchServerStatus();
  fetchCourseTopics();
  renderChatHistory();

  // --- Sidebar Toggle ---
  sidebarToggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
  });

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener("click", () => {
      sidebar.classList.add("collapsed");
    });
  }

  // Auto-collapse on small screens
  if (window.innerWidth < 860) {
    sidebar.classList.add("collapsed");
  }

  // --- Textarea Auto-expand & Submit on Enter ---
  userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 180) + "px";
    sendBtn.disabled = userInput.value.trim().length === 0;
  });

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isGenerating && userInput.value.trim().length > 0) {
        handleSubmit();
      }
    }
  });

  sendBtn.addEventListener("click", () => {
    if (!isGenerating && userInput.value.trim().length > 0) {
      handleSubmit();
    }
  });

  // --- New Chat & Restart Buttons ---
  newChatBtn.addEventListener("click", resetChat);
  restartChatBtn.addEventListener("click", resetChat);

  function resetChat() {
    messagesContainer.innerHTML = "";
    messagesContainer.classList.add("hidden");
    welcomeView.classList.remove("hidden");
    userInput.value = "";
    userInput.style.height = "auto";
    sendBtn.disabled = true;
    userInput.focus();
  }

  // --- Starter Prompt Cards ---
  document.querySelectorAll(".prompt-card").forEach((card) => {
    card.addEventListener("click", () => {
      const prompt = card.getAttribute("data-prompt");
      if (prompt && !isGenerating) {
        userInput.value = prompt;
        userInput.style.height = "auto";
        sendBtn.disabled = false;
        handleSubmit();
      }
    });
  });

  // --- Clear History ---
  clearHistoryBtn.addEventListener("click", () => {
    chatHistory = [];
    localStorage.removeItem("course_rag_history");
    renderChatHistory();
  });

  // --- Fetch System Status ---
  async function fetchServerStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        
        // Ollama status
        if (data.ollama && data.ollama.online) {
          ollamaDot.classList.add("online");
          ollamaDot.classList.remove("offline");
          ollamaDot.title = "Ollama is online";
        } else {
          ollamaDot.classList.remove("online");
          ollamaDot.classList.add("offline");
          ollamaDot.title = "Ollama offline";
        }

        // Gemini status
        if (data.gemini && data.gemini.available) {
          geminiDot.classList.add("online");
          geminiDot.classList.remove("offline");
          geminiDot.title = "Gemini API ready";
        } else {
          geminiDot.classList.remove("online");
          geminiDot.classList.add("offline");
          geminiDot.title = "Gemini API unavailable";
        }
      }
    } catch (err) {
      console.warn("Status fetch failed:", err);
    }
  }

  // --- Fetch Course Topics for Sidebar ---
  async function fetchCourseTopics() {
    try {
      const res = await fetch("/api/topics");
      if (res.ok) {
        const data = await res.json();
        const videos = data.videos || [];
        courseCountBadge.textContent = videos.length;
        
        if (videos.length === 0) {
          courseTopicsList.innerHTML = `<div class="topic-item">No lectures found</div>`;
          return;
        }

        courseTopicsList.innerHTML = videos
          .map(
            (v) => `
          <div class="topic-item" data-number="${v.number}" data-title="${v.title}" title="Tutorial #${v.number}: ${v.title}">
            <span class="topic-num">#${v.number}</span>
            <span class="topic-title">${v.title}</span>
          </div>
        `
          )
          .join("");

        // Add click listener to ask about that lecture
        document.querySelectorAll(".topic-item").forEach((item) => {
          item.addEventListener("click", () => {
            const num = item.getAttribute("data-number");
            const title = item.getAttribute("data-title");
            if (num && title && !isGenerating) {
              userInput.value = `What is covered in Tutorial #${num}: ${title} and what are the key timestamps?`;
              userInput.style.height = "auto";
              sendBtn.disabled = false;
              handleSubmit();
            }
          });
        });
      }
    } catch (err) {
      courseTopicsList.innerHTML = `<div class="topic-item">Unable to load topics</div>`;
    }
  }

  // --- Render Local History ---
  function renderChatHistory() {
    if (chatHistory.length === 0) {
      chatHistoryList.innerHTML = `<div class="topic-item" style="color:var(--text-muted); cursor:default;">No recent questions</div>`;
      return;
    }

    chatHistoryList.innerHTML = chatHistory
      .slice(0, 15)
      .map(
        (query, i) => `
        <div class="history-item" data-index="${i}" title="${escapeHtml(query)}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="min-width:14px; opacity:0.6;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(query)}</span>
        </div>
      `
      )
      .join("");

    document.querySelectorAll(".history-item").forEach((item) => {
      item.addEventListener("click", () => {
        const text = item.getAttribute("title");
        if (text && !isGenerating) {
          userInput.value = text;
          userInput.style.height = "auto";
          sendBtn.disabled = false;
          handleSubmit();
        }
      });
    });
  }

  function saveToHistory(query) {
    // Avoid duplicates at top
    chatHistory = [query, ...chatHistory.filter((q) => q !== query)].slice(0, 25);
    localStorage.setItem("course_rag_history", JSON.stringify(chatHistory));
    renderChatHistory();
  }

  // --- Main Chat Submit & Streaming Handler ---
  async function handleSubmit() {
    const query = userInput.value.trim();
    if (!query || isGenerating) return;

    // Reset input
    userInput.value = "";
    userInput.style.height = "auto";
    sendBtn.disabled = true;

    // Hide welcome screen, show container
    welcomeView.classList.add("hidden");
    messagesContainer.classList.remove("hidden");

    // Append User Message Bubble
    appendUserMessage(query);
    saveToHistory(query);

    // Scroll to bottom
    scrollToBottom();

    // Show Typing Indicator
    isGenerating = true;
    typingIndicator.classList.remove("hidden");
    typingStatusText.textContent = "Retrieving lecture chunks & timestamps...";
    scrollToBottom();

    const selectedModel = modelSelect.value;
    const topK = parseInt(topKSelect.value, 10) || 5;

    // Create Assistant Message Placeholder
    const assistantRow = createAssistantMessageRow();
    const assistantBubble = assistantRow.querySelector(".assistant-bubble");
    const sourcesWrapper = assistantRow.querySelector(".sources-container");
    const sourcesHeader = assistantRow.querySelector(".sources-header");
    const sourcesList = assistantRow.querySelector(".sources-list");
    const sourcesCount = assistantRow.querySelector(".sources-count");

    let fullAnswer = "";
    let retrievedChunks = [];

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          model: selectedModel,
          top_k: topK
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      // Hide typing indicator once streaming starts
      typingIndicator.classList.add("hidden");
      messagesContainer.appendChild(assistantRow);

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // Keep unfinished slice in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const rawJson = line.slice(6);
            try {
              const eventData = JSON.parse(rawJson);

              if (eventData.type === "sources") {
                retrievedChunks = eventData.chunks || [];
                renderSources(retrievedChunks, sourcesWrapper, sourcesList, sourcesCount);
              } else if (eventData.type === "token") {
                fullAnswer += eventData.token;
                renderAssistantMarkdown(assistantBubble, fullAnswer);
                scrollToBottom();
              } else if (eventData.type === "error") {
                fullAnswer += `\n\n> ⚠️ **Error:** ${eventData.message}`;
                renderAssistantMarkdown(assistantBubble, fullAnswer);
              }
            } catch (err) {
              console.error("Error parsing SSE event:", err, line);
            }
          }
        }
      }

      // Final markdown render and code highlighting
      renderAssistantMarkdown(assistantBubble, fullAnswer, true);

    } catch (err) {
      typingIndicator.classList.add("hidden");
      if (!assistantRow.parentElement) {
        messagesContainer.appendChild(assistantRow);
      }
      assistantBubble.innerHTML = `<p style="color:var(--accent-red);">⚠️ Failed to connect to server: ${escapeHtml(err.message)}</p>`;
    } finally {
      isGenerating = false;
      sendBtn.disabled = userInput.value.trim().length === 0;
      scrollToBottom();
    }
  }

  // --- Helper UI Functions ---

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row user";
    row.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
    messagesContainer.appendChild(row);
  }

  function createAssistantMessageRow() {
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.innerHTML = `
      <div class="assistant-avatar">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <path d="M12 2L14.4 9.6L22 12L14.4 14.4L12 22L9.6 14.4L2 12L9.6 9.6L12 2Z" fill="url(#assist-grad)"/>
          <defs>
            <linearGradient id="assist-grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
              <stop stop-color="#4285F4"/>
              <stop offset="0.5" stop-color="#9B72CB"/>
              <stop offset="1" stop-color="#D96570"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div class="assistant-content-wrapper">
        <div class="assistant-bubble"></div>
        <div class="sources-container hidden">
          <div class="sources-header">
            <span>📚 Retrieved Course Sources (<span class="sources-count">0</span>)</span>
            <svg class="sources-toggle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
          <div class="sources-list"></div>
        </div>
        <div class="message-actions">
          <button class="action-btn copy-msg-btn" title="Copy response">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>Copy</span>
          </button>
        </div>
      </div>
    `;

    // Wire up sources accordion toggle
    const sourcesContainer = row.querySelector(".sources-container");
    const sourcesHeader = row.querySelector(".sources-header");
    sourcesHeader.addEventListener("click", () => {
      sourcesContainer.classList.toggle("open");
    });

    // Wire up copy button
    const copyBtn = row.querySelector(".copy-msg-btn");
    copyBtn.addEventListener("click", () => {
      const bubble = row.querySelector(".assistant-bubble");
      navigator.clipboard.writeText(bubble.innerText).then(() => {
        copyBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5cd67b" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          <span style="color:#5cd67b;">Copied!</span>
        `;
        setTimeout(() => {
          copyBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>Copy</span>
          `;
        }, 2000);
      });
    });

    return row;
  }

  function renderAssistantMarkdown(container, text, isFinal = false) {
    if (window.marked) {
      container.innerHTML = marked.parse(text);
      if (isFinal && window.hljs) {
        container.querySelectorAll("pre code").forEach((block) => {
          hljs.highlightElement(block);
        });
      }
    } else {
      container.innerText = text;
    }
  }

  function renderSources(chunks, container, listElement, countElement) {
    if (!chunks || chunks.length === 0) return;

    container.classList.remove("hidden");
    countElement.textContent = chunks.length;

    listElement.innerHTML = chunks
      .map(
        (c) => `
      <div class="source-card">
        <div class="source-top">
          <div class="source-video">
            <span class="source-tut-num">Tutorial #${c.number}</span>
            <span>${escapeHtml(c.title)}</span>
          </div>
          <div class="source-badges">
            <span class="time-badge">⏱️ ${c.timestamp_range}</span>
            <span class="match-badge">🎯 ${c.match_pct}</span>
          </div>
        </div>
        <div class="source-excerpt">"${escapeHtml(c.text.length > 260 ? c.text.substring(0, 260) + '...' : c.text)}"</div>
      </div>
    `
      )
      .join("");
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});

