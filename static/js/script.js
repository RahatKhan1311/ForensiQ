let CASES = [];

// Fetch cases from backend
function fetchCases() {
  fetch("/api/cases")
    .then(res => res.json())
    .then(cases => {  // Direct array, not nested in 'data' object
          
      if (!Array.isArray(cases)) {
        console.error('Expected array but got:', cases);
        return;
      }
      
      CASES = cases;
      renderCases();

      const casesContainer = document.getElementById("cases-container");
      if(casesContainer){
        casesContainer.innerHTML="";
        CASES.forEach(c => {
          const btn = document.createElement("button");
          btn.className="select-case-btn py-1 px-2 m-1 rounded-md bg-gray-800 text-white hover:bg-cyan-600";
          
          // Use the correct field names
          const caseId = c.case_id || c.id;
          const caseTitle = c.title || `Case ${caseId}`;
          
          btn.dataset.caseId = caseId;
          btn.innerText = caseTitle;
          btn.onclick = () => {
            document.getElementById("case-id-input").value = caseId;
            console.log('Selected case:', caseId);
          };
          casesContainer.appendChild(btn);
        });
      }
    })
    .catch(err => console.error("Error fetching cases:", err));
}


function deleteCase(id) {
  fetch(`/api/delete_case/${id}`, { method: "DELETE" })
    .then(res => res.json())
    .then(data => {
      console.log("Case deleted:", data);
      fetchCases();     // refresh after delete
      showSection("dashboard"); 
    })
    .catch(err => console.error("Error deleting case:", err));
}

async function addNoteToCase(caseId) {
  const note = prompt("Enter a new note:");

  if (!note || note.trim() === "") return;

  const res = await fetch(`/api/add_note/${caseId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note })
  });

  const data = await res.json();
  alert(data.message);

  fetchCases();
  openCase(caseId);
}

async function assignCaseToAnalyst(caseId) {
  const analyst = prompt("Enter analyst name:");

  if (!analyst) return;

  const res = await fetch(`/api/assign_analyst/${caseId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analyst })
  });

  const data = await res.json();
  alert(data.message);

  fetchCases();
  openCase(caseId);
}

function exportCaseReport(caseId) {
    window.open(`/api/export/${caseId}`, "_blank");
}

// Render recent cases & full case list
function renderCases() {
  const recentEl = document.getElementById('recent-cases');
  const listEl = document.getElementById('cases-list');
  if (!recentEl || !listEl) return;

  recentEl.innerHTML = '';
  listEl.innerHTML = '';

  const recentCases = CASES.slice(-6).reverse();

  recentCases.forEach(c => {
    const li = document.createElement('li');
    li.className = 'p-3 rounded-lg bg-white/10 border border-white/10 flex justify-between items-center hover:scale-[1.01] transition';

    li.innerHTML = `
      <div class="cursor-pointer" onclick="openCase('${c.id}')">
        <div class="font-medium">${c.title}</div>
        <div class="text-xs text-slate-400">${c.id} • ${c.date}</div>
      </div>
      <div class="flex items-center gap-2">
        <div class="text-sm">${c.status}</div>
        <button onclick="deleteCase('${c.id}'); event.stopPropagation();" class="text-red-500 hover:text-red-400 text-xs px-2 py-1 rounded bg-white/5">Delete</button>
      </div>
    `;

    recentEl.appendChild(li);
  });

  // Full cases list (with delete buttons)
  CASES.forEach(c => {
    const li2 = document.createElement('li');
    li2.className = 'p-3 rounded-lg bg-white/10 border border-white/10 flex justify-between items-center hover:scale-[1.01] transition';

    li2.innerHTML = `
      <div class="cursor-pointer" onclick="openCase('${c.id}')">
        <div class="font-medium">${c.title}</div>
        <div class="text-xs text-slate-400">${c.id} • ${c.date}</div>
      </div>
      <div class="flex items-center gap-2">
        <div class="text-sm">${c.status}</div>
        <button onclick="deleteCase('${c.id}'); event.stopPropagation();" class="text-red-500 hover:text-red-400 text-xs px-2 py-1 rounded bg-white/5">Delete</button>
      </div>
    `;

    listEl.appendChild(li2);
  });
}

