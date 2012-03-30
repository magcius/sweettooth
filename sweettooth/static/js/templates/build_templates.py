#!/usr/bin/python

import json
import os
import os.path

compile_template = "c(%s)"

def _build_templates(directory):
    templates = {}
    for filename in os.listdir(directory):
        joined = os.path.join(directory, filename)
        name, ext = os.path.splitext(filename)
        if os.path.isdir(joined):
            templates[name] = _build_templates(joined)
        elif ext == ".mustache":
            f = open(joined, 'r')
            templates[name] = f.read().strip()
            f.close()
    return templates

def build_templates(directory):
    templates = _build_templates(directory)
    f = open(os.path.join(directory, 'templatedata.js'), 'w')
    f.write("""
"use strict";

define(%s);
""" % (json.dumps(templates),))
    f.close()

if __name__ == "__main__":
    templates_dir = os.path.realpath(os.path.dirname(__file__))
    build_templates(templates_dir)
