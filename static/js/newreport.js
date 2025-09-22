// ============================================================
// Global Variable
let currentDocumentUUID = null;
// ============================================================

// ============================================================
// Utility Functions
// ============================================================

/**
 * Convert plain text with simple Markdown (# headings) into HTML for display.
 * Removes 'TERMINATE' markers and wraps lines in <p> or <h4>.
 */
function formatReportText(text) {
  text = text.replace(/TERMINATE/g, "").trim(); // Remove 'TERMINATE' markers

  const lines = text.split("\n");
  let html = "";

  for (let line of lines) {
    const trimmed = line.trim();

    if (!trimmed) {
      html += "<br>"; // Keep spacing for empty lines
      continue;
    }

    if (/^# (.+)/.test(trimmed)) {
      const heading = trimmed.replace(/^# (.+)/, '<h4 class="mt-3 mb-2">$1</h4>'); // Convert Markdown-style header to <h4>
      html += heading;
    } else {
      html += `<p>${trimmed}</p>`; // Wrap normal lines in <p>
    }
  }

  return html;
}

/**
 * Appends a message to the chat window.
 */
function appendChat(role, message) {
  const chatWindow = document.getElementById("chatWindow");
  const msgContainer = document.createElement("div");

  const formatted = role === "bot" ? formatReportText(message) : `<p>${message}</p>`;
  msgContainer.innerHTML = `<div class="chat-msg ${role}">${formatted}</div>`;

  chatWindow.appendChild(msgContainer);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * Update DOCX and PDF download links and reveal the download section.
 */
function updateDownloadLinks(docx, pdf) {
  const docxName = docx.split("/").pop();
  const pdfName = pdf.split("/").pop();

  const docxLink = document.getElementById("docxLink");
  const pdfLink = document.getElementById("pdfLink");

  // Ensure correct paths
  const docxPath = docx.startsWith("/") ? docx : `/${docx}`;
  const pdfPath = pdf.startsWith("/") ? pdf : `/${pdf}`;

  docxLink.href = docxPath;
  docxLink.download = docxName;

  pdfLink.href = pdfPath;
  pdfLink.download = pdfName;

  document.getElementById("downloadLinks").classList.remove("d-none"); // Show the download section
}

/**
 * Remove selected file and reset UI elements to initial state.
 */
function removeFile() {
  document.getElementById('filePreview').classList.add('d-none');
  document.getElementById('docFile').value = "";
  document.getElementById('chatSection').style.display = "none";
  document.getElementById('progressBar').style.width = "33%";
  document.getElementById('progressBar').innerText = "Step 1: Upload";
}

// ============================================================
// Template & File Handling
// ============================================================

/**
 * Load available document templates and populate the dropdown.
 */
async function loadTemplateOptions() {
  try {
    const res = await fetch("/documents/templates/");
    if (!res.ok) throw new Error("Failed to fetch templates");
    const data = await res.json();
    const templateSelect = document.getElementById("templateSelect");
    templateSelect.innerHTML = "";

    if (data.available_templates && data.available_templates.length > 0) {
      for (const template of data.available_templates) {
        const option = document.createElement("option");
        option.value = template;
        option.textContent = template.replace(/_/g, " ").replace(".json", "");
        templateSelect.appendChild(option);
      }
    } else {
      const option = document.createElement("option");
      option.textContent = "No templates available";
      option.disabled = true;
      templateSelect.appendChild(option);
    }
  } catch (error) {
    alert("Error loading templates: " + error.message);
  }
}

/**
 * Handle file upload, send to server for processing, and display the generated report.
 */
/*async function uploadFile() {
  try {
    const fileInput = document.getElementById("docFile");
    if (!fileInput.files.length) {
      alert("Please select a file first.");
      return;
    }

    updateProgress(2);

    // Get the selected template name from the dropdown
    const templateSelect = document.getElementById("templateSelect");
    const selectedTemplate = templateSelect.value;

    const formData = new FormData();
    for (const file of fileInput.files) {
      formData.append("files", file);
    }

    // Append template_name to formData
    formData.append("template_name", selectedTemplate);

    const res = await fetch("/documents/process/", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const text = await res.text();
      alert("Upload failed: " + text);
      return;
    }

    const result = await res.json();
    console.log("Upload API response:", result);

    currentDocumentUUID = result.uuid || null;

    updateProgress(2);

    if (result.flattened_sections) {
      let fullReport = "";
      const sections = Object.values(result.flattened_sections);

      // Group children by their parent title
      const parentMap = {};

      for (const section of sections) {
        const parent = section.parent_title || null;
        const title = section.title || "";
        const content = section.content || "";

        if (parent) {
          if (!parentMap[parent]) {
            parentMap[parent] = [];
          }
          parentMap[parent].push({ title, content });
        } else {
          // No parent, render directly as top-level section
          fullReport += `# ${title}\n\n${content}\n\n`;
        }
      }

      // Render parents and their children
      for (const [parentTitle, children] of Object.entries(parentMap)) {
        fullReport += `# ${parentTitle}\n\n`; // Parent heading
        for (const child of children) {
          fullReport += `# ${child.title}\n\n${child.content}\n\n`;
        }
      }

      document.getElementById("docContent").value = fullReport.trim();
      appendChat("bot", fullReport.trim());

      document.getElementById("chatSection").style.display = "block";
      document.getElementById("feedbackSection").classList.remove("d-none");
      updateDownloadLinks(result.docx_path, result.pdf_path);

      updateProgress(3);
    } else {
      alert("Failed to generate report.");
    }
  } catch (error) {
    alert("Error uploading file: " + error.message);
  }
}*/
/**
 * Handle file upload, send to server for processing, and display the generated report.
 */
async function uploadFile() {
  try {
    const fileInput = document.getElementById("docFile");
    if (!fileInput.files.length) {
      alert("Please select a file first.");
      return;
    }

    updateProgress(2);

    // Get the selected template name from the dropdown
    const templateSelect = document.getElementById("templateSelect");
    const selectedTemplate = templateSelect.value;

    const formData = new FormData();
    for (const file of fileInput.files) {
      formData.append("files", file);
    }

    // Append template_name to formData
    formData.append("template_name", selectedTemplate);

    const res = await fetch("/documents/process/", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const text = await res.text();
      alert("Upload failed: " + text);
      return;
    }

    const result = await res.json();
    console.log("Upload API response:", result);

    currentDocumentUUID = result.uuid || null;

    updateProgress(2);

    if (result.flattened_sections) {
      let fullReport = "";
      const sections = Object.values(result.flattened_sections);

      // Group children by their parent title
      const parentMap = {};

      for (const section of sections) {
        const parent = section.parent_title || null;
        const title = section.title || "";
        const content = section.content || "";

        if (parent) {
          if (!parentMap[parent]) {
            parentMap[parent] = [];
          }
          parentMap[parent].push({ title, content });
        } else {
          // No parent, render directly as top-level section
          fullReport += `# ${title}\n\n${content}\n\n`;
        }
      }

      // Render parents and their children
      for (const [parentTitle, children] of Object.entries(parentMap)) {
        fullReport += `# ${parentTitle}\n\n`; // Parent heading
        for (const child of children) {
          fullReport += `## ${child.title}\n\n${child.content}\n\n`;
        }
      }

      // 1️⃣ Save raw markdown text to textarea
      document.getElementById("docContent").value = fullReport.trim();

      // 2️⃣ Render formatted HTML using marked.js
      const renderedHTML = marked.parse(fullReport.trim());
      document.getElementById("chatWindow").innerHTML = renderedHTML;

      // 3️⃣ Reveal chat & feedback sections
      document.getElementById("chatSection").style.display = "block";
      document.getElementById("feedbackSection").classList.remove("d-none");

      // 4️⃣ Update download links
      updateDownloadLinks(result.docx_path, result.pdf_path);

      // 5️⃣ Progress complete
      updateProgress(3);
    } else {
      alert("Failed to generate report.");
    }
  } catch (error) {
    alert("Error uploading file: " + error.message);
  }
}

const progressBar = document.getElementById('progressBar');
function updateProgress(step, isRevision = false) {
  progressBar.classList.remove('processing');

  if (isRevision) {
    // Revision flow
    if (step === 2) {
      progressBar.style.width = "66%";
      progressBar.innerText = "Updating Report…";
      progressBar.classList.add('processing'); //
    } else if (step === 3) {
      progressBar.style.width = "80%";
      progressBar.innerText = "Step 2: Review AI Report → Download or Suggest Changes";
    }
  } else {
    // Initial generation flow
    if (step === 1) {
      progressBar.style.width = "33%";
      progressBar.innerText = "Step 1: Upload Reference Material (.DOCX)";
    } else if (step === 2) {
      progressBar.style.width = "66%";
      progressBar.innerText = "Sit tight! Your AI-powered report is on the way…";
      progressBar.classList.add('processing'); //
    } else if (step === 3) {
      progressBar.style.width = "80%";
      progressBar.innerText = "Step 2: Review AI Report → Download or Suggest Changes";
    } else if (step === 4) {
      progressBar.style.width = "100%";
      progressBar.innerText = "Report Downloaded. Thank you!";
    }
  }
}


// ============================================================
// Chat Functions
// ============================================================

/**
 * Send a question to the server using the current document as context.
 */
/*async function sendQuestion() {
  const docContent = document.getElementById("docContent").value;
  const question = document.getElementById("userInput").value;

  if (!question.trim()) return;

  updateProgress(2, true);

  appendChat("user", question);
  document.getElementById("userInput").value = "";

  const res = await fetch("/documents/chat/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_content: docContent, question: question })
  });

  const result = await res.json();
  const reply = result.answer || "No response.";

  appendChat("bot", reply);
  document.getElementById("docContent").value = reply;

  currentDocumentUUID = result.uuid || currentDocumentUUID;

  if (result.docx_path && result.pdf_path) {
    updateDownloadLinks(result.docx_path, result.pdf_path);
  }

  updateProgress(3, true);
}*/
async function sendQuestion() {
  const docContent = document.getElementById("docContent").value;
  const question = document.getElementById("userInput").value;

  if (!question.trim()) return;

  updateProgress(2, true);

  appendChat("user", question);
  document.getElementById("userInput").value = "";

  try {
    const res = await fetch("/documents/chat/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_content: docContent, question: question })
    });

    if (!res.ok) {
      const text = await res.text();
      alert("Chat request failed: " + text);
      return;
    }

    const result = await res.json();
    console.log("Chat API response:", result);

    const reply = (result.answer || "No response.").replace(/TERMINATE/g, "");

    currentDocumentUUID = result.uuid || currentDocumentUUID;

    // ✅ Format reply as Markdown → HTML
    const formattedReply = reply.trim();
    const renderedHTML = marked.parse(formattedReply);

    // 1️⃣ Append raw markdown to textarea (history)
    document.getElementById("docContent").value += "\n\n" + formattedReply;

    // 2️⃣ Append formatted HTML to chat window
    const chatWindow = document.getElementById("chatWindow");
    const botMsgDiv = document.createElement("div");
    botMsgDiv.classList.add("chat-msg", "bot", "mb-3");
    botMsgDiv.innerHTML = renderedHTML;
    chatWindow.appendChild(botMsgDiv);

    // 3️⃣ Auto-scroll to bottom
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // 4️⃣ Reveal feedback section if hidden
    document.getElementById("chatSection").style.display = "block";
    document.getElementById("feedbackSection").classList.remove("d-none");

    // 5️⃣ Update download links if provided
    if (result.docx_path && result.pdf_path) {
      updateDownloadLinks(result.docx_path, result.pdf_path);
    }

    // 6️⃣ Progress complete
    updateProgress(3, true);

  } catch (error) {
    alert("Error sending question: " + error.message);
  }
}

// ============================================================
// Feedback Functions
// ============================================================

/**
 * Submit feedback with a text type (currently unused rating variable in payload).
 */
async function submitFeedback(type) {
  const content = document.getElementById("docContent").value;
  const template = document.getElementById("templateSelect").value;

  const payload = {
    rating: rating,
    document_content: content,
    template_name: template,
    timestamp: new Date().toISOString(),
    uuid: currentDocumentUUID
  };

  try {
    const res = await fetch("/documents/feedback/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok) {
      console.log("Feedback saved:", data);
      alert(`Thanks for rating this report ${rating}/5!`);
    } else {
      console.error("Feedback failed:", data);
      alert("Failed to submit feedback.");
    }
  } catch (err) {
    console.error("Feedback error:", err);
    alert("Error sending feedback.");
  }
}

/**
 * Submit numeric rating for the current report.
 */
function submitRating(rating) {
  const content = document.getElementById("docContent").value;
  const template = document.getElementById("templateSelect").value;

  const payload = {
    rating: rating,
    document_content: content,
    template_name: template || "None",
    timestamp: new Date().toISOString(),
    uuid: currentDocumentUUID
  };

  fetch("/documents/feedback/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(async (res) => {
      const data = await res.json();
      if (res.ok) {
        console.log("Feedback saved:", data);
        alert(`Thanks for rating this report ${rating}/5!`);
      } else {
        console.error("Feedback failed:", data);
        alert("Failed to submit feedback.");
      }
    })
    .catch((err) => {
      console.error("Feedback error:", err);
      alert("Error sending feedback.");
    });
}

