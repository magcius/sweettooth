
"use strict";

define({
  "extensions": {
    "configure_button": "<span class=\"launch-prefs-button\">Configure</span>", 
    "error_report_template": "What's wrong?\n\n\n\nWhat have you tried?\n\n\n\nAutomatically detected errors:\n\n{{#errors}}\n  {{.}}\n\n================\n{{/errors}}\n{{^errors}}\nGNOME Shell Extensions did not detect any errors with this extension.\n{{/errors}}\n\nVersion information:\n\n    Shell version: {{sv}}\n    Extension version: {{#ev}}{{ev}}{{/ev}}{{^ev}}Unknown{{/ev}}", 
    "info": "<div class=\"extension\" data-uuid=\"{{uuid}}\">\n  {{>extensions.info_contents}}\n</div>", 
    "info_contents": "<div class=\"switch\"></div>\n<img class=\"icon\" src=\"{{icon}}\">\n<h3 class=\"extension-name\">\n  {{#link}}\n    <a href=\"{{link}}\" class=\"title-link\"> <img src=\"{{icon}}\" class=\"icon\"> {{name}} </a>\n  {{/link}}\n  {{^link}}\n  {{name}}\n  {{/link}}\n</h3>\n{{#creator}}\n  <span class=\"author\">by <a href=\"{{creator_url}}\"> {{creator}} </a></span>\n{{/creator}}\n{{#want_configure}}\n  {{>extensions.configure_button}}\n{{/want_configure}}\n<p class=\"description\">\n  {{description}}\n</p>\n{{#want_uninstall}}\n  <button class=\"uninstall\" title=\"Uninstall\">Uninstall</button>\n{{/want_uninstall}}", 
    "info_list": "<ul class=\"extensions\">\n{{#extensions}}\n  <li class=\"extension\" data-svm=\"{{shell_version_map}}\">\n    {{>extensions.info_contents}}\n  </li>\n{{/extensions}}\n</ul>", 
    "uninstall": "You uninstalled <b>{{name}}. <a href=\"#\">Undo?</a>"
  }, 
  "messages": {
    "cannot_list_errors": "GNOME Shell Extensions cannot automatically detect any errors.", 
    "cannot_list_local": "GNOME Shell Extensions cannot list your installed extensions.", 
    "dummy_proxy": "You do not appear to have an up to date version of GNOME3. You won't be able to install extensions from here. See the <a href=\"about/#old-version\">about page</a> for more information."
  }, 
  "paginator": {
    "loading_page": "<div class=\"loading-page\">\n  Loading page... please wait.\n</div>"
  }
});
