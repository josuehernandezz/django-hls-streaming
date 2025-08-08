(function() {
  function toggleFields() {
    var src = document.getElementById("id_source_type");
    if (!src) return;

    var serverRow = document.querySelector(".form-row.field-server_path, .field-server_path");
    var uploadRow = document.querySelector(".form-row.field-video, .field-video");

    var isServer = src.value === "server";

    if (serverRow) serverRow.style.display = isServer ? "" : "none";
    if (uploadRow) uploadRow.style.display = isServer ? "none" : "";
  }

  document.addEventListener("DOMContentLoaded", function() {
    var src = document.getElementById("id_source_type");
    if (src) {
      toggleFields();
      src.addEventListener("change", toggleFields);
    }
  });
})();