// ============================================================
// UI Effects
// ============================================================

// Fade-in sections on scroll
const fadeSections = document.querySelectorAll('.fade-section');
const revealOnScroll = () => {
  const trigger = window.innerHeight * 0.85;
  fadeSections.forEach(section => {
    const top = section.getBoundingClientRect().top;
    if (top < trigger) section.classList.add('visible');
  });
}


// ============================================================
// Initialization
// ============================================================

window.addEventListener("DOMContentLoaded", () => {
  loadTemplateOptions();
  revealOnScroll();

  const docxLink = document.getElementById("docxLink");
  const pdfLink = document.getElementById("pdfLink");

  if (docxLink) {
    docxLink.addEventListener("click", () => {
      updateProgress(4);
    });
  }
  if (pdfLink) {
    pdfLink.addEventListener("click", () => {
      updateProgress(4);
    });
  }
});

// ============================================================
// Dynamic Star Rating (Enhancement)
// ============================================================

window.addEventListener("DOMContentLoaded", () => {
  const stars = document.querySelectorAll('.star-rating .star');
  let currentRating = 0;

  stars.forEach((star, index) => {
    // Hover preview
    star.addEventListener('mouseover', () => {
      highlightStars(index + 1);
    });

    // Reset to the current rating when hover ends
    star.addEventListener('mouseout', () => {
      highlightStars(currentRating);
    });

    // Click to set rating (onclick="submitRating(n)" still runs)
    star.addEventListener('click', () => {
      currentRating = index + 1;
      highlightStars(currentRating);

      // Tiny pop animation
      star.classList.add('pop');
      setTimeout(() => star.classList.remove('pop'), 150);
    });
  });

  function highlightStars(rating) {
    stars.forEach((star, idx) => {
      star.classList.toggle('active', idx < rating);
    });
  }
});