// Show section helper
function showSection(id) {
  document.querySelectorAll('main section').forEach(s => s.classList.add('hidden'));
  const el = document.getElementById(id);
  if(el){
    el.classList.remove('hidden');
    el.classList.add('fade-enter');
    requestAnimationFrame(()=> el.classList.add('fade-enter-active'));
    setTimeout(()=>{ 
        el.classList.remove('fade-enter'); 
        el.classList.remove('fade-enter-active'); 
    }, 350);
  }
}

// Open a case in detail
function openCase(id) {
  const c = CASES.find(x => x.id === id);
  if(!c) return;

  // Fill case detail section
  document.getElementById('case-title').innerText = `${c.title} — ${c.id}`;
  document.getElementById('case-sub').innerText = `Title: ${c.title}`;
  document.getElementById('case-status').innerText = c.status;
  document.getElementById('case-owner').innerText = c.owner;
  document.getElementById('case-priority').innerText = c.priority;

  const evidenceList = document.getElementById('evidence-list');
  evidenceList.innerHTML = ''; // clear previous
  if (c.evidence && c.evidence.length > 0) {
    c.evidence.forEach(fileName => {
      const li = document.createElement('li');
      li.className = 'text-sm text-blue-400 hover:underline cursor-pointer';
      
      // Link to download/view
      const a = document.createElement('a');
      a.href = `/uploads/${fileName}`; // ensure Flask serves /uploads/
      a.textContent = fileName;
      a.target = '_blank';
      
      li.appendChild(a);
      evidenceList.appendChild(li);
    });
  } else {
    evidenceList.textContent = 'No evidence uploaded yet.';
  }

  // Notes
  const notesEl = document.getElementById('case-notes');
  notesEl.innerHTML = "";

  if (c.notes && c.notes.length > 0) {
    c.notes.forEach(note => {
      const p = document.createElement("p");
      p.className = "mb-2 border-b border-white/10 pb-1";
      p.textContent = note;
      notesEl.appendChild(p);
    });
  } else {
    notesEl.innerHTML = `<p class="text-slate-400 italic">No notes available.</p>`;
  }

// Add Note action button
  const addNoteBtn = document.createElement("button");
  addNoteBtn.textContent = "Add Note";
  addNoteBtn.className = "mt-2 py-2 rounded-md bg-[#22c55e] text-black font-semibold w-full";
  addNoteBtn.onclick = () => addNoteToCase(c.id);
  
  notesEl.appendChild(addNoteBtn);

  //Dynamic Actions
  const actionBox = document.getElementById("case-actions");
  actionBox.innerHTML = ""; // clear old buttons

  const assignBtn = document.createElement("button");
  assignBtn.textContent = c.owner === "Unassigned" ? "Assign to Analyst" : "Reassign Analyst";
  assignBtn.className = "py-2 rounded-md bg-[#0ea5e9] text-black font-semibold";
  assignBtn.onclick = () => assignCaseToAnalyst(c.id);

  const exportBtn = document.createElement("button");
  exportBtn.textContent = "Export Report";
  exportBtn.className = "py-2 rounded-md border border-white/10";
  exportBtn.onclick = () => exportCaseReport(c.id);

  actionBox.appendChild(assignBtn);
  actionBox.appendChild(exportBtn);

  showSection('case-detail');
}

