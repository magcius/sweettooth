#!/usr/bin/python

import json
import os
import os.path

def _build_templates(directory):
    templates = {}
    for path, dirs, files in os.walk(directory):
        relpath = os.path.relpath(path, directory)
        path_parts = relpath.split(os.path.sep)
        for filename in files:
            name, ext = os.path.splitext(filename)
            if ext != ".mustache":
                continue

            with open(os.path.join(path, filename)) as f:
                template = f.read().strip()
            full_name = '/'.join(path_parts + [name])
            templates[full_name] = template
    return templates

def build_templates(directory):
    templates = _build_templates(directory)
    f = open(os.path.join(directory, 'templatedata.js'), 'w')
    f.write("""
"use strict";

define(%s);
""" % (json.dumps(templates, sort_keys=True, indent=2),))
    f.close()

if __name__ == "__main__":
    templates_dir = os.path.realpath(os.path.dirname(__file__))
    build_templates(templates_dir)
