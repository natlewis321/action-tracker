document.addEventListener('DOMContentLoaded', function () {
    var chartStatus = document.getElementById('chartStatus');
    if (!chartStatus) return;

    var COLORS = ['#2c3e80', '#e67e22', '#27ae60', '#7f8c8d', '#c0392b', '#2980b9', '#8e44ad', '#16a085'];
    var PRIORITY_COLORS = { Critical: '#c0392b', High: '#e67e22', Medium: '#2980b9', Low: '#27ae60' };
    var AGEING_COLORS = ['#27ae60', '#e67e22', '#c0392b', '#7b241c'];

    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.position = 'bottom';

    var chartParams = new URLSearchParams(window.location.search);
    var chartUrl = '/api/chart-data' + (chartParams.toString() ? '?' + chartParams.toString() : '');

    fetch(chartUrl)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            new Chart(chartStatus, {
                type: 'doughnut',
                data: {
                    labels: data.by_status.map(function (d) { return d.name; }),
                    datasets: [{ data: data.by_status.map(function (d) { return d.count; }), backgroundColor: COLORS }]
                },
                options: { responsive: true, plugins: { legend: { position: 'right' } } }
            });

            new Chart(document.getElementById('chartCategory'), {
                type: 'bar',
                data: {
                    labels: data.by_category.map(function (d) { return d.name; }),
                    datasets: [{ label: 'Actions', data: data.by_category.map(function (d) { return d.count; }), backgroundColor: COLORS[0] }]
                },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
            });

            var priorityLabels = data.by_priority.map(function (d) { return d.priority; });
            new Chart(document.getElementById('chartPriority'), {
                type: 'doughnut',
                data: {
                    labels: priorityLabels,
                    datasets: [{ data: data.by_priority.map(function (d) { return d.count; }), backgroundColor: priorityLabels.map(function (l) { return PRIORITY_COLORS[l] || '#999'; }) }]
                },
                options: { responsive: true, plugins: { legend: { position: 'right' } } }
            });

            var ageingOrder = ['0-30 days', '31-60 days', '61-90 days', '90+ days'];
            var ageingData = ageingOrder.map(function (band) {
                var found = data.ageing.find(function (d) { return d.band === band; });
                return found ? found.count : 0;
            });
            new Chart(document.getElementById('chartAgeing'), {
                type: 'bar',
                data: {
                    labels: ageingOrder,
                    datasets: [{ label: 'Open Actions', data: ageingData, backgroundColor: AGEING_COLORS }]
                },
                options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
            });

            new Chart(document.getElementById('chartCommittee'), {
                type: 'bar',
                data: {
                    labels: data.by_committee.map(function (d) { return d.name; }),
                    datasets: [{ label: 'Actions', data: data.by_committee.map(function (d) { return d.count; }), backgroundColor: COLORS[5] }]
                },
                options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } } }
            });

            new Chart(document.getElementById('chartOverdueOwner'), {
                type: 'bar',
                data: {
                    labels: data.overdue_by_owner.map(function (d) { return d.name; }),
                    datasets: [{ label: 'Overdue', data: data.overdue_by_owner.map(function (d) { return d.count; }), backgroundColor: COLORS[4] }]
                },
                options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } } }
            });
        });
});
