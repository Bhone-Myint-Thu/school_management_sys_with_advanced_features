document.querySelectorAll("canvas.chart").forEach((canvas) => {
  const labels = JSON.parse(canvas.dataset.labels || "[]");
  const values = JSON.parse(canvas.dataset.values || "[]");
  if (!window.Chart || labels.length === 0) return;
  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Marks",
        data: values,
        borderColor: "#2e5fa3",
        backgroundColor: "rgba(0, 166, 223, .18)",
        tension: .35,
        fill: true
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
});
