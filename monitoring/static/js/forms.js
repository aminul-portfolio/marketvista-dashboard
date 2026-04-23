(function () {
  "use strict";

  function qs(selector, scope = document) {
    return scope.querySelector(selector);
  }

  function qsa(selector, scope = document) {
    return Array.from(scope.querySelectorAll(selector));
  }

  function enhanceFormFields(form) {
    qsa("input, select, textarea", form).forEach((field) => {
      field.classList.add("mv-form-field");
    });
  }

  function autofocusFirstField(form) {
    const firstField = qs("input:not([type='hidden']), select, textarea", form);
    if (firstField) {
      firstField.focus();
    }
  }

  function preventDoubleSubmit(form) {
    form.addEventListener("submit", function () {
      const submitButton = this.querySelector("button[type='submit'], input[type='submit']");
      if (submitButton) {
        submitButton.disabled = true;

        if (submitButton.tagName === "BUTTON") {
          submitButton.dataset.originalText = submitButton.textContent;
          submitButton.textContent = "Submitting...";
        }
      }
    });
  }

  function initRegisterPasswordCheck(form) {
    const password1 = qs("#id_password1", form);
    const password2 = qs("#id_password2", form);
    const hint = qs("[data-password-match-hint]", form);

    if (!password1 || !password2 || !hint) return;

    function updateHint() {
      if (!password2.value) {
        hint.textContent = "";
        return;
      }

      if (password1.value === password2.value) {
        hint.textContent = "Passwords match.";
        hint.classList.remove("is-error");
        hint.classList.add("is-success");
      } else {
        hint.textContent = "Passwords do not match.";
        hint.classList.remove("is-success");
        hint.classList.add("is-error");
      }
    }

    password1.addEventListener("input", updateHint);
    password2.addEventListener("input", updateHint);
  }

  function initForms() {
    qsa("form").forEach((form) => {
      enhanceFormFields(form);
      preventDoubleSubmit(form);
    });

    const createAlertForm = qs("#createAlertForm");
    if (createAlertForm) {
      autofocusFirstField(createAlertForm);
    }

    const loginForm = qs("#loginForm");
    if (loginForm) {
      autofocusFirstField(loginForm);
    }

    const registerForm = qs("#registerForm");
    if (registerForm) {
      autofocusFirstField(registerForm);
      initRegisterPasswordCheck(registerForm);
    }
  }

  document.addEventListener("DOMContentLoaded", initForms);
})();