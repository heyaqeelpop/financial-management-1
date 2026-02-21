document.addEventListener("DOMContentLoaded", function () {

  // ---------- Income vs Expense ----------
  if (typeof totalIncome !== "undefined" && typeof totalExpense !== "undefined") {
    const canvas1 = document.getElementById("incomeExpenseChart");

    if (canvas1) {
      const income = totalIncome || 0;
      const expense = totalExpense || 0;
      const data = (income === 0 && expense === 0) ? [1, 0] : [income, expense];
      const labels = (income === 0 && expense === 0) ? ["No Data", ""] : ["Income", "Expense"];

      new Chart(canvas1.getContext("2d"), {
        type: "bar",
        data: {
          labels: labels,
          datasets: [{
            label: "Amount",
            data: data,
            backgroundColor: ["#36A2EB", "#FF6384"]
          }]
        },
        options: {
          plugins: {
            tooltip: {
              enabled: income !== 0 || expense !== 0
            }
          }
        }
      });
    }
  }

  // ---------- Expense by Category ----------
  if (typeof categoryData !== "undefined") {
    const canvas2 = document.getElementById("categoryChart");

    if (canvas2) {
      const labels = Object.keys(categoryData);
      const values = Object.values(categoryData);

      let chartData, chartLabels;

      if (values.length === 0 || values.every(v => v === 0)) {
        chartLabels = ["No Data"];
        chartData = [1];
      } else {
        chartLabels = labels;
        chartData = values;
      }

      new Chart(canvas2.getContext("2d"), {
        type: "pie",
        data: {
          labels: chartLabels,
          datasets: [{
            data: chartData,
            backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
          }]
        },
        options: {
          plugins: {
            tooltip: {
              enabled: values.length > 0
            },
            legend: {
              display: true
            }
          }
        }
      });
    }
  }

  // ---------- Monthly Analytics ----------
  const months = Object.keys(monthlyData);
  const incomeValues = months.map(m => monthlyData[m].income || 0);
  const expenseValues = months.map(m => monthlyData[m].expense || 0);

  const ctx3 = document.getElementById("monthlyChart");

  if (ctx3) {
    const hasData = incomeValues.some(v => v > 0) || expenseValues.some(v => v > 0);

    new Chart(ctx3.getContext("2d"), {
      type: "line",
      data: {
        labels: hasData ? months : ["No Data"],
        datasets: hasData ? [
          { label: "Income", data: incomeValues, tension: 0.3, borderColor: "#36A2EB", backgroundColor: "rgba(54,162,235,0.2)" },
          { label: "Expense", data: expenseValues, tension: 0.3, borderColor: "#FF6384", backgroundColor: "rgba(255,99,132,0.2)" }
        ] : [
          { label: "No Data", data: [1], borderColor: "#999", backgroundColor: "#ddd" }
        ]
      },
      options: {
        plugins: {
          tooltip: {
            enabled: hasData
          },
          legend: {
            display: true
          }
        }
      }
    });
  }
});

/* ✅ Global Chart Download */
function downloadChart(chartId) {
  const canvas = document.getElementById(chartId);

  if (!canvas) {
    alert("Chart not found!");
    return;
  }

  const link = document.createElement("a");
  link.href = canvas.toDataURL("image/png");
  link.download = chartId + ".png";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


// ---------- Financial Health Trend ----------
if (typeof healthTrendData !== "undefined") {
  const ctx = document.getElementById("healthTrendChart");

  if (ctx) {
    const months = Object.keys(healthTrendData);
    const scores = Object.values(healthTrendData);

    new Chart(ctx.getContext("2d"), {
      type: "line",
      data: {
        labels: months.length ? months : ["No Data"],
        datasets: [{
          label: "Health Score",
          data: scores.length ? scores : [0],
          tension: 0.3,
          borderColor: "#22c55e",
          backgroundColor: "rgba(34,197,94,0.2)",
          fill: true
        }]
      },
      options: {
        scales: {
          y: {
            min: 0,
            max: 100
          }
        },
        plugins: {
          tooltip: {
            enabled: scores.length > 0
          }
        }
      }
    });
  }
}

