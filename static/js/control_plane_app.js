(function () {
  const DEFAULT_LOGIN_URL = "/api/platform-mod/login";

  function byId(id) {
    return document.getElementById(id);
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function showToast(message, type) {
    const toastContainer = byId("toast-container");
    if (!toastContainer || !message) {
      return;
    }

    const toast = document.createElement("div");
    const isError = type === "error";

    toast.className =
      "pointer-events-auto flex items-start gap-3 rounded-3xl border px-4 py-3 shadow-soft transition duration-200 " +
      (isError ? "border-rose-200 bg-rose-50 text-rose-800" : "border-emerald-200 bg-emerald-50 text-emerald-800");
    toast.innerHTML =
      '<div class="mt-0.5 h-2.5 w-2.5 rounded-full ' +
      (isError ? "bg-rose-500" : "bg-emerald-500") +
      '"></div><div class="min-w-0 flex-1"><p class="text-sm font-semibold">' +
      (isError ? "Action failed" : "Success") +
      '</p><p class="mt-1 text-sm leading-6">' +
      escapeHtml(message) +
      "</p></div>";

    toastContainer.appendChild(toast);

    window.setTimeout(function () {
      toast.classList.add("opacity-0", "translate-y-2");
      window.setTimeout(function () {
        toast.remove();
      }, 220);
    }, 3200);
  }

  function showModalBanner(form, message) {
    const banner = form.querySelector("[data-form-error]");
    if (!banner) {
      showToast(message, "error");
      return;
    }

    banner.textContent = message;
    banner.classList.remove("hidden");
  }

  function hideModalBanner(form) {
    const banner = form.querySelector("[data-form-error]");
    if (!banner) {
      return;
    }

    banner.textContent = "";
    banner.classList.add("hidden");
  }

  function extractFormPayload(form) {
    const payload = {};

    Array.from(form.elements).forEach(function (element) {
      if (!element.name || element.disabled) {
        return;
      }

      if (element.name === "csrfmiddlewaretoken" || element.name === "form_context") {
        return;
      }

      if (element.type === "checkbox") {
        payload[element.name] = element.checked;
        return;
      }

      if (element.type === "radio") {
        if (element.checked) {
          payload[element.name] = element.value;
        }
        return;
      }

      if (element.type === "file") {
        return;
      }

      payload[element.name] = element.value;
    });

    if (payload.password === "") {
      delete payload.password;
    }

    return payload;
  }

  async function requestJson(url, options) {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: {
        ...(options && options.headers ? options.headers : {}),
      },
    });

    const contentType = response.headers.get("content-type") || "";
    let data = null;
    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const error = new Error("Request failed");
      error.data = data;
      error.response = response;
      throw error;
    }

    return { response, data };
  }

  function stringifyError(data) {
    if (!data) {
      return "We could not complete that request.";
    }

    if (typeof data === "string") {
      return data;
    }

    if (data.detail) {
      return data.detail;
    }

    if (data.error) {
      return data.error;
    }

    if (Array.isArray(data)) {
      return data.join(" ");
    }

    if (typeof data === "object") {
      const messages = [];
      Object.entries(data).forEach(function ([field, value]) {
        const normalized = Array.isArray(value) ? value.join(" ") : String(value);
        messages.push(field === "non_field_errors" ? normalized : `${field}: ${normalized}`);
      });
      return messages.join(" ");
    }

    return "We could not complete that request.";
  }

  function openModal(url) {
    const modal = byId("modal-body");
    if (!modal || !url) {
      return;
    }

    modal.innerHTML =
      '<div class="fixed inset-0 z-50 flex items-center justify-center p-4"><div class="rounded-3xl border border-white/10 bg-white px-5 py-4 text-slate-700 shadow-soft">Loading…</div></div>';

    fetch(url, {
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (response) {
        if (response.redirected || response.url.includes("/accounts/login/")) {
          window.location.href = response.url;
          return null;
        }
        if (!response.ok) {
          throw new Error("Could not open modal");
        }
        return response.text();
      })
      .then(function (html) {
        if (html === null) {
          return;
        }
        modal.innerHTML = html;
      })
      .catch(function () {
        modal.innerHTML = "";
        showToast("The form could not be opened. Please try again.", "error");
      });
  }

  function closeModal() {
    const modal = byId("modal-body");
    if (modal) {
      modal.innerHTML = "";
    }
  }

  async function submitApiForm(form) {
    const apiUrl = form.dataset.apiUrl || form.getAttribute("action");
    const apiMethod = (form.dataset.apiMethod || form.getAttribute("method") || "post").toUpperCase();
    const successMessage = form.dataset.successMessage || "Saved successfully.";
    const payload = extractFormPayload(form);
    const submitButton = form.querySelector('[type="submit"]');

    hideModalBanner(form);
    if (submitButton) {
      submitButton.disabled = true;
    }

    try {
      await requestJson(apiUrl, {
        method: apiMethod,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      showToast(successMessage, "success");
      closeModal();
      window.setTimeout(function () {
        window.location.reload();
      }, 600);
    } catch (error) {
      const message = stringifyError(error.data);
      showModalBanner(form, message);
      showToast(message, "error");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }
  }

  function bindSidebar() {
    const body = document.body;
    const sidebar = byId("sidebar");
    const overlay = byId("sidebar-overlay");
    const toggleButtons = document.querySelectorAll("[data-sidebar-toggle]");

    function openSidebar() {
      body.classList.add("sidebar-open");
      if (overlay) {
        overlay.classList.remove("hidden");
      }
      if (sidebar) {
        sidebar.classList.remove("-translate-x-full");
      }
    }

    function closeSidebar() {
      body.classList.remove("sidebar-open");
      if (overlay) {
        overlay.classList.add("hidden");
      }
      if (sidebar) {
        sidebar.classList.add("-translate-x-full");
      }
    }

    function toggleSidebar() {
      const isMobile = window.matchMedia("(max-width: 1279px)").matches;
      if (isMobile) {
        if (body.classList.contains("sidebar-open")) {
          closeSidebar();
        } else {
          openSidebar();
        }
        return;
      }

      body.classList.toggle("sidebar-collapsed");
      localStorage.setItem(
        "sidebar-state",
        body.classList.contains("sidebar-collapsed") ? "collapsed" : "expanded"
      );
    }

    const savedState = localStorage.getItem("sidebar-state");
    if (savedState === "collapsed") {
      body.classList.add("sidebar-collapsed");
    }

    toggleButtons.forEach(function (button) {
      button.addEventListener("click", toggleSidebar);
    });

    if (overlay) {
      overlay.addEventListener("click", closeSidebar);
    }

    window.addEventListener("resize", function () {
      if (window.matchMedia("(min-width: 1280px)").matches) {
        closeSidebar();
      }
    });
  }

  function bindActionMenus() {
    function resetMenuPlacement(menu) {
      const panel = menu.querySelector("[data-action-menu-panel]");
      if (!panel) {
        return;
      }

      panel.classList.remove("bottom-full", "mb-2", "top-auto", "mt-0");
      panel.classList.add("top-full", "mt-2");
    }

    function flipMenuIfNeeded(menu) {
      const panel = menu.querySelector("[data-action-menu-panel]");
      if (!panel) {
        return;
      }

      resetMenuPlacement(menu);

      requestAnimationFrame(function () {
        const bounds = panel.getBoundingClientRect();
        const viewportHeight = window.innerHeight;

        if (bounds.bottom > viewportHeight - 12 && bounds.top > bounds.height + 12) {
          panel.classList.remove("top-full", "mt-2");
          panel.classList.add("bottom-full", "mb-2", "top-auto", "mt-0");
        }
      });
    }

    document.querySelectorAll("details[data-action-menu]").forEach(function (menu) {
      menu.addEventListener("toggle", function () {
        if (menu.open) {
          document.querySelectorAll("details[data-action-menu]").forEach(function (otherMenu) {
            if (otherMenu !== menu) {
              otherMenu.removeAttribute("open");
              resetMenuPlacement(otherMenu);
            }
          });

          flipMenuIfNeeded(menu);
        } else {
          resetMenuPlacement(menu);
        }
      });
    });

    document.addEventListener("click", function (event) {
      const activeMenu = event.target.closest("details[data-action-menu]");
      document.querySelectorAll("details[data-action-menu]").forEach(function (menu) {
        if (!activeMenu || menu !== activeMenu) {
          menu.removeAttribute("open");
          resetMenuPlacement(menu);
        }
      });
    });
  }

  function bindToastTriggers() {
    document.body.addEventListener("showToast", function (event) {
      const detail = event.detail || {};
      showToast(detail.message, detail.type || "success");
    });
  }

  function bindModalTriggers() {
    document.addEventListener("click", function (event) {
      const modalTrigger = event.target.closest("[data-modal-url]");
      if (modalTrigger) {
        event.preventDefault();
        openModal(modalTrigger.dataset.modalUrl);
        return;
      }

      const closeModalTrigger = event.target.closest("[data-close-modal]");
      if (closeModalTrigger) {
        event.preventDefault();
        closeModal();
        return;
      }

      const logoutTrigger = event.target.closest("[data-logout-url]");
      if (logoutTrigger) {
        event.preventDefault();
        window.location.href = logoutTrigger.dataset.logoutUrl;
      }
    });

    document.addEventListener("submit", function (event) {
      const form = event.target.closest("form[data-api-form]");
      if (!form) {
        return;
      }

      event.preventDefault();
      submitApiForm(form);
    });
  }

  function bindLoginForm() {
    const loginForm = byId("platform-login-form");
    if (!loginForm) {
      return;
    }

    loginForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const submitButton = loginForm.querySelector('[type="submit"]');
      const username = loginForm.querySelector('[name="username"]');
      const password = loginForm.querySelector('[name="password"]');
      const banner = loginForm.querySelector("[data-form-error]");

      if (banner) {
        banner.classList.add("hidden");
        banner.textContent = "";
      }

      if (submitButton) {
        submitButton.disabled = true;
      }

      try {
        await requestJson(loginForm.dataset.apiUrl || DEFAULT_LOGIN_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: username ? username.value : "",
            password: password ? password.value : "",
          }),
        });

        window.location.href = loginForm.dataset.nextUrl || "/dashboard";
      } catch (error) {
        const message = stringifyError(error.data);
        if (banner) {
          banner.textContent = message;
          banner.classList.remove("hidden");
        }
        showToast(message, "error");
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
        }
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindSidebar();
    bindActionMenus();
    bindToastTriggers();
    bindModalTriggers();
    bindLoginForm();
  });
})();
