// Utility Function to Format Currency
const formatCurrency = (amount) => `NPR ${parseFloat(amount).toFixed(2).toLocaleString()}`;

// 1. Rented vs Cancel Chart (Pie Chart)
const initializeRentedCancelChart = () => {
  const rentedCancelCtx = document.getElementById("rentedCancelChart").getContext("2d");
  return new Chart(rentedCancelCtx, {
    type: "doughnut",
    data: {
      labels: ["Rented", "Cancelled", "Pending"],
      datasets: [
        {
          data: [54, 20, 26], // Example data
          backgroundColor: ["#4CAF50", "#F44336", "#FF9800"], // Green, Red, Orange
          hoverBackgroundColor: ["#45d16a", "#ff6666", "#ffa640"], // Hover Colors
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom", // Move legend below the chart
        },
      },
    },
  });
};

// 2. Earning Summary Chart (Line Chart)
const initializeEarningChart = () => {
  const earningChartCtx = document.getElementById("earningChart").getContext("2d");
  return new Chart(earningChartCtx, {
    type: "line",
    data: {
      labels: ["May", "Jun", "Jul", "Aug", "Sep", "Oct"], // X-Axis Labels
      datasets: [
        {
          label: "Last 6 months",
          data: [100, 200, 150, 300, 250, 400], // Example data for this year
          borderColor: "#00aaff",
          backgroundColor: "rgba(0, 170, 255, 0.2)",
          fill: true,
          tension: 0.4,
        },
        {
          label: "Same period last year",
          data: [90, 180, 120, 270, 220, 360], // Example data for last year
          borderColor: "#f44336",
          backgroundColor: "rgba(244, 67, 54, 0.2)",
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom", // Move legend below the chart
        },
      },
      scales: {
        y: {
          beginAtZero: true, // Start Y-axis from 0
        },
      },
    },
  });
};

// 3. Dynamic Property Availability Filter
const initializePropertyFilter = () => {
  const propertyFilterButton = document.querySelector(".property-section .filter button");
  propertyFilterButton.addEventListener("click", () => {
    const propertyNumber = document.querySelector(".property-section .filter select").value;
    const selectedDate = document.querySelector(".property-section .filter input[type='date']").value;
    const selectedTime = document.querySelector(".property-section .filter input[type='time']").value;

    if (propertyNumber && selectedDate && selectedTime) {
      alert(
        `Filtering properties for:\nProperty Number: ${propertyNumber}\nDate: ${selectedDate}\nTime: ${selectedTime}`
      );
      // Add logic to fetch and display filtered data dynamically
    } else {
      alert("Please fill all the fields to filter properties.");
    }
  });
};

// 4. Dynamic Table Status Highlight
const initializeTableRowClick = () => {
  const tableBody = document.querySelector(".status-section table tbody");
  tableBody.addEventListener("click", (event) => {
    const row = event.target.closest("tr");
    if (row) {
      const clientName = row.querySelector("td:nth-child(3)").textContent;
      const status = row.querySelector("td:nth-child(4)").textContent;
      const earning = row.querySelector("td:nth-child(5)").textContent;

      alert(`Client: ${clientName}\nStatus: ${status}\nEarning: ${earning}`);
    }
  });
};

// 5. Add Dummy Data Dynamically to Table
const addDataToTable = (data) => {
  const tableBody = document.querySelector(".status-section table tbody");
  tableBody.innerHTML = ""; // Clear existing rows

  data.forEach((entry) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${entry.id}</td>
      <td>${entry.proNo}</td>
      <td>${entry.client}</td>
      <td class="status ${entry.status.toLowerCase()}">${entry.status}</td>
      <td>${formatCurrency(entry.earning)}</td>
      <td><button class="btn-details">Details</button></td>
    `;
    tableBody.appendChild(row);
  });
};

// 6. Initialize the Dashboard with Dummy Data
const initializeDashboard = () => {
  initializeRentedCancelChart();
  initializeEarningChart();
  initializePropertyFilter();
  initializeTableRowClick();

  const dummyData = [
    { id: "01", proNo: "6465", client: "Alex Norman", status: "Completed", earning: 35.44 },
    { id: "02", proNo: "5665", client: "Razib Rahman", status: "Pending", earning: 0.0 },
    { id: "03", proNo: "1755", client: "Luke Norton", status: "Cancelled", earning: 23.5 },
    { id: "04", proNo: "9001", client: "John Doe", status: "Completed", earning: 45.0 },
    { id: "05", proNo: "9015", client: "Jane Smith", status: "Pending", earning: 30.0 },
    { id: "06", proNo: "9020", client: "Sam Wilson", status: "Cancelled", earning: 10.0 },
  ];

  addDataToTable(dummyData);
};

// Run the Dashboard Initialization on Page Load
initializeDashboard();


// Function to get and format the current date and time
const updateCurrentDateTime = () => {
    const now = new Date();
    const options = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    };
    const formattedDateTime = now.toLocaleDateString("en-US", options);
    document.getElementById("currentDateTime").innerHTML = `<i class="fas fa-calendar-alt"></i> ${formattedDateTime}`;
  };
  
  // Update date and time on page load
  updateCurrentDateTime();
  
  // Refresh date and time every second
  setInterval(updateCurrentDateTime, 1000);
  