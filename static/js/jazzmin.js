// ----------------------------------------------------------
// Handling Form Groups (Multiple columns)
// ----------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
  document
    .querySelectorAll(".form-group .row > label.col-sm-3")
    .forEach(function (label) {
      label.classList.remove("col-sm-3");
      label.classList.add("col-sm-1-5");
    });
});

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".form-group .row").forEach(function (row) {
    const children = Array.from(row.children);

    children.forEach((el, index) => {
      if (
        el.tagName === "LABEL" &&
        index > 0 &&
        children[index - 1].classList.contains("fieldBox")
      ) {
        el.style.marginLeft = "80px";
        el.classList.add("col-sm-1-5");
      }
    });
  });
});

// ----------------------------------------------------------
// Remove Eye Icon from Dropdown (Related Field)
// ----------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
  document
    .querySelectorAll(".related-widget-wrapper-link.view-related")
    .forEach((el) => el.remove());
});

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("input[type='email']").forEach(function (el) {
    el.classList.add("vTextField");
  });
});

// ----------------------------------------------------------
// Sidebar Search Panel
// ----------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
  const userPanel = document.querySelector("#jazzy-sidebar .user-panel");

  if (!userPanel) return;

  // replace entire content
  userPanel.innerHTML = `
        <div class="sidebar-search-wrapper">
            <input type="text" class="sidebar-search" placeholder="Search menu...">
        </div>
    `;
});

document.addEventListener("DOMContentLoaded", function () {
  const input = document.querySelector(".sidebar-search");
  if (!input) return;

  const items = document.querySelectorAll(
    "#jazzy-sidebar .nav-sidebar .nav-item",
  );

  input.addEventListener("input", function () {
    const query = this.value.toLowerCase().trim();

    items.forEach((item) => {
      const link = item.querySelector(".nav-link");
      if (!link) return;

      const text = link.innerText.toLowerCase();

      if (query === "") {
        item.style.display = "";
        return;
      }

      const match = text.includes(query);

      item.style.display = match ? "" : "none";
    });
  });
});
