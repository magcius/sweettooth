require(['extensionUtils', 'jquery', 'test/qunit'], function(extensionUtils) {

    var versionCheck = extensionUtils.versionCheck;
    test("versionCheck", function() {
        equal(versionCheck(["3.2.1"], "3.2.1"), true, "testing basic capability");
        equal(versionCheck(["3.3.1"], "3.2.1"), false);

        equal(versionCheck(["3.3.1", "3.2.1"], "3.2.1"), true, "multiple versions");
        equal(versionCheck(["3.3.1", "3.3.2"], "3.2.1"), false);

        equal(versionCheck(["3.2"], "3.2.1"), true, "stable release checking");
        equal(versionCheck(["3.3"], "3.3.1"), false);
    });

    var grabProperExtensionVersion = extensionUtils.grabProperExtensionVersion;
    test("grabProperExtensionVersion", function() {
        var map = { "3.0": { version: 1, pk: 1 },
                    "3.0.1": { version: 2, pk: 2 },
                    "3.2.1": { version: 3, pk: 3 },
                    "3.2": { version: 4, pk: 4 },
                    "3.3": { version: 5, pk: 5 },
                    "3.3.1": { version: 6, pk: 6 } };

        equal(grabProperExtensionVersion(map, "3.4.0"), null);
        equal(grabProperExtensionVersion(map, "3.0.0").version, 1);
        equal(grabProperExtensionVersion(map, "3.0.1").version, 2);
        equal(grabProperExtensionVersion(map, "3.2.0").version, 4);
        equal(grabProperExtensionVersion(map, "3.2.1").version, 4);
        equal(grabProperExtensionVersion(map, "3.3.0"), null, "stable release checking");
        equal(grabProperExtensionVersion(map, "3.3.1").version, 6);
    });
});
