/**
 * FAQ Chatbot Frontend Client
 * 
 * Features:
 * - Strict XSS protection: Safe DOM manipulation via textContent
 * - Real-time NLP status and knowledge base inspection
 * - Suggested question chips & follow-up suggestions
 * - Clipboard copy with visual confirmation
 * - Responsive typing indicator and loading states
 */

(() => {
  "use strict";

  // DOM Elements
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const sendBtn = document.getElementById("sendBtn");
  const sendIcon = document.getElementById("sendIcon");
  const sendSpinner = document.getElementById("sendSpinner");
  const charCount = document.getElementById("charCount");
  const inputFeedback = document.getElementById("inputFeedback");
  const typingIndicator = document.getElementById("typingIndicator");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const viewFaqsBtn = document.getElementById("viewFaqsBtn");
  const faqModal = document.getElementById("faqModal");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const modalCategoryFilters = document.getElementById("modalCategoryFilters");
  const modalFaqList = document.getElementById("modalFaqList");
  const quickChipsContainer = document.getElementById("quickChipsContainer");
  const faqCountBadge = document.getElementById("faqCountBadge");
  const engineStatusText = document.getElementById("engineStatusText");

  // State
  let isSubmitting = false;
  let allFaqs = [];
  let selectedCategory = "All";

  // API Endpoints
  const API_BASE = "/api/v1";

  /**
   * Safe helper to format current time string (e.g. "10:45 AM")
   */
  function getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  /**
   * Displays or hides input validation warning
   */
  function showFeedback(message) {
    if (!message) {
      inputFeedback.textContent = "";
      inputFeedback.classList.add("hidden");
    } else {
      inputFeedback.textContent = message;
      inputFeedback.classList.remove("hidden");
    }
  }

  /**
   * Updates loading state of UI elements
   */
  function setLoadingState(loading) {
    isSubmitting = loading;
    userInput.disabled = loading;
    sendBtn.disabled = loading;

    if (loading) {
      sendIcon.classList.add("hidden");
      sendSpinner.classList.remove("hidden");
      typingIndicator.classList.remove("hidden");
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
      sendIcon.classList.remove("hidden");
      sendSpinner.classList.add("hidden");
      typingIndicator.classList.add("hidden");
      userInput.focus();
    }
  }

  /**
   * Appends a user message bubble to chat window safely using DOM textContent
   */
  function appendUserMessage(text) {
    const wrapper = document.createElement("div");
    wrapper.className = "message-wrapper user-wrapper";

    const avatar = document.createElement("div");
    avatar.className = "avatar-small user";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "You";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble user-bubble";

    const header = document.createElement("div");
    header.className = "bubble-header";

    const timeSpan = document.createElement("span");
    timeSpan.className = "message-time";
    timeSpan.textContent = getCurrentTime();
    header.appendChild(timeSpan);

    const content = document.createElement("div");
    content.className = "bubble-content";
    content.textContent = text; // Safe text rendering (No XSS)

    bubble.appendChild(header);
    bubble.appendChild(content);

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    chatMessages.appendChild(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  /**
   * Appends an assistant response bubble with metadata and actions
   */
  function appendBotMessage(data) {
    const wrapper = document.createElement("div");
    wrapper.className = "message-wrapper bot-wrapper";

    // Avatar matching robot mascot
    const avatar = document.createElement("div");
    avatar.className = "avatar-robot-round";
    avatar.setAttribute("aria-hidden", "true");
    avatar.innerHTML = `
      <svg width="38" height="38" viewBox="0 0 38 38" fill="none">
        <rect width="38" height="38" rx="19" fill="#2563eb" />
        <circle cx="19" cy="9" r="2" fill="#38bdf8" />
        <line x1="19" y1="11" x2="19" y2="13" stroke="#ffffff" stroke-width="1.5" />
        <rect x="10" y="13" width="18" height="15" rx="6" fill="#ffffff" />
        <rect x="12" y="15" width="14" height="10" rx="4" fill="#0f172a" />
        <path d="M14 21 Q15.5 18 17 21" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round" fill="none" />
        <path d="M21 21 Q22.5 18 24 21" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round" fill="none" />
      </svg>
    `;

    // Bubble
    const bubble = document.createElement("div");
    bubble.className = "message-bubble bot-bubble";

    // Header
    const header = document.createElement("div");
    header.className = "bubble-header";

    const sender = document.createElement("span");
    sender.className = "sender-name";
    sender.textContent = "Assistant";

    const time = document.createElement("span");
    time.className = "live-dot-time";
    time.innerHTML = `<span class="live-green-dot"></span> Just now`;

    header.appendChild(sender);
    header.appendChild(time);

    // Content
    const content = document.createElement("div");
    content.className = "bubble-content";
    content.textContent = data.answer; // Strictly textContent (prevents XSS)

    bubble.appendChild(header);
    bubble.appendChild(content);

    // Metadata Bar (Confidence, Category, Copy button)
    const metaBar = document.createElement("div");
    metaBar.className = "match-meta-bar";

    const metaBadges = document.createElement("div");
    metaBadges.className = "meta-badges";

    if (data.category) {
      const catBadge = document.createElement("span");
      const catSlug = data.category.toLowerCase().replace(/[^a-z0-9]/g, "-");
      catBadge.className = `category-tag cat-${catSlug}`;
      catBadge.textContent = data.category;
      metaBadges.appendChild(catBadge);
    }

    const confBadge = document.createElement("span");
    const scorePct = Math.round(data.confidence * 100);

    if (data.is_fallback) {
      confBadge.className = "confidence-badge fallback";
      confBadge.textContent = "No match (Fallback)";
    } else if (scorePct >= 70) {
      confBadge.className = "confidence-badge high";
      confBadge.textContent = `✓ ${scorePct}% Match`;
    } else {
      confBadge.className = "confidence-badge medium";
      confBadge.textContent = `~ ${scorePct}% Match`;
    }
    metaBadges.appendChild(confBadge);

    // Copy action
    const actions = document.createElement("div");
    actions.className = "meta-actions";

    const copyBtn = document.createElement("button");
    copyBtn.className = "btn-copy";
    copyBtn.title = "Copy answer to clipboard";
    copyBtn.setAttribute("aria-label", "Copy answer to clipboard");
    copyBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
    `;

    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(data.answer);
        copyBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        `;
        setTimeout(() => {
          copyBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          `;
        }, 1800);
      } catch (err) {
        console.error("Clipboard copy failed:", err);
      }
    });

    actions.appendChild(copyBtn);
    metaBar.appendChild(metaBadges);
    metaBar.appendChild(actions);
    bubble.appendChild(metaBar);

    // Follow-up Suggestions (if available and helpful)
    if (data.suggestions && data.suggestions.length > 0) {
      const followupBox = document.createElement("div");
      followupBox.className = "followup-suggestions";

      const fLabel = document.createElement("div");
      fLabel.className = "followup-label";
      fLabel.textContent = data.is_fallback ? "Did you mean one of these?" : "Related questions:";
      followupBox.appendChild(fLabel);

      const fList = document.createElement("div");
      fList.className = "followup-list";

      data.suggestions.slice(0, 3).forEach((suggestionText) => {
        const fBtn = document.createElement("button");
        fBtn.className = "followup-btn";
        fBtn.textContent = suggestionText;
        fBtn.addEventListener("click", () => {
          submitQuestion(suggestionText);
        });
        fList.appendChild(fBtn);
      });

      followupBox.appendChild(fList);
      bubble.appendChild(followupBox);
    }

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    chatMessages.appendChild(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  /**
   * Submits a question to the backend NLP service
   */
  async function submitQuestion(questionText) {
    const query = (questionText || userInput.value).trim();
    showFeedback("");

    if (!query) {
      showFeedback("Please enter a question before sending.");
      userInput.focus();
      return;
    }

    if (query.length > 500) {
      showFeedback("Question is too long (maximum 500 characters).");
      return;
    }

    // Append user's query immediately
    appendUserMessage(query);

    // Clear and reset input field
    userInput.value = "";
    charCount.textContent = "0 / 500";
    setLoadingState(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ question: query })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const errMsg = errData.detail || `Server error (${response.status})`;
        throw new Error(errMsg);
      }

      const data = await response.json();
      appendBotMessage(data);
    } catch (err) {
      console.error("Chat API error:", err);
      appendBotMessage({
        answer: "I am having trouble connecting to the knowledge base right now. Please check your connection and try again.",
        category: "System",
        confidence: 0.0,
        is_fallback: true,
        suggestions: []
      });
    } finally {
      setLoadingState(false);
    }
  }

  /**
   * Fetches health and FAQ stats on startup
   */
  async function checkSystemHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        if (faqCountBadge) faqCountBadge.textContent = `${data.indexed_faqs} FAQs`;
        if (engineStatusText) engineStatusText.textContent = "NLP Matcher Active";
      }
    } catch (err) {
      console.warn("Health check error:", err);
      if (engineStatusText) engineStatusText.textContent = "Offline Mode";
    }
  }

  /**
   * Loads the full FAQ catalog for the directory modal
   */
  async function loadFaqCatalog() {
    try {
      const res = await fetch(`${API_BASE}/faqs`);
      if (!res.ok) return;
      const data = await res.json();
      allFaqs = data.faqs;
      renderModalFilters(data.categories);
      renderModalFaqs(allFaqs);
    } catch (err) {
      console.error("Failed to load FAQ list:", err);
    }
  }

  function renderModalFilters(categories) {
    modalCategoryFilters.innerHTML = "";
    
    const allChip = document.createElement("button");
    allChip.className = "filter-chip active";
    allChip.textContent = "All Categories";
    allChip.addEventListener("click", () => {
      document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
      allChip.classList.add("active");
      selectedCategory = "All";
      renderModalFaqs(allFaqs);
    });
    modalCategoryFilters.appendChild(allChip);

    categories.forEach((cat) => {
      const chip = document.createElement("button");
      chip.className = "filter-chip";
      chip.textContent = cat;
      chip.addEventListener("click", () => {
        document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        selectedCategory = cat;
        const filtered = allFaqs.filter(f => f.category === cat);
        renderModalFaqs(filtered);
      });
      modalCategoryFilters.appendChild(chip);
    });
  }

  function renderModalFaqs(faqsToRender) {
    modalFaqList.innerHTML = "";
    if (faqsToRender.length === 0) {
      modalFaqList.innerHTML = "<div class='loading-placeholder'>No FAQs found in this category.</div>";
      return;
    }

    faqsToRender.forEach((faq) => {
      const item = document.createElement("div");
      item.className = "faq-card-item";
      item.title = "Click to ask this question in chat";

      const cat = document.createElement("div");
      cat.className = "faq-item-category";
      cat.textContent = faq.category;

      const q = document.createElement("div");
      q.className = "faq-item-question";
      q.textContent = faq.question;

      const a = document.createElement("div");
      a.className = "faq-item-answer";
      a.textContent = faq.answer;

      item.appendChild(cat);
      item.appendChild(q);
      item.appendChild(a);

      item.addEventListener("click", () => {
        faqModal.classList.add("hidden");
        submitQuestion(faq.question);
      });

      modalFaqList.appendChild(item);
    });
  }

  // Event Listeners
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!isSubmitting) {
      submitQuestion();
    }
  });

  userInput.addEventListener("input", () => {
    const len = userInput.value.length;
    charCount.textContent = `${len} / 500`;
    if (len > 0) showFeedback("");
  });

  // Suggested / Topic Chip Clicks
  if (quickChipsContainer) {
    quickChipsContainer.addEventListener("click", (e) => {
      const btn = e.target.closest(".topic-chip, .suggestion-chip");
      if (btn && btn.dataset.query) {
        submitQuestion(btn.dataset.query);
      }
    });
  }

  // Clear Chat History
  if (clearChatBtn) {
    clearChatBtn.addEventListener("click", () => {
      if (confirm("Are you sure you want to clear this conversation?")) {
        chatMessages.innerHTML = `
          <div class="message-wrapper bot-wrapper">
            <div class="avatar-robot-round" aria-hidden="true">
              <svg width="38" height="38" viewBox="0 0 38 38" fill="none">
                <rect width="38" height="38" rx="19" fill="#2563eb" />
                <circle cx="19" cy="9" r="2" fill="#38bdf8" />
                <line x1="19" y1="11" x2="19" y2="13" stroke="#ffffff" stroke-width="1.5" />
                <rect x="10" y="13" width="18" height="15" rx="6" fill="#ffffff" />
                <rect x="12" y="15" width="14" height="10" rx="4" fill="#0f172a" />
                <path d="M14 21 Q15.5 18 17 21" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round" fill="none" />
                <path d="M21 21 Q22.5 18 24 21" stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round" fill="none" />
              </svg>
            </div>
            <div class="message-bubble bot-bubble">
              <div class="bubble-header">
                <span class="sender-name">Assistant</span>
                <span class="live-dot-time"><span class="live-green-dot"></span> Just now</span>
              </div>
              <div class="bubble-content">
                <p>Conversation history cleared. How can I assist you today?</p>
              </div>
            </div>
          </div>
        `;
        showFeedback("");
        userInput.focus();
      }
    });
  }

  // Modal Controls
  if (viewFaqsBtn) {
    viewFaqsBtn.addEventListener("click", () => {
      if (faqModal) faqModal.classList.remove("hidden");
      if (allFaqs.length === 0) loadFaqCatalog();
    });
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
      if (faqModal) faqModal.classList.add("hidden");
    });
  }

  if (faqModal) {
    faqModal.addEventListener("click", (e) => {
      if (e.target === faqModal) {
        faqModal.classList.add("hidden");
      }
    });
  }

  closeModalBtn.addEventListener("click", () => {
    faqModal.classList.add("hidden");
  });

  faqModal.addEventListener("click", (e) => {
    if (e.target === faqModal) {
      faqModal.classList.add("hidden");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !faqModal.classList.contains("hidden")) {
      faqModal.classList.add("hidden");
    }
  });

  // Initialize
  checkSystemHealth();
  loadFaqCatalog();
})();
