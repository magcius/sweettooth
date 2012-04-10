require(['paginatorUtils', 'jquery', 'test/qunit'], function(paginatorUtils) {

    function validateModel(page, numPages, context, expected) {
        var model = [];
        var html = paginatorUtils.buildPaginator(page, numPages, context);
        html.find('.paginator-content').children().each(function() {
            if ($(this).hasClass("prev") || $(this).hasClass("next"))
                return;

            model.push($(this).text());
        });
        deepEqual(model, expected);
    }

    test("testModel", function() {
        validateModel(1, 1, 3, ['1']);
        validateModel(1, 2, 3, ['1', '2']);
        validateModel(1, 3, 3, ['1', '2', '3']);
        validateModel(1, 4, 3, ['1', '2', '3', '4']);
        validateModel(1, 5, 3, ['1', '2', '3', '4', '5']);
        validateModel(1, 6, 3, ['1', '2', '3', '4', '5', '6']);
        validateModel(1, 7, 3, ['1', '2', '3', '4', '...', '7']);
        validateModel(1, 8, 3, ['1', '2', '3', '4', '...', '8']);
        validateModel(1, 9, 3, ['1', '2', '3', '4', '...', '9']);

        validateModel(1, 5, 3, ['1', '2', '3', '4', '5']);
        validateModel(2, 5, 3, ['1', '2', '3', '4', '5']);
        validateModel(3, 5, 3, ['1', '2', '3', '4', '5']);
        validateModel(4, 5, 3, ['1', '2', '3', '4', '5']);
        validateModel(5, 5, 3, ['1', '2', '3', '4', '5']);

        validateModel(3, 10, 3, ['1', '2', '3', '4', '5', '6', '...', '10']);
        validateModel(4, 10, 3, ['1', '2', '3', '4', '5', '6', '7', '...', '10']);
        validateModel(5, 10, 3, ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']);
        validateModel(6, 10, 3, ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']);
        validateModel(7, 10, 3, ['1', '...', '4', '5', '6', '7', '8', '9', '10']);

        validateModel(1, 1, 2, ['1']);
        validateModel(1, 2, 2, ['1', '2']);
        validateModel(1, 3, 2, ['1', '2', '3']);
        validateModel(1, 4, 2, ['1', '2', '3', '4']);
        validateModel(1, 5, 2, ['1', '2', '3', '4', '5']);
        validateModel(1, 6, 2, ['1', '2', '3', '...', '6']);
        validateModel(1, 7, 2, ['1', '2', '3', '...', '7']);
        validateModel(1, 8, 2, ['1', '2', '3', '...', '8']);
        validateModel(1, 9, 2, ['1', '2', '3', '...', '9']);
    });

});
