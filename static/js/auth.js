// ================= POPUP SYSTEM =================
function openPopup({ title, message, showInput=false, defaultValue="", showCancel=false }) {
  return new Promise(resolve => {
    const overlay = document.getElementById("popupOverlay");
    const titleEl = document.getElementById("popupTitle");
    const msgEl = document.getElementById("popupMessage");
    const inputEl = document.getElementById("popupInput");
    const okBtn = document.getElementById("popupOk");
    const cancelBtn = document.getElementById("popupCancel");

    if (!overlay) {
      console.log(message);
      return resolve(null);
    }

    titleEl.innerText = title;
    msgEl.innerText = message;

    inputEl.classList.toggle("hidden", !showInput);
    inputEl.value = defaultValue;

    cancelBtn.classList.toggle("hidden", !showCancel);

    overlay.classList.remove("hidden");
    overlay.classList.add("flex");

    okBtn.onclick = () => {
      const val = showInput ? inputEl.value.trim() : true;
      closePopup();
      resolve(val);
    };

    cancelBtn.onclick = () => {
      closePopup();
      resolve(null);
    };
  });
}

function closePopup() {
  const overlay = document.getElementById("popupOverlay");
  overlay.classList.remove("flex");
  overlay.classList.add("hidden");
}


// ================= PASSWORD RULES =================
function validatePassword(password) {
  return {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*]/.test(password),
  };
}


// ================= SIGNUP PASSWORD LIVE CHECK =================
const signupPassword = document.getElementById("signupPassword");

if (signupPassword) {
  const rLength  = document.getElementById("rLength");
  const rUpper   = document.getElementById("rUpper");
  const rLower   = document.getElementById("rLower");
  const rNumber  = document.getElementById("rNumber");
  const rSpecial = document.getElementById("rSpecial");

  signupPassword.addEventListener("input", () => {
    const rules = validatePassword(signupPassword.value);

    rLength.className  = rules.length  ? "text-green-400" : "text-red-400";
    rUpper.className   = rules.upper   ? "text-green-400" : "text-red-400";
    rLower.className   = rules.lower   ? "text-green-400" : "text-red-400";
    rNumber.className  = rules.number  ? "text-green-400" : "text-red-400";
    rSpecial.className = rules.special ? "text-green-400" : "text-red-400";
  });
}


// ================= PASSWORD TOGGLE =================
function togglePassword(inputId, buttonId) {
  const input = document.getElementById(inputId);
  const btn = document.getElementById(buttonId);

  if (btn && input) {
    btn.addEventListener("click", () => {
      if (input.type === "password") {
        input.type = "text";
        btn.textContent = "Hide";
      } else {
        input.type = "password";
        btn.textContent = "Show";
      }
    });
  }
}

togglePassword("signupPassword", "toggleSignupPassword");
togglePassword("loginPassword", "toggleLoginPassword");


// ================= SIGNUP FORM =================
const signupForm = document.getElementById("signupForm");

if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("signupName").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value;

    const rules = validatePassword(password);

    if (!Object.values(rules).every(Boolean)) {
      await openPopup({
        title: "Weak Password",
        message: "Password does not meet all requirements."
      });
      return;
    }

    try {
      const res = await fetch("/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
      });

      const data = await res.json();

      if (res.ok) {
        await openPopup({
          title: "Signup Success",
          message: data.message || "Account created successfully"
        });

        window.location.href = "/login";
      } else {
        await openPopup({
          title: "Signup Failed",
          message: data.error || "Signup failed"
        });
      }

    } catch (err) {
      console.error(err);
      await openPopup({
        title: "Error",
        message: "Signup request failed"
      });
    }
  });
}


// ================= LOGIN FORM =================
const loginForm = document.getElementById("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("token", data.token);

        await openPopup({
          title: "Login Success",
          message: data.message || "Welcome to ForensiQ"
        });

        window.location.href = "/dashboard";

      } else {
        await openPopup({
          title: "Login Failed",
          message: data.error || "Invalid credentials"
        });
      }

    } catch (err) {
      console.error(err);
      await openPopup({
        title: "Error",
        message: "Login request failed"
      });
    }
  });
}
