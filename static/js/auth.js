// Password validation rules
function validatePassword(password) {
  return {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*]/.test(password),
  };
}

// Signup password input + live rules
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

// Toggle password visibility
function togglePassword(inputId, buttonId) {
  const input = document.getElementById(inputId);
  const btn = document.getElementById(buttonId);

  if (btn) {
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

// ================== SIGNUP FORM ==================
const signupForm = document.getElementById("signupForm");
if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("signupName").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value;

    const rules = validatePassword(password);
    if (!Object.values(rules).every(Boolean)) {
      alert("Password does not meet requirements!");
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
        alert(data.message);
        window.location.href = "/login";
      } else {
        alert(data.error || "Signup failed");
      }
    } catch (err) {
      console.error(err);
      alert("Signup request failed");
    }
  });
}

// ================== LOGIN FORM ==================
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
        alert(data.message);
        localStorage.setItem("token", data.token);
        window.location.href = "/dashboard";
      } else {
        alert(data.error || "Login failed");
      }
    } catch (err) {
      console.error(err);
      alert("Login request failed");
    }
  });
}
