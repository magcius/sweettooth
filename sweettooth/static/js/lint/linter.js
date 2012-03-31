#!/usr/bin/env gjs

const Gio = imports.gi.Gio;

imports.searchPath.push(".");
const JSLint = imports.jslint;

const options = { white: true, vars: true, nomen: true, plusplus: true,
                  'continue': true,
                  predef: ['define', 'document', 'window'] };
const vendorFiles = ["mustache.js", "require.js"];

function scanJSFiles(dir) {
    let fileEnum = dir.enumerate_children('standard::*', Gio.FileQueryInfoFlags.NONE, null);
    let info;
    let errors = {};

    while ((info = fileEnum.next_file(null)) != null) {
        let name = info.get_name();
        if (!name.match(/\.js$/))
            continue;
        if (name.match(/^jquery/))
            continue;
        if (vendorFiles.indexOf(name) >= 0)
            continue;

        let jsFile = dir.get_child(info.get_name());
        let [success, contents, etag] = jsFile.load_contents(null);
        let linted = JSLint.JSLINT(contents.toString(), options);
        errors[jsFile.get_path()] = JSLint.JSLINT.errors;
    }

    return errors;
}

function main() {
    let errors = scanJSFiles(Gio.file_new_for_path(".."));
    print(JSON.stringify(errors, null, 4));
}

main();
