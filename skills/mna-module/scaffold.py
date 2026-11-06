#!/usr/bin/env python3
"""Scaffold a version-correct Odoo module.

    python3 scaffold.py --name stock_alert --version 18.0 --model stock.alert
    python3 scaffold.py --name stock_alert --version 16.0 --dry-run

Writes the form that the target version accepts: attrs only on 16.0, <list>
instead of <tree> from 18.0, _compute_display_name instead of name_get from
17.0. Creates files and nothing else. Installs nothing, touches no database.
"""

import argparse
import os
import sys

SUPPORTED = ["16.0", "17.0", "18.0", "19.0"]


def major(version):
    return int(str(version).split(".")[0])


def list_tag(version):
    return "list" if major(version) >= 18 else "tree"


def view_mode(version):
    return "list,form" if major(version) >= 18 else "tree,form"


def invisible_attr(version, expr):
    if major(version) >= 17:
        return 'invisible="%s"' % expr
    return """attrs="{'invisible': [('state', '!=', 'draft')]}\"""" if expr else ""


MANIFEST = '''\
{{
    "name": "{title}",
    "version": "{version}.1.0.0",
    "category": "{category}",
    "summary": "{summary}",
    "author": "{author}",
    "website": "{website}",
    "license": "{license}",
    "depends": [{depends}],
    "data": [
        "security/ir.model.access.csv",
        "views/{model_file}_views.xml",
    ],
    "installable": True,
    "application": False,
}}
'''

MODEL = '''\
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class {cls}(models.Model):
    _name = "{model}"
    _description = "{title}"
    _order = "id desc"

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        default="draft",
        required=True,
        tracking=True,
    )
    note = fields.Text()

{display_name}
    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not record.name.strip():
                raise ValidationError(_("The name cannot be blank."))
'''

DISPLAY_NEW = '''\
    @api.depends("name", "state")
    def _compute_display_name(self):
        for record in self:
            record.display_name = "%s (%s)" % (record.name, record.state)

'''

DISPLAY_OLD = '''\
    def name_get(self):
        return [(r.id, "%s (%s)" % (r.name, r.state)) for r in self]

'''

VIEWS = '''\
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <record id="{model_file}_view_{tag}" model="ir.ui.view">
        <field name="name">{model}.{tag}</field>
        <field name="model">{model}</field>
        <field name="arch" type="xml">
            <{tag}>
                <field name="name"/>
                <field name="state"/>
                <field name="company_id" groups="base.group_multi_company"/>
            </{tag}>
        </field>
    </record>

    <record id="{model_file}_view_form" model="ir.ui.view">
        <field name="name">{model}.form</field>
        <field name="model">{model}</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="state"/>
                        <field name="company_id" groups="base.group_multi_company"/>
                    </group>
                    <group {note_visibility}>
                        <field name="note"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="{model_file}_action" model="ir.actions.act_window">
        <field name="name">{title}</field>
        <field name="res_model">{model}</field>
        <field name="view_mode">{view_mode}</field>
    </record>

</odoo>
'''

ACCESS = '''\
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_{model_file}_user,{model}.user,model_{model_file},base.group_user,1,1,1,0
access_{model_file}_manager,{model}.manager,model_{model_file},base.group_system,1,1,1,1
'''


def build(args):
    version = args.version
    name = args.name.strip().strip("_")
    module = "%s%s" % (args.prefix, name) if not name.startswith(args.prefix) else name
    model = args.model or "%s.%s" % (args.prefix.strip("_"), name.replace("_", "."))
    model_file = model.replace(".", "_")
    cls = "".join(p.capitalize() for p in model.split("."))
    title = args.title or name.replace("_", " ").title()
    tag = list_tag(version)

    files = {}
    files["__init__.py"] = "from . import models\n"
    files["models/__init__.py"] = "from . import %s\n" % model_file
    files["__manifest__.py"] = MANIFEST.format(
        title=title,
        version=version,
        category=args.category,
        summary=args.summary or title,
        author=args.author,
        website=args.website,
        license=args.license,
        depends=", ".join('"%s"' % d for d in args.depends.split(",") if d.strip()),
        model_file=model_file,
    )
    files["models/%s.py" % model_file] = MODEL.format(
        cls=cls,
        model=model,
        title=title,
        display_name=DISPLAY_NEW if major(version) >= 17 else DISPLAY_OLD,
    )
    files["views/%s_views.xml" % model_file] = VIEWS.format(
        model=model,
        model_file=model_file,
        title=title,
        tag=tag,
        view_mode=view_mode(version),
        note_visibility=invisible_attr(version, "state == 'draft'"),
    )
    files["security/ir.model.access.csv"] = ACCESS.format(
        model=model, model_file=model_file
    )
    return module, files


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name", required=True, help="module name without the prefix")
    p.add_argument("--version", required=True, choices=SUPPORTED)
    p.add_argument("--prefix", default="mna_")
    p.add_argument("--model", default="", help="dotted model name")
    p.add_argument("--title", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--author", default="Mohammad Najjarine")
    p.add_argument("--website", default="")
    p.add_argument("--license", default="LGPL-3")
    p.add_argument("--category", default="Technical")
    p.add_argument("--depends", default="base")
    p.add_argument("--out", default=".", help="where to create the module folder")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    module, files = build(args)
    root = os.path.join(args.out, module)

    if args.dry_run:
        print("would create %s/ with %d files for Odoo %s"
              % (root, len(files), args.version))
        for path in sorted(files):
            print("  %s" % path)
        print("\nlist tag: <%s>   view_mode: %s   display name: %s"
              % (list_tag(args.version), view_mode(args.version),
                 "_compute_display_name" if major(args.version) >= 17 else "name_get"))
        return 0

    if os.path.exists(root):
        print("refused: %s already exists" % root)
        return 2

    for path, content in files.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content)

    print("created %s/ with %d files for Odoo %s" % (root, len(files), args.version))
    for path in sorted(files):
        print("  %s" % path)
    print("\nnext: odoo-bin -d <db> -i %s --stop-after-init" % module)
    print("read the log. a warning is not a clean install.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
