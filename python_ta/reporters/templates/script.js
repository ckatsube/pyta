$("body").on("click", ".slider", function () {
    $(this).parent().next().toggleClass("hide-and-maintain-width");
});

$.get('creationTime', function(originalPageDate, status) {
    setInterval(function() {
        $.get('creationTime', function(currentPageDate, status) {
            if (originalPageDate !== currentPageDate) {
                window.location.reload()
            }
        })
    }, 1000)
})
