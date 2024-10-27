<head>
    <!-- Other meta tags and links -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    var ctx = document.getElementById('myChart').getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'bar',  // You can change this to 'line', 'pie', etc.
        data: {
            labels: ['January', 'February', 'March', 'April', 'May', 'June'], // X-axis labels
            datasets: [{
                label: 'Sales for 2024 (in USD)',
                data: [12000, 15000, 8000, 19000, 13000, 17000], // Y-axis data points
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
</script>
</head>

