let currentDocumentUUID = null;

// Reveal sections on scroll
const fadeSections = document.querySelectorAll('.fade-section');
const revealOnScroll = () => {
  const trigger = window.innerHeight * 0.85;
  fadeSections.forEach(section => {
    const top = section.getBoundingClientRect().top;
    if (top < trigger) section.classList.add('visible');
  });
}
window.addEventListener('scroll', revealOnScroll);
revealOnScroll(); // initial call

function formatReportText(text) {
  // Remove 'TERMINATE'
  text = text.replace(/TERMINATE/g, "").trim();

  // Split the input into lines
  const lines = text.split("\n");

  let html = "";
  for (let line of lines) {
    const trimmed = line.trim();

    if (!trimmed) {
      // Skip empty lines (for spacing)
      html += "<br>";
      continue;
    }

    if (/^# (.+)/.test(trimmed)) {
      // Convert Markdown-style header to <h4>
      const heading = trimmed.replace(/^# (.+)/, '<h4 class="mt-3 mb-2">$1</h4>');
      html += heading;
    } else {
      // Wrap normal lines in <p>
      html += `<p>${trimmed}</p>`;
    }
  }

  return html;
}

async function sendQuestion() {
  const docContent = document.getElementById("docContent").value;
  const question = document.getElementById("userInput").value;

  if (!question.trim()) return;

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
}

function appendChat(role, message) {
  const chatWindow = document.getElementById("chatWindow");
  const msgContainer = document.createElement("div");

  const formatted = role === "bot" ? formatReportText(message) : `<p>${message}</p>`;
  msgContainer.innerHTML = `<div class="chat-msg ${role}">${formatted}</div>`;
  chatWindow.appendChild(msgContainer);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function updateDownloadLinks(docx, pdf) {
  const docxName = docx.split("/").pop();
  const pdfName = pdf.split("/").pop();

  const docxLink = document.getElementById("docxLink");
  const pdfLink = document.getElementById("pdfLink");

  // Ensure correct paths, avoid double "/outputs/outputs/"
  const docxPath = docx.startsWith("/") ? docx : `/${docx}`;
  const pdfPath = pdf.startsWith("/") ? pdf : `/${pdf}`;

  docxLink.href = docxPath;
  docxLink.download = docxName;

  pdfLink.href = pdfPath;
  pdfLink.download = pdfName;

  // Show the download section
  document.getElementById("downloadLinks").classList.remove("d-none");
}

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

    if (res.ok) {
      alert("Thanks for your feedback!");
    } else {
      alert("Failed to submit feedback.");
    }
  } catch (err) {
    console.error("Feedback error:", err);
    alert("Error sending feedback.");
  }
}

function submitRating(rating) {
  const content = document.getElementById("docContent").value;
  const template = document.getElementById("templateSelect").value;

  const payload = {
    rating: rating,
    document_content: content,
    template_name: template,
    timestamp: new Date().toISOString(),
    uuid: currentDocumentUUID
  };

  fetch("/documents/feedback/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then((res) => {
      if (res.ok) {
        alert(`Thanks for rating this report ${rating}/5!`);
      } else {
        alert("Failed to submit feedback.");
      }
    })
    .catch((err) => {
      console.error("Feedback error:", err);
      alert("Error sending feedback.");
    });
}

window.addEventListener("DOMContentLoaded", () => {
  loadTemplateOptions();
});