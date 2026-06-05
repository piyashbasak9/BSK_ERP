// Global Tabulator helpers
function initGrid(elementId, ajaxUrl, columns) {
    return new Tabulator("#" + elementId, {
        ajaxURL: ajaxUrl,
        layout: "fitColumns",
        pagination: "remote",
        paginationSize: 20,
        columns: columns,
        downloadDataFormatter: function(data) { return data; },
        downloadReady: function(data, blob) { return blob; }
    });
}