// Show New Case form
function createNewCase() {
  // Switch to a dynamic new case form
  const formHtml = `
    <div class="p-4 rounded-2xl bg-white/5 border border-white/10">
      <h2 class="text-lg font-semibold mb-4">Create New Case</h2>
      <form id="dynamic-new-case-form" class="space-y-4">
        <div>
          <label class="block text-sm mb-1">Case Title</label>
          <input type="text" id="new-case-title" class="w-full p-2 rounded-md bg-black/20 text-white" required>
        </div>
        <div>
          <label class="block text-sm mb-1">Description</label>
          <textarea id="new-case-description" class="w-full p-2 rounded-md bg-black/20 text-white" rows="4" required></textarea>
        </div>
        <div>
          <label class="block text-sm mb-1">Priority</label>
          <select id="new-case-priority" class="w-full p-2 rounded-md bg-black/20 text-white">
            <option value="Low">Low</option>
            <option value="Medium" selected>Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        <div>
          <label class="block text-sm mb-1">Assigned Investigator</label>
          <input type="text" id="new-case-owner" class="w-full p-2 rounded-md bg-black/20 text-white" required>
        </div>
        <div>
          <label class="block mt-2 mb-1 text-sm text-slate-300">Upload Evidence</label>
          <input type="file" id="new-case-evidence" multiple class="w-full p-2 rounded-md bg-black/20 text-white"/>
        </div>
        <button type="submit" class="py-2 px-4 rounded-md bg-gradient-to-r from-cyan-500 to-blue-300 text-black font-semibold">
          Submit Case
        </button>
      </form>
    </div>
  `;

  // Inject into 'cases' section
  const casesSection = document.getElementById('cases');
  casesSection.innerHTML = formHtml;
  showSection('cases');

  // Handle form submission
  const form = document.getElementById('dynamic-new-case-form');
  form.onsubmit = (e) => {
    e.preventDefault();

    const newCase = {
      id: 'FQ-2025-' + (Math.floor(Math.random() * 900 + 100)),
      title: document.getElementById('new-case-title').value,
      description: document.getElementById('new-case-description').value,
      priority: document.getElementById('new-case-priority').value,
      owner: document.getElementById('new-case-owner').value,
      status: 'Open',
      date: new Date().toISOString().slice(0, 10),
      evidence: [],
      notes: []
    };

    // Prepare FormData for file upload
    const formData = new FormData();
    formData.append('caseData', JSON.stringify(newCase));

    const files = document.getElementById('new-case-evidence').files;
    for (let file of files) {
      formData.append('evidence', file);
    }

    // POST to backend
    fetch("/api/new_case", {
      method: "POST",
      body: formData // send as multipart/form-data
    })
    .then(res => res.json())
    .then(data => {
      console.log("Case added with evidence:", data);
      form.reset();
      form.classList.add('hidden');
      renderCases(); // Refresh the dashboard recent cases
      openCase(data.id); // Go directly to case detail view
    })
    .catch(err => console.error("Error adding case:", err));
  };
}

function loadDashboardStats() {
  fetch("/api/dashboard")
    .then(res => res.json())
    .then(data => {
      // Make sure keys match exactly what Flask returns
      document.getElementById("openCasesCount").innerText = data.open_cases;
      document.getElementById("pendingCasesCount").innerText = data.pending_analysis;
      document.getElementById('avgResponse').innerText = data.avg_response;
    })
    .catch(err => console.error("Error loading dashboard stats:", err));
}

// Call on page load
loadDashboardStats();

// Optional: auto-refresh every 30 seconds
setInterval(loadDashboardStats, 30000);

let lastInsertedId = null;

document.getElementById("run-ocr").addEventListener("click", async () => {

  const summaryBox = document.getElementById("ai-summary");
  const findingsList = document.getElementById("key-findings");
  const keywordBox = document.getElementById("keyword-tags");
  const ocrBox = document.getElementById("ocr-output");

  const fileInput = document.getElementById("file-input");
  const caseIdInput = document.getElementById("case-id-input"); 

  if (!fileInput.files[0]) {
    return alert("Please select a file!");
  }

  // Remove the case selection check
  if (!caseIdInput.value) return alert("Please select a case!"); 

  // Clear UI
  summaryBox.innerHTML = "Analyzing document...";
  findingsList.innerHTML = "";
  keywordBox.innerHTML = "";
  ocrBox.textContent = "";

  try {
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("case_id", caseIdInput.value); 

    const res = await fetch("/api/analyze/ocr", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      // Try to get error details from response
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.error || `Server error: ${res.status} ${res.statusText}`);
    }

    // Only now parse the successful response
    const data = await res.json();

    // Store the inserted ID
    lastInsertedId = data.inserted_id;

    // Raw OCR
    ocrBox.textContent = data.ocr_text || "No OCR text";

    // AI Analysis
    if (data.analysis_text) {
      summaryBox.innerHTML = data.analysis_text.summary || "No summary available";

      // Combine key_insights and entities if they're separate
      const insights = data.analysis_text.key_insights || {};
      const entities = data.analysis_text.entities || {};
      
      // Merge insights and entities for display
      const allInsights = { ...insights, ...entities };

      if (allInsights.emails?.length)
        findingsList.innerHTML += `<li>📧 Emails: ${allInsights.emails.join(", ")}</li>`;

      if (allInsights.urls?.length)
        findingsList.innerHTML += `<li>🌐 URLs: ${allInsights.urls.join(", ")}</li>`;

      if (allInsights.organizations?.length)
        findingsList.innerHTML += `<li>🏢 Organizations: ${allInsights.organizations.join(", ")}</li>`;

      if (allInsights.persons?.length)
        findingsList.innerHTML += `<li>👤 Persons: ${allInsights.persons.join(", ")}</li>`;

      if (allInsights.locations?.length)
        findingsList.innerHTML += `<li>📍 Locations: ${allInsights.locations.join(", ")}</li>`;

      if (allInsights.phones?.length)
        findingsList.innerHTML += `<li>📞 Phone Numbers: ${allInsights.phones.join(", ")}</li>`;

      if (allInsights.dates?.length)
        findingsList.innerHTML += `<li>📅 Dates: ${allInsights.dates.join(", ")}</li>`;

      if (allInsights.money?.length)
        findingsList.innerHTML += `<li>💰 Money: ${allInsights.money.join(", ")}</li>`;

      // Keywords
      (data.analysis_text.keywords || []).forEach(k => {
        const tag = document.createElement("span");
        tag.className = "px-2 py-1 bg-cyan-500/20 text-cyan-300 rounded text-xs";
        tag.textContent = k;
        keywordBox.appendChild(tag);
      });
    } else {
      summaryBox.textContent = "No AI analysis generated.";
    }

  } catch (err) {
    summaryBox.textContent = "Error: " + err.message;
    findingsList.innerHTML = "";
    keywordBox.innerHTML = "";
    ocrBox.textContent = "";
  }
});

