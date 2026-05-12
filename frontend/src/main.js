import htmx from "htmx.org";
import Alpine from "alpinejs";
import ApexCharts from "apexcharts";

window.htmx = htmx;
window.Alpine = Alpine;
window.ApexCharts = ApexCharts;

Alpine.start();

// Charts hydrate from <script type="application/json" data-chart-id="..."> blocks.
document.querySelectorAll("script[data-chart-id]").forEach((node) => {
  const target = document.querySelector(`[data-chart-target="${node.dataset.chartId}"]`);
  if (!target) return;
  const options = JSON.parse(node.textContent);
  new ApexCharts(target, options).render();
});

// CSRF: htmx auto-includes the cookie on same-origin requests; ensure header for non-form.
document.body.addEventListener("htmx:configRequest", (evt) => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (token) evt.detail.headers["X-CSRFToken"] = token;
});
