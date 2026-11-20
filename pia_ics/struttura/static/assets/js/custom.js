"use strict";
$(function () {
    // index.html
    /*chart1();
    $('#table_appuntamenti_index').DataTable({
        "language": {
            "url": "https://cdn.datatables.net/plug-ins/1.10.20/i18n/Italian.json"
        },
    });
    $('#table_contratti_index').DataTable({
        "language": {
            "url": "https://cdn.datatables.net/plug-ins/1.10.20/i18n/Italian.json"
        },
    });*/
});

function chart1() {

    var options = {
        series: [{
            name: 'Dollari al barile',
            data: valori_list
        }],
        chart: {
            type: 'area',
            stacked: false,
            height: 350,
            zoom: {
                type: 'x',
                enabled: true,
                autoScaleYaxis: true
            },
            toolbar: {
                autoSelected: 'zoom'
            }
        },
        labels: date_list,
        markers: {
            size: 0,
        }
        ,
        fill: {
            type: 'gradient',
            gradient:
                {
                    shadeIntensity: 1,
                    inverseColors:
                        false,
                    opacityFrom:
                        0.5,
                    opacityTo:
                        0,
                    stops:
                        [0, 90, 100]
                },
        }
        ,
        yaxis: {
            labels: {
                formatter: function (val) {
                    return val;
                },
            },
            title: {
                text: 'Quantità'
            },
        },
        xaxis: {
            type: 'datetime',
        },
        tooltip: {
            shared: false,
            y:
                {
                    formatter: function (val) {
                        return val;
                    }
                }
        }
    };

    var options = {
        series: [{
            name: "Premio",
            data: valori_list,
        }],
        chart: {
            type: 'area',
            height: 350,
            zoom: {
                enabled: false
            }
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'straight'
        },
        subtitle: {
            text: '',
            align: 'left'
        },
        labels: date_list,
        xaxis: {
            labels: {
                datetimeFormatter: {
                    year: 'yyyy',
                    month: 'MMM \'yy',
                    day: 'dd MMM',
                    hour: 'HH:mm',
                }
            }
        },
        yaxis: {
            opposite: false
        },
        legend: {
            horizontalAlign: 'left'
        }
    };

    var chart = new ApexCharts(document.querySelector("#chart_petrolio"), options);
    chart.render();
}