// ==================== SIMILARITY BUTTON ====================
document.getElementById("run-sim").addEventListener("click", async () => {
  if (!lastInsertedId) {
    alert("Please run OCR on a document first so the system has text to compare!");
    return;
  }
  
  const container = document.getElementById("similarityResults");
  const listContainer = document.getElementById("sim-results");
  
  container.innerHTML = "Analyzing similarities...";
  listContainer.innerHTML = "";
  
  try {    
    const res = await fetch("/api/analyze/similarity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ inserted_id: lastInsertedId })
    });
    
    if (!res.ok) {
      // Try to get detailed error
      let errorData;
      try {
        errorData = await res.json();
        console.log("Error response:", errorData);
      } catch (e) {
        console.log("Could not parse error response");
      }
      throw new Error(errorData?.error || errorData?.detail || `Server error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    
    // ---- Animated similarity bars ----
    renderSimilarity(data.results);

    // ---- Optional list view ----
    listContainer.innerHTML = "";
    if (!data.results || data.results.length === 0) {
      listContainer.innerText = "No results found.";
    } else {
      data.results.forEach(r => {
        const div = document.createElement("div");
        div.className = "p-2 bg-white/10 rounded-md text-xs";
        div.innerHTML = `
          <strong>${r.case_id}</strong> — ${r.title || "No title"}
          (${(r.similarity_score ?? 0)}%)
        `;
        listContainer.appendChild(div);
      });
    }

  } catch (err) {
    console.error("Similarity Error Details:", err);
    container.innerHTML = `<p style='color:red'>Error: ${err.message}</p>`;
    listContainer.innerText = "";
  }
});

function renderSimilarity(results) {
    const container = document.getElementById("similarityResults");
    const listContainer = document.getElementById("sim-results");
    container.innerHTML = "";
    listContainer.innerHTML = "";

    if (!results || results.length === 0) {
        container.innerHTML = "<p>No similar cases found.</p>";
        return;
    }

    results.forEach(r => {
      // 1. Determine Color based on similarity severity
        let color = "#22c55e"; // Success Green
        if (r.similarity_score > 70) color = "#ef4444"; // Danger Red
        else if (r.similarity_score > 40) color = "#f59e0b"; // Warning Orange

        // 2. Create a unified result card
        const card = document.createElement("div");
        card.className = "mb-4 p-3 rounded-lg bg-white/5 border border-white/5 fade-enter-active";
        
        card.innerHTML = `
            <div class="flex justify-between text-[11px] mb-1.5">
                <span class="font-bold text-cyan-400 uppercase tracking-wider">${r.case_id}</span>
                <span class="text-slate-400 truncate ml-4">${r.title || 'Untitled Case'}</span>
            </div>
            <div class="sim-bar-outer h-3 bg-black/40 rounded-full overflow-hidden border border-white/5">
                <div class="sim-bar-inner h-full transition-all duration-1000 ease-out flex items-center justify-end pr-2 text-[9px] font-bold" 
                     style="width: 0%; background: ${color}; box-shadow: 0 0 10px ${color}33">
                     0%
                </div>
            </div>
        `;

        container.appendChild(card);

        // 3. Trigger the animation slightly after appending to DOM
        setTimeout(() => {
            const barInner = card.querySelector('.sim-bar-inner');
            barInner.style.width = r.similarity_score + "%";
            
            // Text counter effect
            let count = 0;
            const target = Math.floor(r.similarity_score);
            const timer = setInterval(() => {
                if (count >= target) {
                    clearInterval(timer);
                    barInner.innerText = target + "%";
                } else {
                    count++;
                    barInner.innerText = count + "%";
                }
            }, 15);
        }, 50);
    });
}


// ==================== LOAD LATEST AI ANALYSIS ====================
async function loadLatestAnalysis() {
  try {
    const res = await fetch("/api/analyze/latest");
    const data = await res.json();

    // OCR text
    document.getElementById("ocr-output").innerText =
    data.ocr_text || "No OCR yet";

    // Similarity results
    const simContainer = document.getElementById("sim-results");
    simContainer.innerHTML = "";

    if (!data.similarity_results || data.similarity_results.length === 0) {
      simContainer.innerText = "No similarity results yet";
    } else {
      data.similarity_results.forEach(r => {
        const div = document.createElement("div");
        div.className = "p-2 bg-white/10 rounded-md text-xs";
        div.innerHTML = `<strong>${r.case_id || "N/A"}</strong>: ${r.title || "Untitled"} 
                        (Score: ${
                          r.score ? (r.score * 100).toFixed(1) + "%" : "N/A"
                        })`;
        simContainer.appendChild(div);
      });
    }
  } catch (err) {
    document.getElementById("ocr-output").innerText = "Failed loading OCR";
    document.getElementById("sim-results").innerText = "Failed loading similarity results";
  }
}

// Function to fill the dropdown with your database cases
async function refreshCaseDropdown() {
    const caseSelect = document.getElementById("case-id-input");
    
    try {
        const res = await fetch("/api/cases");
        const cases = await res.json();  // This is a direct array
                
        // Clear dropdown and add default option
        caseSelect.innerHTML = '<option value="">-- Select a Case --</option>';
        
        if (Array.isArray(cases) && cases.length > 0) {
            cases.forEach(c => {
                const option = document.createElement("option");
                
                // Try different possible field names
                const caseId = c.case_id || c.id || c.caseId || c.CaseID || '';
                const title = c.title || c.case_title || c.name || `Case ${caseId}`;
                
                if (caseId) {
                    option.value = caseId;
                    option.textContent = title;
                    caseSelect.appendChild(option);
                } else {
                    console.warn('Skipping case with no ID:', c);
                }
            });
          
        } else {
            console.warn('No cases array found or empty');
            caseSelect.innerHTML = '<option value="">-- No Cases Available --</option>';
        }
        
    } catch (err) {
        console.error('Error loading cases for dropdown:', err);
        caseSelect.innerHTML = '<option value="">-- Error Loading Cases --</option>';
    }
}

// Run this immediately so the list is ready when the page opens
refreshCaseDropdown();

// === Save functions  ===
  function saveProfile() {
    const data = {
      name: document.getElementById("user-name").value,
      email: document.getElementById("user-email").value,
      password: document.getElementById("user-password").value
    };
    console.log("Profile saved:", data);
    alert("Profile saved!");
  }

  function savePreferences() {
    const data = {
      darkTheme: document.getElementById("toggle-dark-theme").checked,
      neonTheme: document.getElementById("toggle-neon-theme").checked,
      sidebarBehavior: document.getElementById("sidebar-behavior").value,
      refreshInterval: parseInt(document.getElementById("refresh-interval").value)
    };

    localStorage.setItem("appPreferences", JSON.stringify(data));
    console.log("Preferences saved:", data);
    alert("Preferences saved!");

    applyTheme(); // apply dark/neon immediately
  }

  function saveIntegrations() {
    const data = {
      ocrApiKey: document.getElementById("ocr-api-key").value,
      aiApiKey: document.getElementById("ai-api-key").value
    };
    console.log("API Keys saved:", data);
    alert("API keys saved!");
  }

  function resetApp() {
    if(confirm("Are you sure? This will reset all app settings!")) {
      console.log("App reset!");
      alert("App reset!");
    }
  }

// On page load
document.addEventListener('DOMContentLoaded', () => {
  fetchCases();
  showSection('dashboard');
  loadLatestAnalysis();

  const casesContainer = document.getElementById("cases-container");
  function renderCaseButtons() {
    if(!casesContainer) return;
    casesContainer.innerHTML = ""; // clear previous
    CASES.forEach(c => {
      const btn = document.createElement("button");
      btn.className = "select-case-btn py-1 px-2 m-1 rounded-md bg-gray-800 text-white hover:bg-cyan-500";
      btn.dataset.caseId = c.id; // use your DB case id
      btn.innerText = c.title;
      btn.onclick = () => {
        document.getElementById("case-id-input").value = c.id;
        alert(`Selected Case: ${c.id}`);
      };
      casesContainer.appendChild(btn);
    });
  }

  renderCaseButtons(); 

  // Attach New Case button
  const newCaseBtn = document.querySelector('button[onclick="createNewCase()"]');
  if(newCaseBtn) newCaseBtn.onclick = createNewCase;

  const caseSelect = document.getElementById("case-id-input");

  async function loadCasesForReports() {
  const select = document.getElementById("report-case-select");
  if (!select) return;

  try {
    const res = await fetch("/api/cases");
    const cases = await res.json();

    select.innerHTML = '<option value="">-- Select a Case --</option>';

    if (Array.isArray(cases)) {
      cases.forEach(c => {
        const option = document.createElement("option");
        option.value = c.case_id || c.id;  // backend case_id
        option.textContent = c.title || `Case ${c.id}`;
        select.appendChild(option);
      });
    } else {
      select.innerHTML = '<option value="">No cases available</option>';
    }

  } catch (err) {
    console.error("Error loading cases for reports:", err);
    select.innerHTML = '<option value="">Error loading cases</option>';
  }
}

// Run it immediately
loadCasesForReports();

const downloadBtn = document.getElementById("downloadReportBtn");
if (downloadBtn) {
  downloadBtn.addEventListener("click", async () => {
    const caseSelect = document.getElementById("report-case-select");
    const selectedCaseId = caseSelect.value;

    if (!selectedCaseId) return alert("Please select a case first!");

    downloadBtn.disabled = true;
    downloadBtn.textContent = "Generating PDF...";

    try {
      const res = await fetch(`/api/reports/${selectedCaseId}/pdf`);
      if (!res.ok) throw new Error("Failed to generate PDF");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Case_${selectedCaseId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      downloadBtn.disabled = false;
      downloadBtn.textContent = "Generate PDF Summary";
    }
  });
}

// === SETTINGS TABS ===
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;

      // Show selected content
      document.querySelectorAll(".tab-content").forEach(tc => tc.classList.add("hidden"));
      const selected = document.querySelector(`.tab-content[data-tab='${tab}']`);
      if (selected) selected.classList.remove("hidden");

      // Highlight active tab
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("border-cyan-400"));
      btn.classList.add("border-cyan-400");
    });
  });


  // === Load settings from localStorage ===
  function loadSettings() {
    const prefs = JSON.parse(localStorage.getItem("appPreferences") || "{}");

    document.getElementById("toggle-dark-theme").checked = prefs.darkTheme || false;
    document.getElementById("toggle-neon-theme").checked = prefs.neonTheme || false;
    document.getElementById("sidebar-behavior").value = prefs.sidebarBehavior || "sticky";
    document.getElementById("refresh-interval").value = prefs.refreshInterval || 30;

    applyTheme();
  }

  loadSettings();

  // === APPLY THEME FUNCTION ===
  function applyTheme() {
  const dark = document.getElementById("toggle-dark-theme").checked;
  const neon = document.getElementById("toggle-neon-theme").checked;

  // Dark Mode
  if(dark) {
    document.body.classList.add("dark");
  } else {
    document.body.classList.remove("dark");
  }

  // Neon Mode
  if(neon) {
    document.body.classList.add("neon");
  } else {
    document.body.classList.remove("neon");
  }
}

// Instant apply on checkbox change
document.getElementById("toggle-dark-theme").addEventListener("change", applyTheme);
document.getElementById("toggle-neon-theme").addEventListener("change", applyTheme);


});